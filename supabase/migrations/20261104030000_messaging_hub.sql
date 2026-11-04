-- Messaging hub: channels, threads, reactions, attachments (files and voice notes), read tracking.

-- ---------- channels ----------
create table public.channels (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{1,30}$'),
  name text not null check (length(trim(name)) between 2 and 40),
  description text check (description is null or length(description) <= 200),
  admin_only boolean not null default false,   -- only the studio starts posts; everyone can reply in threads
  archived boolean not null default false,
  position int not null default 0,
  created_by uuid default auth.uid() references public.profiles (id),
  created_at timestamptz not null default now()
);
create index on public.channels (created_by);
alter table public.channels enable row level security;
create policy "channels: active members read" on public.channels for select to authenticated
  using ((select public.is_active_user()));
create policy "channels: admin adds" on public.channels for insert to authenticated
  with check ((select public.is_admin()));
create policy "channels: admin edits" on public.channels for update to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
grant select on public.channels to authenticated;
grant insert (slug, name, description, admin_only, position) on public.channels to authenticated;
grant update (name, description, admin_only, archived, position) on public.channels to authenticated;
insert into public.channels (slug, name, description, position) values
  ('general', 'general', 'The whole partner community. Say hello, ask questions, share tips.', 0),
  ('wins', 'wins', 'Closed a deal or got a referral approved? Share it here.', 1);
create trigger audit after insert or update or delete on public.channels
  for each row execute function public.audit_row();

-- ---------- channel messages and threads ----------
alter table public.community_messages
  add column channel_id uuid references public.channels (id) on delete cascade,
  add column parent_id uuid references public.community_messages (id) on delete cascade,
  add column attachments jsonb not null default '[]'::jsonb,
  add column mentions uuid[] not null default '{}',
  add column edited_at timestamptz;
update public.community_messages set channel_id = (select id from public.channels where slug = 'general') where channel_id is null;
alter table public.community_messages alter column channel_id set not null;
alter table public.community_messages drop constraint community_messages_body_check;
alter table public.community_messages add constraint community_messages_body_check
  check (length(body) <= 4000 and (length(trim(body)) > 0 or jsonb_array_length(attachments) > 0));
alter table public.community_messages add constraint community_messages_attachments_check
  check (jsonb_typeof(attachments) = 'array' and jsonb_array_length(attachments) <= 6);
create index on public.community_messages (channel_id, created_at);
create index on public.community_messages (parent_id);

drop policy "community: active users post as themselves" on public.community_messages;
create policy "community: active members post where allowed" on public.community_messages for insert to authenticated
  with check (sender_id = (select auth.uid()) and (select public.is_active_user()) and exists (
    select 1 from public.channels c where c.id = channel_id and not c.archived
      and (not c.admin_only or parent_id is not null or (select public.is_admin()))));
create policy "community: author edits own" on public.community_messages for update to authenticated
  using (sender_id = (select auth.uid()) and (select public.is_active_user()))
  with check (sender_id = (select auth.uid()));
grant insert (body, channel_id, parent_id, attachments, mentions) on public.community_messages to authenticated;
grant update (body) on public.community_messages to authenticated;

-- ---------- direct messages ----------
alter table public.messages
  add column attachments jsonb not null default '[]'::jsonb,
  add column edited_at timestamptz;
alter table public.messages drop constraint messages_body_check;
alter table public.messages add constraint messages_body_check
  check (length(body) <= 4000 and (length(trim(body)) > 0 or jsonb_array_length(attachments) > 0));
alter table public.messages add constraint messages_attachments_check
  check (jsonb_typeof(attachments) = 'array' and jsonb_array_length(attachments) <= 6);
create policy "messages: author or admin deletes" on public.messages for delete to authenticated
  using ((select public.is_admin()) or (sender_id = (select auth.uid()) and (select public.is_active_user())));
create policy "messages: author edits own" on public.messages for update to authenticated
  using (sender_id = (select auth.uid()) and (select public.is_active_user()))
  with check (sender_id = (select auth.uid()));
grant insert (partner_id, body, attachments) on public.messages to authenticated;
grant update (body) on public.messages to authenticated;
grant delete on public.messages to authenticated;
create trigger audit after delete on public.messages
  for each row execute function public.audit_row();

