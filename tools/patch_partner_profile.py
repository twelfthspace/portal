"""A richer partner page for the studio: profile cover with photo and contact chips, readiness,
a commission bar, a payout card, an activity feed and tabbed tables.
python3 -I tools/patch_partner_profile.py site/index.html"""
import sys
p = sys.argv[1]
h = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f'expected {count}, found {n}: {old[:100]!r}')
    h = h.replace(old, new)

# icons
rep("const ic=(n,s=20,w=1.8)=>", '''Object.assign(I,{copy:"M9 9h11v11H9zM5 15H4V4h11v1",phone:"M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z",pin:"M12 22s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5",eye:"M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6",eyeoff:"M3 3l18 18M10.6 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.2M6.6 6.6A17 17 0 0 0 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6M9.9 9.9a3 3 0 0 0 4.2 4.2",wa:"M21 11.5a8.4 8.4 0 0 1-12.3 7.5L3 21l2-5.6A8.4 8.4 0 1 1 21 11.5zM9 9.5c0 3 2.5 5.5 5.5 5.5"});
const ic=(n,s=20,w=1.8)=>''')

# the page heading is the name on the profile cover
rep("(key==='dashboard'?'<h1 class=\"sr\">Dashboard</h1>':`<h1 class=\"ptitle\">${esc(title)}</h1>`)",
    "(key==='dashboard'?'<h1 class=\"sr\">Dashboard</h1>':route.startsWith('admin-partner-')?`<h1 class=\"sr\">${esc(title)}</h1>`:`<h1 class=\"ptitle\">${esc(title)}</h1>`)")

# tab clicks
rep("  const tb=t.closest('[data-tab]');",
    "  const ptb=t.closest('[data-ptab]');if(ptb){S.ptab=ptb.dataset.ptab;const y=scrollY;render();scrollTo(0,y);return}\n  const tb=t.closest('[data-tab]');")

