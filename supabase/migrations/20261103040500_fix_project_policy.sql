-- Qualify column references so "id" means projects.id, not payments.id.
drop policy if exists "projects: own client, earned on, or admin" on public.projects;
create policy "projects: own client, earned on, or admin" on public.projects for select to authenticated
  using ((select public.is_admin()) or ((select public.is_active_user()) and (
    exists (select 1 from public.clients c where c.id = projects.client_id and c.partner_id = (select auth.uid()))
    or exists (select 1 from public.payments p where p.project_id = projects.id and p.partner_id = (select auth.uid())))));