-- Only the author may change the text; only the recipient may mark as read. Edits are stamped.
create function public.chat_before_update() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if new.body is distinct from old.body then
    if auth.uid() is distinct from old.sender_id then raise exception 'You can only edit your own messages.'; end if;
    new.edited_at := now();
  end if;
  if tg_table_name = 'messages' and new.read_at is distinct from old.read_at and auth.uid() = old.sender_id then
    new.read_at := old.read_at;
  end if;
  return new;
end $$;
create trigger chat_guard before update on public.community_messages for each row execute function public.chat_before_update();
create trigger chat_guard before update on public.messages for each row execute function public.chat_before_update();

-- Attachments must point into the sender's own upload folder for that conversation.
create function public.chat_check_attachments() returns trigger
language plpgsql security definer set search_path = '' as $$
declare a jsonb; v_prefix text;
begin
  if tg_table_name = 'community_messages' then
    v_prefix := 'community/' || new.sender_id::text || '/';
    if new.parent_id is not null and not exists (
      select 1 from public.community_messages p where p.id = new.parent_id and p.channel_id = new.channel_id and p.parent_id is null) then
      raise exception 'Replies must belong to a post in the same channel.';
    end if;
  else
    v_prefix := 'dm/' || new.partner_id::text || '/' || new.sender_id::text || '/';
  end if;
  for a in select * from jsonb_array_elements(new.attachments) loop
    if jsonb_typeof(a) <> 'object' or coalesce(a ->> 'path', '') not like v_prefix || '%'
       or length(coalesce(a ->> 'name', '')) not between 1 and 200
       or coalesce((a ->> 'size')::bigint, 0) not between 1 and 26214400 then
      raise exception 'Attachment is not valid.';
    end if;
  end loop;
  return new;
end $$;
create trigger chat_attachments before insert or update of attachments on public.community_messages
  for each row execute function public.chat_check_attachments();
create trigger chat_attachments before insert or update of attachments on public.messages
  for each row execute function public.chat_check_attachments();