# the page
old_start = "PG.partnerD=id=>{const p=P(id);if(!p)return PG['admin-partners']();"
old_end = "${card('Referrals sent',tbl(['Business','Budget','Status'],rf.map(r=>({c:[`<b>${esc(r.biz)}</b>`,r.bud?g(r.bud):'—',stTag(r.st)]})),[1]))}</div>`};"
i = h.index(old_start); j = h.index(old_end, i) + len(old_end)
if h.count(old_start) != 1: sys.exit('partnerD start not unique')
h = h[:i] + r'''PG.partnerD=id=>{const p=P(id);if(!p)return PG['admin-partners']();
  return `<div class="pha">${back('admin-partners','Partners')}<span class="grow"></span><button type="button" class="btn white" data-chat="${id}">${ic('chat',16)} Message</button>${p.st==='Removed'?'':act('View as partner','viewas',id,'white')+act(p.st==='Active'?'Suspend':'Reactivate','suspend',id,'white')+act('Remove partner','remove',id,'line')}<button class="btn pink" data-act="payout" data-id="${id}" type="button">${ic('plus',16)} Record payout</button></div>
  <div class="stack pprof">${pHero(id)}<div class="pgrid">${pMoney(id)}${pWallet(id)}</div><div class="pgrid2">${pTabs(id)}${pAct(id)}</div></div>`};
const pFirst=n=>String(n||'').trim().split(/\s+/)[0]||'They';
const ghTel=ph=>{let d=String(ph||'').replace(/\D/g,'');if(d.length===10&&d[0]==='0')d='233'+d.slice(1);return d};
const netOf=a=>a.kind==='bank'?'bank':/mtn/i.test(a.provider)?'mtn':/telecel|vodafone/i.test(a.provider)?'tel':/(^|\W)at(\W|$)|airtel|tigo/i.test(a.provider)?'at':'bank';
const spaced=n=>{const s=String(n||'').replace(/\s/g,'');return /^0\d{9}$/.test(s)?s.replace(/(\d{3})(\d{3})(\d{4})/,'$1 $2 $3'):s.replace(/(.{4})(?=.)/g,'$1 ')};
const andList=a=>a.length<2?a.join(''):a.slice(0,-1).join(', ')+' and '+a[a.length-1];
const relD=d=>{const s=String(d||'').slice(0,10);if(!s)return'';const n=Math.round((new Date(TODAY+'T00:00:00')-new Date(s+'T00:00:00'))/864e5);return n===0?'Today':n===1?'Yesterday':n>1&&n<7?n+' days ago':dfmt(s)};
function pHero(id){const p=P(id),a=D.pay[id],rem=p.st==='Removed',first=esc(pFirst(p.name)),on=!rem&&!!(D.online&&D.online.has(id)),rf=D.refs.filter(x=>x.p===id);
  const miss=[[p.phone,'a phone number'],[p.city,'a city'],[a,'payout details'],[rf.length,'a first referral']].filter(c=>!c[0]).map(c=>c[1]),pc=Math.round((5-miss.length)/5*100);
  const pic=D.avById&&D.avById[id],tel=ghTel(p.phone),since=p.joined?new Date(p.joined).toLocaleDateString('en-GB',{month:'short',year:'numeric'}):'';
  const lastPo=D.payouts.filter(x=>x.p===id&&!x.void).sort((x,y)=>y.d.localeCompare(x.d))[0];
  const facts=[['Clients',D.clients.filter(c=>c.p===id).length],['Projects',D.projects.filter(x=>CL(x.c).p===id).length],['Referrals',rf.length],['Last payout',lastPo?dfmt(lastPo.d):'None yet']];
  const chips=rem?'':`<div class="ph-chips">
    <span class="chip-g"><a class="chip" href="mailto:${esc(p.email)}">${ic('mail',16)}<span>${fmtEmail(p.email)}</span></a><button type="button" class="chip-c" data-act="copytxt" data-id="${esc(p.email)}" aria-label="Copy email address" title="Copy email">${ic('copy',15)}</button></span>
    ${p.phone?`<span class="chip-g"><a class="chip" href="tel:+${tel}">${ic('phone',16)}<span>${esc(p.phone)}</span></a><a class="chip-c wa" href="https://wa.me/${tel}" target="_blank" rel="noopener" aria-label="WhatsApp ${first}" title="WhatsApp">${ic('wa',15)}</a></span>`:`<span class="chip ghost">${ic('phone',16)}<span>No phone yet</span></span>`}
    ${p.city?`<span class="chip">${ic('pin',16)}<span>${esc(p.city)}</span></span>`:`<span class="chip ghost">${ic('pin',16)}<span>City not added</span></span>`}</div>`;
  const ready=rem?`<div class="ph-ready"><div class="ptx"><b>Left the studio</b><p>Their login is closed. Past commission and payouts stay in the books.</p></div></div>`
    :`<div class="ph-ready"><div class="ring" style="--p:${pc}"><span>${pc}%</span></div><div class="ptx"><b>${miss.length?'Profile '+pc+'% ready':'Ready to be paid'}</b><p>${miss.length?'Missing '+andList(miss)+'.':'Every detail is in place.'}</p></div>${miss.length?`<button type="button" class="btn sm white" data-chat="${id}">${ic('chat',15)} Ask ${first}</button>`:''}</div>`;
  return `<section class="card phero ${rem?'gone':p.st==='Suspended'?'sus':''}"><div class="ph-cover" aria-hidden="true"></div>
  <div class="ph-main"><span class="ph-av" style="background:${AVC[Math.abs(pIdx(id))%AVC.length]}">${pic?`<img src="${esc(pic)}" alt="">`:inits(p.name)}${on?'<i class="ph-on" title="Online now"></i>':''}</span>
  <div class="ph-id"><p class="ph-eb">${rem?'Former partner':'Growth Partner'}${since?' · since '+since:''}</p><div class="ph-nm">${esc(p.name)}</div><div class="ph-tags">${stTag(p.st)}${on?tag('Online now','mint'):''}</div></div>${ready}</div>
  ${chips}<div class="ph-facts">${facts.map(f=>`<div><span>${f[0]}</span><b>${f[1]}</b></div>`).join('')}</div></section>`}
function pMoney(id){const b=B(id),pa=Math.max(b.paid,0),av=Math.max(b.available,0),hd=Math.max(b.held,0),tot=pa+av+hd,first=esc(pFirst(P(id).name));
  const seg=(v,c)=>v>0?`<i class="${c}" style="flex:${v} 1 0"></i>`:'';
  const by={};D.payments.filter(x=>x.p===id&&!x.rev).forEach(x=>{const c=CL(PR(x.pr).c).id;by[c]=(by[c]||0)+com(x)});
  const src=Object.entries(by).filter(e=>e[1]>0).sort((a,b)=>b[1]-a[1]),top=src.slice(0,3),sum=sumBy(src,e=>e[1]);
  return `<section class="card pmoney"><div class="pm-top"><div><span class="lab">Earned so far</span><div class="big">${gs(b.earned)}</div></div><div class="pm-owed"><span class="lab">Still owed</span><b>${g(b.balance)}</b></div></div>
  <div class="pm-bar" role="img" aria-label="Paid out ${g(pa)}, available now ${g(av)}, on hold ${g(hd)}">${seg(pa,'s-paid')}${seg(av,'s-av')}${seg(hd,'s-hold')}</div>
  <div class="pm-leg"><div><span><i class="s-paid"></i>Paid out</span><b>${g(b.paid)}</b></div><div><span><i class="s-av"></i>Available now</span><b>${g(b.available)}</b></div><div><span><i class="s-hold"></i>On hold</span><b>${g(b.held)}</b></div></div>
  <p class="pm-note">${tot?`New commission waits ${D.hold} business day${D.hold===1?'':'s'} on hold before it can be paid out.`:`Nothing earned yet. Commission shows up here when a client ${first} brought in pays the studio.`}</p>
  ${top.length?`<div class="pm-src"><span class="lab">Where it comes from</span>${top.map(e=>`<a class="pm-row" href="#admin-client-${esc(e[0])}"><span class="nm">${esc(CL(e[0]).name)}</span><b>${g(e[1])}<small>${Math.round(e[1]/sum*100)}%</small></b><span class="pm-tr"><i style="width:${Math.max(3,Math.round(e[1]/top[0][1]*100))}%"></i></span></a>`).join('')}${src.length>3?`<p class="pm-note">And ${src.length-3} more client${src.length-3===1?'':'s'}.</p>`:''}</div>`:''}</section>`}
function pWallet(id){const a=D.pay[id],p=P(id),first=esc(pFirst(p.name));
  if(!a)return `<section class="card pwal"><h2>Payout account</h2><div class="wallet none"><span class="w-ic">${ic('wallet',22)}</span><b>No payout account yet</b><p>${first} hasn't said where to send money yet. They add it under Profile, and you're told when they do.</p>${p.st==='Removed'?'':`<button type="button" class="btn sm" data-chat="${id}">${ic('chat',15)} Ask ${first} to add it</button>`}</div></section>`;
  const show=S.reveal===id,num=show?spaced(a.account_number):'•••• '+esc(String(a.account_number).slice(-4));
  return `<section class="card pwal"><h2>Payout account</h2><div class="wallet w-${netOf(a)}"><div class="w-top"><span class="w-kind">${esc(KINDS[a.kind]||'')}</span><span class="w-sim" aria-hidden="true"></span></div><div class="w-prov">${esc(a.provider)}</div><div class="w-no">${show?esc(num):num}</div>
  <div class="w-bot"><div><small>Account name</small><b>${esc(a.account_name)}</b></div>${a.branch?`<div><small>Branch</small><b>${esc(a.branch)}</b></div>`:''}</div></div>
  <div class="w-acts"><button type="button" class="btn sm line" data-act="reveal" data-id="${id}" aria-pressed="${show}">${ic(show?'eyeoff':'eye',15)} ${show?'Hide number':'Show number'}</button><button type="button" class="btn sm line" data-act="copytxt" data-id="${esc(a.account_number)}">${ic('copy',15)} Copy number</button></div>
  <p class="pm-note">Changed ${dfmt(String(a.updated_at).slice(0,10))}. ${first} keeps these up to date, and you're told whenever they change.</p></section>`}
function pFeed(id){const p=P(id),a=D.pay[id],ev=[];
  if(p.joined)ev.push({d:String(p.joined).slice(0,10),k:'join',i:'user',t:'Invited to the portal',s:'Growth Partner'});
  D.refs.filter(r=>r.p===id).forEach(r=>ev.push({d:r.d,k:'ref',i:'send',t:'Referred '+esc(r.biz),s:stTag(r.st)+(r.bud?' Budget '+g(r.bud):'')}));
  D.payments.filter(x=>x.p===id).forEach(x=>{const pr=PR(x.pr);ev.push({d:x.d,k:x.rev?'bad':'earn',i:'pct',t:x.rev?'Commission reversed':'Earned commission',s:esc(CL(pr.c).name)+' · '+esc(pr.name),amt:x.rev?`<s>${g(Math.trunc(Math.max(0,x.amt-x.tax-x.refunded)*x.rate/10000))}</s>`:'+'+g(com(x))})});
  D.payouts.filter(x=>x.p===id).forEach(x=>ev.push({d:x.d,k:x.void?'bad':'pay',i:'wallet',t:x.void?'Payout voided':'Paid out',s:esc(x.m)+' · '+esc(x.ref),amt:x.void?`<s>${g(x.amt)}</s>`:'−'+g(x.amt)}));
  D.adj.filter(x=>x.p===id).forEach(x=>ev.push({d:x.d,k:'adj',i:'sliders',t:'Balance adjusted',s:esc(x.reason),amt:(x.amt>0?'+':'')+g(x.amt)}));
  if(a&&a.updated_at)ev.push({d:String(a.updated_at).slice(0,10),k:'card',i:'card',t:'Updated payout details',s:esc(KINDS[a.kind]||'')+' · '+esc(a.provider)});
  return ev.sort((x,y)=>y.d.localeCompare(x.d))}
function pAct(id){const ev=pFeed(id),all=S.pfeed===id,n=all?ev.length:6;
  return `<section class="card pact"><h2>Recent activity${ev.length>6?`<button type="button" class="more" data-act="pfeed" data-id="${id}">${all?'Show less':'Show all '+ev.length}</button>`:''}</h2>${ev.length?`<ol class="feed">${ev.slice(0,n).map(e=>`<li class="f-${e.k}"><span class="fi">${ic(e.i,16)}</span><div class="fb"><b>${e.t}</b>${e.s?`<div class="fs">${e.s}</div>`:''}</div><div class="fr">${e.amt?`<b class="fa">${e.amt}</b>`:''}<span>${relD(e.d)}</span></div></li>`).join('')}</ol>`:'<p class="muted">Nothing yet.</p>'}</section>`}
function pTabs(id){const cs=D.clients.filter(c=>c.p===id),prs=D.projects.filter(x=>CL(x.c).p===id),po=D.payouts.filter(x=>x.p===id).sort((a,b)=>b.d.localeCompare(a.d)),rf=D.refs.filter(x=>x.p===id);
  const T=[['clients','Clients',cs.length],['projects','Projects',prs.length],['payouts','Payouts',po.length],['refs','Referrals',rf.length]],k=T.some(t=>t[0]===S.ptab)?S.ptab:'clients';
  const body={clients:()=>tbl(['Client','Projects','Paid so far','Commission'],cs.map(c=>({href:'admin-client-'+c.id,c:[who(c.name,c.contact,D.clients.indexOf(c)),D.projects.filter(x=>x.c===c.id).length,g(cPaid(c)),g(cCom(c))]})),[2,3],'No clients yet. They appear when a referral is approved.'),
    projects:()=>tbl(['Project','Client','Rate','Status'],prs.map(x=>({href:'admin-project-'+x.id,c:[`<b>${esc(x.name)}</b>`,esc(CL(x.c).name),pct(x.rate),stTag(x.st)]})),[2],'No projects yet.'),
    payouts:()=>tbl(['Date','Reference','Method','Amount'],po.map(x=>({c:[dfmt(x.d),esc(x.id)+'<div class="small muted">'+esc(x.ref)+'</div>',esc(x.m),x.void?tag('Voided'):g(x.amt)]})),[3],'No payouts yet.'),
    refs:()=>tbl(['Business','Budget','Status'],rf.map(r=>({c:[`<b>${esc(r.biz)}</b>`,r.bud?g(r.bud):'—',stTag(r.st)]})),[1],'No referrals yet.')}[k]();
  return `<section class="card ptabs"><div class="pt-h"><div class="tabs" role="tablist" aria-label="Partner records">${T.map(t=>`<button type="button" role="tab" aria-selected="${t[0]===k}" data-ptab="${t[0]}" class="${t[0]===k?'on':''}">${t[1]}<span class="tcnt">${t[2]}</span></button>`).join('')}</div></div>${body}</section>`}
ACT.copytxt=v=>{if(v)copy(v)};
ACT.reveal=id=>{S.reveal=S.reveal===id?null:id;const y=scrollY;render();scrollTo(0,y)};
ACT.pfeed=id=>{S.pfeed=S.pfeed===id?null:id;const y=scrollY;render();scrollTo(0,y)};''' + h[j:]

