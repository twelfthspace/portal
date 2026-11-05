-- Studio staff who run the money side but are not the owner.
alter type public.user_role add value if not exists 'accounts';
