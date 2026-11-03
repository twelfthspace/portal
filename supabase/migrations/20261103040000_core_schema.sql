-- Twelfth Space Growth Partner portal: core tables, helpers and row level security.
-- Money is stored as whole pesewas (bigint). Rates are basis points (1250 = 12.5%).

create type public.user_role as enum ('admin', 'partner');
create type public.account_status as enum ('active', 'suspended');
create type public.project_status as enum ('not_started', 'in_progress', 'on_hold', 'completed', 'cancelled');
create type public.pay_method as enum ('mobile_money', 'bank_transfer', 'cash');
create type public.referral_status as enum ('pending', 'flagged', 'approved', 'rejected');

-- ---------- tables ----------

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  role public.user_role not null default 'partner',
  status public.account_status not null default 'active',
  full_name text not null default '',
  email text not null unique,
  phone text,
  city text,
  created_at timestamptz not null default now()
);

create table public.settings (
  id int primary key default 1 check (id = 1),
  hold_days int not null default 5 check (hold_days between 0 and 60),
  invite_expiry_days int not null default 1 check (invite_expiry_days between 1 and 30)
);
insert into public.settings (id) values (1);

create table public.clients (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(trim(name)) > 0),
  contact text,
  email text,
  partner_id uuid not null references public.profiles (id),
  created_at timestamptz not null default now()
);
create index on public.clients (partner_id);

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients (id),
  name text not null check (length(trim(name)) > 0),
  budget bigint not null check (budget > 0),
  rate_bp int not null check (rate_bp between 1 and 10000),
  status public.project_status not null default 'not_started',
  created_at timestamptz not null default now()
);
create index on public.projects (client_id);

-- partner_id and rate_bp are copied from the project when the payment is recorded,
-- so later reassignments and rate changes never rewrite past commission.
create table public.payments (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id),
  partner_id uuid not null references public.profiles (id),
  rate_bp int not null check (rate_bp between 1 and 10000),
  received_on date not null,
  amount bigint not null check (amount > 0),
  tax bigint not null default 0 check (tax >= 0),
  refunded bigint not null default 0 check (refunded >= 0),
  reversed boolean not null default false,
  method public.pay_method not null,
  reference text not null check (length(trim(reference)) > 0),
  commission bigint generated always as (
    case when reversed then 0 else greatest(0, amount - tax - refunded) * rate_bp / 10000 end
  ) stored,
  recorded_by uuid default auth.uid() references public.profiles (id),
  created_at timestamptz not null default now(),
  check (tax <= amount),
  check (refunded <= amount - tax)
);
create unique index payments_method_ref on public.payments (method, lower(reference));
create index on public.payments (partner_id);
create index on public.payments (project_id);

create sequence public.payout_seq;
create table public.payouts (
  id uuid primary key default gen_random_uuid(),
  code text not null unique default ('PO-' || lpad(nextval('public.payout_seq')::text, 4, '0')),
  partner_id uuid not null references public.profiles (id),
  paid_on date not null,
  amount bigint not null check (amount > 0),
  method public.pay_method not null check (method <> 'cash'),
  reference text not null check (length(trim(reference)) > 0),
  account_mask text check (account_mask !~ '\d{5,}'),
  voided boolean not null default false,
  recorded_by uuid references public.profiles (id),
  created_at timestamptz not null default now()
);
create unique index payouts_method_ref on public.payouts (method, lower(reference));
create index on public.payouts (partner_id);

create table public.adjustments (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.profiles (id),
  amount bigint not null check (amount <> 0),
  reason text not null check (length(trim(reason)) >= 3),
  created_on date not null default current_date,
  created_by uuid default auth.uid() references public.profiles (id),
  created_at timestamptz not null default now()
);
create index on public.adjustments (partner_id);

create table public.referrals (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null default auth.uid() references public.profiles (id),
  business text not null check (length(trim(business)) > 0),
  email text,
  budget bigint not null default 0 check (budget >= 0),
  status public.referral_status not null default 'pending',
  decision_note text,
  client_id uuid references public.clients (id),
  created_at timestamptz not null default now()
);
create index on public.referrals (partner_id);

