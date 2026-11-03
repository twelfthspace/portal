-- Balances, ledger and the admin actions that change money.
-- Every action that needs a reason sets app.reason so the audit trigger records it.

create function public.add_business_days(d date, n int) returns date
language sql immutable set search_path = '' as $$
  select case when n <= 0 then d else (
    select x::date from generate_series(d + 1, d + n * 2 + 7, interval '1 day') as x
    where extract(isodow from x) < 6
    order by x offset n - 1 limit 1)
  end;
$$;

-- Payment snapshot: copy the owning partner and current rate onto the row.
create function public.payments_before_insert() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_partner uuid; v_rate int; v_status public.project_status;
begin
  select c.partner_id, p.rate_bp, p.status into v_partner, v_rate, v_status
  from public.projects p join public.clients c on c.id = p.client_id
  where p.id = new.project_id;
  if not found then raise exception 'Project not found'; end if;
  if v_status = 'cancelled' then raise exception 'This project is cancelled.'; end if;
  if new.received_on > current_date then raise exception 'The date received cannot be in the future.'; end if;
  new.partner_id := v_partner;
  new.rate_bp := v_rate;
  new.refunded := 0;
  new.reversed := false;
  new.recorded_by := auth.uid();
  return new;
end $$;
create trigger payments_snapshot before insert on public.payments
  for each row execute function public.payments_before_insert();

create view public.partner_balances with (security_invoker = true) as
with s as (select hold_days from public.settings where id = 1),
e as (
  select partner_id,
         sum(commission)::bigint as commission,
         (sum(commission) filter (
            where public.add_business_days(received_on, (select hold_days from s)) > current_date))::bigint as held
  from public.payments group by partner_id),
a as (select partner_id, sum(amount)::bigint as adj from public.adjustments group by partner_id),
o as (select partner_id, sum(amount)::bigint as paid from public.payouts where not voided group by partner_id)
select pr.id as partner_id,
       pr.full_name,
       coalesce(e.commission, 0) + coalesce(a.adj, 0) as earned,
       coalesce(o.paid, 0) as paid,
       coalesce(e.held, 0) as held,
       coalesce(e.commission, 0) + coalesce(a.adj, 0) - coalesce(o.paid, 0) as balance,
       greatest(0, coalesce(e.commission, 0) + coalesce(a.adj, 0) - coalesce(o.paid, 0) - coalesce(e.held, 0)) as available
from public.profiles pr
left join e on e.partner_id = pr.id
left join a on a.partner_id = pr.id
left join o on o.partner_id = pr.id
where pr.role = 'partner';

create view public.ledger with (security_invoker = true) as
select p.received_on as on_date, p.partner_id,
       case when p.reversed then 'reversed' else 'accrual' end as kind,
       pj.name || ' · ' || p.reference as detail, p.commission as amount, p.id as source_id
from public.payments p join public.projects pj on pj.id = p.project_id
union all
select po.paid_on, po.partner_id, 'payout', po.code || ' · ' || po.reference, -po.amount, po.id
from public.payouts po where not po.voided
union all
select ad.created_on, ad.partner_id, 'adjustment', ad.reason, ad.amount, ad.id
from public.adjustments ad;

grant select on public.partner_balances, public.ledger to authenticated;

-- ---------- admin actions ----------

create function public._require_admin() returns void
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_admin() then
    raise exception 'Only an active admin can do this.' using errcode = '42501';
  end if;
end $$;