-- ---------- reactions ----------
create table public.message_reactions (
  id uuid primary key default gen_random_uuid(),
  message_type text not null check (message_type in ('community', 'dm')),
  message_id uuid not null,
  user_id uuid not null default auth.uid() references public.profiles (id) on delete cascade,
  emoji text not null check (char_length(emoji) between 1 and 16),
  created_at timestamptz not null default now(),
  unique (message_type, message_id, user_id, emoji)
);
create index on public.message_reactions (message_type, message_id);
create index on public.message_reactions (user_id);
alter table public.message_reactions enable row level security;
create function public.can_see_message(p_type text, p_id uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select public.is_active_user() and case
    when p_type = 'community' then exists (select 1 from public.community_messages m where m.id = p_id)
    when p_type = 'dm' then exists (select 1 from public.messages m where m.id = p_id
                                     and (public.is_admin() or m.partner_id = auth.uid()))
    else false end;
$$;
revoke execute on function public.can_see_message(text, uuid) from public, anon;
grant execute on function public.can_see_message(text, uuid) to authenticated;
create policy "reactions: visible with the message" on public.message_reactions for select to authenticated
  using ((select public.can_see_message(message_type, message_id)));
create policy "reactions: add own" on public.message_reactions for insert to authenticated
  with check (user_id = (select auth.uid()) and (select public.can_see_message(message_type, message_id)));
create policy "reactions: remove own" on public.message_reactions for delete to authenticated
  using (user_id = (select auth.uid()));
grant select, delete on public.message_reactions to authenticated;
grant insert (message_type, message_id, emoji) on public.message_reactions to authenticated;

create function public.chat_after_delete() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  delete from public.message_reactions
   where message_type = case when tg_table_name = 'messages' then 'dm' else 'community' end and message_id = old.id;
  return null;
end $$;
create trigger chat_cleanup after delete on public.community_messages for each row execute function public.chat_after_delete();
create trigger chat_cleanup after delete on public.messages for each row execute function public.chat_after_delete();

-- ---------- read tracking for channels ----------
create table public.channel_reads (
  user_id uuid not null default auth.uid() references public.profiles (id) on delete cascade,
  channel_id uuid not null references public.channels (id) on delete cascade,
  last_read_at timestamptz not null default now(),
  primary key (user_id, channel_id)
);
create index on public.channel_reads (channel_id);
alter table public.channel_reads enable row level security;
create policy "channel reads: own" on public.channel_reads for select to authenticated using (user_id = (select auth.uid()));
create policy "channel reads: add own" on public.channel_reads for insert to authenticated with check (user_id = (select auth.uid()));
create policy "channel reads: update own" on public.channel_reads for update to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
grant select on public.channel_reads to authenticated;
grant insert (channel_id, last_read_at) on public.channel_reads to authenticated;
grant update (last_read_at) on public.channel_reads to authenticated;

-- ---------- notifications: mentions, thread replies, and direct-message links ----------
create function public.notify_on_community() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_name text; v_slug text; v_parent_author uuid; r record;
begin
  select full_name into v_name from public.profiles where id = new.sender_id;
  select slug into v_slug from public.channels where id = new.channel_id;
  for r in select p.id, p.role from public.profiles p
           where p.id = any(new.mentions) and p.id <> new.sender_id and p.status = 'active' loop
    insert into public.notifications (user_id, text, link)
    values (r.id, coalesce(v_name, 'Someone') || ' mentioned you in #' || v_slug,
            r.role || '-messages~' || v_slug || case when new.parent_id is not null then '~t-' || new.parent_id else '' end);
  end loop;
  if new.parent_id is not null then
    select sender_id into v_parent_author from public.community_messages where id = new.parent_id;
    if v_parent_author is not null and v_parent_author <> new.sender_id and not (v_parent_author = any(new.mentions)) then
      insert into public.notifications (user_id, text, link)
      select p.id, coalesce(v_name, 'Someone') || ' replied to your post in #' || v_slug,
             p.role || '-messages~' || v_slug || '~t-' || new.parent_id
      from public.profiles p where p.id = v_parent_author and p.status = 'active';
    end if;
  end if;
  return null;
end $$;
create trigger notify after insert on public.community_messages
  for each row execute function public.notify_on_community();

create or replace function public.notify_on_message() returns trigger
language plpgsql security definer set search_path = '' as $$
declare v_name text;
begin
  if new.sender_id = new.partner_id then
    select full_name into v_name from public.profiles where id = new.partner_id;
    perform public.notify_admins(v_name || ' sent you a message', 'admin-messages~dm-' || new.partner_id);
  else
    insert into public.notifications (user_id, text, link)
    values (new.partner_id, 'New message from the studio', 'partner-messages~dm');
  end if;
  return null;
end $$;

revoke execute on function public.chat_before_update(), public.chat_check_attachments(), public.chat_after_delete(),
  public.notify_on_community() from public, anon, authenticated;

-- ---------- file storage for chat ----------
-- community/<sender>/...            readable by every active member
-- dm/<partner>/<sender>/...         readable by that partner and admins
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('chat-files', 'chat-files', false, 26214400, array[
  'image/jpeg','image/png','image/webp','image/gif','application/pdf','text/plain','text/csv',
  'audio/webm','audio/ogg','audio/mp4','audio/mpeg','audio/wav','audio/x-m4a','video/mp4',
  'application/zip','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint','application/vnd.openxmlformats-officedocument.presentationml.presentation']);

create policy "chat files: members read what they can see" on storage.objects for select to authenticated
  using (bucket_id = 'chat-files' and (select public.is_active_user()) and (
    (storage.foldername(name))[1] = 'community'
    or ((storage.foldername(name))[1] = 'dm' and ((select public.is_admin()) or (storage.foldername(name))[2] = (select auth.uid())::text))));
create policy "chat files: upload to own folder" on storage.objects for insert to authenticated
  with check (bucket_id = 'chat-files' and (select public.is_active_user()) and (
    ((storage.foldername(name))[1] = 'community' and (storage.foldername(name))[2] = (select auth.uid())::text)
    or ((storage.foldername(name))[1] = 'dm' and (storage.foldername(name))[3] = (select auth.uid())::text
        and ((select public.is_admin()) or (storage.foldername(name))[2] = (select auth.uid())::text))));
create policy "chat files: remove own or admin" on storage.objects for delete to authenticated
  using (bucket_id = 'chat-files' and ((select public.is_admin())
    or ((storage.foldername(name))[1] = 'community' and (storage.foldername(name))[2] = (select auth.uid())::text)
    or ((storage.foldername(name))[1] = 'dm' and (storage.foldername(name))[3] = (select auth.uid())::text)));

-- ---------- live updates ----------
alter publication supabase_realtime add table public.community_messages, public.messages, public.message_reactions;