-- Admin-only detail about why a referral was flagged. Kept out of public.referrals
-- so a partner never learns which other partner already owns a client.
create table public.referral_flags (
  referral_id uuid primary key references public.referrals (id) on delete cascade,
  matched_referral_id uuid references public.referrals (id),
  matched_client_id uuid references public.clients (id),
  note text not null,
  created_at timestamptz not null default now()
);

-- Private admin <-> partner threads. partner_id names the thread.
create table public.messages (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.profiles (id),
  sender_id uuid not null default auth.uid() references public.profiles (id),
  body text not null check (length(trim(body)) > 0 and length(body) <= 4000),
  read_at timestamptz,
  created_at timestamptz not null default now()
);
create index on public.messages (partner_id, created_at);

create table public.announcements (
  id uuid primary key default gen_random_uuid(),
  title text not null check (length(trim(title)) >= 3),
  body text not null check (length(trim(body)) >= 10),
  pinned boolean not null default false,
  created_by uuid default auth.uid() references public.profiles (id),
  created_at timestamptz not null default now()
);

create table public.announcement_reads (
  announcement_id uuid references public.announcements (id) on delete cascade,
  user_id uuid default auth.uid() references public.profiles (id) on delete cascade,
  read_at timestamptz not null default now(),
  primary key (announcement_id, user_id)
);

create table public.community_messages (
  id uuid primary key default gen_random_uuid(),
  sender_id uuid not null default auth.uid() references public.profiles (id),
  body text not null check (length(trim(body)) > 0 and length(body) <= 2000),
  created_at timestamptz not null default now()
);
create index on public.community_messages (created_at);

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  text text not null,
  link text,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
create index on public.notifications (user_id, created_at desc);

create table public.audit_log (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  actor_id uuid,
  action text not null,
  entity text not null,
  entity_id text,
  reason text,
  old_row jsonb,
  new_row jsonb
);
create index on public.audit_log (at desc);

-- ---------- helpers used by policies ----------

create function public.is_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and role = 'admin' and status = 'active'
  );
$$;

create function public.is_active_user() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and status = 'active'
  );
$$;

-- ---------- row level security ----------

alter table public.profiles enable row level security;
alter table public.settings enable row level security;
alter table public.clients enable row level security;
alter table public.projects enable row level security;
alter table public.payments enable row level security;
alter table public.payouts enable row level security;
alter table public.adjustments enable row level security;
alter table public.referrals enable row level security;
alter table public.referral_flags enable row level security;
alter table public.messages enable row level security;
alter table public.announcements enable row level security;
alter table public.announcement_reads enable row level security;
alter table public.community_messages enable row level security;
alter table public.notifications enable row level security;
alter table public.audit_log enable row level security;

-- profiles
create policy "profiles: read own or admin" on public.profiles for select to authenticated
  using (id = (select auth.uid()) or (select public.is_admin()));
create policy "profiles: edit own details or admin" on public.profiles for update to authenticated
  using ((id = (select auth.uid()) and (select public.is_active_user())) or (select public.is_admin()))
  with check ((id = (select auth.uid()) and (select public.is_active_user())) or (select public.is_admin()));

-- settings
create policy "settings: active users read" on public.settings for select to authenticated
  using ((select public.is_active_user()));
create policy "settings: admin edits" on public.settings for update to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));

-- clients
create policy "clients: own or admin" on public.clients for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "clients: admin adds" on public.clients for insert to authenticated
  with check ((select public.is_admin()));
create policy "clients: admin edits" on public.clients for update to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));

-- projects
create policy "projects: own client or admin" on public.projects for select to authenticated
  using ((select public.is_admin()) or ((select public.is_active_user()) and exists (
    select 1 from public.clients c where c.id = client_id and c.partner_id = (select auth.uid()))));
create policy "projects: admin adds" on public.projects for insert to authenticated
  with check ((select public.is_admin()));
create policy "projects: admin edits" on public.projects for update to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));

-- payments (no update or delete: refunds and reversals go through functions)
create policy "payments: own or admin" on public.payments for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "payments: admin records" on public.payments for insert to authenticated
  with check ((select public.is_admin()));

