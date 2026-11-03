-- Smoke test for access rules. Runs as one block and always rolls back (raises at the end).
do $$
declare
  adm uuid := gen_random_uuid(); ama uuid := gen_random_uuid(); kojo uuid := gen_random_uuid();
  cl uuid; pr uuid; pay uuid; out text := ''; n int; ok boolean; v_ref uuid;
  procedure_note text;
begin
  insert into auth.users (id, email, raw_user_meta_data, aud, role, instance_id)
  values (adm, 'admin@t.test', '{"full_name":"Studio Admin"}', 'authenticated', 'authenticated', '00000000-0000-0000-0000-000000000000'),
         (ama, 'ama@t.test',   '{"full_name":"Ama Mensah"}',  'authenticated', 'authenticated', '00000000-0000-0000-0000-000000000000'),
         (kojo,'kojo@t.test',  '{"full_name":"Kojo Boateng"}','authenticated', 'authenticated', '00000000-0000-0000-0000-000000000000');
  update public.profiles set role = 'admin' where id = adm;

  -- act as admin
  perform set_config('request.jwt.claims', json_build_object('sub', adm, 'role', 'authenticated')::text, true);
  set local role authenticated;
  insert into public.clients (name, partner_id) values ('Accra Bakery', ama) returning id into cl;
  insert into public.projects (client_id, name, budget, rate_bp) values (cl, 'Brand refresh', 1500000, 1500) returning id into pr;
  insert into public.payments (project_id, received_on, amount, tax, method, reference)
    values (pr, current_date - 30, 200000, 0, 'mobile_money', 'MM-1') returning id into pay;
  select commission into n from public.payments where id = pay;
  out := out || 'commission on 2000.00 at 15% = ' || n || E'\n';
  perform public.record_payout(ama, 10000, current_date, 'mobile_money', 'MTN-1', '****1234');
  begin perform public.record_payout(ama, 999999, current_date, 'mobile_money', 'MTN-2'); out := out || 'FAIL overpay allowed' || E'\n';
  exception when others then out := out || 'ok overpay blocked: ' || sqlerrm || E'\n'; end;
  -- rate change does not rewrite history
  perform public.change_project_rate(pr, 500, 'Agreed new rate');
  select commission into n from public.payments where id = pay;
  out := out || 'after rate change, old payment commission = ' || n || E'\n';
  -- reassign keeps history with Ama
  perform public.reassign_client(cl, kojo, 'Moved to Kojo');
  select earned into n from public.partner_balances where partner_id = ama;
  out := out || 'Ama earned after reassign = ' || n || E'\n';
  begin update public.clients set partner_id = ama where id = cl; out := out || 'FAIL direct partner_id update allowed' || E'\n';
  exception when others then out := out || 'ok direct reassign blocked' || E'\n'; end;
  reset role;

  -- act as Ama (partner)
  perform set_config('request.jwt.claims', json_build_object('sub', ama, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n from public.profiles; out := out || 'Ama sees profiles: ' || n || E'\n';
  select count(*) into n from public.payments; out := out || 'Ama sees payments: ' || n || E'\n';
  select count(*) into n from public.clients; out := out || 'Ama sees clients (now Kojo''s): ' || n || E'\n';
  select count(*) into n from public.audit_log; out := out || 'Ama sees audit rows: ' || n || E'\n';
  begin perform public.record_payout(ama, 100, current_date, 'mobile_money', 'X'); out := out || 'FAIL partner payout' || E'\n';
  exception when others then out := out || 'ok partner payout blocked' || E'\n'; end;
  begin update public.profiles set role = 'admin' where id = ama; out := out || 'FAIL self-promote' || E'\n';
  exception when others then out := out || 'ok self-promote blocked' || E'\n'; end;
  update public.profiles set city = 'Accra' where id = ama; out := out || 'ok Ama edits own city' || E'\n';
  insert into public.referrals (business, email) values ('accra bakery', null) returning id into v_ref;
  select status::text into procedure_note from public.referrals where id = v_ref;
  out := out || 'Ama dup referral status = ' || procedure_note || E'\n';
  select count(*) into n from public.referral_flags; out := out || 'Ama sees flag details: ' || n || E'\n';
  begin insert into public.payments (project_id, received_on, amount, method, reference) values (pr, current_date, 100, 'cash', 'C1'); out := out || 'FAIL partner insert payment' || E'\n';
  exception when others then out := out || 'ok partner payment insert blocked' || E'\n'; end;
  reset role;

  -- suspend Kojo, he loses access
  perform set_config('request.jwt.claims', json_build_object('sub', adm, 'role', 'authenticated')::text, true);
  set local role authenticated;
  perform public.set_partner_status(kojo, 'suspended', 'Testing suspension');
  select count(*) into n from public.audit_log where reason is not null; out := out || 'audit rows with reasons: ' || n || E'\n';
  reset role;
  perform set_config('request.jwt.claims', json_build_object('sub', kojo, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n from public.clients; out := out || 'suspended Kojo sees clients: ' || n || E'\n';
  reset role;

  -- anonymous
  perform set_config('request.jwt.claims', '{"role":"anon"}', true);
  set local role anon;
  begin select count(*) into n from public.profiles; out := out || 'FAIL anon read profiles: ' || n || E'\n';
  exception when others then out := out || 'ok anon blocked' || E'\n'; end;
  reset role;

  raise exception E'TEST RESULTS (rolled back)\n%', out;
end $$;
