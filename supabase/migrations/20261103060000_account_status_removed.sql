-- A partner who has left for good. Kept separate from 'suspended', which can be reversed.
alter type public.account_status add value if not exists 'removed';