-- payouts (inserted and voided only through functions)
create policy "payouts: own or admin" on public.payouts for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));

-- adjustments
create policy "adjustments: own or admin" on public.adjustments for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "adjustments: admin adds" on public.adjustments for insert to authenticated
  with check ((select public.is_admin()));

-- referrals (decisions go through functions)
create policy "referrals: own or admin" on public.referrals for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "referrals: active partner submits own" on public.referrals for insert to authenticated
  with check (partner_id = (select auth.uid()) and (select public.is_active_user()));

-- referral_flags
create policy "referral flags: admin only" on public.referral_flags for select to authenticated
  using ((select public.is_admin()));

-- messages
create policy "messages: thread member or admin" on public.messages for select to authenticated
  using ((select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user())));
create policy "messages: send in own thread or admin" on public.messages for insert to authenticated
  with check (sender_id = (select auth.uid()) and (
    (select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user()))));
create policy "messages: recipient marks read" on public.messages for update to authenticated
  using (sender_id <> (select auth.uid()) and (
    (select public.is_admin()) or (partner_id = (select auth.uid()) and (select public.is_active_user()))))
  with check (sender_id <> (select auth.uid()));

-- announcements
create policy "announcements: active users read" on public.announcements for select to authenticated
  using ((select public.is_active_user()));
create policy "announcements: admin posts" on public.announcements for insert to authenticated
  with check ((select public.is_admin()));
create policy "announcements: admin edits" on public.announcements for update to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy "announcements: admin deletes" on public.announcements for delete to authenticated
  using ((select public.is_admin()));

create policy "announcement reads: own" on public.announcement_reads for select to authenticated
  using (user_id = (select auth.uid()));
create policy "announcement reads: mark own" on public.announcement_reads for insert to authenticated
  with check (user_id = (select auth.uid()) and (select public.is_active_user()));

-- community
create policy "community: active users read" on public.community_messages for select to authenticated
  using ((select public.is_active_user()));
create policy "community: active users post as themselves" on public.community_messages for insert to authenticated
  with check (sender_id = (select auth.uid()) and (select public.is_active_user()));
create policy "community: author or admin deletes" on public.community_messages for delete to authenticated
  using ((select public.is_admin()) or (sender_id = (select auth.uid()) and (select public.is_active_user())));

-- notifications
create policy "notifications: own" on public.notifications for select to authenticated
  using (user_id = (select auth.uid()));
create policy "notifications: mark own read" on public.notifications for update to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

-- audit log
create policy "audit: admin reads" on public.audit_log for select to authenticated
  using ((select public.is_admin()));

-- ---------- table privileges (defence in depth on top of RLS) ----------

revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;

grant select on all tables in schema public to authenticated;
grant update (full_name, phone, city) on public.profiles to authenticated;
grant update (hold_days, invite_expiry_days) on public.settings to authenticated;
grant insert (name, contact, email, partner_id) on public.clients to authenticated;
grant update (name, contact, email) on public.clients to authenticated;            -- partner_id via reassign_client()
grant insert (client_id, name, budget, rate_bp, status) on public.projects to authenticated;
grant update (name, budget, status) on public.projects to authenticated;           -- rate via change_project_rate()
grant insert (project_id, received_on, amount, tax, method, reference) on public.payments to authenticated;
grant insert (partner_id, amount, reason) on public.adjustments to authenticated;
grant insert (business, email, budget) on public.referrals to authenticated;
grant insert (partner_id, body) on public.messages to authenticated;
grant update (read_at) on public.messages to authenticated;
grant insert (title, body, pinned) on public.announcements to authenticated;
grant update (title, body, pinned) on public.announcements to authenticated;
grant delete on public.announcements to authenticated;
grant insert (announcement_id) on public.announcement_reads to authenticated;
grant insert (body) on public.community_messages to authenticated;
grant delete on public.community_messages to authenticated;
grant update (read_at) on public.notifications to authenticated;

revoke execute on all functions in schema public from public, anon;
grant execute on function public.is_admin() to authenticated;
grant execute on function public.is_active_user() to authenticated;
