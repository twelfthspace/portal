// Layout check: opens every page at several screen sizes and reports anything that
// sticks out of the screen or out of its card. Supabase is mocked with realistic data.
// node tools/layout.js site/index.html <dir with supabase.js> <screens dir> [--shots]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [pagePath, sbdir, outdir, flag] = process.argv.slice(2);
const html = fs.readFileSync(pagePath, 'utf8');
const SHOTS = flag === '--shots';

const ADM = '00000000-0000-4000-8000-000000000001', AMA = '00000000-0000-4000-8000-000000000002', KOJO = '00000000-0000-4000-8000-000000000003', OLD = '00000000-0000-4000-8000-000000000004';
const day = n => { const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
const T = new Date().toISOString();
const profiles = [
  { id: ADM, role: 'admin', status: 'active', full_name: 'Twelfth Space Studio', email: 'twelfthspaces@gmail.com', phone: null, city: null, avatar_path: null },
  { id: AMA, role: 'partner', status: 'active', full_name: 'Ama Serwaa Mensah-Bonsu', email: 'ama.serwaa.mensahbonsu@longdomain-example.com', phone: '0240000000', city: 'Accra', avatar_path: null },
  { id: KOJO, role: 'partner', status: 'suspended', full_name: 'Kojo Boateng', email: 'kojo@studio.test', phone: null, city: null, avatar_path: null },
  { id: OLD, role: 'partner', status: 'removed', full_name: 'Former Partner Name', email: 'removed@x.invalid', phone: null, city: null, avatar_path: null }];
const C = i => '10000000-0000-4000-8000-00000000000' + i, P = i => '20000000-0000-4000-8000-00000000000' + i;
const clients = [1, 2, 3].map(i => ({ id: C(i), name: ['Accra Bakery and Pastry Company Limited', 'Kumasi Logistics', 'Osu Fitness Studio'][i - 1], contact: 'Nana Aidoo', email: null, partner_id: i === 2 ? KOJO : AMA, created_at: T }));
const projects = [1, 2, 3].map(i => ({ id: P(i), client_id: C(i), name: ['Complete brand refresh, packaging and signage system', 'Company website', 'Social media retainer'][i - 1], budget: 2500000 * i, rate_bp: 1250, status: ['in_progress', 'on_hold', 'completed'][i - 1], created_at: T }));
const payments = Array.from({ length: 14 }, (_, k) => ({ id: 'p' + k, project_id: P((k % 3) + 1), partner_id: k % 3 === 1 ? KOJO : AMA, rate_bp: 1250, received_on: day(k * 3), amount: 12345678 + k * 1000, tax: 50000, refunded: k === 2 ? 10000 : 0, reversed: k === 5, method: ['mobile_money', 'bank_transfer', 'cash'][k % 3], reference: 'REF-2026-LONG-REFERENCE-' + k, commission: 1500000 + k, created_at: T }));
const data = {
  settings: { id: 1, hold_days: 5, invite_expiry_days: 1 }, clients, projects, payments,
  payouts: [1, 2, 3].map(i => ({ id: 'o' + i, code: 'PO-000' + i, partner_id: AMA, paid_on: day(i * 4), amount: 250000 * i, method: 'mobile_money', reference: 'MTN-77310-' + i, account_mask: '****1234', voided: i === 3, created_at: T })),
  adjustments: [{ id: 'a1', partner_id: AMA, amount: -5000, reason: 'Correction for a duplicated payment that was recorded twice by mistake', created_on: day(2), created_at: T }],
  referrals: [
    { id: 'r1', partner_id: AMA, business: 'Labadi Beach Gym and Wellness Centre', email: 'gym@labadi.test', budget: 300000, status: 'pending', decision_note: null, client_id: null, created_at: T },
    { id: 'r2', partner_id: KOJO, business: 'Accra Bakery', email: null, budget: 0, status: 'flagged', decision_note: null, client_id: null, created_at: T },
    { id: 'r3', partner_id: AMA, business: 'Tema Printworks', email: null, budget: 550000, status: 'rejected', decision_note: 'Outside our service area for now', client_id: null, created_at: T },
    { id: 'r4', partner_id: AMA, business: 'Takoradi Café', email: null, budget: 900000, status: 'approved', decision_note: null, client_id: C(1), created_at: T }],
  referral_flags: [{ referral_id: 'r2', note: 'Same as existing client "Accra Bakery and Pastry Company Limited", attributed to Ama Serwaa Mensah-Bonsu.' }],
  messages: [{ id: 'm1', partner_id: AMA, sender_id: AMA, body: 'Hello studio, a very long message that keeps going to check that chat bubbles wrap properly instead of overflowing the screen on small phones. https://example.com/a/really/long/link/without/spaces/that/could/overflow', read_at: null, created_at: T },
             { id: 'm2', partner_id: AMA, sender_id: ADM, body: 'Thanks, noted.', read_at: null, created_at: T }],
  announcements: [{ id: 'n1', title: 'Payout days move to Fridays from the start of next month', body: 'From this month, recorded payouts are sent on Fridays.\nIf a payout date matters to you, message the studio.', pinned: true, created_at: T }],
  announcement_reads: [],
  community_messages: [{ id: 'c1', sender_id: ADM, body: 'Welcome @Ama to the community space, please read the announcement.', created_at: T }, { id: 'c2', sender_id: AMA, body: 'Thank you!', created_at: T }],
  notifications: [{ id: 'x1', user_id: ADM, text: 'Ama Serwaa Mensah-Bonsu changed their payout details to MTN MoMo •••• 2264', link: 'admin-partners', read_at: null, created_at: T }],
  partner_balances: [{ partner_id: AMA, full_name: 'Ama', earned: 123456789, paid: 750000, held: 1500000, balance: 122706789, available: 121206789 },
                     { partner_id: KOJO, full_name: 'Kojo', earned: 0, paid: 0, held: 0, balance: 0, available: 0 },
                     { partner_id: OLD, full_name: 'Former', earned: 40000, paid: 40000, held: 0, balance: 0, available: 0 }],
  payout_accounts: [{ partner_id: AMA, kind: 'bank', provider: 'Standard Chartered Ghana', account_number: '01234567890123', account_name: 'Ama Serwaa Mensah-Bonsu', branch: 'Accra High Street Branch', updated_at: T }],
  audit_log: [{ id: 1, at: T, actor_id: ADM, action: 'update', entity: 'projects', entity_id: P(1), reason: 'Agreed with the client during the quarterly review meeting', old_row: { name: 'Complete brand refresh', rate_bp: 1000 }, new_row: { name: 'Complete brand refresh', rate_bp: 1250 } }],
};

async function mock(page, me) {
  await page.route('https://portal.test/**', r => r.fulfill({ contentType: 'text/html', body: html }));
  await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(path.join(sbdir, path.basename(new URL(r.request().url()).pathname))) }));
  await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ contentType: 'text/css', body: '' }));
  await page.route('https://bflvfcvltkpyshnedgtf.supabase.co/**', r => {
    const u = new URL(r.request().url()), m = r.request().method(), acc = r.request().headers()['accept'] || '';
    const json = b => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    const user = { id: me.id, email: me.email, aud: 'authenticated', role: 'authenticated', user_metadata: {} };
    if (u.pathname === '/auth/v1/token') return json({ access_token: 'x.y.z', token_type: 'bearer', expires_in: 3600, expires_at: Math.floor(Date.now() / 1000) + 3600, refresh_token: 'r', user });
    if (u.pathname === '/auth/v1/user') return json(user);
    if (u.pathname.startsWith('/storage/')) return json([]);
    if (u.pathname.startsWith('/functions/')) return json({});
    if (u.pathname.startsWith('/rest/v1/rpc/')) {
      const fn = u.pathname.split('/').pop();
      if (fn === 'community_directory') return json(profiles.filter(p => p.status === 'active').map(p => ({ id: p.id, full_name: p.full_name, role: p.role, avatar_path: null })));
      if (fn === 'pending_invitations') return json([{ id: 'i1', email: 'a.very.long.invited.email.address@example-company.com', full_name: 'Nii Lamptey', invited_at: T }]);
      return json(null);
    }
    const t = u.pathname.replace('/rest/v1/', '');
    if (m !== 'GET') return json(acc.includes('object') ? { id: 'n' } : []);
    let rows = t === 'profiles' ? (me.role === 'admin' ? profiles : [me]) : data[t];
    if (me.role === 'partner' && ['referral_flags', 'audit_log', 'notifications'].includes(t)) rows = [];
    if (me.role === 'partner' && ['partner_balances', 'payout_accounts', 'payments', 'payouts', 'adjustments', 'referrals'].includes(t)) rows = rows.filter(b => b.partner_id === me.id);
    if (u.searchParams.get('id') && t === 'profiles') rows = profiles.filter(p => 'eq.' + p.id === u.searchParams.get('id'));
    if (acc.includes('object')) return json(Array.isArray(rows) ? (rows[0] || null) : rows);
    return json(Array.isArray(rows) ? rows : [rows]);
  });
}

