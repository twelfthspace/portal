-- Remove a partner who has left: personal details go, money history stays.
-- Called through the partner-admin Edge Function, which also closes the login for good.
create function public.remove_partner(p_partner uuid, p_reason text)
returns text   -- the old photo path, so the caller can delete the file
language plpgsql security definer set search_path = '' as $$
declare v_avatar text;
begin
  perform public._require_admin();
  perform public._require_reason(p_reason);
  select avatar_path into v_avatar from public.profiles
  where id = p_partner and role = 'partner' and status <> 'removed' for update;
  if not found then raise exception 'Partner not found, or already removed.'; end if;
  delete from public.payout_accounts where partner_id = p_partner;
  update public.profiles
     set status = 'removed', phone = null, city = null, avatar_path = null, account_mask = null
   where id = p_partner;
  return v_avatar;
end $$;
revoke execute on function public.remove_partner(uuid, text) from public, anon;
grant execute on function public.remove_partner(uuid, text) to authenticated;

-- Suspend and reactivate never touch removed partners.
create or replace function public.set_partner_status(
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
  if p_status = 'removed' then raise exception 'Use Remove partner for someone who has left.'; end if;
  perform public._require_reason(p_reason);
  if p_actor is not null and coalesce(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role', '') = 'service_role' then
    perform set_config('app.actor', p_actor::text, true);
  end if;
  update public.profiles set status = p_status
  where id = p_partner and role = 'partner' and status <> p_status and status <> 'removed';
  if not found then raise exception 'Partner not found, removed, or already %.', p_status; end if;
end $$;
