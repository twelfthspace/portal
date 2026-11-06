// Invitation links: the owner makes a fresh link for someone who never accepted, and the invitee
// opens it, sees an Accept button (nothing is redeemed until they press it), and lands on Set up your account.
// node tools/invite_test.js site/index.html <dir with supabase.js>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [pagePath, sbdir] = process.argv.slice(2);
const html = fs.readFileSync(pagePath, 'utf8');
const ADM = '00000000-0000-4000-8000-000000000001', FRA = '00000000-0000-4000-8000-000000000009';
const T = '2026-11-04T10:36:14.919Z', TOKEN = 'a'.repeat(56);
const profiles = [
  { id: ADM, role: 'admin', status: 'active', full_name: 'Twelfth Space', email: 'owner@studio.test', phone: null, city: null, avatar_path: null, created_at: T },
  { id: FRA, role: 'partner', status: 'active', full_name: 'Francisca Anamsakia', email: 'francisca@example.com', phone: null, city: null, avatar_path: null, created_at: T },
];
const out = [], fail = [];
const check = (ok, what) => { (ok ? out : fail).push((ok ? 'ok   ' : 'FAIL ') + what); };

async function open(meId, url, opts = {}) {
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 1280, height: 860 } })).newPage();
  const st = { me: meId, verify: 0, calls: [], errors: [] };
  page.on('pageerror', e => st.errors.push(e.message));
  await page.route('https://portal.test/**', r => r.fulfill({ contentType: 'text/html', body: html }));
  await page.route('https://cdn.jsdelivr.net/**', r => r.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(path.join(sbdir, path.basename(new URL(r.request().url()).pathname))) }));
  await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ contentType: 'text/css', body: '' }));
  await page.route('https://bflvfcvltkpyshnedgtf.supabase.co/**', r => {
    const u = new URL(r.request().url()), m = r.request().method(), acc = r.request().headers()['accept'] || '';
    const json = (b, s = 200) => r.fulfill({ status: s, contentType: 'application/json', body: JSON.stringify(b) });
    const me = profiles.find(p => p.id === st.me);
    const user = me && { id: me.id, email: me.email, aud: 'authenticated', role: 'authenticated', user_metadata: {} };
    const session = () => ({ access_token: 'fake.jwt.token', token_type: 'bearer', expires_in: 3600, expires_at: Math.floor(Date.now() / 1000) + 3600, refresh_token: 'r', user });
    if (u.pathname === '/auth/v1/verify') {
      st.verify++; st.calls.push('verify ' + r.request().postData());
      if (opts.badToken) return json({ code: 403, error_code: 'otp_expired', msg: 'Email link is invalid or has expired' }, 403);
      st.me = FRA; const fu = profiles[1];
      return json({ access_token: 'fake.jwt.token', token_type: 'bearer', expires_in: 3600, expires_at: Math.floor(Date.now() / 1000) + 3600, refresh_token: 'r', user: { id: fu.id, email: fu.email, aud: 'authenticated', role: 'authenticated', user_metadata: {} } });
    }
    if (u.pathname === '/auth/v1/token') return json(session());
    if (u.pathname === '/auth/v1/user') return user ? json(user) : json({ msg: 'no' }, 401);
    if (u.pathname === '/auth/v1/logout') return r.fulfill({ status: 204, body: '' });
    if (u.pathname.startsWith('/functions/v1/')) {
      const b = r.request().postData(); st.calls.push('function ' + b);
      return json(JSON.parse(b).send_email ? { sent: true } : { link: 'https://twelfthspace.github.io/portal/#join=' + TOKEN });
    }
    if (u.pathname.startsWith('/rest/v1/rpc/')) {
      const fn = u.pathname.split('/').pop();
      if (fn === 'pending_invitations') return json([{ id: FRA, email: 'francisca@example.com', full_name: 'Francisca Anamsakia', invited_at: T, role: 'partner' }]);
      if (fn === 'community_directory') return json(profiles.map(p => ({ id: p.id, full_name: p.full_name, role: p.role, avatar_path: null })));
      return json(null);
    }
    if (u.pathname.startsWith('/storage/v1/')) return json([]);
    const t = u.pathname.replace('/rest/v1/', '');
    if (m !== 'GET') return json([]);
    if (t === 'profiles') {
      let rows = me && me.role !== 'partner' ? profiles : profiles.filter(p => me && p.id === me.id);
      if (u.searchParams.get('id')) rows = profiles.filter(p => 'eq.' + p.id === u.searchParams.get('id'));
      return json(acc.includes('object') ? rows[0] || null : rows);
    }
    if (t === 'settings') return json(acc.includes('object') ? { id: 1, hold_days: 5 } : [{ id: 1, hold_days: 5 }]);
    return json(acc.includes('object') ? null : []);
  });
  if (opts.signedIn) {
    await page.goto('https://portal.test/#signin'); await page.waitForSelector('#signinform');
    await page.fill('#f-email', profiles.find(p => p.id === meId).email); await page.fill('#f-cur', 'Passw0rd!x');
    await page.click('#signinform button[type=submit]');
    await page.waitForFunction(() => /-dashboard$/.test(location.hash) && !document.body.classList.contains('authmode'), null, { timeout: 10000 });
  }
  if (url) { await page.goto(url); await page.waitForTimeout(700); }
  return { browser, page, st };
}

