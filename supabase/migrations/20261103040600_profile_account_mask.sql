-- Partners can store a masked payout account on their profile (never a full number).
alter table public.profiles add column account_mask text check (account_mask !~ '\d{5,}');
grant update (account_mask) on public.profiles to authenticated;
