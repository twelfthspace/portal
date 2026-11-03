-- Audit log, notifications and new-user profiles. All written by triggers, never by the browser.

-- ---------- audit ----------

create function public.audit_row() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_actor uuid;
begin
  v_actor := coalesce(auth.uid(), nullif(current_setting('app.actor', true), '')::uuid);
  insert into public.audit_log (actor_id, action, entity, entity_id, reason, old_row, new_row)
  values (
    v_actor, lower(tg_op), tg_table_name,
    coalesce((case when tg_op = 'DELETE' then to_jsonb(old) else to_jsonb(new) end) ->> 'id', null),
    nullif(current_setting('app.reason', true), ''),
    case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) end,
    case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) end
  );
  return null;
end $$;

do $$
declare t text;
begin
  foreach t in array array['profiles','settings','clients','projects','payments','payouts',
                           'adjustments','referrals','announcements'] loop
    execute format('create trigger audit after insert or update or delete on public.%I
                    for each row execute function public.audit_row()', t);
  end loop;
end $$;
create trigger audit after delete on public.community_messages
  for each row execute function public.audit_row();

-- ---------- notifications ----------

create function public.notify_admins(p_text text, p_link text) returns void
language sql security definer set search_path = '' as $$
  insert into public.notifications (user_id, text, link)
  select id, p_text, p_link from public.profiles where role = 'admin' and status = 'active';
$$;

create function public.notify_on_referral() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_name text;
begin
  if tg_op = 'INSERT' then
    select full_name into v_name from public.profiles where id = new.partner_id;
    perform public.notify_admins(v_name || ' submitted ' || new.business, 'admin-referrals');
  elsif new.status is distinct from old.status and new.status in ('approved', 'rejected') then
    insert into public.notifications (user_id, text, link)
    values (new.partner_id,
            'Your referral ' || new.business ||
              case when new.status = 'approved' then ' was approved' else ' was not accepted' end,
            'partner-referrals');
  end if;
  return null;
end $$;
create trigger notify after insert or update of status on public.referrals
  for each row execute function public.notify_on_referral();

create function public.notify_on_payment() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_client text;
begin
  select c.name into v_client from public.projects p join public.clients c on c.id = p.client_id
  where p.id = new.project_id;
  insert into public.notifications (user_id, text, link)
  values (new.partner_id, 'Payment received from ' || v_client, 'partner-commissions');
  return null;
end $$;
create trigger notify after insert on public.payments
  for each row execute function public.notify_on_payment();

create function public.notify_on_payout() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.notifications (user_id, text, link)
  values (new.partner_id,
          'A payout of GHS ' || to_char(new.amount / 100.0, 'FM999,999,990.00') || ' was recorded for you',
          'partner-payments');
  return null;
end $$;
create trigger notify after insert on public.payouts
  for each row execute function public.notify_on_payout();

create function public.notify_on_announcement() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.notifications (user_id, text, link)
  select id, 'New announcement: ' || new.title, 'partner-announcements'
  from public.profiles where role = 'partner' and status = 'active';
  return null;
end $$;
create trigger notify after insert on public.announcements
  for each row execute function public.notify_on_announcement();

create function public.notify_on_message() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_name text;
begin
  if new.sender_id = new.partner_id then
    select full_name into v_name from public.profiles where id = new.partner_id;
    perform public.notify_admins(v_name || ' sent a message', 'admin-messages');
  else
    insert into public.notifications (user_id, text, link)
    values (new.partner_id, 'New message from the studio', 'partner-messages');
  end if;
  return null;
end $$;
create trigger notify after insert on public.messages
  for each row execute function public.notify_on_message();

-- ---------- new users ----------
-- Every new auth user (created by an admin invitation) gets a partner profile.
-- Promote the first admin by hand: update public.profiles set role = 'admin' where email = '...';

create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, lower(new.email), coalesce(new.raw_user_meta_data ->> 'full_name', ''));
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

create function public.sync_profile_email() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  update public.profiles set email = lower(new.email) where id = new.id;
  return new;
end $$;
create trigger on_auth_user_email_changed after update of email on auth.users
  for each row when (new.email is distinct from old.email)
  execute function public.sync_profile_email();

revoke execute on all functions in schema public from public, anon;