(async () => {
  // 1. Owner: Francisca shows as Invited, and a new link can be made and shared on WhatsApp.
  {
    const { browser, page, st } = await open(ADM, null, { signedIn: true });
    await page.evaluate(() => { location.hash = 'admin-partners' }); await page.waitForTimeout(300);
    const row = await page.evaluate(() => [...document.querySelectorAll('tr')].map(t => t.textContent).find(t => t.includes('Francisca')) || '');
    check(row.includes('Invited') && !row.includes('Active'), 'partners table shows Francisca as Invited: ' + row.replace(/\s+/g, ' ').slice(0, 80));
    check(await page.isVisible('[data-act=relink][data-id="' + FRA + '"]'), 'pending invitations list has a New link button');
    await page.evaluate(id => { location.hash = 'admin-partner-' + id }, FRA); await page.waitForTimeout(300);
    await page.setViewportSize({ width: 1440, height: 900 }); await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(process.env.SHOTS || '.', 'invite-owner-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 1280, height: 860 });
    const ban = await page.textContent('.pban');
    check(ban.includes("hasn't accepted the invitation yet") && ban.includes('Emailed 4 Nov'), 'partner page banner says the invitation was not accepted, emailed 4 Nov');
    check((await page.textContent('.phd')).includes('Invited') && (await page.textContent('.pset')).includes('0 of 5'), 'header shows Invited and setup shows 0 of 5');
    check(!(await page.isVisible('.pwal [data-chat]')), 'no "Ask her to add it" chat button before she has joined');
    await page.click('.pban [data-act=relink]'); await page.waitForTimeout(200);
    await page.fill('#f-wa', '024 123 4567');
    await page.click('#mform button[type=submit]'); await page.waitForTimeout(500);
    check(st.calls.some(c => c === 'function {"action":"invite_link","user_id":"' + FRA + '","send_email":false}'), 'asks the server for a fresh link');
    const box = await page.inputValue('#linkbox').catch(() => '');
    check(box === 'https://twelfthspace.github.io/portal/#join=' + TOKEN, 'shows the new link');
    const wa = await page.getAttribute('#modal a[href^="https://wa.me/"]', 'href').catch(() => '');
    check(decodeURIComponent(wa || '').includes('#join=' + TOKEN) && decodeURIComponent(wa).includes('Hi Francisca'), 'Send on WhatsApp is prefilled with a greeting and the link');
    check((wa || '').startsWith('https://wa.me/233241234567?text='), 'with a number, WhatsApp opens straight to her chat: ' + (wa || '').slice(0, 40));
    check((await page.textContent('#modal')).includes('Send to Francisca on WhatsApp'), 'button says Send to Francisca on WhatsApp');
    await page.click('[data-close]');
    await page.click('.pban [data-act=relink]'); await page.waitForTimeout(200);
    await page.fill('#f-wa', '12ab'); await page.click('#mform button[type=submit]'); await page.waitForTimeout(150);
    check((await page.textContent('#merr')).includes('digits only'), 'a bad WhatsApp number is caught');
    await page.fill('#f-wa', '');
    await page.selectOption('#f-how', 'email'); await page.click('#mform button[type=submit]'); await page.waitForTimeout(500);
    check(st.calls.some(c => c.includes('"send_email":true')), 'Email it again asks the server to re-send the email');
    check((await page.textContent('#toast')).includes('Spam'), 'tells you to ask her to check Spam: ' + await page.textContent('#toast'));
    await page.setViewportSize({ width: 390, height: 844 }); await page.evaluate(() => { location.hash = 'admin-partner-00000000-0000-4000-8000-000000000009' }); await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(process.env.SHOTS || '.', 'invite-owner-phone.png'), fullPage: false });
    check(st.errors.length === 0, 'no page errors (owner) ' + st.errors.join(' | '));
    await browser.close();
  }
  // 2. Invitee: opening the link does nothing until Accept is pressed.
  {
    const { browser, page, st } = await open(null, 'https://portal.test/#join=' + TOKEN);
    check(await page.isVisible('[data-act=joinnow]'), 'invitee sees an Accept invitation button');
    check(await page.evaluate(() => location.hash) === '#join', 'the token is removed from the address bar');
    check(st.verify === 0, 'nothing is redeemed just by opening the link (previews are safe)');
    await page.screenshot({ path: path.join(process.env.SHOTS || '.', 'invite-join.png') });
    await page.click('[data-act=joinnow]');
    await page.waitForSelector('#acceptform', { timeout: 8000 }).catch(() => {});
    check(st.verify === 1 && st.calls[0].includes('"token_hash":"' + TOKEN + '"') && st.calls[0].includes('"type":"invite"'), 'Accept redeems the token once: ' + st.calls[0]);
    check(await page.evaluate(() => location.hash) === '#accept-invite' && await page.isVisible('#acceptform'), 'lands on Set up your account');
    check(st.errors.length === 0, 'no page errors (invitee) ' + st.errors.join(' | '));
    await browser.close();
  }
  // 3. An old or used link says so.
  {
    const { browser, page, st } = await open(null, 'https://portal.test/#join=' + TOKEN, { badToken: true });
    await page.click('[data-act=joinnow]'); await page.waitForTimeout(800);
    check(await page.evaluate(() => location.hash) === '#accept-invite-expired', 'an expired link shows "This invitation is no longer valid"');
    check(st.errors.length === 0, 'no page errors (expired) ' + st.errors.join(' | '));
    await browser.close();
  }
  console.log(out.concat(fail).join('\n'));
  console.log(fail.length ? fail.length + ' FAILED' : 'ALL PASSED');
  process.exit(fail.length ? 1 : 0);
})();
