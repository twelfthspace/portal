"""Partner page, tidier: a compact header, an invitation banner, then two independent columns
(commission and records on the left; contact, setup, payout and activity on the right) so nothing
stretches or floats. Invitations default to a WhatsApp link and can open the person's chat directly.
python3 -I tools/patch_partner_profile2.py site/index.html"""
import sys
p = sys.argv[1]
h = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f'expected {count}, found {n}: {old[:100]!r}')
    h = h.replace(old, new)

def cut(start, end_marker):
    """Return (i, j) spanning from start to the end of the line that begins with end_marker."""
    i = h.index(start)
    k = h.index('\n' + end_marker, i) + 1
    j = h.index('\n', k) + 1
    return i, j

# ---------- CSS ----------
i, j = cut('/* partner profile */', '.ph-ready.inv{')
h = h[:i] + r'''/* partner profile */
.pprof{display:flex;flex-direction:column;gap:16px;container-type:inline-size}
.pcols{display:grid;gap:16px;grid-template-columns:minmax(0,1fr) 340px;align-items:start}
.pcol{display:flex;flex-direction:column;gap:16px;min-width:0}
@container (min-width:1500px){.pcols{grid-template-columns:minmax(0,1fr) 380px}}
@container (max-width:1039px){.pcols{grid-template-columns:repeat(2,minmax(0,1fr))}.pcol{display:contents}.pcols>.pcol>*{grid-column:1/-1}.pcols .pcon{order:1;grid-column:auto}.pcols .pset{order:2;grid-column:auto}.pcols .pmoney{order:3}.pcols .pwal{order:4}.pcols .ptabs{order:5}.pcols .pact{order:6}}
@container (max-width:620px){.pcols .pcon,.pcols .pset{grid-column:1/-1}}
.card h2 .h2c{margin-left:auto;font-size:12.5px;font-weight:500;color:var(--muted)}
.card h2 button.more{padding:4px 0}.card h2 button.more:hover{color:var(--ink)}
/* header */
.phd{padding:0;overflow:hidden;container-type:inline-size}
.ph-cover{position:relative;height:96px;overflow:hidden;background:radial-gradient(circle at 1px 1px,rgba(62,70,49,.14) 1px,transparent 1.6px) 0 0/16px 16px,radial-gradient(70% 170% at 100% 0%,#FAFF7E 0 20%,rgba(250,255,126,0) 60%),linear-gradient(115deg,#D2E3C0 0%,#E6EDC8 50%,#FEFFDA 100%)}
.ph-cover::before{content:"";position:absolute;border-radius:50%;width:230px;height:230px;right:-70px;top:-130px;border:24px solid rgba(255,255,255,.4)}
.phd.sus .ph-cover{filter:sepia(.45) hue-rotate(-35deg) saturate(.9)}.phd.gone .ph-cover{filter:grayscale(1) opacity(.8)}
.ph-row{display:flex;align-items:flex-start;gap:18px;padding:0 24px 20px}
.ph-av{position:relative;width:104px;height:104px;margin-top:-52px;border-radius:50%;border:5px solid #fff;display:grid;place-items:center;font-size:32px;font-weight:700;color:#3E4631;box-shadow:0 6px 18px rgba(36,40,44,.12);flex:none}
.ph-av img{width:100%;height:100%;border-radius:50%;object-fit:cover}
.ph-on{position:absolute;right:4px;bottom:6px;width:18px;height:18px;border-radius:50%;background:var(--ok);border:3px solid #fff}
.ph-on::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:2px solid var(--ok);animation:phpulse 2s ease-out infinite}
@keyframes phpulse{from{transform:scale(.8);opacity:.8}to{transform:scale(1.7);opacity:0}}
@media (prefers-reduced-motion:reduce){.ph-on::after{animation:none;opacity:0}}
.ph-id{flex:1;min-width:0;padding-top:14px}
.ph-eb{margin:0;font-size:11.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600}
.ph-nm{font-size:26px;font-weight:700;line-height:1.2;margin:4px 0 8px;letter-spacing:-.01em;overflow-wrap:anywhere}
.ph-tags{display:flex;gap:6px;flex-wrap:wrap}
.ph-qa{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;align-self:center;padding-top:14px;flex:none}.ph-qa .qwa .ic{color:#25803d}
@container (max-width:560px){.ph-row{flex-wrap:wrap;gap:10px 14px;padding:0 16px 16px}.ph-av{width:88px;height:88px;margin-top:-44px;font-size:26px}.ph-qa{order:4;flex:1 1 100%;justify-content:flex-start;padding-top:2px}.ph-id{order:3;flex:1 1 100%;padding-top:0}.ph-nm{font-size:22px}.ph-cover{height:84px}}
/* invitation banner */
.pban{display:flex;align-items:center;gap:14px;padding:14px 16px 14px 14px;border-radius:18px;background:var(--sand-2);border:1px solid #E3E79B}
.pb-ic{width:44px;height:44px;border-radius:14px;background:#fff;border:1px solid var(--line);display:grid;place-items:center;flex:none}
.pb-tx{flex:1;min-width:0}.pb-tx b{display:block;font-size:14.5px}.pb-tx p{margin:2px 0 0;font-size:13px;color:var(--muted)}
@container (max-width:620px){.pban{flex-wrap:wrap}.pban>.btn{flex:1 1 100%}}
/* contact */
.crow{display:flex;align-items:center;gap:12px;padding:11px 0;border-top:1px solid var(--line-2);min-width:0}
.pcon h2+.crow{border-top:0;padding-top:0}
.ci{width:34px;height:34px;border-radius:10px;background:var(--canvas);display:grid;place-items:center;color:var(--muted);flex:none}
.cval{flex:1;min-width:0}.cval small{display:block;font-size:12px;color:var(--muted);margin-bottom:1px}.cval b{font-weight:600;font-size:14px}
.cnone{color:var(--muted);font-size:13.5px}
.cbtn{width:32px;height:32px;border-radius:9px;display:grid;place-items:center;color:var(--muted);flex:none}.cbtn:hover{background:var(--canvas);color:var(--ink)}
/* setup */
.sbar{height:8px;border-radius:99px;background:#EDECE1;overflow:hidden;margin:2px 0 8px}.sbar i{display:block;height:100%;border-radius:99px;background:var(--ok)}
.slist{list-style:none;margin:0;padding:0}
.slist li{display:flex;align-items:center;gap:10px;padding:7px 0;font-size:13.5px;color:var(--muted)}
.slist .ck{width:20px;height:20px;border-radius:50%;border:1.5px solid var(--grey-1);display:grid;place-items:center;flex:none;color:#fff;background:#fff}
.slist .done{color:var(--ink)}.slist .done .ck{background:var(--ok);border-color:var(--ok)}
.pset>.btn{margin-top:12px}
/* commission */
.pmoney{display:flex;flex-direction:column;gap:14px;container-type:inline-size}.pmoney h2{margin:0}
.mtiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.mt{background:var(--canvas);border-radius:14px;padding:12px 14px;min-width:0}
.mt span{display:flex;align-items:center;gap:7px;font-size:12.5px;color:var(--muted);white-space:nowrap}
.mt i{width:9px;height:9px;border-radius:3px;flex:none}
.mt b{display:block;margin-top:6px;font-size:clamp(14px,2.3cqi,18px);font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
.mt.t-earn{background:var(--dark);color:#fff}.t-earn span{color:#DCE5C8}.t-earn i{background:var(--sand)}
.t-paid i,.pm-bar .s-paid{background:var(--dark)}.t-av i,.pm-bar .s-av{background:#7FB24F}.t-hold i,.pm-bar .s-hold{background:repeating-linear-gradient(45deg,#E8D65C 0 4px,#F5EBA0 4px 8px)}
@container (max-width:719px){.mtiles{grid-template-columns:repeat(2,minmax(0,1fr))}.mt b{font-size:16px}}
.pm-bar{display:flex;gap:3px;height:12px;border-radius:999px;background:#EDECE1;overflow:hidden}.pm-bar i{display:block;min-width:8px;height:100%}
.pm-note{margin:0;font-size:12.5px;color:var(--muted)}
.pm-src>.lab{display:block;font-size:13px;font-weight:500;color:var(--muted);margin-bottom:2px}
.pm-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 12px;align-items:baseline;padding:10px 0;border-top:1px solid var(--line-2);color:inherit;text-decoration:none}
.pm-row:hover .nm{text-decoration:underline}
.pm-row .nm{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pm-row b{white-space:nowrap;font-variant-numeric:tabular-nums}.pm-row b small{margin-left:8px;font-size:12px;font-weight:500;color:var(--muted)}
.pm-tr{grid-column:1/-1;height:6px;border-radius:99px;background:#EDECE1;overflow:hidden}.pm-tr i{display:block;height:100%;border-radius:99px;background:#9DBE73}
.pm-src>.pm-note{padding-top:8px;border-top:1px solid var(--line-2)}
/* empty states */
.pempty{display:flex;align-items:flex-start;gap:12px;padding:14px;border-radius:14px;background:var(--canvas);border:1px dashed var(--grey-1)}
.pe-ic{width:38px;height:38px;border-radius:11px;background:#fff;border:1px solid var(--line);display:grid;place-items:center;flex:none;color:var(--muted)}
.pempty b{display:block;font-size:14px}.pempty p{margin:2px 0 0;font-size:13px;color:var(--muted)}
/* payout card */
.pwal{display:flex;flex-direction:column;gap:12px;container-type:inline-size}.pwal h2{margin:0}.pwal>.btn{align-self:flex-start}
.pwal-b{display:flex;flex-direction:column;gap:12px}.pwal-s{display:flex;flex-direction:column;gap:10px}
@container (min-width:620px){.pwal-b{display:grid;grid-template-columns:minmax(0,400px) minmax(0,1fr);gap:20px;align-items:start}}
.wallet{position:relative;overflow:hidden;border-radius:18px;padding:18px 20px;min-height:180px;display:flex;flex-direction:column;gap:4px;color:#fff;background:linear-gradient(135deg,#4F5A3D 0%,#2A2F29 100%);box-shadow:0 10px 24px rgba(36,40,44,.16);container-type:inline-size}
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
.w-acts{display:flex;gap:8px;flex-wrap:wrap}
/* activity */
.pact{container-type:inline-size}
.feed{list-style:none;margin:0;padding:0}
.feed li{position:relative;display:grid;grid-template-columns:34px minmax(0,1fr);gap:12px;padding:9px 0}
.feed li:not(:last-child)::before{content:"";position:absolute;left:16px;top:45px;bottom:-7px;width:2px;border-radius:2px;background:var(--line-2)}
.fi{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:var(--canvas);color:var(--dark);border:1px solid var(--line)}
.f-earn .fi{background:var(--up-bg);color:var(--up);border-color:transparent}
.f-pay .fi{background:var(--sand-2);border-color:#E3E79B}
.f-ref .fi{background:#E6EDFB;color:var(--info);border-color:transparent}
.f-bad .fi{background:var(--dn-bg);color:var(--dn);border-color:transparent}
.f-join .fi{background:var(--dark);color:var(--sand);border-color:var(--dark)}
.fb{min-width:0;padding-top:1px}
.fl{display:flex;align-items:baseline;justify-content:space-between;gap:10px}.fl>b:first-child{font-weight:600;min-width:0;overflow-wrap:anywhere}
.fa{flex:none;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}.f-earn .fa{color:var(--up)}.f-bad .fa{color:var(--muted)}
.fs{display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px;margin-top:3px;font-size:12.5px;color:var(--muted);overflow-wrap:anywhere}.fs .tag{font-size:11px;padding:2px 8px}
.fs>*+.fd::before{content:"·";margin-right:8px}.fd{white-space:nowrap}
/* records */
.ptabs .pt-h{margin-bottom:14px}
.tcnt{display:inline-grid;place-items:center;min-width:20px;height:20px;padding:0 6px;margin-left:6px;border-radius:999px;background:rgba(62,70,49,.1);font-size:11.5px;color:inherit}
.tabs .on .tcnt{background:rgba(255,255,255,.2)}
''' + h[j:]

