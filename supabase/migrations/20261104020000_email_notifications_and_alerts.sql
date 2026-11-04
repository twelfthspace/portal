-- Notification preferences, emails for every notification, and live alerts.

-- ---------- preferences ----------
alter table public.profiles
  add column notify_email boolean not null default true,    -- send each notification by email
  add column notify_alerts boolean not null default true;   -- pop-up alerts in the portal and on the desktop
grant update (notify_email, notify_alerts) on public.profiles to authenticated;

-- ---------- email delivery ----------
-- Each notification carries a random token. The email function only sends a notification
-- whose id and token match and that has not been emailed yet, so it cannot be used to send
-- arbitrary mail or to send the same email twice.
alter table public.notifications
  add column email_token uuid not null default gen_random_uuid(),
  add column emailed_at timestamptz;

create extension if not exists pg_net with schema extensions;

create function public.notifications_send_email() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if exists (select 1 from public.profiles
             where id = new.user_id and notify_email and status = 'active') then
    perform net.http_post(
      url := 'https://bflvfcvltkpyshnedgtf.supabase.co/functions/v1/send-notification-email',
      body := jsonb_build_object('id', new.id, 'token', new.email_token),
      headers := '{"Content-Type": "application/json"}'::jsonb,
      timeout_milliseconds := 8000);
  end if;
  return null;
end $$;
create trigger send_email after insert on public.notifications
  for each row execute function public.notifications_send_email();
revoke execute on function public.notifications_send_email() from public, anon, authenticated;

-- ---------- live alerts ----------
-- Realtime respects RLS, so each person only receives their own notifications.
alter publication supabase_realtime add table public.notifications;
