# Twelfth Space Growth Partner portal

Private portal for the studio and its invited Growth Partners. The page itself is a static site (GitHub Pages). Everything private lives in Supabase and is protected by Row Level Security: the page's code is public, the data is not.

- Supabase project: `twelfth-space-portal` (`bflvfcvltkpyshnedgtf`, eu-west-3)
- API URL: `https://bflvfcvltkpyshnedgtf.supabase.co`
- Browser key: the **publishable** key (`sb_publishable_...`). It is safe in the page. Never put a `sb_secret_...` key in the page or the repo.

## What is where

| Path | What it does |
| --- | --- |
| `supabase/migrations/` | Tables, access rules (RLS), money functions, audit log, notifications. Already applied to the project. |
| `supabase/functions/partner-admin/` | Edge Function for invite, revoke invite, suspend, reactivate. Already deployed. |
| `supabase/tests/rls_smoke_test.sql` | Access-rule test. Run it in the SQL editor; it always rolls back and prints results as an error. |
| `site/index.html` | The live portal page. Published by `.github/workflows/pages.yml` on every push to `main`. |
| `tools/make_live.py` | Rebuilds `site/index.html` from the design preview: `python3 -I tools/make_live.py preview.html site/index.html`. |
| `tools/smoke.js` | Headless browser test with Supabase mocked: signs in as admin and partner and opens every page. |

## Rules the database enforces

- Money is whole pesewas; rates are basis points (1250 = 12.5%).
- Each payment keeps the partner and rate it had when recorded. Changing a project's rate or reassigning a client only affects payments recorded afterwards.
- Payments, payouts and adjustments cannot be edited or deleted. Refund, reverse, void, rate change, reassign and suspend go through functions that require a reason and write it to `audit_log`.
- `record_payout` locks the partner and refuses more than the available balance (earned − paid − commission still in its hold period).
- Partners only see their own clients, projects they earned on, payments, payouts, referrals, messages and notifications. Suspended partners see nothing.
- Duplicate referrals are flagged automatically; the reason (which names the other partner) is visible to admins only, in `referral_flags`.

## Calling it from the page

```js
const sb = supabase.createClient('https://bflvfcvltkpyshnedgtf.supabase.co', 'sb_publishable_...');
await sb.auth.signInWithPassword({ email, password });
const { data: bal } = await sb.from('partner_balances').select('*');          // own row for partners, all for admin
await sb.rpc('record_payout', { p_partner, p_amount: 50000, p_paid_on: '2026-11-03',
  p_method: 'mobile_money', p_reference: 'MTN-123', p_account_mask: '****1234' });
await sb.functions.invoke('partner-admin', { body: { action: 'invite', email, full_name, send_email: false } });
```

## One-time setup in the Supabase dashboard

1. **Authentication → Sign In / Providers**: turn **off** "Allow new users to sign up". Invites still work.
2. **Authentication → URL Configuration**: set Site URL to the portal's address (for example `https://twelfthspace.github.io/portal/`) and add the same address to Redirect URLs. Invite and reset links land there and the page takes it from the link.
3. **Edge Functions → Secrets**: add `PORTAL_URL` (e.g. `https://portal.example.com`) and `PORTAL_ORIGIN` (same value, so only your site can call the function).
4. **Authentication → Emails → SMTP**: connect your own email provider. The built-in sender is heavily rate limited and is not meant for real invites.
5. **First admin**: Authentication → Users → Invite user with your own email, accept the invite, then run:
   ```sql
   update public.profiles set role = 'admin' where email = 'you@example.com';
   ```
6. Optional on paid plans: turn on leaked password protection.

Invite and reset links expire according to Auth's email link expiry setting (24 hours at most). The page says 24 hours for invites and 1 hour for resets.

## Publishing on GitHub Pages

In the repo: **Settings → Pages → Source: GitHub Actions**. Pages from a private repository needs a paid GitHub plan, and the published site is public either way. That is fine: the page holds no data, and sign-in plus RLS guard everything.