# ---------- page ----------
i, j = cut("PG.partnerD=id=>{const p=P(id);if(!p)return PG['admin-partners']();", 'ACT.pfeed=id=>')
h = h[:i] + r'''PG.partnerD=id=>{const p=P(id);if(!p)return PG['admin-partners']();const inv=D.invites.find(x=>x.id===id);
  return `<div class="pha">${back('admin-partners','Partners')}<span class="grow"></span><button type="button" class="btn white" data-chat="${id}">${ic('chat',16)} Message</button>${p.st==='Removed'?'':act('View as partner','viewas',id,'white')+act(p.st==='Active'?'Suspend':'Reactivate','suspend',id,'white')+act('Remove partner','remove',id,'line')}<button class="btn pink" data-act="payout" data-id="${id}" type="button">${ic('plus',16)} Record payout</button></div>
  <div class="pprof">${pHead(id)}${inv?pInvite(id,inv):''}<div class="pcols"><div class="pcol">${pMoney(id)}${pTabs(id)}${pAct(id)}</div><div class="pcol">${pContact(id)}${pSetup(id)}${pWallet(id)}</div></div></div>`};
const pFirst=n=>String(n||'').trim().split(/\s+/)[0]||'They';
const ghTel=ph=>{let d=String(ph||'').replace(/\D/g,'');if(d.length===10&&d[0]==='0')d='233'+d.slice(1);return d};
const netOf=a=>a.kind==='bank'?'bank':/mtn/i.test(a.provider)?'mtn':/telecel|vodafone/i.test(a.provider)?'tel':/(^|\W)at(\W|$)|airtel|tigo/i.test(a.provider)?'at':'bank';
const spaced=n=>{const s=String(n||'').replace(/\s/g,'');return /^0\d{9}$/.test(s)?s.replace(/(\d{3})(\d{3})(\d{4})/,'$1 $2 $3'):s.replace(/(.{4})(?=.)/g,'$1 ')};
const relD=d=>{const s=String(d||'').slice(0,10);if(!s)return'';const n=Math.round((new Date(TODAY+'T00:00:00')-new Date(s+'T00:00:00'))/864e5);return n===0?'Today':n===1?'Yesterday':n>1&&n<7?n+' days ago':dfmt(s)};
const pEmpty=(i,t,s)=>`<div class="pempty"><span class="pe-ic">${ic(i,18)}</span><div><b>${t}</b><p>${s}</p></div></div>`;
function pHead(id){const p=P(id),rem=p.st==='Removed',first=esc(pFirst(p.name)),on=!rem&&!!(D.online&&D.online.has(id)),pic=D.avById&&D.avById[id],tel=ghTel(p.phone);
  const since=p.joined?new Date(p.joined).toLocaleDateString('en-GB',{month:'short',year:'numeric'}):'';
  const qa=rem?'':`<div class="ph-qa">${p.email?`<a class="btn sm white" href="mailto:${esc(p.email)}">${ic('mail',15)} Email</a>`:''}${p.phone?`<a class="btn sm white" href="tel:+${tel}">${ic('phone',15)} Call</a><a class="btn sm white qwa" href="https://wa.me/${tel}" target="_blank" rel="noopener">${ic('wa',15)} WhatsApp</a>`:''}</div>`;
  return `<section class="card phd ${rem?'gone':p.st==='Suspended'?'sus':''}"><div class="ph-cover" aria-hidden="true"></div><div class="ph-row"><span class="ph-av" style="background:${AVC[Math.abs(pIdx(id))%AVC.length]}">${pic?`<img src="${esc(pic)}" alt="">`:inits(p.name)}${on?'<i class="ph-on" title="Online now"></i>':''}</span>
  <div class="ph-id"><p class="ph-eb">${rem?'Former partner':'Growth Partner'}${since?' · since '+since:''}</p><div class="ph-nm">${esc(p.name)}</div><div class="ph-tags">${stTag(pSt(p))}${on?tag('Online now','mint'):''}</div></div>${qa}</div></section>`}
function pInvite(id,inv){const first=esc(pFirst(P(id).name));
  return `<div class="pban" role="status"><span class="pb-ic">${ic('mail',20)}</span><div class="pb-tx"><b>${first} hasn't accepted the invitation yet</b><p>Emailed ${sentD(inv.at)}. It may be in Spam, or the link has expired. Send a fresh one on WhatsApp.</p></div><button type="button" class="btn" data-act="relink" data-id="${id}">${ic('wa',16)} Send a new link</button></div>`}
function pContact(id){const p=P(id),inv=D.invites.some(x=>x.id===id);if(p.st==='Removed')return'';
  const row=(i,l,v,x='')=>`<div class="crow"><span class="ci">${ic(i,16)}</span><div class="cval"><small>${l}</small>${v}</div>${x}</div>`,none='<span class="cnone">Not added yet</span>';
  const cp=(v,l)=>`<button type="button" class="cbtn" data-act="copytxt" data-id="${esc(v)}" title="Copy ${l}" aria-label="Copy ${l}">${ic('copy',15)}</button>`;
  return `<section class="card pcon"><h2>Contact</h2>${row('mail','Email',`<b>${fmtEmail(p.email)}</b>`,cp(p.email,'email address'))}${row('phone','Phone',p.phone?`<b>${esc(p.phone)}</b>`:none,p.phone?cp(p.phone,'phone number'):'')}${row('pin','City',p.city?`<b>${esc(p.city)}</b>`:none)}${p.joined?row('clock',inv?'Invited':'Member since',`<b>${dfmt(String(p.joined).slice(0,10))}</b>`):''}</section>`}
function pSetup(id){const p=P(id);if(p.st==='Removed')return'';const inv=D.invites.some(x=>x.id===id),first=esc(pFirst(p.name));
  const L=[[!inv,'Accepted the invitation'],[!!p.phone,'Added a phone number'],[!!p.city,'Added their city'],[!!D.pay[id],'Added payout details'],[D.refs.some(x=>x.p===id),'Sent a first referral']],n=L.filter(x=>x[0]).length;
  return `<section class="card pset"><h2>Getting set up<span class="h2c">${n} of ${L.length}</span></h2><div class="sbar" role="img" aria-label="${n} of ${L.length} steps done"><i style="width:${n/L.length*100}%"></i></div><ul class="slist">${L.map(x=>`<li class="${x[0]?'done':''}"><span class="ck">${x[0]?ic('check',12,2.6):''}</span>${x[1]}</li>`).join('')}</ul>${n<L.length&&!inv?`<button type="button" class="btn sm line wide" data-chat="${id}">${ic('chat',15)} Ask ${first} to finish</button>`:''}</section>`}
function pMoney(id){const b=B(id),pa=Math.max(b.paid,0),av=Math.max(b.available,0),hd=Math.max(b.held,0),tot=pa+av+hd,first=esc(pFirst(P(id).name));
  const seg=(v,c)=>v>0?`<i class="${c}" style="flex:${v} 1 0"></i>`:'',tile=(c,l,v)=>`<div class="mt ${c}"><span><i></i>${l}</span><b>${v}</b></div>`;
  const by={};D.payments.filter(x=>x.p===id&&!x.rev).forEach(x=>{const c=CL(PR(x.pr).c).id;by[c]=(by[c]||0)+com(x)});
  const src=Object.entries(by).filter(e=>e[1]>0).sort((a,b)=>b[1]-a[1]),top=src.slice(0,3),sum=sumBy(src,e=>e[1]);
  const lastPo=D.payouts.filter(x=>x.p===id&&!x.void).sort((x,y)=>y.d.localeCompare(x.d))[0];
  return `<section class="card pmoney"><h2>Commission${lastPo?`<span class="h2c">Last payout ${dfmt(lastPo.d)}</span>`:''}</h2>
  <div class="mtiles">${tile('t-earn','Earned so far',g(b.earned))}${tile('t-paid','Paid out',g(b.paid))}${tile('t-av','Available now',g(b.available))}${tile('t-hold','On hold',g(b.held))}</div>
  ${tot?`<div class="pm-bar" role="img" aria-label="Paid out ${g(pa)}, available now ${g(av)}, on hold ${g(hd)}">${seg(pa,'s-paid')}${seg(av,'s-av')}${seg(hd,'s-hold')}</div>`:''}
  <p class="pm-note">${tot?`Still owed <b>${g(b.balance)}</b>. New commission waits ${D.hold} business day${D.hold===1?'':'s'} on hold before it can be paid out.`:`Nothing earned yet. Commission shows up here when a client ${first} brought in pays the studio.`}</p>
  ${top.length?`<div class="pm-src"><span class="lab">Where it comes from</span>${top.map(e=>`<a class="pm-row" href="#admin-client-${esc(e[0])}"><span class="nm">${esc(CL(e[0]).name)}</span><b>${g(e[1])}<small>${Math.round(e[1]/sum*100)}%</small></b><span class="pm-tr"><i style="width:${Math.max(3,Math.round(e[1]/top[0][1]*100))}%"></i></span></a>`).join('')}${src.length>3?`<p class="pm-note">And ${src.length-3} more client${src.length-3===1?'':'s'}.</p>`:''}</div>`:''}</section>`}
function pWallet(id){const a=D.pay[id],p=P(id),first=esc(pFirst(p.name)),inv=D.invites.some(x=>x.id===id);
  if(!a)return `<section class="card pwal"><h2>Payout account</h2>${pEmpty('wallet','No payout account yet',inv?first+' can add it after accepting the invitation.':first+' adds it under Profile, and you\'re told when they do.')}${p.st==='Removed'||inv?'':`<button type="button" class="btn sm line" data-chat="${id}">${ic('chat',15)} Ask ${first} to add it</button>`}</section>`;
  const show=S.reveal===id,num=show?esc(spaced(a.account_number)):'•••• '+esc(String(a.account_number).slice(-4));
  return `<section class="card pwal"><h2>Payout account</h2><div class="pwal-b"><div class="wallet w-${netOf(a)}"><div class="w-top"><span class="w-kind">${esc(KINDS[a.kind]||'')}</span><span class="w-sim" aria-hidden="true"></span></div><div class="w-prov">${esc(a.provider)}</div><div class="w-no">${num}</div>
  <div class="w-bot"><div><small>Account name</small><b>${esc(a.account_name)}</b></div>${a.branch?`<div><small>Branch</small><b>${esc(a.branch)}</b></div>`:''}</div></div>
  <div class="pwal-s"><div class="w-acts"><button type="button" class="btn sm line" data-act="reveal" data-id="${id}" aria-pressed="${show}">${ic(show?'eyeoff':'eye',15)} ${show?'Hide number':'Show number'}</button><button type="button" class="btn sm line" data-act="copytxt" data-id="${esc(a.account_number)}">${ic('copy',15)} Copy number</button></div>
  <p class="pm-note">Changed ${dfmt(String(a.updated_at).slice(0,10))}. ${first} keeps these up to date, and you're told whenever they change.</p></div></div></section>`}
function pFeed(id){const p=P(id),a=D.pay[id],ev=[];
  if(p.joined)ev.push({d:String(p.joined).slice(0,10),k:'join',i:'user',t:'Invited to the portal',s:''});
  D.refs.filter(r=>r.p===id).forEach(r=>ev.push({d:r.d,k:'ref',i:'send',t:'Referred '+esc(r.biz),s:stTag(r.st)}));
  D.payments.filter(x=>x.p===id).forEach(x=>{const pr=PR(x.pr);ev.push({d:x.d,k:x.rev?'bad':'earn',i:'pct',t:x.rev?'Commission reversed':'Earned commission',s:esc(CL(pr.c).name),amt:x.rev?`<s>${g(Math.trunc(Math.max(0,x.amt-x.tax-x.refunded)*x.rate/10000))}</s>`:'+'+g(com(x))})});
  D.payouts.filter(x=>x.p===id).forEach(x=>ev.push({d:x.d,k:x.void?'bad':'pay',i:'wallet',t:x.void?'Payout voided':'Paid out',s:esc(x.m),amt:x.void?`<s>${g(x.amt)}</s>`:'−'+g(x.amt)}));
  D.adj.filter(x=>x.p===id).forEach(x=>ev.push({d:x.d,k:'adj',i:'sliders',t:'Balance adjusted',s:esc(x.reason),amt:(x.amt>0?'+':'')+g(x.amt)}));
  if(a&&a.updated_at)ev.push({d:String(a.updated_at).slice(0,10),k:'card',i:'card',t:'Updated payout details',s:esc(a.provider)});
  return ev.sort((x,y)=>y.d.localeCompare(x.d))}
function pAct(id){const ev=pFeed(id),all=S.pfeed===id,n=all?ev.length:6;
  return `<section class="card pact"><h2>Recent activity${ev.length>6?`<button type="button" class="more" data-act="pfeed" data-id="${id}">${all?'Show less':'Show all '+ev.length}</button>`:''}</h2>${ev.length?`<ol class="feed">${ev.slice(0,n).map(e=>`<li class="f-${e.k}"><span class="fi">${ic(e.i,15)}</span><div class="fb"><div class="fl"><b>${e.t}</b>${e.amt?`<b class="fa">${e.amt}</b>`:''}</div><div class="fs">${e.s?`<span>${e.s}</span>`:''}<span class="fd">${relD(e.d)}</span></div></div></li>`).join('')}</ol>`:pEmpty('clock','Nothing yet','Referrals, commission and payouts will show up here.')}</section>`}
function pTabs(id){const first=esc(pFirst(P(id).name)),cs=D.clients.filter(c=>c.p===id),prs=D.projects.filter(x=>CL(x.c).p===id),po=D.payouts.filter(x=>x.p===id).sort((a,b)=>b.d.localeCompare(a.d)),rf=D.refs.filter(x=>x.p===id);
  const T=[['clients','Clients',cs.length],['projects','Projects',prs.length],['payouts','Payouts',po.length],['refs','Referrals',rf.length]],k=T.some(t=>t[0]===S.ptab)?S.ptab:'clients';
  const E={clients:['brief','No clients yet',`Clients appear here when one of ${first}'s referrals is approved.`],projects:['layers','No projects yet',`Projects for ${first}'s clients show up here.`],payouts:['wallet','No payouts yet',`Payouts you record for ${first} are listed here.`],refs:['send','No referrals yet',`Businesses ${first} refers to the studio appear here.`]};
  const body=T.find(t=>t[0]===k)[2]?{clients:()=>tbl(['Client','Projects','Paid so far','Commission'],cs.map(c=>({href:'admin-client-'+c.id,c:[who(c.name,c.contact,D.clients.indexOf(c)),D.projects.filter(x=>x.c===c.id).length,g(cPaid(c)),g(cCom(c))]})),[2,3]),
    projects:()=>tbl(['Project','Client','Rate','Status'],prs.map(x=>({href:'admin-project-'+x.id,c:[`<b>${esc(x.name)}</b>`,esc(CL(x.c).name),pct(x.rate),stTag(x.st)]})),[2]),
    payouts:()=>tbl(['Date','Reference','Method','Amount'],po.map(x=>({c:[dfmt(x.d),esc(x.id)+'<div class="small muted">'+esc(x.ref)+'</div>',esc(x.m),x.void?tag('Voided'):g(x.amt)]})),[3]),
    refs:()=>tbl(['Business','Budget','Status'],rf.map(r=>({c:[`<b>${esc(r.biz)}</b>`,r.bud?g(r.bud):'—',stTag(r.st)]})),[1])}[k]():pEmpty(...E[k]);
  return `<section class="card ptabs"><div class="pt-h"><div class="tabs" role="tablist" aria-label="Partner records">${T.map(t=>`<button type="button" role="tab" aria-selected="${t[0]===k}" data-ptab="${t[0]}" class="${t[0]===k?'on':''}">${t[1]}<span class="tcnt">${t[2]}</span></button>`).join('')}</div></div>${body}</section>`}
ACT.copytxt=v=>{if(v)copy(v)};
ACT.reveal=id=>{S.reveal=S.reveal===id?null:id;const y=scrollY;render();scrollTo(0,y)};
ACT.pfeed=id=>{S.pfeed=S.pfeed===id?null:id;const y=scrollY;render();scrollTo(0,y)};
''' + h[j:]

