-- The read_at check must only run for direct messages; channel messages have no read_at.
create or replace function public.chat_before_update() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if new.body is distinct from old.body then
    if auth.uid() is distinct from old.sender_id then raise exception 'You can only edit your own messages.'; end if;
    new.edited_at := now();
  end if;
  if tg_table_name = 'messages' then
    if (to_jsonb(new) ->> 'read_at') is distinct from (to_jsonb(old) ->> 'read_at') and auth.uid() = old.sender_id then
      new := jsonb_populate_record(new, jsonb_build_object('read_at', to_jsonb(old) -> 'read_at'));
    end if;
  end if;
  return new;
end $$;
revoke execute on function public.chat_before_update() from public, anon, authenticated;
