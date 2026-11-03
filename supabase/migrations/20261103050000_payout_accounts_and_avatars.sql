-- Payout details (Mobile Money or bank) and profile photos.

-- ---------- payout details ----------
-- Full numbers live only here. Readable by the partner who owns them and by admins.
create type public.payout_kind as enum ('momo', 'bank');

create table public.payout_accounts (
  partner_id uuid primary key references public.profiles (id) on delete cascade,
  kind public.payout_kind not null,
  provider text not null check (length(trim(provider)) between 2 and 60),       -- MoMo network or bank name
  account_number text not null check (account_number ~ '^[0-9]{6,20}$'),
  account_name text not null check (length(trim(account_name)) between 2 and 100),
  branch text check (branch is null or length(branch) <= 100),
  updated_at timestamptz not null default now(),
  updated_by uuid default auth.uid() references public.profiles (id)
);
create index on public.payout_accounts (updated_by);
alter table public.payout_accounts enable row level security;

create policy "payout accounts: own or admin read" on public.payout_accounts for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "payout accounts: own or admin add" on public.payout_accounts for insert to authenticated
  with check ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "payout accounts: own or admin edit" on public.payout_accounts for update to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())))
  with check ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));

grant select on public.payout_accounts to authenticated;
grant insert (partner_id, kind, provider, account_number, account_name, branch) on public.payout_accounts to authenticated;
grant update (kind, provider, account_number, account_name, branch) on public.payout_accounts to authenticated;

create function public.payout_accounts_stamp() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  new.updated_at := now();
  new.updated_by := auth.uid();
  new.provider := trim(new.provider);
  new.account_name := trim(new.account_name);
  new.branch := nullif(trim(new.branch), '');
  return new;
end $$;
create trigger stamp before insert or update on public.payout_accounts
  for each row execute function public.payout_accounts_stamp();

-- Audit with the number masked, and tell the other side whenever details change.
create function public.payout_accounts_after() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_name text; v_mask text;
begin
  v_mask := '•••• ' || right(new.account_number, 4);
  insert into public.audit_log (actor_id, action, entity, entity_id, reason, old_row, new_row)
  values (auth.uid(), lower(tg_op), 'payout_accounts', new.partner_id::text, null,
          case when tg_op = 'UPDATE' then jsonb_build_object('kind', old.kind, 'provider', old.provider,
               'account_number', '•••• ' || right(old.account_number, 4), 'account_name', old.account_name) end,
          jsonb_build_object('kind', new.kind, 'provider', new.provider, 'account_number', v_mask, 'account_name', new.account_name));
  select full_name into v_name from public.profiles where id = new.partner_id;
  if auth.uid() = new.partner_id then
    perform public.notify_admins(coalesce(v_name, 'A partner') || ' changed their payout details to ' || new.provider || ' ' || v_mask,
                                 'admin-partner-' || new.partner_id);
  else
    insert into public.notifications (user_id, text, link)
    values (new.partner_id, 'The studio updated your payout details to ' || new.provider || ' ' || v_mask, 'partner-profile');
  end if;
  return null;
end $$;
create trigger after_change after insert or update on public.payout_accounts
  for each row execute function public.payout_accounts_after();

-- ---------- profile photos ----------
alter table public.profiles add column avatar_path text
  check (avatar_path is null or (avatar_path like id::text || '/%' and avatar_path ~ '^[0-9a-f-]{36}/[A-Za-z0-9._-]{1,80}$'));
grant update (avatar_path) on public.profiles to authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', false, 2097152, array['image/jpeg', 'image/png', 'image/webp']);

create policy "avatars: active members view" on storage.objects for select to authenticated
  using (bucket_id = 'avatars' and (select public.is_active_user()));
create policy "avatars: upload to own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text and (select public.is_active_user()));
create policy "avatars: replace own" on storage.objects for update to authenticated
  using (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text)
  with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "avatars: remove own or admin" on storage.objects for delete to authenticated
  using (bucket_id = 'avatars' and ((storage.foldername(name))[1] = (select auth.uid())::text or (select public.is_admin())));

-- The member directory now includes photos.
drop function public.community_directory();
create function public.community_directory()
returns table (id uuid, full_name text, role public.user_role, avatar_path text)
language sql stable security definer set search_path = '' as $$
  select p.id, p.full_name, p.role, p.avatar_path from public.profiles p
  where p.status = 'active' and public.is_active_user();
$$;
revoke execute on function public.community_directory() from public, anon;
grant execute on function public.community_directory() to authenticated;
revoke execute on function public.payout_accounts_stamp(), public.payout_accounts_after() from public, anon, authenticated;
