-- A partner keeps seeing projects they earned commission on, even after the client is reassigned.
drop policy "projects: own client or admin" on public.projects;
create policy "projects: own client, earned on, or admin" on public.projects for select to authenticated
  using ((select public.is_admin()) or ((select public.is_active_user()) and (
    exists (select 1 from public.clients c where c.id = projects.client_id and c.partner_id = (select auth.uid()))
    or exists (select 1 from public.payments p where p.project_id = projects.id and p.partner_id = (select auth.uid())))));

-- Ledger rows never disappear because a related row is hidden.
create or replace view public.ledger with (security_invoker = true) as
select p.received_on as on_date, p.partner_id,
       case when p.reversed then 'reversed' else 'accrual' end as kind,
       coalesce(pj.name, 'Project') || ' · ' || p.reference as detail, p.commission as amount, p.id as source_id
from public.payments p left join public.projects pj on pj.id = p.project_id
union all
select po.paid_on, po.partner_id, 'payout', po.code || ' · ' || po.reference, -po.amount, po.id
from public.payouts po where not po.voided
union all
select ad.created_on, ad.partner_id, 'adjustment', ad.reason, ad.amount, ad.id
from public.adjustments ad;
