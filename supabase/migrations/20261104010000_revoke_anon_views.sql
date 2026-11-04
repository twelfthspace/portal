-- Signed-out visitors get nothing from the summary views (they already returned no rows).
revoke all on public.ledger, public.partner_balances from anon;