# ---------- icons ----------
rep('eye:"M2 12s3.5-7 10-7', 'check:"M5 12.5l4.5 4.5L19 7.5",eye:"M2 12s3.5-7 10-7')

# ---------- invitations: WhatsApp first, optionally straight to their chat ----------
WA = "field('WhatsApp number (optional)','wa',{type:'tel',inputmode:'tel',ph:'024 123 4567',hint:'Opens WhatsApp straight to their chat. Not saved.'})"
rep("field('How to send it','how',{opts:[['email','Email the invitation for me'],['link','Give me a link to send myself']]}),'Create invitation',",
    "field('How to send it','how',{opts:[['link','Give me a link to send on WhatsApp (recommended)'],['email','Email the invitation for me']]})+" + WA + ",'Create invitation',")
rep("field('How to send it','how',{opts:[['email','Email the invitation for me'],['link','Give me a link to send myself']]}),'Send invitation',",
    "field('How to send it','how',{opts:[['link','Give me a link to send on WhatsApp (recommended)'],['email','Email the invitation for me']]})+" + WA + ",'Send invitation',")
rep("  if(!n)return'Enter the partner\\'s name.';if(!MAIL.test(m))return'Enter a valid email address.';",
    "  if(!n)return'Enter the partner\\'s name.';if(!MAIL.test(m))return'Enter a valid email address.';if(badWa(f.wa))return badWa(f.wa);")
