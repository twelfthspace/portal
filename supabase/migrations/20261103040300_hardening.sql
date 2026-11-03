-- Supabase grants EXECUTE on new public functions to authenticated by default.
-- Take it all back, then allow only the functions the app is meant to call.
revoke execute on all functions in schema public from public, anon, authenticated;
alter default privileges in schema public revoke execute on functions from public, anon, authenticated;

grant execute on function
  public.is_admin(),
  public.is_active_user(),
  public.add_business_days(date, int),
  public.record_payout(uuid, bigint, date, public.pay_method, text, text),
  public.void_payout(uuid, text),
  public.refund_payment(uuid, bigint, text),
  public.reverse_payment(uuid, text),
  public.change_project_rate(uuid, int, text),
  public.reassign_client(uuid, uuid, text),
  public.set_partner_status(uuid, public.account_status, text, uuid),
  public.approve_referral(uuid),
  public.reject_referral(uuid, text),
  public.resolve_referral_flag(uuid, boolean, text),
  public.community_directory(),
  public.pending_invitations()
to authenticated;
grant execute on function public.set_partner_status(uuid, public.account_status, text, uuid),
                          public.is_admin() to service_role;

-- New tables should not be readable by default either.
alter default privileges in schema public revoke all on tables from anon;

-- Indexes for foreign keys flagged by the performance advisor.
create index on public.adjustments (created_by);
create index on public.announcement_reads (user_id);
create index on public.announcements (created_by);
create index on public.community_messages (sender_id);
create index on public.messages (sender_id);
create index on public.payments (recorded_by);
create index on public.payouts (recorded_by);
create index on public.referral_flags (matched_client_id);
create index on public.referral_flags (matched_referral_id);
create index on public.referrals (client_id);