css = r'''
/* partner profile */
.pprof{container-type:inline-size}
.pgrid,.pgrid2{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
@container (min-width:860px){.pgrid{grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)}}
@container (min-width:1300px){.pgrid2{grid-template-columns:minmax(0,1.6fr) minmax(0,1fr)}}
.phero{padding:0;overflow:hidden;container-type:inline-size}
.ph-cover{position:relative;height:112px;overflow:hidden;background:radial-gradient(circle at 1px 1px,rgba(62,70,49,.14) 1px,transparent 1.6px) 0 0/16px 16px,radial-gradient(70% 170% at 100% 0%,#FAFF7E 0 20%,rgba(250,255,126,0) 60%),linear-gradient(115deg,#D2E3C0 0%,#E6EDC8 50%,#FEFFDA 100%)}
.ph-cover::before,.ph-cover::after{content:"";position:absolute;border-radius:50%}
.ph-cover::before{width:230px;height:230px;right:-70px;top:-120px;border:24px solid rgba(255,255,255,.4)}
.ph-cover::after{width:110px;height:110px;right:170px;top:52px;border:14px solid rgba(62,70,49,.07)}
.phero.sus .ph-cover{filter:sepia(.45) hue-rotate(-35deg) saturate(.9)}
.phero.gone .ph-cover{filter:grayscale(1) opacity(.8)}
.ph-main{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:14px 20px;padding:0 24px;align-items:start}
.ph-av{position:relative;width:108px;height:108px;margin-top:-54px;border-radius:50%;border:5px solid #fff;display:grid;place-items:center;font-size:32px;font-weight:700;color:#3E4631;box-shadow:0 6px 18px rgba(36,40,44,.12);flex:none}
.ph-av img{width:100%;height:100%;border-radius:50%;object-fit:cover}
.ph-on{position:absolute;right:4px;bottom:6px;width:18px;height:18px;border-radius:50%;background:var(--ok);border:3px solid #fff}
.ph-on::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:2px solid var(--ok);animation:phpulse 2s ease-out infinite}
@keyframes phpulse{from{transform:scale(.8);opacity:.8}to{transform:scale(1.7);opacity:0}}
@media (prefers-reduced-motion:reduce){.ph-on::after{animation:none;opacity:0}}
.ph-id{padding-top:14px;min-width:0}
.ph-eb{margin:0;font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600}
.ph-nm{font-size:26px;font-weight:700;line-height:1.2;margin:4px 0 8px;letter-spacing:-.01em;overflow-wrap:anywhere}
.ph-tags{display:flex;gap:6px;flex-wrap:wrap}
.ph-ready{margin-top:14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--canvas);border:1px solid var(--line-2);border-radius:18px;padding:12px 14px;max-width:380px;min-width:0}
.ph-ready .ring{width:48px;height:48px}.ph-ready .ring::before{background:var(--canvas)}
.ph-ready .ptx{flex:1 1 160px;min-width:0}.ph-ready .ptx b{display:block;font-size:14px}.ph-ready .ptx p{margin:2px 0 0;font-size:12.5px;color:var(--muted)}
.ph-chips{display:flex;flex-wrap:wrap;gap:8px;padding:16px 24px 0}
.chip,.chip-g{display:inline-flex;align-items:center;min-width:0;max-width:100%;border:1px solid var(--line);border-radius:999px;background:#fff}
.chip{gap:8px;min-height:38px;padding:6px 14px;color:var(--ink);font-weight:500;font-size:13.5px;text-decoration:none}
.chip .ic{flex:none;color:var(--muted)}.chip>span{min-width:0}
.chip-g{align-items:stretch}.chip-g .chip{border:0;background:none;border-radius:999px 0 0 999px;padding-right:10px}
a.chip:hover{background:#F8F8EE}
.chip-c{display:grid;place-items:center;width:40px;flex:none;border-left:1px solid var(--line-2);color:var(--muted);border-radius:0 999px 999px 0;text-decoration:none}
.chip-c:hover{background:#F8F8EE;color:var(--ink)}.chip-c.wa{color:#25803d}
.chip.ghost{border-style:dashed;background:transparent;color:var(--muted)}
.ph-facts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:18px 24px 0;border-top:1px solid var(--line)}
.ph-facts>div{padding:14px 0 18px;min-width:0}.ph-facts>div+div{padding-left:18px;border-left:1px solid var(--line-2)}
.ph-facts span{display:block;font-size:12.5px;color:var(--muted)}.ph-facts b{display:block;font-size:18px;font-weight:700;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@container (max-width:780px){.ph-main{grid-template-columns:auto minmax(0,1fr)}.ph-ready{grid-column:1/-1;max-width:none;margin-top:2px}}
@container (max-width:560px){.ph-facts{grid-template-columns:repeat(2,minmax(0,1fr))}.ph-facts>div:nth-child(3){padding-left:0;border-left:0}.ph-facts>div:nth-child(n+3){border-top:1px solid var(--line-2)}}
@container (max-width:480px){.ph-main{grid-template-columns:minmax(0,1fr);padding:0 16px;gap:10px}.ph-av{width:92px;height:92px;margin-top:-46px;font-size:26px}.ph-id{padding-top:0}.ph-nm{font-size:22px}.ph-chips{padding:14px 16px 0}.ph-facts{margin:16px 16px 0}.ph-cover{height:92px}.chip-g,.chip-g .chip{flex:1 1 auto}}
.pmoney{display:flex;flex-direction:column;gap:14px;container-type:inline-size}
.pm-top{display:flex;justify-content:space-between;align-items:flex-end;gap:10px 16px;flex-wrap:wrap}
.pm-top .lab{display:block;font-size:13px;font-weight:500;color:var(--muted)}.pmoney .big{font-size:clamp(26px,2.6vw,34px);margin-top:4px}
.pm-owed{text-align:right}.pm-owed b{display:block;margin-top:4px;font-size:18px;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
.pm-bar{display:flex;gap:3px;height:16px;border-radius:999px;background:#EDECE1;overflow:hidden}
.pm-bar i{display:block;min-width:8px;height:100%}
.s-paid{background:var(--dark)}.s-av{background:#7FB24F}.s-hold{background:repeating-linear-gradient(45deg,#E8D65C 0 5px,#F5EBA0 5px 10px)}
.pm-leg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.pm-leg>div{background:var(--canvas);border-radius:14px;padding:10px 12px;min-width:0}
.pm-leg span{display:flex;align-items:center;gap:7px;font-size:12.5px;color:var(--muted)}.pm-leg i{width:10px;height:10px;border-radius:3px;flex:none}
.pm-leg b{display:block;margin-top:4px;font-size:15px;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
@container (max-width:560px){.pm-owed{text-align:left}.pm-leg{grid-template-columns:minmax(0,1fr)}.pm-leg>div{display:flex;justify-content:space-between;align-items:center;gap:10px}.pm-leg b{margin-top:0}}
.pm-note{margin:0;font-size:12.5px;color:var(--muted)}
.pm-src{margin-top:auto;padding-top:4px}.pm-src>.lab{display:block;font-size:13px;font-weight:500;color:var(--muted);margin-bottom:2px}
.pm-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 12px;align-items:baseline;padding:10px 0;border-top:1px solid var(--line-2);color:inherit;text-decoration:none}
.pm-row:hover .nm{text-decoration:underline}
.pm-row .nm{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pm-row b{white-space:nowrap;font-variant-numeric:tabular-nums}.pm-row b small{margin-left:8px;font-size:12px;font-weight:500;color:var(--muted)}
.pm-tr{grid-column:1/-1;height:6px;border-radius:99px;background:#EDECE1;overflow:hidden}.pm-tr i{display:block;height:100%;border-radius:99px;background:#9DBE73}
.pm-src>.pm-note{padding-top:8px;border-top:1px solid var(--line-2)}
.pwal{display:flex;flex-direction:column;gap:12px}.pwal h2{margin:0}
.wallet{position:relative;overflow:hidden;border-radius:20px;padding:18px 20px;min-height:196px;display:flex;flex-direction:column;gap:4px;color:#fff;background:linear-gradient(135deg,#4F5A3D 0%,#2A2F29 100%);box-shadow:0 10px 24px rgba(36,40,44,.16);container-type:inline-size}
.wallet::before,.wallet::after{content:"";position:absolute;border-radius:50%;pointer-events:none}
.wallet::before{width:240px;height:240px;right:-80px;top:-120px;background:rgba(255,255,255,.1)}
.wallet::after{width:180px;height:180px;right:-20px;bottom:-120px;background:rgba(255,255,255,.07)}
.wallet>*{position:relative;z-index:1;min-width:0}
.w-top{display:flex;justify-content:space-between;align-items:center;gap:10px}
.w-kind{font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;font-weight:600;opacity:.85}
.w-sim{width:38px;height:28px;border-radius:7px;background:linear-gradient(135deg,#F5EAB0,#C9B35A);box-shadow:inset 0 0 0 1px rgba(0,0,0,.08);position:relative}
.w-sim::after{content:"";position:absolute;inset:6px 8px;border:1px solid rgba(0,0,0,.18);border-radius:3px}
.w-prov{font-size:16px;font-weight:700;margin-top:10px;overflow-wrap:anywhere}
.w-no{margin-top:auto;padding-top:12px;font:600 clamp(17px,7cqi,23px)/1.2 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:.06em;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.w-bot{display:flex;gap:6px 18px;flex-wrap:wrap;margin-top:8px}.w-bot>div{min-width:0;flex:1 1 140px}
.w-bot small{display:block;font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;opacity:.72}.w-bot b{font-size:14px;font-weight:600;overflow-wrap:anywhere}
.w-mtn{background:linear-gradient(135deg,#FFD84A 0%,#EDB200 100%);color:#24282C}.w-mtn::before{background:rgba(255,255,255,.28)}
.w-tel{background:linear-gradient(135deg,#E04A50 0%,#9C1C23 100%)}
.w-at{background:linear-gradient(135deg,#4374D9 0%,#1E3F8E 100%)}
.wallet.none{background:var(--canvas);color:var(--ink);border:2px dashed var(--grey-1);box-shadow:none;align-items:flex-start;justify-content:center;gap:6px}
.wallet.none::before,.wallet.none::after{display:none}
.wallet.none .w-ic{width:44px;height:44px;border-radius:14px;background:#fff;display:grid;place-items:center;border:1px solid var(--line);margin-bottom:4px}
.wallet.none p{margin:0 0 6px;color:var(--muted);font-size:13px;max-width:42ch}
.w-acts{display:flex;gap:8px;flex-wrap:wrap}
.pact{container-type:inline-size}
.card h2 button.more{padding:4px 0}.card h2 button.more:hover{color:var(--ink)}
.feed{list-style:none;margin:0;padding:0}
.feed li{position:relative;display:grid;grid-template-columns:36px minmax(0,1fr) auto;gap:12px;align-items:start;padding:10px 0}
.feed li:not(:last-child)::before{content:"";position:absolute;left:17px;top:48px;bottom:-8px;width:2px;border-radius:2px;background:var(--line-2)}
.fi{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:var(--canvas);color:var(--dark);border:1px solid var(--line)}
.f-earn .fi{background:var(--up-bg);color:var(--up);border-color:transparent}
.f-pay .fi{background:var(--sand-2);border-color:#E3E79B}
.f-ref .fi{background:#E6EDFB;color:var(--info);border-color:transparent}
.f-bad .fi{background:var(--dn-bg);color:var(--dn);border-color:transparent}
.f-join .fi{background:var(--dark);color:var(--sand);border-color:var(--dark)}
.fb{min-width:0;padding-top:1px}.fb>b{display:block;font-weight:600;overflow-wrap:anywhere}
.fs{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;font-size:12.5px;color:var(--muted);margin-top:3px;overflow-wrap:anywhere}.fs .tag{font-size:11px;padding:2px 8px}
.fr{text-align:right;padding-top:1px}.fr span{display:block;font-size:12px;color:var(--muted);white-space:nowrap}
.fa{display:block;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}.f-earn .fa{color:var(--up)}.f-bad .fa{color:var(--muted)}
@container (max-width:330px){.feed li{grid-template-columns:36px minmax(0,1fr)}.fr{grid-column:2;text-align:left;display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline}}
.ptabs .pt-h{margin-bottom:14px}
.tcnt{display:inline-grid;place-items:center;min-width:20px;height:20px;padding:0 6px;margin-left:6px;border-radius:999px;background:rgba(62,70,49,.1);font-size:11.5px;color:inherit}
.tabs .on .tcnt{background:rgba(255,255,255,.2)}
'''
rep('.pop .pall{display:block;', css.strip() + '\n.pop .pall{display:block;')

open(p, 'w', encoding='utf-8').write(h)
print('ok', len(h))