rep("const n=f.name.trim(),m=f.email.trim().toLowerCase();if(!n)return'Enter their name.';if(!MAIL.test(m))return'Enter a valid email address.';",
    "const n=f.name.trim(),m=f.email.trim().toLowerCase();if(!n)return'Enter their name.';if(!MAIL.test(m))return'Enter a valid email address.';if(badWa(f.wa))return badWa(f.wa);")
rep("if(d&&d.link){linkReady(n,d.link);render();return{keep:true}}", "if(d&&d.link){linkReady(n,d.link,'',f.wa);render();return{keep:true}}")
rep("if(d&&d.link){linkReady(n,d.link,' When they accept, they join as Accounts staff.');render();return{keep:true}}",
    "if(d&&d.link){linkReady(n,d.link,' When they accept, they join as Accounts staff.',f.wa);render();return{keep:true}}")
rep("field('How to send it','how',{opts:[['link','Give me a link to send on WhatsApp (recommended)'],['email','Email it again']]}),'Make new link',async f=>{",
    "field('How to send it','how',{opts:[['link','Give me a link to send on WhatsApp (recommended)'],['email','Email it again']]})+field('WhatsApp number (optional)','wa',{type:'tel',inputmode:'tel',ph:'024 123 4567',val:(D.partners.find(x=>x.id===id)||{}).phone||'',hint:'Opens WhatsApp straight to their chat. Not saved.'}),'Make new link',async f=>{\n    if(badWa(f.wa))return badWa(f.wa);")
