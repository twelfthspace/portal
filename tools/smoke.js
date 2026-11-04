// Headless smoke test of the live portal page with Supabase mocked out.
// node smoke.js <index.html> <supabase.js dir> <screens dir>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [page_, sbdir, outdir] = process.argv.slice(2);
const html = fs.readFileSync(page_, 'utf8');

const ADM = '00000000-0000-4000-8000-000000000001', AMA = '00000000-0000-4000-8000-000000000002', KOJO = '00000000-0000-4000-8000-000000000003';
const CL1 = '10000000-0000-4000-8000-000000000001', PR1 = '20000000-0000-4000-8000-000000000001';
const day = n => { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
const T = new Date().toISOString();
const profiles = [
  { id: ADM, role: 'admin', status: 'active', full_name: 'Studio Admin', email: 'admin@studio.test', phone: null, city: null, account_mask: null },
  { id: AMA, role: 'partner', status: 'active', full_name: 'Ama Mensah', email: 'ama@studio.test', phone: '0240000000', city: 'Accra', account_mask: '****1234' },
  { id: KOJO, role: 'partner', status: 'active', full_name: 'Kojo Boateng', email: 'kojo@studio.test', phone: null, city: null, account_mask: null }];
const data = {
  settings: { id: 1, hold_days: 5, invite_expiry_days: 1 },
  clients: [{ id: CL1, name: 'Accra Bakery', contact: 'Nana', email: null, partner_id: AMA, created_at: T }],
  projects: [{ id: PR1, client_id: CL1, name: 'Brand refresh', budget: 1500000, rate_bp: 1500, status: 'in_progress', created_at: T }],
  payments: [
    { id: 'p1', project_id: PR1, partner_id: AMA, rate_bp: 1500, received_on: day(30), amount: 200000, tax: 0, refunded: 0, reversed: false, method: 'mobile_money', reference: 'MM-1', commission: 30000, created_at: T },
    { id: 'p2', project_id: PR1, partner_id: AMA, rate_bp: 1500, received_on: day(1), amount: 100000, tax: 10000, refunded: 0, reversed: false, method: 'bank_transfer', reference: 'BT-2', commission: 13500, created_at: T }],
  payouts: [{ id: 'o1', code: 'PO-0001', partner_id: AMA, paid_on: day(3), amount: 10000, method: 'mobile_money', reference: 'MTN-1', account_mask: '****1234', voided: false, created_at: T }],
  adjustments: [{ id: 'a1', partner_id: AMA, amount: -500, reason: 'Correction', created_on: day(2), created_at: T }],
  referrals: [{ id: 'r1', partner_id: AMA, business: 'Labadi Gym', email: null, budget: 300000, status: 'pending', decision_note: null, client_id: null, created_at: T },
              { id: 'r2', partner_id: KOJO, business: 'Accra Bakery', email: null, budget: 0, status: 'flagged', decision_note: null, client_id: null, created_at: T }],
  referral_flags: [{ referral_id: 'r2', note: 'Same as existing client "Accra Bakery", attributed to Ama Mensah.' }],
  messages: [{ id: 'm1', partner_id: AMA, sender_id: AMA, body: 'Hello <b>studio</b>', read_at: null, created_at: T }],
  announcements: [{ id: 'n1', title: 'Payout days', body: 'Payouts move to Fridays from now on.', pinned: true, created_at: T }],
  announcement_reads: [],
  community_messages: [{ id: 'c1', sender_id: ADM, body: 'Welcome @Ama', created_at: T }],
  notifications: [{ id: 'x1', user_id: ADM, text: 'Ama Mensah sent a message', link: 'admin-messages', read_at: null, created_at: T }],
  partner_balances: [{ partner_id: AMA, full_name: 'Ama Mensah', earned: 43000, paid: 10000, held: 13500, balance: 33000, available: 19500 },
                     { partner_id: KOJO, full_name: 'Kojo Boateng', earned: 0, paid: 0, held: 0, balance: 0, available: 0 }],
  payout_accounts: [{ partner_id: AMA, kind: 'momo', provider: 'MTN MoMo', account_number: '0240312264', account_name: 'Ama Mensah', branch: null, updated_at: T }],
  audit_log: [{ id: 1, at: T, actor_id: ADM, action: 'update', entity: 'projects', entity_id: PR1, reason: 'Agreed', old_row: { name: 'Brand refresh', rate_bp: 1000 }, new_row: { name: 'Brand refresh', rate_bp: 1500 } }],
};

async function run(who) {
  const me = profiles.find(p => p.id === who);
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 } });
  const page = await ctx.newPage();
  const errors = [], writes = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.route('https://portal.test/**', r => r.fulfill({ contentType: 'text/html', body: html }));
  await page.route('https://cdn.jsdelivr.net/**', r => {
    const f = path.join(sbdir, path.basename(new URL(r.request().url()).pathname));
    r.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(f) });
  });
  await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ contentType: 'text/css', body: '' }));
  await page.route('https://bflvfcvltkpyshnedgtf.supabase.co/**', r => {
    const u = new URL(r.request().url()), m = r.request().method(), acc = r.request().headers()['accept'] || '';
    const json = (b, s = 200) => r.fulfill({ status: s, contentType: 'application/json', body: JSON.stringify(b) });
    const user = { id: me.id, email: me.email, aud: 'authenticated', role: 'authenticated', user_metadata: {} };
    if (u.pathname === '/auth/v1/token') return json({ access_token: 'fake.jwt.token', token_type: 'bearer', expires_in: 3600, expires_at: Math.floor(Date.now() / 1000) + 3600, refresh_token: 'r', user });
    if (u.pathname === '/auth/v1/user') return json(user);
    if (u.hostname === 'bflvfcvltkpyshnedgtf.supabase.co' && u.pathname.startsWith('/storage/v1/object/sign/avatars/') && m === 'GET') return r.fulfill({ contentType: 'image/png', body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64') });
    if (u.pathname === '/auth/v1/logout') return r.fulfill({ status: 204, body: '' });
    if (u.pathname.startsWith('/functions/v1/')) { writes.push('function ' + r.request().postData()); return json({ removed: true }); }
    if (u.pathname.startsWith('/rest/v1/rpc/')) {
      const fn = u.pathname.split('/').pop();
      if (fn === 'community_directory') return json(profiles.map(p => ({ id: p.id, full_name: p.full_name, role: p.role, avatar_path: p.id === AMA ? AMA + '/avatar-1.jpg' : null })));
      if (fn === 'pending_invitations') return json([{ id: 'i1', email: 'nii@studio.test', full_name: 'Nii Lamptey', invited_at: T }]);
      writes.push(m + ' rpc ' + fn + ' ' + r.request().postData()); return json(null);
    }
    if (u.pathname.startsWith('/storage/v1/object/sign/')) { const b = JSON.parse(r.request().postData() || '{}'); return json((b.paths || []).map(x => ({ path: x, signedURL: '/object/sign/avatars/' + x + '?token=t', error: null }))); }
    if (u.pathname.startsWith('/storage/v1/object/avatars/')) { writes.push(m + ' storage ' + u.pathname.replace('/storage/v1/object/', '')); return json({ Key: 'avatars/x', Id: 'x' }); }
    if (u.pathname.startsWith('/storage/v1/')) { return json([]); }
    const t = u.pathname.replace('/rest/v1/', '');
    if (m !== 'GET') { writes.push(m + ' ' + t + ' ' + (r.request().postData() || u.search)); return json(acc.includes('object') ? { id: 'new-id', status: 'pending' } : []); }
    let rows = t === 'profiles' ? (me.role === 'admin' ? profiles : [me]) : data[t];
    if (me.role === 'partner' && Array.isArray(rows) && ['referral_flags', 'audit_log'].includes(t)) rows = [];
    if (me.role === 'partner' && t === 'partner_balances') rows = rows.filter(b => b.partner_id === me.id);
    if (me.role === 'partner' && t === 'notifications') rows = [];
    if (u.searchParams.get('id') && t === 'profiles') rows = profiles.filter(p => 'eq.' + p.id === u.searchParams.get('id'));
    if (acc.includes('object')) return json(Array.isArray(rows) ? (rows[0] || null) : rows);
    return json(Array.isArray(rows) ? rows : [rows]);
  });
  await page.goto('https://portal.test/#signin');
  await page.waitForSelector('#signinform');
  await page.screenshot({ path: path.join(outdir, 'signin.png') });
  await page.fill('#f-email', me.email); await page.fill('#f-cur', 'Passw0rd!x');
  await page.click('#signinform button[type=submit]');
  await page.waitForFunction(r => location.hash === '#' + r + '-dashboard' && !document.body.classList.contains('authmode'), me.role, { timeout: 10000 });
  const routes = await page.evaluate(() => [...document.querySelectorAll('#nav a')].map(a => a.getAttribute('href').slice(1)));
  const extra = me.role === 'admin' ? ['admin-project-' + PR1, 'admin-partner-' + AMA, 'admin-client-' + CL1, 'admin-settings', 'admin-notifications']
                                    : ['partner-profile', 'partner-statement', 'partner-client-' + CL1, 'partner-notifications', 'admin-dashboard'];
  const bad = [];
  for (const r of routes.concat(extra)) {
    await page.evaluate(r => { location.hash = r }, r); await page.waitForTimeout(150);
    const txt = await page.textContent('#view');
    if (/Something went wrong|could not find that page/.test(txt)) bad.push(r);
    if (r.endsWith('-dashboard') || r === 'admin-referrals' || r === 'admin-partners' || r === 'partner-commissions') await page.screenshot({ path: path.join(outdir, r + '.png'), fullPage: false });
  }
  const finalHash = await page.evaluate(() => location.hash);
  // exercise a few writes
  if (me.role === 'admin') {
    await page.evaluate(() => { location.hash = 'admin-payouts' }); await page.waitForTimeout(150);
    await page.click('[data-act=payout][data-id="' + AMA + '"]');
    await page.fill('#f-amt', '50.00'); await page.fill('#f-ref', 'MTN-9'); await page.fill('#f-mask', '****9');
    await page.click('#mform button[type=submit]'); await page.waitForTimeout(400);
    await page.click('[data-act=payout][data-id="' + AMA + '"]');
    await page.fill('#f-amt', '9999.00'); await page.fill('#f-ref', 'MTN-10');
    await page.click('#mform button[type=submit]'); await page.waitForTimeout(200);
    writes.push('overpay msg: ' + await page.textContent('#merr'));
    await page.click('[data-close]');
    // view as partner (read-only)
    await page.evaluate(id => { location.hash = 'admin-partner-' + id }, AMA); await page.waitForTimeout(200);
    await page.click('[data-act=viewas]'); await page.waitForTimeout(300);
    const va = await page.evaluate(() => ({ hash: location.hash, banner: !!document.querySelector('[data-act=exitview]'), nav: [...document.querySelectorAll('#nav a')].length, who: document.querySelector('#urow b').textContent }));
    writes.push('view-as: ' + JSON.stringify(va));
    const before = writes.length;
    await page.click('button[data-act=referral]'); await page.waitForTimeout(150);
    writes.push('view-as blocked write: modal open=' + await page.evaluate(() => document.querySelector('#mbg').classList.contains('open')) + ' toast=' + await page.textContent('#toast'));
    await page.evaluate(() => { location.hash = 'admin-payouts' }); await page.waitForTimeout(250);
    writes.push('view-as admin url sends to: ' + await page.evaluate(() => location.hash));
    await page.screenshot({ path: path.join(outdir, 'view-as.png') });
    await page.click('[data-act=exitview]'); await page.waitForTimeout(300);
    writes.push('after exit: ' + await page.evaluate(() => location.hash + ' nav=' + document.querySelectorAll('#nav a').length));
    // remove partner
    await page.click('[data-act=remove]'); await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(outdir, 'remove-modal.png') });
    await page.fill('#f-reason', 'Resigned in November'); await page.click('#mform button[type=submit]'); await page.waitForTimeout(150);
    writes.push('remove without confirm: ' + await page.textContent('#merr'));
    await page.fill('#f-confirm', 'remove'); await page.click('#mform button[type=submit]'); await page.waitForTimeout(500);
    writes.push('after remove: ' + await page.evaluate(() => location.hash));
  } else {
    await page.evaluate(() => { location.hash = 'partner-profile' }); await page.waitForTimeout(200);
    writes.push('photo shown: ' + await page.evaluate(() => !!document.querySelector('.pav img')));
    await page.fill('#f-phone', 'Raymond Kwabla'); await page.click('#pform button[type=submit]'); await page.waitForTimeout(100);
    writes.push('bad phone msg: ' + await page.textContent('#perr'));
    await page.fill('#f-phone', '+233 24 031-2264'); await page.click('#pform .sw input[name=notify_email]'); await page.click('#pform button[type=submit]'); await page.waitForTimeout(300);
    await page.fill('#f-acct', '024 031 2264'); await page.fill('#f-acct2', '0240312265'); await page.click('#payform button[type=submit]'); await page.waitForTimeout(100);
    writes.push('mismatch msg: ' + await page.textContent('#payerr'));
    await page.fill('#f-acct2', '+233240312264'); await page.click('#payform button[type=submit]'); await page.waitForTimeout(300);
    await page.selectOption('#f-kind', 'bank'); await page.waitForTimeout(150);
    writes.push('bank form: branch=' + await page.evaluate(() => !!document.querySelector('#f-branch')) + ' label=' + await page.textContent('label[for=f-provider]'));
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
    await page.setInputFiles('#photo-in', { name: 'me.png', mimeType: 'image/png', buffer: png }); await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(outdir, 'partner-profile.png'), fullPage: true });
    await page.evaluate(() => { location.hash = 'partner-referrals' }); await page.waitForTimeout(150);
    await page.click('button[data-act=referral]'); await page.fill('#f-biz', 'Tema Prints');
    await page.click('#mform button[type=submit]'); await page.waitForTimeout(400);
    const xss = await page.evaluate(() => { location.hash = 'partner-messages'; return new Promise(r => setTimeout(() => r(document.querySelector('#msgs').innerHTML), 200)) });
    writes.push('message html: ' + xss.slice(0, 120));
  }
  await page.click('[data-act=signout]'); await page.waitForTimeout(400);
  const afterOut = await page.evaluate(() => location.hash);
  console.log(JSON.stringify({ who: me.role, routes: routes.length + extra.length, bad, finalHash, afterOut, errors, writes }, null, 1));
  await browser.close();
}
(async () => { await run(ADM); await run(AMA); })().catch(e => { console.error(e); process.exit(1); });