create function public._require_reason(p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if p_reason is null or length(trim(p_reason)) < 3 then
    raise exception 'Enter a reason of at least a few words.' using errcode = '22023';
  end if;
  perform set_config('app.reason', trim(p_reason), true);
end $$;

create function public.record_payout(
  p_partner uuid, p_amount bigint, p_paid_on date, p_method public.pay_method,
  p_reference text, p_account_mask text default null
) returns public.payouts
language plpgsql security definer set search_path = '' as $$
declare v_available bigint; r public.payouts;
begin
  perform public._require_admin();
  -- lock the partner so two payouts cannot both pass the balance check
  perform 1 from public.profiles where id = p_partner and role = 'partner' for update;
  if not found then raise exception 'Partner not found.'; end if;
  if p_paid_on is null or p_paid_on > current_date then raise exception 'Choose a valid date. It cannot be in the future.'; end if;
  select available into v_available from public.partner_balances where partner_id = p_partner;
  if p_amount is null or p_amount <= 0 then raise exception 'Enter the amount paid.'; end if;
  if p_amount > coalesce(v_available, 0) then
    raise exception 'That is more than this partner can be paid now (% pesewas available).', coalesce(v_available, 0);
  end if;
  insert into public.payouts (partner_id, paid_on, amount, method, reference, account_mask, recorded_by)
  values (p_partner, p_paid_on, p_amount, p_method, trim(p_reference), nullif(trim(p_account_mask), ''), auth.uid())
  returning * into r;
  return r;
end $$;

create function public.void_payout(p_payout uuid, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  update public.payouts set voided = true where id = p_payout and not voided;
  if not found then raise exception 'Payout not found or already voided.'; end if;
end $$;

create function public.refund_payment(p_payment uuid, p_amount bigint, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
declare v public.payments;
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  select * into v from public.payments where id = p_payment for update;
  if not found then raise exception 'Payment not found.'; end if;
  if v.reversed then raise exception 'This payment was reversed.'; end if;
  if p_amount is null or p_amount <= 0 then raise exception 'Enter the refund amount.'; end if;
  if p_amount > v.amount - v.tax - v.refunded then
    raise exception 'That is more than the % pesewas left on this payment.', v.amount - v.tax - v.refunded;
  end if;
  update public.payments set refunded = refunded + p_amount where id = p_payment;
end $$;

create function public.reverse_payment(p_payment uuid, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  update public.payments set reversed = true where id = p_payment and not reversed;
  if not found then raise exception 'Payment not found or already reversed.'; end if;
end $$;

create function public.change_project_rate(p_project uuid, p_rate_bp int, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  if p_rate_bp is null or p_rate_bp < 1 or p_rate_bp > 10000 then
    raise exception 'Enter a rate between 0.01 and 100.';
  end if;
  update public.projects set rate_bp = p_rate_bp where id = p_project;
  if not found then raise exception 'Project not found.'; end if;
end $$;

create function public.reassign_client(p_client uuid, p_partner uuid, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  if not exists (select 1 from public.profiles where id = p_partner and role = 'partner') then
    raise exception 'Partner not found.';
  end if;
  update public.clients set partner_id = p_partner where id = p_client and partner_id <> p_partner;
  if not found then raise exception 'Client not found, or already with that partner.'; end if;
end $$;

-- Called by an admin directly, or by the partner-admin Edge Function (service role)
-- which also bans the auth user so open sessions stop refreshing.
create function public.set_partner_status(
  p_partner uuid, p_status public.account_status, p_reason text, p_actor uuid default null
) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role', '') <> 'service_role' then
    perform public._require_admin();
  elsif p_actor is null or not exists (
    select 1 from public.profiles where id = p_actor and role = 'admin' and status = 'active') then
    raise exception 'Unknown admin.' using errcode = '42501';
  end if;
  perform public._require_reason(p_reason);
  if p_actor is not null and coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role', '') = 'service_role' then
    perform set_config('app.actor', p_actor::text, true);
  end if;
  update public.profiles set status = p_status
  where id = p_partner and role = 'partner' and status <> p_status;
  if not found then raise exception 'Partner not found, or already %.', p_status; end if;
end $$;

-- ---------- referrals ----------

create function public.referrals_before_insert() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_admin() then
    new.partner_id := auth.uid();
  end if;
  new.status := 'pending';
  new.decision_note := null;
  new.client_id := null;
  new.business := trim(new.business);
  new.email := nullif(lower(trim(new.email)), '');
  return new;
end $$;
create trigger referrals_clean before insert on public.referrals
  for each row execute function public.referrals_before_insert();

create function public.referrals_after_insert() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_ref uuid; v_client uuid; v_note text;
begin
  select r.id, 'Possible duplicate of referral "' || r.business || '" from ' || p.full_name || '.'
    into v_ref, v_note
  from public.referrals r join public.profiles p on p.id = r.partner_id
  where r.id <> new.id and r.status <> 'rejected'
    and (lower(r.business) = lower(new.business) or (new.email is not null and r.email = new.email))
  order by r.created_at limit 1;
  if v_ref is null then
    select c.id, 'Same as existing client "' || c.name || '", attributed to ' || p.full_name || '.'
      into v_client, v_note
    from public.clients c join public.profiles p on p.id = c.partner_id
    where lower(c.name) = lower(new.business) or (new.email is not null and lower(c.email) = new.email)
    limit 1;
  end if;
  if v_ref is not null or v_client is not null then
    update public.referrals set status = 'flagged' where id = new.id;
    insert into public.referral_flags (referral_id, matched_referral_id, matched_client_id, note)
    values (new.id, v_ref, v_client, v_note);
  end if;
  return null;
end $$;
create trigger referrals_dupe_check after insert on public.referrals
  for each row execute function public.referrals_after_insert();

create function public.approve_referral(p_referral uuid) returns uuid
language plpgsql security definer set search_path = '' as $$
declare r public.referrals; v_client uuid;
begin
  perform public._require_admin();
  select * into r from public.referrals where id = p_referral for update;
  if not found then raise exception 'Referral not found.'; end if;
  if r.status <> 'pending' then raise exception 'Only referrals waiting for review can be approved.'; end if;
  insert into public.clients (name, email, partner_id) values (r.business, r.email, r.partner_id)
  returning id into v_client;
  update public.referrals set status = 'approved', client_id = v_client where id = p_referral;
  return v_client;
end $$;

create function public.reject_referral(p_referral uuid, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  update public.referrals set status = 'rejected', decision_note = trim(p_reason)
  where id = p_referral and status in ('pending', 'flagged');
  if not found then raise exception 'Referral not found or already decided.'; end if;
end $$;

create function public.resolve_referral_flag(p_referral uuid, p_is_duplicate boolean, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  update public.referrals
     set status = case when p_is_duplicate then 'rejected'::public.referral_status else 'pending' end,
         decision_note = case when p_is_duplicate then 'Duplicate' else decision_note end
   where id = p_referral and status = 'flagged';
  if not found then raise exception 'Referral not found or not flagged.'; end if;
  delete from public.referral_flags where referral_id = p_referral;
end $$;

-- ---------- lookups ----------

-- Names of active members, for the community space and @mentions.
create function public.community_directory()
returns table (id uuid, full_name text, role public.user_role)
language sql stable security definer set search_path = '' as $$
  select p.id, p.full_name, p.role from public.profiles p
  where p.status = 'active' and public.is_active_user();
$$;

-- Invitations that have not been accepted yet (admin only).
create function public.pending_invitations()
returns table (id uuid, email text, full_name text, invited_at timestamptz)
language plpgsql stable security definer set search_path = '' as $$
begin
  perform public._require_admin();
  return query
    select u.id, u.email::text, coalesce(u.raw_user_meta_data ->> 'full_name', ''), u.invited_at
    from auth.users u
    where u.invited_at is not null and u.last_sign_in_at is null
    order by u.invited_at desc;
end $$;

revoke execute on all functions in schema public from public, anon;
grant execute on function
  public.record_payout(uuid, bigint, date, public.pay_method, text, text),
  public.void_payout(uuid, text),
  public.refund_payment(uuid, bigint, text),
  public.reverse_payment(uuid, text),
  public.change_project_rate(uuid, int, text),
  public.reassign_client(uuid, uuid, text),
  public.set_partner_status(uuid, public.account_status, text, uuid),
  public.approve_referral(uuid),
  public.reject_referral(uuid, text),
  public.resolve_referral_flag(uuid, boolean, text),
  public.community_directory(),
  public.pending_invitations(),
  public.add_business_days(date, int)
to authenticated;
grant execute on function public.set_partner_status(uuid, public.account_status, text, uuid) to service_role;
revoke execute on function public._require_admin(), public._require_reason(text) from authenticated;
