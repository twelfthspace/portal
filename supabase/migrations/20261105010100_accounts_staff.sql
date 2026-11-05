-- Accounts staff: studio-side access with owner-only restrictions.
-- is_admin() now means "active studio staff" (owner or accounts); is_owner() is the owner alone.

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles
                 where id = (select auth.uid()) and role in ('admin', 'accounts') and status = 'active');
$$;

create function public.is_owner() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.profiles
                 where id = (select auth.uid()) and role = 'admin' and status = 'active');
$$;

create function public._require_owner() returns void
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.is_owner() then
    raise exception 'Only the owner can do this.' using errcode = '42501';
  end if;
end $$;

-- ---------- owner-only actions ----------
create or replace function public.change_project_rate(p_project uuid, p_rate_bp int, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_owner();
  perform public._require_reason(p_reason);
  if p_rate_bp is null or p_rate_bp < 1 or p_rate_bp > 10000 then
    raise exception 'Enter a rate between 0.01 and 100.';
  end if;
  update public.projects set rate_bp = p_rate_bp where id = p_project;
  if not found then raise exception 'Project not found.'; end if;
end $$;

create or replace function public.reassign_client(p_client uuid, p_partner uuid, p_reason text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_owner();
  perform public._require_reason(p_reason);
  if not exists (select 1 from public.profiles where id = p_partner and role = 'partner') then
    raise exception 'Partner not found.';
  end if;
  update public.clients set partner_id = p_partner where id = p_client and partner_id <> p_partner;
  if not found then raise exception 'Client not found, or already with that partner.'; end if;
end $$;

-- Suspend / reactivate partners and staff (never the owner).
create or replace function public.set_partner_status(
  p_partner uuid, p_status public.account_status, p_reason text, p_actor uuid default null
) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role', '') <> 'service_role' then
    perform public._require_owner();
  elsif p_actor is null or not exists (
    select 1 from public.profiles where id = p_actor and role = 'admin' and status = 'active') then
    raise exception 'Unknown owner.' using errcode = '42501';
  end if;
  if p_status = 'removed' then raise exception 'Use Remove for someone who has left.'; end if;
  perform public._require_reason(p_reason);
  if p_actor is not null and coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role', '') = 'service_role' then
    perform set_config('app.actor', p_actor::text, true);
  end if;
  update public.profiles set status = p_status
  where id = p_partner and role in ('partner', 'accounts') and status <> p_status and status <> 'removed';
  if not found then raise exception 'Person not found, removed, or already %.', p_status; end if;
end $$;

-- Remove a partner or staff member who has left: personal details go, money history stays.
create or replace function public.remove_partner(p_partner uuid, p_reason text)
returns text
language plpgsql security definer set search_path = '' as $$
declare v_avatar text;
begin
  perform public._require_owner();
  perform public._require_reason(p_reason);
  select avatar_path into v_avatar from public.profiles
  where id = p_partner and role in ('partner', 'accounts') and status <> 'removed' for update;
  if not found then raise exception 'Person not found, or already removed.'; end if;
  delete from public.payout_accounts where partner_id = p_partner;
  update public.profiles
     set status = 'removed', phone = null, city = null, avatar_path = null, account_mask = null
   where id = p_partner;
  return v_avatar;
end $$;

-- A brand-new invite becomes an Accounts staff member (used by the partner-admin function).
create function public.make_staff(p_user uuid) returns void
language plpgsql security definer set search_path = '' as $$
begin
  perform public._require_owner();
  perform set_config('app.reason', 'Invited as Accounts staff', true);
  update public.profiles set role = 'accounts'
   where id = p_user and role = 'partner'
     and not exists (select 1 from public.clients where partner_id = p_user)
     and not exists (select 1 from public.payments where partner_id = p_user)
     and not exists (select 1 from public.payouts where partner_id = p_user)
     and not exists (select 1 from public.referrals where partner_id = p_user);
  if not found then raise exception 'Only a brand-new invitation can be made a staff member.'; end if;
end $$;

-- Invitations now say whether they are for a partner or staff.
drop function public.pending_invitations();
create function public.pending_invitations()
returns table (id uuid, email text, full_name text, invited_at timestamptz, role public.user_role)
language plpgsql stable security definer set search_path = '' as $$
begin
  perform public._require_admin();
  return query
    select u.id, u.email::text, coalesce(u.raw_user_meta_data ->> 'full_name', ''), u.invited_at, p.role
    from auth.users u left join public.profiles p on p.id = u.id
    where u.invited_at is not null and u.last_sign_in_at is null
    order by u.invited_at desc;
end $$;

-- Staff get the studio's notifications too.
create or replace function public.notify_admins(p_text text, p_link text) returns void
language sql security definer set search_path = '' as $$
  insert into public.notifications (user_id, text, link)
  select id, p_text, p_link from public.profiles where role in ('admin', 'accounts') and status = 'active';
$$;

-- Notification links point at the right side of the portal for staff.
create or replace function public.notify_on_community() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_name text; v_slug text; v_parent_author uuid; r record;
begin
  select full_name into v_name from public.profiles where id = new.sender_id;
  select slug into v_slug from public.channels where id = new.channel_id;
  for r in select p.id, case when p.role = 'partner' then 'partner' else 'admin' end as side from public.profiles p
           where p.id = any(new.mentions) and p.id <> new.sender_id and p.status = 'active' loop
    insert into public.notifications (user_id, text, link)
    values (r.id, coalesce(v_name, 'Someone') || ' mentioned you in #' || v_slug,
            r.side || '-messages~' || v_slug || case when new.parent_id is not null then '~t-' || new.parent_id else '' end);
  end loop;
  if new.parent_id is not null then
    select sender_id into v_parent_author from public.community_messages where id = new.parent_id;
    if v_parent_author is not null and v_parent_author <> new.sender_id and not (v_parent_author = any(new.mentions)) then
      insert into public.notifications (user_id, text, link)
      select p.id, coalesce(v_name, 'Someone') || ' replied to your post in #' || v_slug,
             case when p.role = 'partner' then 'partner' else 'admin' end || '-messages~' || v_slug || '~t-' || new.parent_id
      from public.profiles p where p.id = v_parent_author and p.status = 'active';
    end if;
  end if;
  return null;
end $$;

-- ---------- owner-only edits in the access rules ----------
drop policy "settings: admin edits" on public.settings;
create policy "settings: owner edits" on public.settings for update to authenticated
  using ((select public.is_owner())) with check ((select public.is_owner()));

drop policy "channels: admin adds" on public.channels;
drop policy "channels: admin edits" on public.channels;
create policy "channels: owner adds" on public.channels for insert to authenticated
  with check ((select public.is_owner()));
create policy "channels: owner edits" on public.channels for update to authenticated
  using ((select public.is_owner())) with check ((select public.is_owner()));

drop policy "profiles: edit own details or admin" on public.profiles;
create policy "profiles: edit own details or owner" on public.profiles for update to authenticated
  using ((id = (select auth.uid()) and (select public.is_active_user())) or (select public.is_owner()))
  with check ((id = (select auth.uid()) and (select public.is_active_user())) or (select public.is_owner()));

drop policy "payout accounts: own or admin add" on public.payout_accounts;
drop policy "payout accounts: own or admin edit" on public.payout_accounts;
create policy "payout accounts: own or owner add" on public.payout_accounts for insert to authenticated
  with check ((select public.is_owner()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "payout accounts: own or owner edit" on public.payout_accounts for update to authenticated
  using ((select public.is_owner()) or (partner_id = (select auth.uid()) and (select public.is_active_user())))
  with check ((select public.is_owner()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));

revoke execute on function public.is_owner(), public._require_owner(), public.make_staff(uuid),
  public.pending_invitations(), public.notify_admins(text, text), public.notify_on_community() from public, anon;
revoke execute on function public._require_owner(), public.notify_admins(text, text), public.notify_on_community() from authenticated;
grant execute on function public.is_owner(), public.make_staff(uuid), public.pending_invitations() to authenticated;