// Measures, in the page: page-wide horizontal scroll, and elements poking out of the screen or their card.
const MEASURE = () => {
  const vw = document.documentElement.clientWidth, out = [];
  const name = el => (el.id ? '#' + el.id : el.tagName.toLowerCase()) + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '') + (el.textContent ? ' "' + el.textContent.trim().slice(0, 30) + '"' : '');
  const clips = el => { for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) { const s = getComputedStyle(p); if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) return p; } return null; };
  const visible = el => { const s = getComputedStyle(el); return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity !== 0 && el.getClientRects().length; };
  const root = document.body.classList.contains('authmode') ? document.querySelector('#auth') : document.querySelector('.app');
  const scope = [...root.querySelectorAll('*')].concat([...document.querySelectorAll('#mbg.open *')]);
  for (const el of scope) {
    if (!visible(el) || el.closest('.sr,.tip,.rmenu,.pop,.sres,.sug,.toast,#scrim')) continue;
    if (el.closest('#rail') && !document.querySelector('#rail').classList.contains('open') && innerWidth < 1100) continue;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const c = clips(el);
    if (!c || c === document.documentElement) {
      if (r.right > vw + 1 || r.left < -1) out.push('off-screen: ' + name(el) + ` [${Math.round(r.left)}..${Math.round(r.right)} of ${vw}]`);
    }
    const card = el.closest('.card,.acard,.modal,.glass,.navcard,.prof,.urow');
    let scroller = null; for (let q = el.parentElement; q && q !== card; q = q.parentElement) { const ox = getComputedStyle(q).overflowX; if (ox === 'auto' || ox === 'scroll') { scroller = q; break; } }
    if (card && card !== el && !scroller) {
      const k = card.getBoundingClientRect();
      if (r.right > k.right + 1 || r.left < k.left - 1) out.push('outside card: ' + name(el) + ` [${Math.round(r.left)}..${Math.round(r.right)} card ${Math.round(k.left)}..${Math.round(k.right)}]`);
    }
  }
  // icon buttons and arrows that sit on top of text
  const icons = [...root.querySelectorAll('.mini-link,.swap,.dots,.ibtn,.more,.go,.circ,a > svg.ic,button > svg.ic')].filter(visible);
  const texts = [...root.querySelectorAll('b,span,small,p,h1,h2,h3,label,select,input,.v,.amt,.big,.lab')].filter(t => visible(t) && t.children.length === 0 || /SELECT|INPUT/.test(t.tagName));
  const drawer = document.querySelector('#rail').classList.contains('open') && innerWidth < 1100;
  for (const ic of icons) {
    if (drawer) break; // the open menu drawer covers the page on purpose
    const a = ic.getBoundingClientRect(); if (!a.width) continue;
    for (const t of texts) {
      if (ic.contains(t) || t.contains(ic) || ic.closest('button,a') && ic.closest('button,a').contains(t)) continue;
      if (t.closest('#rail') && !document.querySelector('#rail').classList.contains('open') && innerWidth < 1100) continue;
      const b = t.getBoundingClientRect(); if (!b.width || !b.height) continue;
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 3 && oy > 3) out.push('overlaps: ' + name(ic.closest('button,a') || ic) + ' covers ' + name(t));
    }
  }
  const sw = document.documentElement.scrollWidth;
  if (sw > vw + 1) out.unshift(`PAGE SCROLLS SIDEWAYS: ${sw}px wide on a ${vw}px screen`);
  return [...new Set(out)].slice(0, 12);
};