rep("if(d&&d.link){linkReady(i.name,d.link,D.staffInvites.some(x=>x.id===id)?' When they accept, they join as Accounts staff.':'');render();return{keep:true}}",
    "if(d&&d.link){linkReady(i.name,d.link,D.staffInvites.some(x=>x.id===id)?' When they accept, they join as Accounts staff.':'',f.wa);render();return{keep:true}}")
rep("function linkReady(name,link,extra){D.newlink=link;const fn=String(name||'').trim().split(/\\s+/)[0]||'there';",
    "const badWa=v=>{const d=String(v||'').replace(/[\\s\\-().]/g,'');return d&&!/^\\+?\\d{9,15}$/.test(d)?'Enter the WhatsApp number using digits only, like 024 123 4567.':''};\n"
    "function linkReady(name,link,extra,wa){D.newlink=link;const fn=String(name||'').trim().split(/\\s+/)[0]||'there',to=ghTel(wa);")
rep('<a class="btn" href="https://wa.me/?text=${encodeURIComponent(msg)}" target="_blank" rel="noopener">${ic(\'wa\',15)} Send on WhatsApp</a>',
    '<a class="btn" href="https://wa.me/${to}?text=${encodeURIComponent(msg)}" target="_blank" rel="noopener">${ic(\'wa\',15)} ${to?\'Send to \'+esc(fn)+\' on WhatsApp\':\'Send on WhatsApp\'}</a>')

open(p, 'w', encoding='utf-8').write(h)
print('ok', len(h))