const SIZES = [[360, 740, 'phone-s'], [390, 844, 'phone'], [768, 1024, 'tablet'], [1000, 760, 'yours'], [1024, 768, 'laptop-s'], [1280, 800, 'laptop'], [1536, 900, 'wide']];

async function run(who, extra) {
  const me = profiles.find(p => p.id === who), report = {};
  const browser = await chromium.launch();
  for (const [w, h, label] of SIZES) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage(); const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await mock(page, me);
    await page.goto('https://portal.test/#signin'); await page.waitForSelector('#signinform');
    report[`${label} auth:signin`] = await page.evaluate(MEASURE);
    if (SHOTS) await page.screenshot({ path: path.join(outdir, `${label}-signin.png`) });
    for (const r of ['forgot']) { await page.evaluate(r => { location.hash = r }, r); await page.waitForTimeout(120); report[`${label} auth:${r}`] = await page.evaluate(MEASURE); }
    await page.evaluate(() => { location.hash = 'signin' }); await page.waitForTimeout(120);
    await page.fill('#f-email', me.email); await page.fill('#f-cur', 'Passw0rd!x'); await page.click('#signinform button[type=submit]');
    await page.waitForFunction(r => location.hash === '#' + r + '-dashboard' && !document.body.classList.contains('authmode'), me.role);
    const routes = (await page.evaluate(() => [...document.querySelectorAll('#nav a')].map(a => a.getAttribute('href').slice(1)))).concat(extra);
    for (const r of routes) {
      await page.evaluate(r => { location.hash = r }, r); await page.waitForTimeout(140);
      const res = await page.evaluate(MEASURE); if (res.length) report[`${label} ${r}`] = res;
      if (SHOTS && (label === 'phone' || label === 'laptop' || label === 'yours')) await page.screenshot({ path: path.join(outdir, `${label}-${r}.png`), fullPage: true });
    }
    // a few dialogs
    const dialogs = me.role === 'admin' ? [['admin-payouts', '[data-act=payout]'], ['admin-partners', '[data-act=invite]'], ['admin-partner-' + AMA, '[data-act=remove]']] : [['partner-referrals', 'button[data-act=referral]']];
    for (const [r, sel] of dialogs) {
      await page.evaluate(r => { location.hash = r }, r); await page.waitForTimeout(140);
      const b = page.locator('#view ' + sel + ':visible').first(); if (!(await b.count())) { report[`${label} dialog ${sel}`] = ['button not visible']; continue; }
      await b.click({ timeout: 5000 }); await page.waitForTimeout(150);
      const res = await page.evaluate(MEASURE); if (res.length) report[`${label} dialog ${sel}`] = res;
      if (SHOTS && label === 'phone-s') await page.screenshot({ path: path.join(outdir, `${label}-dialog-${sel.replace(/\W+/g, '')}.png`) });
      await page.keyboard.press('Escape');
    }
    if (w < 900) { // the menu drawer on small screens
      await page.evaluate(r => { location.hash = r + '-dashboard' }, me.role); await page.waitForTimeout(120);
      const mb = await page.$('#menubtn'); if (mb && await mb.isVisible()) { await mb.click(); await page.waitForTimeout(250); const res = await page.evaluate(MEASURE); if (res.length) report[`${label} menu drawer`] = res; if (SHOTS && label === 'phone') await page.screenshot({ path: path.join(outdir, `${label}-menu.png`) }); }
    }
    if (errs.length) report[`${label} SCRIPT ERRORS`] = errs;
    await ctx.close();
  }
  await browser.close();
  return report;
}
(async () => {
  const a = await run(ADM, ['admin-project-' + P(1), 'admin-partner-' + AMA, 'admin-client-' + C(1), 'admin-settings', 'admin-notifications']);
  const p = await run(AMA, ['partner-profile', 'partner-statement', 'partner-client-' + C(1), 'partner-notifications']);
  const all = Object.assign({}, ...Object.entries(a).map(([k, v]) => ({ ['ADMIN ' + k]: v })), ...Object.entries(p).map(([k, v]) => ({ ['PARTNER ' + k]: v })));
  const bad = Object.entries(all).filter(([, v]) => v.length);
  console.log(bad.length ? JSON.stringify(Object.fromEntries(bad), null, 1) : 'NO LAYOUT PROBLEMS FOUND');
  console.log('pages with problems:', bad.length);
})().catch(e => { console.error(e); process.exit(1); });
