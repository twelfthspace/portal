"""Turn the portal preview into the live Supabase-backed page.
Usage: python3 -I make_live.py <preview.html> <out/index.html>
Every replacement must match exactly the expected number of times, or the script stops."""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f'expected {count} match(es), found {n}: {old[:90]!r}')
    h = h.replace(old, new)

def between(start, end, new):
    """Replace from start marker through end marker (inclusive). Both must be unique."""
    global h
    a = h.find(start)
    if a < 0 or h.count(start) != 1:
        sys.exit(f'start marker not unique/found: {start[:90]!r}')
    b = h.find(end, a)
    if b < 0:
        sys.exit(f'end marker not found: {end[:90]!r}')
    h = h[:a] + new + h[b + len(end):]

# ---------- document head ----------
first_line_end = h.index('\n')
h = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
     '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
     '<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer">'
     '<style>:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
     'html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0}img{max-width:100%}'
     '[hidden]:not([hidden=until-found i]){display:none!important}</style>'
     + h[first_line_end:])
rep('<title>Twelfth Space Portal Preview</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n',
    '<title>Twelfth Space Portal</title>\n')
rep('</style>\n<div class="app">', '</style>\n</head>\n<body>\n<div class="app">')

# ---------- markup: remove preview switcher and feedback widget ----------
h, n = re.subn(r'\n    <div class="switch" id="roleswitch">.*?\n', '\n', h, count=1)
assert n == 1, 'role switcher not found'
a = h.index('<button class="fab" id="fab"')
b = h.index('</aside>', h.index('<aside class="fbp"')) + len('</aside>')
h = h[:a] + h[b:]
rep('\n<script>\n(function(){',
    '\n<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/dist/umd/supabase.js"></script>\n<script>\n(function(){')

# ---------- data layer ----------
between('/* ---------- state (sample data, fictional) ---------- */', "let ME='ama';", r'''/* ---------- live data (Supabase) ---------- */
const SB_URL='https://bflvfcvltkpyshnedgtf.supabase.co',SB_KEY='sb_publishable_G6saB-vGvsaXFFuP38v1sA_KmD6NzRB';
const BOOT_HASH=location.hash,BASE=location.origin+location.pathname;
const sb=window.supabase.createClient(SB_URL,SB_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
const PST={not_started:'Not started',in_progress:'In progress',on_hold:'On hold',completed:'Completed',cancelled:'Cancelled'};
const PM={mobile_money:'Mobile money',bank_transfer:'Bank transfer',cash:'Cash'};
const RST={pending:'Pending review',flagged:'Flagged',approved:'Approved',rejected:'Rejected'};
const flip=o=>Object.fromEntries(Object.entries(o).map(([k,v])=>[v,k])),PSTr=flip(PST),PMr=flip(PM);
const blankD=()=>({hold:5,notes:[],audit:[],adj:[],partners:[],invites:[],clients:[],projects:[],payments:[],payouts:[],refs:[],msgs:{},unreadA:{},unreadP:{},ann:[],read:{},chat:[],cs:{admin:{},partner:{}},dir:[],bal:{},newlink:null});
const D=blankD();const resetD=()=>Object.assign(D,blankD());
let ME=null,MEP=null,ROLE=null,BOOTED=false;
const q=async p=>{const {data,error}=await p;if(error)throw error;return data};
const lsGet=k=>{try{return localStorage.getItem(k)}catch(_){return null}},lsSet=(k,v)=>{try{localStorage.setItem(k,v)}catch(_){}};
const mtime=s=>{const d=new Date(s);return (new Date().toDateString()===d.toDateString()?'Today':d.toLocaleDateString('en-GB',{day:'numeric',month:'short'}))+' '+d.toTimeString().slice(0,5)};
const nice=e=>{const m=String((e&&e.message)||e||'');
  if(/payments_method_ref|payouts_method_ref/.test(m))return'This transaction reference is already recorded for that method.';
  if(/account_mask/.test(m))return'Enter only a masked account such as ****1234.';
  if(/violates check constraint/.test(m))return'Some of these details are not valid. Check them and try again.';
  if(/JWT|refresh token/i.test(m))return'Your session has expired. Sign in again.';
  if(/Failed to fetch|NetworkError|Load failed/i.test(m))return'Could not reach the server. Check your connection and try again.';
  return m||'Something went wrong. Try again.'};
const ENT={profiles:'partner',settings:'settings',clients:'client',projects:'project',payments:'payment',payouts:'payout',adjustments:'adjustment',referrals:'referral',announcements:'announcement',community_messages:'community message'};
function describe(a){const n=a.new_row||{},o=a.old_row||{},r=a.action==='delete'?o:n,lab=r.full_name||r.name||r.business||r.title||r.code||r.reference||'',e=ENT[a.entity]||a.entity,L=lab?' '+lab:'';
  if(a.action==='update'){
    if(a.entity==='payments'&&n.reversed&&!o.reversed)return'Reversed payment'+L;
    if(a.entity==='payments'&&n.refunded!==o.refunded)return'Refunded '+g(n.refunded-o.refunded)+' on payment'+L;
    if(a.entity==='payouts'&&n.voided&&!o.voided)return'Voided payout'+L;
    if(a.entity==='projects'&&n.rate_bp!==o.rate_bp)return'Changed rate on'+L+' from '+pct(o.rate_bp)+' to '+pct(n.rate_bp);
    if(a.entity==='projects'&&n.status!==o.status)return'Set'+L+' to '+(PST[n.status]||n.status);
    if(a.entity==='clients'&&n.partner_id!==o.partner_id)return'Reassigned'+L;
    if(a.entity==='profiles'&&n.status!==o.status)return(n.status==='suspended'?'Suspended':'Reactivated')+L;
    if(a.entity==='profiles'&&n.role!==o.role)return'Changed role of'+L+' to '+n.role;
    if(a.entity==='referrals'&&n.status!==o.status)return({approved:'Approved',rejected:'Rejected',flagged:'Flagged',pending:'Moved to review'}[n.status]||'Updated')+' referral'+L;
    if(a.entity==='settings')return'Changed settings';
    return'Updated '+e+L}
  if(a.action==='insert'){
    if(a.entity==='payments')return'Recorded payment'+L+' of '+g(n.amount);
    if(a.entity==='payouts')return'Recorded payout'+L+' of '+g(n.amount);
    if(a.entity==='adjustments')return'Adjusted balance by '+g(n.amount);
    if(a.entity==='profiles')return'New account'+L;
    return'Added '+e+L}
  return'Deleted '+e+L}
async function loadAll(){
  const adm=ROLE==='admin',none=Promise.resolve([]);
  const [profiles,settings,clients,projects,payments,payouts,adj,refs,flags,msgs,ann,reads,chatm,notes,bals,dir,audit,invites]=await Promise.all([
    q(sb.from('profiles').select('*')),
    q(sb.from('settings').select('*').eq('id',1).maybeSingle()),
    q(sb.from('clients').select('*').order('created_at')),
    q(sb.from('projects').select('*').order('created_at')),
    q(sb.from('payments').select('*').order('received_on').order('created_at')),
    q(sb.from('payouts').select('*').order('created_at')),
    q(sb.from('adjustments').select('*').order('created_at')),
    q(sb.from('referrals').select('*').order('created_at',{ascending:false})),
    adm?q(sb.from('referral_flags').select('*')):none,
    q(sb.from('messages').select('*').order('created_at')),
    q(sb.from('announcements').select('*').order('created_at',{ascending:false})),
    q(sb.from('announcement_reads').select('announcement_id')),
    q(sb.from('community_messages').select('*').order('created_at',{ascending:false}).limit(300)),
    q(sb.from('notifications').select('*').order('created_at',{ascending:false}).limit(100)),
    q(sb.from('partner_balances').select('*')),
    q(sb.rpc('community_directory')),
    adm?q(sb.from('audit_log').select('*').order('at',{ascending:false}).limit(300)):none,
    adm?q(sb.rpc('pending_invitations')):none]);
  const nameOf=id=>{const p=profiles.find(x=>x.id===id)||dir.find(x=>x.id===id);return p?(p.full_name||p.email||'Member'):'Former member'};
  const roleOf=id=>{const p=dir.find(x=>x.id===id)||profiles.find(x=>x.id===id);return p&&p.role};
  MEP=profiles.find(p=>p.id===ME)||MEP;
  D.hold=settings?settings.hold_days:5;
  D.dir=dir.map(x=>({id:x.id,name:x.full_name||'Member',role:x.role,st:'Active',email:'',city:'',phone:''}));
  D.partners=profiles.filter(p=>p.role==='partner').map(p=>({id:p.id,name:p.full_name||p.email,email:p.email,city:p.city||'',phone:p.phone||'',acct:p.account_mask||'',st:p.status==='active'?'Active':'Suspended'}));
  D.clients=clients.map(c=>({id:c.id,name:c.name,contact:c.contact||'',email:c.email||'',p:c.partner_id}));
  D.projects=projects.map(p=>({id:p.id,name:p.name,c:p.client_id,budget:p.budget,rate:p.rate_bp,st:PST[p.status]}));
  D.payments=payments.map(x=>({id:x.id,d:x.received_on,pr:x.project_id,amt:x.amount,tax:x.tax,m:PM[x.method],mk:x.method,ref:x.reference,refunded:x.refunded,rev:x.reversed,p:x.partner_id,rate:x.rate_bp,cm:x.commission}));
  D.payouts=payouts.map(x=>({id:x.code,uid:x.id,d:x.paid_on,p:x.partner_id,amt:x.amount,m:PM[x.method],ref:x.reference,void:x.voided}));
  D.adj=adj.map(a=>({d:a.created_on,p:a.partner_id,amt:a.amount,reason:a.reason}));
  const fl=Object.fromEntries(flags.map(f=>[f.referral_id,f.note]));
  D.refs=refs.map(r=>({id:r.id,biz:r.business,p:r.partner_id,bud:r.budget,st:RST[r.status],d:r.created_at.slice(0,10),email:r.email||'',flag:fl[r.id]||'',note:r.decision_note||''}));
  D.msgs={};D.unreadA={};D.unreadP={};
  D.partners.forEach(p=>{D.msgs[p.id]=[];D.unreadA[p.id]=0;D.unreadP[p.id]=0});
  msgs.forEach(m=>{const k=m.partner_id;(D.msgs[k]=D.msgs[k]||[]).push({id:m.id,sid:m.sender_id,f:m.sender_id===k?'p':'a',t:m.body,at:mtime(m.created_at),read:!!m.read_at});
    if(!m.read_at){if(m.sender_id===k)D.unreadA[k]=(D.unreadA[k]||0)+1;else D.unreadP[k]=(D.unreadP[k]||0)+1}});
  D.ann=ann.map(a=>({id:a.id,t:a.title,b:a.body,d:a.created_at.slice(0,10),pin:a.pinned}));
  D.read=Object.fromEntries(reads.map(r=>[r.announcement_id,true]));
  D.chat=chatm.slice().reverse().map(m=>({id:m.id,sid:m.sender_id,f:roleOf(m.sender_id)==='admin'?'admin':m.sender_id,t:m.body,at:Date.parse(m.created_at)}));
  D.cs={admin:{},partner:{}};const seen=+(lsGet('ts-seen-'+ME)||0);D.chat.forEach(m=>{if(m.at<=seen||m.sid===ME)D.cs[ROLE][m.id]=true});
  D.notes=notes.map(n=>({id:n.id,r:ROLE,t:n.text,h:n.link||(ROLE+'-dashboard'),n:!n.read_at}));
  D.bal=Object.fromEntries(bals.map(b=>[b.partner_id,b]));
  D.invites=invites.map(i=>({id:i.id,name:i.full_name||i.email,email:i.email,link:null}));
  D.audit=audit.map(a=>({t:new Date(a.at),who:a.actor_id?nameOf(a.actor_id):'System',what:describe(a),reason:a.reason||''}));
  if(adm&&!D.partners.some(p=>p.id===S.conv))S.conv=(D.partners[0]||{}).id;
}
async function reload(){try{await loadAll()}catch(e){toast(nice(e))}}
const callAdmin=async body=>{const {data,error}=await sb.functions.invoke('partner-admin',{body});
  if(error){let m=error.message;try{const j=await error.context.json();if(j&&j.error)m=j.error}catch(_){}throw new Error(m)}
  if(data&&data.error)throw new Error(data.error);return data};
const rpc=(fn,args)=>q(sb.rpc(fn,args));
const doit=async(fn,ok)=>{try{await fn()}catch(e){return nice(e)}await reload();if(ok)toast(ok);return''};
const fire=async(fn,ok)=>{const e=await doit(fn,ok);if(e)toast(e);render()};
const nowIso=()=>new Date().toISOString();
const markNotesRead=()=>{const L=notesFor(role()).filter(n=>n.n);if(!L.length)return;L.forEach(n=>n.n=false);sb.from('notifications').update({read_at:nowIso()}).in('id',L.map(n=>n.id)).then(()=>{})};
const dl=(name,t)=>{const b=new Blob(['﻿'+t],{type:'text/csv;charset=utf-8'}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);toast('CSV downloaded')};''')

rep("const P=id=>D.partners.find(x=>x.id===id),CL=id=>D.clients.find(x=>x.id===id),PR=id=>D.projects.find(x=>x.id===id);",
    "const P=id=>D.partners.find(x=>x.id===id)||D.dir.find(x=>x.id===id)||{id,name:'Former member',email:'',city:'',phone:'',acct:'',st:'Suspended'},"
    "CL=id=>D.clients.find(x=>x.id===id)||{id,name:'Client',contact:'',email:'',p:null},"
    "PR=id=>D.projects.find(x=>x.id===id)||{id,name:'Project',c:null,budget:0,rate:0,st:'Not started'};")
between('const com=x=>', 'const note=(r,t,h)=>D.notes.unshift({r,t,h,n:true});', '''const com=x=>x.cm;
const own=x=>x.p;
const sumBy=(arr,f)=>arr.reduce((a,x)=>a+f(x),0);
const B=p=>D.bal[p]||{earned:0,paid:0,held:0,available:0,balance:0};
const earned=p=>B(p).earned,paid=p=>B(p).paid,held=p=>B(p).held,avail=p=>B(p).available,bal=p=>B(p).balance;
const role=()=>ROLE||'partner';
const log=()=>{};
const note=()=>{};''')

# ---------- modal engine: async handlers ----------
between("document.addEventListener('submit',e=>{\n  if(e.target.id!=='mform')return;", "if(r&&r.keep)return;closeModal();render();\n});",
'''document.addEventListener('submit',async e=>{
  if(e.target.id!=='mform')return;e.preventDefault();if(!M)return;
  const f=Object.fromEntries(new FormData(e.target)),btn=e.target.querySelector('button[type=submit]');
  if(btn)btn.disabled=true;$('#merr').textContent='';
  let r;try{r=await M(f)}catch(err){r=nice(err)}
  if(btn)btn.disabled=false;
  if(typeof r==='string'&&r){$('#merr').textContent=r;return}
  if(r&&r.keep)return;closeModal();render();
});''')

# ---------- actions ----------
between("const PO=()=>D.partners.map(p=>[p.id,p.name]);\nconst ACT={", " back(){S.open=false;render()}\n};", r'''const PO=()=>D.partners.map(p=>[p.id,p.name]);
const MAIL=/^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const ACT={
 invite(){modal('Invite a Growth Partner','They get a one-time link. There is no public sign-up.',field('Full name','name')+field('Email address','email',{type:'email'})+field('How to send it','how',{opts:[['email','Email the invitation for me'],['link','Give me a link to send myself']]}),'Create invitation',async f=>{
  const n=f.name.trim(),m=f.email.trim().toLowerCase();
  if(!n)return'Enter the partner\'s name.';if(!MAIL.test(m))return'Enter a valid email address.';
  if(D.partners.some(p=>p.email===m)||D.invites.some(i=>i.email===m))return'This email already has an account or a pending invitation.';
  let d;try{d=await callAdmin({action:'invite',email:m,full_name:n,send_email:f.how!=='link'})}catch(e){return nice(e)}
  await reload();
  if(d&&d.link){D.newlink=d.link;info('Invitation ready',`<p class="muted">Copy this link and send it to ${esc(n)} yourself. It works once and expires in 24 hours.</p><div class="fld"><textarea id="linkbox" rows="3" readonly>${esc(d.link)}</textarea></div><div class="mact" style="justify-content:flex-start"><button type="button" class="btn soft" data-act="copylink" data-id="new">Copy link</button></div>`);render();return{keep:true}}
  toast('Invitation emailed to '+m);return''})},
 copylink(id){if(id==='new'&&D.newlink)copy(D.newlink);else toast('Links are only shown when created. Revoke and invite again for a new one.')},
 revoke(id){const i=D.invites.find(x=>x.id===id);modal('Revoke invitation',i?esc(i.name)+' · '+esc(i.email):'','','Revoke',()=>doit(()=>callAdmin({action:'revoke_invite',user_id:id}),'Invitation revoked'),'pink')},
 suspend(id){const p=P(id),on=p.st==='Active';modal(on?'Suspend '+esc(p.name):'Reactivate '+esc(p.name),on?'They will be signed out and cannot sign in until reactivated.':'They will be able to sign in again.',reasonField(),on?'Suspend':'Reactivate',f=>{const e=needReason(f);if(e)return e;return doit(()=>callAdmin({action:on?'suspend':'reactivate',user_id:id,reason:f.reason.trim()}),p.name+' is now '+(on?'suspended':'active'))})},
 approve(id){const r=D.refs.find(x=>x.id==id);fire(()=>rpc('approve_referral',{p_referral:id}),'Approved. '+r.biz+' is now a client of '+P(r.p).name)},
 reject(id){const r=D.refs.find(x=>x.id==id);modal('Reject '+esc(r.biz),'The partner is told it was not accepted.',reasonField(),'Reject',f=>{const e=needReason(f);if(e)return e;return doit(()=>rpc('reject_referral',{p_referral:id,p_reason:f.reason.trim()}),'Referral rejected')})},
 resolve(id){const r=D.refs.find(x=>x.id==id);modal('Resolve duplicate flag',esc(r.flag||''),field('Decision','dec',{opts:[['ok','Not a duplicate. Move to review'],['dup','It is a duplicate. Reject']]})+reasonField(),'Save decision',f=>{const e=needReason(f);if(e)return e;return doit(()=>rpc('resolve_referral_flag',{p_referral:id,p_is_duplicate:f.dec==='dup',p_reason:f.reason.trim()}),'Flag resolved')})},
 reassign(id){const c=CL(id),opts=PO().filter(x=>x[0]!==c.p);if(!opts.length){toast('Invite another partner first.');return}modal('Reassign '+esc(c.name),'Moves the client and its future commission to another partner. Commission already earned stays with the current partner.',field('New partner','p',{opts,val:''})+reasonField(),'Reassign',f=>{const e=needReason(f);if(e)return e;return doit(()=>rpc('reassign_client',{p_client:id,p_partner:f.p,p_reason:f.reason.trim()}),'Client reassigned')})},
 client(){if(!D.partners.length){toast('Invite a partner first. Every client belongs to a partner.');return}modal('New client','Add a client the studio already works with.',field('Client or business name','name')+two(field('Contact person','contact'),field('Email','email',{type:'email'}))+field('Partner','p',{opts:PO()}),'Add client',f=>{
  const n=f.name.trim();if(!n)return'Enter the client name.';const em=f.email.trim().toLowerCase();if(em&&!MAIL.test(em))return'Enter a valid email, or leave it empty.';
  return doit(()=>q(sb.from('clients').insert({name:n,contact:f.contact.trim()||null,email:em||null,partner_id:f.p})),'Client added')})},
 project(){if(!D.clients.length){toast('Add a client first.');return}modal('New project','The agreed commission rate is required.',field('Client','c',{opts:D.clients.map(c=>[c.id,c.name+' · '+P(c.p).name])})+field('Project name','name')+two(field('Budget (GHS)','budget',{inputmode:'decimal',ph:'15,000.00'}),field('Commission rate (%)','rate',{inputmode:'decimal',ph:'12.5'}))+`<div class="hint" id="ratehint">Enter a rate such as 12.5.</div>`,'Create project',async f=>{
  if(!f.name.trim())return'Enter the project name.';const b=parseMoney(f.budget);if(!b)return'Enter the budget, for example 15,000.00.';const r=parseMoney(f.rate);if(r==null||r<=0||r>10000)return'Enter the agreed commission rate between 0.01 and 100.';
  let row;try{row=await q(sb.from('projects').insert({client_id:f.c,name:f.name.trim(),budget:b,rate_bp:r,status:'not_started'}).select('id').single())}catch(e){return nice(e)}
  await reload();toast('Project created');location.hash='admin-project-'+row.id;return''})},
 status(id){const p=PR(id);modal('Project status',esc(p.name),field('Status','st',{opts:Object.values(PST).map(x=>[x,x]),val:p.st}),'Save',f=>doit(()=>q(sb.from('projects').update({status:PSTr[f.st]}).eq('id',id)),'Status updated'))},
 rate(id){const p=PR(id);modal('Change commission rate','Applies to payments recorded from now on. Commission already recorded does not change.',field('New rate (%)','rate',{val:String(p.rate/100),inputmode:'decimal'})+reasonField(),'Change rate',f=>{const r=parseMoney(f.rate);if(r==null||r<=0||r>10000)return'Enter a rate between 0.01 and 100.';const e=needReason(f);if(e)return e;return doit(()=>rpc('change_project_rate',{p_project:id,p_rate_bp:r,p_reason:f.reason.trim()}),'Rate updated for new payments')})},
 payment(id){const open=D.projects.filter(p=>p.st!=='Cancelled');if(!open.length){toast('Create a project first.');return}modal('Record a client payment','Record money that has already arrived. The portal does not move money.',field('Project','pr',{opts:open.map(p=>[p.id,p.name+' · '+CL(p.c).name]),val:id})+two(field('Amount received (GHS)','amt',{inputmode:'decimal',ph:'5,000.00'}),field('Tax included (GHS)','tax',{inputmode:'decimal',val:'0.00'}))+two(field('Date received','d',{type:'date',val:TODAY}),field('Method','m',{opts:Object.values(PM).map(x=>[x,x])}))+field('Transaction reference','ref'),'Record payment',f=>{
  const a=parseMoney(f.amt);if(!a||a<=0)return'Enter the amount received, for example 5,000.00.';const t=parseMoney(f.tax);if(t==null)return'Enter the tax amount, or 0.00.';if(t>a)return'Tax cannot be more than the amount received.';
  if(!f.d||f.d>TODAY)return'Choose the date the money arrived. It cannot be in the future.';const ref=f.ref.trim();if(!ref)return'Enter the transaction reference.';
  return doit(()=>q(sb.from('payments').insert({project_id:f.pr,received_on:f.d,amount:a,tax:t,method:PMr[f.m],reference:ref})),'Payment recorded')})},
 refund(id){const x=D.payments.find(p=>p.id==id),left=x.amt-x.tax-x.refunded;modal('Refund '+esc(x.ref),'Up to '+g(left)+' can still be refunded.',field('Refund amount (GHS)','amt',{inputmode:'decimal'})+reasonField(),'Record refund',f=>{const a=parseMoney(f.amt);if(!a||a<=0)return'Enter the refund amount.';if(a>left)return'That is more than the '+g(left)+' left on this payment.';const e=needReason(f);if(e)return e;return doit(()=>rpc('refund_payment',{p_payment:id,p_amount:a,p_reason:f.reason.trim()}),'Refund recorded. Commission reduced.')})},
 reverse(id){const x=D.payments.find(p=>p.id==id);modal('Reverse '+esc(x.ref),'Use this when the payment never really arrived. Its commission is removed.',reasonField(),'Reverse payment',f=>{const e=needReason(f);if(e)return e;return doit(()=>rpc('reverse_payment',{p_payment:id,p_reason:f.reason.trim()}),'Payment reversed')})},
 payout(id,amt){if(!D.partners.length){toast('Invite a partner first.');return}modal('Record a payout','Send the money outside the portal, then record it here.',field('Partner','p',{opts:PO(),val:id})+two(field('Amount paid (GHS)','amt',{inputmode:'decimal',val:amt||''}),field('Date paid','d',{type:'date',val:TODAY}))+two(field('Method','m',{opts:['Mobile money','Bank transfer'].map(x=>[x,x])}),field('Transaction reference','ref'))+field('Account (masked)','mask',{ph:'****1234',hint:'Store only a masked account. Full numbers are rejected.'}),'Record payout',f=>{
  const a=parseMoney(f.amt);if(!a||a<=0)return'Enter the amount paid.';const av_=avail(f.p);if(a>av_)return'That is more than '+P(f.p).name+' can be paid now ('+g(av_)+').';
  if(!f.ref.trim())return'Enter the transaction reference.';if(/\d{5,}/.test(f.mask))return'Enter only a masked account such as ****1234.';if(!f.d||f.d>TODAY)return'Choose a valid date. It cannot be in the future.';
  return doit(()=>rpc('record_payout',{p_partner:f.p,p_amount:a,p_paid_on:f.d,p_method:PMr[f.m],p_reference:f.ref.trim(),p_account_mask:f.mask.trim()||null}),'Payout recorded')})},
 voidpay(id){const x=D.payouts.find(p=>p.id===id);modal('Void '+x.id,'The amount goes back to the partner\'s balance.',reasonField(),'Void payout',f=>{const e=needReason(f);if(e)return e;return doit(()=>rpc('void_payout',{p_payout:x.uid,p_reason:f.reason.trim()}),'Payout voided')})},
 adjust(){if(!D.partners.length){toast('Invite a partner first.');return}modal('Commission adjustment','A correction is a new ledger line. Use a minus sign to deduct.',field('Partner','p',{opts:PO()})+field('Amount (GHS)','amt',{inputmode:'decimal',ph:'-50.00 or 50.00'})+reasonField(),'Add adjustment',f=>{const neg=/^\s*[-−]/.test(f.amt),a=parseMoney(f.amt.replace(/^\s*[-−+]/,''));if(!a)return'Enter an amount, for example -50.00.';const e=needReason(f);if(e)return e;return doit(()=>q(sb.from('adjustments').insert({partner_id:f.p,amount:neg?-a:a,reason:f.reason.trim()})),'Adjustment added')})},
 referral(){const me=P(ME);if(me.st!=='Active'){toast('Your account is suspended. You cannot submit referrals.');return}modal('Submit a client','The studio checks for duplicates before approving.',field('Client or business name','biz')+two(field('Business email','email',{type:'email'}),field('Estimated budget (GHS)','bud',{inputmode:'decimal'})),'Submit referral',async f=>{
  const n=f.biz.trim();if(!n)return'Enter the client or business name.';const em=f.email.trim().toLowerCase();if(em&&!MAIL.test(em))return'Enter a valid business email, or leave it empty.';
  let b=0;if(f.bud.trim()){b=parseMoney(f.bud);if(b==null)return'Enter the budget as a number, for example 5,000.00.'}
  let row;try{row=await q(sb.from('referrals').insert({business:n,email:em||null,budget:b}).select('id').single())}catch(e){return nice(e)}
  await reload();const r=D.refs.find(x=>x.id===row.id);toast(r&&r.st==='Flagged'?'Submitted. It was flagged as a possible duplicate and will be checked.':'Referral submitted for review');return''})},
 csv(k){const q_=v=>{v=String(v);return /^[=+\-@\t\r]/.test(v)?"'"+v:v};const row=a=>a.map(v=>'"'+q_(v).replace(/"/g,'""')+'"').join(',');let rows;
  if(k==='partners')rows=[['Partner','Email','Status','Earned (GHS)','Paid (GHS)','Balance (GHS)']].concat(D.partners.map(p=>[p.name,p.email,p.st,earned(p.id)/100,paid(p.id)/100,bal(p.id)/100]));
  else if(k==='payments')rows=[['Date','Client','Project','Method','Reference','Received (GHS)','Tax (GHS)','Net (GHS)','Commission (GHS)']].concat(D.payments.map(x=>[x.d,CL(PR(x.pr).c).name,PR(x.pr).name,x.m,x.ref,x.amt/100,x.tax/100,net(x)/100,com(x)/100]));
  else rows=[['Date','Partner','Entry','Amount (GHS)']].concat(ledger().map(l=>[l.d,P(l.p).name,l.t,l.a/100]));
  dl('twelfth-space-'+k+'-'+TODAY+'.csv',rows.map(row).join('\n'))},
 copycsv(){copy(window.__csv)},
 announce(){modal('New announcement','Every Growth Partner sees this and gets a notification. Replies come to you as private messages.',field('Title','t',{ph:'What is this about?'})+field('Message','b',{area:true,ph:'Write the announcement'})+field('Pin to the top','pin',{opts:[['no','No'],['yes','Yes']]}),'Post announcement',f=>{
  if(f.t.trim().length<3)return'Enter a title.';if(f.b.trim().length<10)return'Write a message of at least a few words.';
  return doit(()=>q(sb.from('announcements').insert({title:f.t.trim(),body:f.b.trim(),pinned:f.pin==='yes'})),'Announcement posted to '+D.partners.filter(p=>p.st==='Active').length+' partners')})},
 annpin(id){const a=D.ann.find(x=>x.id===id);fire(()=>q(sb.from('announcements').update({pinned:!a.pin}).eq('id',id)),a.pin?'Unpinned':'Pinned to the top')},
 anndel(id){const a=D.ann.find(x=>x.id===id);modal('Delete announcement',esc(a.t),'','Delete',()=>doit(()=>q(sb.from('announcements').delete().eq('id',id)),'Announcement deleted'))},
 readone(id){D.read[id]=true;render();sb.from('announcement_reads').upsert({announcement_id:id},{onConflict:'announcement_id,user_id',ignoreDuplicates:true}).then(()=>{})},
 readall(){const L=D.ann.filter(a=>!D.read[a.id]);L.forEach(a=>D.read[a.id]=true);toast('All marked as read');render();if(L.length)sb.from('announcement_reads').upsert(L.map(a=>({announcement_id:a.id})),{onConflict:'announcement_id,user_id',ignoreDuplicates:true}).then(()=>{})},
 cdel(id){fire(()=>q(sb.from('community_messages').delete().eq('id',id)),'Message deleted')},
 signout(){sb.auth.signOut()},
 back(){S.open=false;render()}
};''')

# ---------- page tweaks ----------
rep("const qp=()=>{const p0=D.partners.find(p=>avail(p.id)>0)||D.partners[0];",
    "const qp=()=>{const p0=D.partners.find(p=>avail(p.id)>0)||D.partners[0];if(!p0)return `<section class=\"card\"><div class=\"ch\"><div><h2>Quick payout</h2><p class=\"sub\">Pay a partner what is ready</p></div></div><div class=\"empty\">No partners yet. Invite one to get started.</div></section>`;")
rep("${act('Copy link','copylink',i.id)}${act('Revoke','revoke',i.id,'line')}", "${act('Revoke','revoke',i.id,'line')}")
rep("return `<div class=\"pha\">${searchBox('cl','Search clients')}</div>",
    "return `<div class=\"pha\">${searchBox('cl','Search clients')}<span class=\"grow\"></span><button class=\"btn pink\" data-act=\"client\" type=\"button\">${ic('plus',16)} New client</button></div>")
rep("Math.floor((x.amt-x.tax)*PR(x.pr).rate/10000)", "Math.floor(Math.max(0,x.amt-x.tax-x.refunded)*x.rate/10000)")
rep("n=net(x),exact=n*pr.rate/10000", "n=net(x),exact=n*x.rate/10000")
rep("row('Agreed rate',pct(pr.rate))", "row('Agreed rate',pct(x.rate))")
between("document.addEventListener('click',e=>{const a=e.target.closest('#demoadm,#demoptn');", "f.requestSubmit()});", "")
between("PG['admin-audit']=()=>{const base=", "return card('Audit log',tbl(['When','Who','Action','Reason'],rows))};",
    "PG['admin-audit']=()=>card('Audit log',tbl(['When','Who','Action','Reason'],D.audit.map(a=>({c:[a.t.toLocaleString('en-GB',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}),esc(a.who),esc(a.what),esc(a.reason)||'—']})),[],'Nothing recorded yet.'));")
between("PG['admin-settings']=()=>", "</div>`)}</div>`;",
    "PG['admin-settings']=()=>`<div class=\"stack form\" style=\"max-width:640px\">${card('Commission rules',`<div class=\"fld\"><label for=\"s-hold\">Hold before a commission can be paid out</label><select id=\"s-hold\" data-set=\"hold\">${[0,3,5,7,10].map(n=>`<option value=\"${n}\" ${D.hold===n?'selected':''}>${n} business days</option>`).join('')}</select></div>`)}${card('Access',`<div class=\"fld\"><label>Invitation links</label><input value=\"Work once and expire after 24 hours\" readonly></div><div class=\"fld\"><label>Public sign-up</label><input value=\"Off. Invitation only.\" readonly></div>`)}</div>`;")
# Read-by counts need other users' reads, which RLS hides; keep the simpler announcement page.
between("/* ---- read-by counts ---- */", "function render_(){", "function render_(){")

between("const ensureNew=()=>", "const pdash=", "const pdash=")
rep("  if(false&&e.key.toLowerCase()==='f'&&!e.metaKey&&!e.ctrlKey&&!e.altKey&&!/INPUT|TEXTAREA|SELECT/.test(tn)&&!$('#mbg').classList.contains('open')&&!FS.pinning){e.preventDefault();$('#fab').click()}\n", "")

# ---------- sign-in screens ----------
between("let fails=0,AS={};", "AS.done=inv.name.split(' ')[0];authShow('accept-invite')});", r'''let AS={};
const OPEN_ROUTES=['signin','forgot','suspended','accept-invite-expired'];
function authShow(r){
  if(!isAuth(r)){document.body.classList.remove('authmode');return false}
  if(AS.r!==r)AS={r};
  document.body.classList.add('authmode');closeRail();
  const dash=`<a class="btn wide" href="#${role()}-dashboard" style="margin-top:16px">Go to my dashboard</a>`;
  let h='';
  if(r==='signin')h=authCard('Sign in','Use the email your invitation was sent to. There is no public sign-up.',`<form id="signinform" novalidate>${field('Email address','email',{type:'email',ph:'you@example.com'})}${pw('Password','cur')}<div class="err" id="aerr" role="alert"></div><button class="btn wide" type="submit" style="margin-top:16px">Sign in</button></form><div class="alinks"><a href="#forgot">Forgot password?</a></div>`);
  else if(r==='forgot')h=AS.sent?authCard('Check your email','If that address has an account, a reset link is on its way. It works once and expires in 1 hour.',toSignin):authCard('Forgot password','Enter your email and we will send a reset link.',`<form id="forgotform" novalidate>${field('Email address','email',{type:'email',ph:'you@example.com'})}<div class="err" id="aerr" role="alert"></div><button class="btn wide" type="submit" style="margin-top:16px">Send reset link</button></form>${toSignin}`);
  else if(r==='reset')h=AS.done?authCard('Password changed','You are signed in with your new password.',dash):authCard('Choose a new password','Pick something you do not use anywhere else.',`<form id="resetform" novalidate>${pw('New password','new')}${rulesHtml('')}${pw('Confirm new password','new2')}<div class="err" id="aerr" role="alert"></div><button class="btn wide" type="submit" style="margin-top:16px">Change password</button></form>`);
  else if(r==='suspended')h=authCard('Account suspended','Your Growth Partner account is paused, so you cannot sign in right now. Your records are safe and your earnings are not affected. Contact the studio to ask for a review.',toSignin);
  else if(r==='accept-invite-expired')h=authCard('This invitation is no longer valid','The link has expired or was already used. Invitation links work once and expire after 24 hours. Ask the studio to send you a new one.',toSignin);
  else{
    if(AS.done)h=authCard('Welcome, '+esc(AS.done),'Your account is ready.',dash);
    else if(!MEP)h=authCard('This invitation is no longer valid','The link has expired or was already used.',toSignin);
    else{const pp=(MEP.full_name||'').split(' ');h=authCard('Set up your account','Choose a password to finish. Your email comes from the invitation.',`<form id="acceptform" novalidate>${two(field('First name','fn',{val:pp[0]||''}),field('Last name','ln',{val:pp.slice(1).join(' ')}))}${field('Email address','e',{val:MEP.email,ro:true,hint:'This is the email the studio invited. It cannot be changed.'})}${pw('Password','new','Must be at least 8 characters, with a letter and a number.')}<label class="chk"><input type="checkbox" id="f-terms" name="terms"><span>I agree to the studio's terms and to my details being stored to run my partner account.</span></label><div class="err" id="aerr" role="alert"></div><button class="btn wide" type="submit" style="margin-top:16px">Finish setup</button></form>`)}}
  $('#auth').innerHTML=h;window.scrollTo(0,0);
  return true}
const aerr=m=>{const e=$('#aerr');if(e)e.textContent=m};
async function startSession(){
  const {data:{user}}=await sb.auth.getUser();if(!user)return false;
  const {data:p,error}=await sb.from('profiles').select('*').eq('id',user.id).maybeSingle();
  if(error||!p){await sb.auth.signOut();toast('This account is not set up for the portal.');return false}
  if(p.status!=='active'){location.hash='suspended';await sb.auth.signOut();return false}
  ME=user.id;MEP=p;ROLE=p.role;
  try{await loadAll()}catch(e){toast(nice(e))}
  return true}
document.addEventListener('submit',async e=>{
  const id=e.target.id;if(!['signinform','forgotform','resetform','acceptform'].includes(id))return;e.preventDefault();
  const f=Object.fromEntries(new FormData(e.target)),btn=e.target.querySelector('button[type=submit]'),busy=v=>{if(btn)btn.disabled=v};
  if(id==='signinform'){const em=(f.email||'').trim().toLowerCase();
    if(!MAIL.test(em))return aerr('Enter a valid email address.');
    if(!(f.cur||''))return aerr('Enter your password.');
    busy(true);const {error}=await sb.auth.signInWithPassword({email:em,password:f.cur});
    if(error){busy(false);if(/banned/i.test(error.message)){location.hash='suspended';return}return aerr(/invalid login/i.test(error.message)?'That email and password do not match.':nice(error))}
    const ok=await startSession();busy(false);if(ok)location.hash=ROLE+'-dashboard';return}
  if(id==='forgotform'){const em=(f.email||'').trim().toLowerCase();if(!MAIL.test(em))return aerr('Enter a valid email address.');
    busy(true);await sb.auth.resetPasswordForEmail(em,{redirectTo:BASE});busy(false);AS.sent=true;authShow('forgot');return}
  if(id==='acceptform'&&(!(f.fn||'').trim()||!(f.ln||'').trim()))return aerr('Enter your first and last name.');
  const bad=pwRules(f.new||'').find(x=>!x[1]);
  if(bad)return aerr('Your password needs: '+bad[0].toLowerCase()+'.');
  if(f.new2!==undefined&&f.new!==f.new2)return aerr('The two passwords do not match.');
  if(id==='resetform'){busy(true);const {error}=await sb.auth.updateUser({password:f.new});busy(false);if(error)return aerr(nice(error));AS.done=true;authShow('reset');return}
  if(!f.terms)return aerr('Please agree to the terms to continue.');
  const full=((f.fn||'').trim()+' '+(f.ln||'').trim()).trim();busy(true);
  const {error}=await sb.auth.updateUser({password:f.new,data:{full_name:full}});
  if(error){busy(false);return aerr(nice(error))}
  await sb.from('profiles').update({full_name:full}).eq('id',ME);await reload();busy(false);
  AS.done=full.split(' ')[0];authShow('accept-invite')});''')

# ---------- router ----------
rep("""  CUR_Q=null;route=location.hash.slice(1)||'admin-dashboard';
  if(/^(admin|partner)-announcements$/.test(route)){S.ctab='news';location.replace('#'+route.split('-')[0]+'-community');return}
  if(route==='partner-start'){ensureNew();ME='newbie';location.replace('#partner-dashboard');return}
  if(/^admin-/.test(route)&&ME!=='ama')resetMe();
  if(authShow(route))return;""",
"""  CUR_Q=null;if(!BOOTED)return;route=location.hash.slice(1);
  if(!ME){if(!OPEN_ROUTES.includes(route)){location.replace('#signin');return}authShow(route);return}
  if(!(route.startsWith(ROLE+'-')||route==='reset'||route==='accept-invite')){location.replace('#'+ROLE+'-dashboard');return}
  if(/^(admin|partner)-announcements$/.test(route)){S.ctab='news';location.replace('#'+route.split('-')[0]+'-community');return}
  if(authShow(route))return;""")
rep("  $('#r-admin').className=r==='admin'?'on':'';$('#r-partner').className=r==='partner'?'on':'';\n", "")
rep("<b>Studio admin</b><small>admin@sample.test</small>", "<b>${esc(MEP.full_name||'Studio admin')}</b><small>${esc(MEP.email)}</small>")
rep("""<a class="ibtn dk" href="#signin" aria-label="Sign out">${ic('logout',18)}</a>""",
    """<button type="button" class="ibtn dk" data-act="signout" aria-label="Sign out">${ic('logout',18)}</button>""", 2)
rep(";$('#fbpage').textContent=pageName();", ";")
rep("const m=$('#msgs');if(m)m.scrollTop=m.scrollHeight;",
    "const m=$('#msgs');if(m)m.scrollTop=m.scrollHeight;if(route===ROLE+'-messages'){const cid=ROLE==='admin'?S.conv:ME,un=(D.msgs[cid]||[]).filter(x=>!x.read&&x.sid!==ME);if(un.length){un.forEach(x=>x.read=true);sb.from('messages').update({read_at:nowIso()}).in('id',un.map(x=>x.id)).then(()=>{})}}")

# ---------- notifications, refresh, settings, compose forms ----------
rep("notesFor(role()).forEach(n=>n.n=false)", "markNotesRead()", 4)
rep("if(n){n.n=false;location.hash=n.h}", "if(n){n.n=false;sb.from('notifications').update({read_at:nowIso()}).eq('id',n.id).then(()=>{});location.hash=n.h}")
rep("if(t.closest('[data-refresh]')){toast('Transactions are up to date');render();return}",
    "if(t.closest('[data-refresh]')){reload().then(()=>{toast('Up to date');render()});return}")
rep("if(k){D[k]=Number(e.target.value);log('Changed '+k+' setting to '+e.target.value);toast('Setting saved');render()}",
    "if(k==='hold'){fire(()=>q(sb.from('settings').update({hold_days:Number(e.target.value)}).eq('id',1)),'Setting saved')}")
between("  if(e.target.id==='xform'){e.preventDefault();", "const x=$('#xin');x&&x.focus();return}",
    "  if(e.target.id==='xform'){e.preventDefault();const v=$('#xin').value.trim();if(!v)return;$('#xin').value='';fire(()=>q(sb.from('community_messages').insert({body:v}))).then(()=>{const x=$('#xin');x&&x.focus()});return}")
between("  if(e.target.id==='cform'){e.preventDefault();", "render();$('#cin')&&$('#cin').focus();return}",
    "  if(e.target.id==='cform'){e.preventDefault();const v=$('#cin').value.trim();if(!v)return;const cid=role()==='admin'?S.conv:ME;if(!cid)return;$('#cin').value='';fire(()=>q(sb.from('messages').insert({partner_id:cid,body:v}))).then(()=>{$('#cin')&&$('#cin').focus()});return}")
rep("const p=P(ME);p.phone=f.phone.trim();p.city=f.city.trim();p.acct=ac;toast('Profile saved');render()}",
    "fire(()=>q(sb.from('profiles').update({phone:f.phone.trim(),city:f.city.trim(),account_mask:ac||null}).eq('id',ME)),'Profile saved')}")
rep("D.partners.some(p=>hOf(p)===l)", "D.dir.some(p=>hOf(p)===l)")
rep("const o=D.partners.filter(p=>p.st==='Active'&&p.id!==vid()).map(p=>({h:p.name.split(' ')[0],n:p.name,i:pIdx(p.id)}))",
    "const o=D.dir.filter(p=>p.role==='partner'&&p.id!==vid()).map(p=>({h:p.name.split(' ')[0],n:p.name,i:pIdx(p.id)}))")
rep("const r=role();D.chat.forEach(m=>D.cs[r][m.id]=true);", "const r=role();D.chat.forEach(m=>D.cs[r][m.id]=true);lsSet('ts-seen-'+ME,String(Date.now()));")
between("window.__csv=t;\n  info('Export my ledger',", "Copy CSV</button></div>`)};", "dl('my-commission-ledger-'+TODAY+'.csv',t)};")
rep("""const csvq=v=>{v=String(v);return /^[=+\\-@]/.test(v)?"'"+v:v}""", """const csvq=v=>{v=String(v);return /^[=+\\-@\\t\\r]/.test(v)?"'"+v:v}""")

# ---------- feedback widget out, boot in ----------
between("/* ---------- feedback ---------- */", "S.open=false;render();", r'''const FS={pinning:false};
function drawPins(){}function renderFb(){}function closeFb(){}
sb.auth.onAuthStateChange(ev=>{if(ev==='SIGNED_OUT'&&ME){ME=null;MEP=null;ROLE=null;resetD();render()}});
setInterval(()=>{if(!ME||document.hidden||$('#mbg').classList.contains('open'))return;const a=document.activeElement;if(a&&/INPUT|TEXTAREA|SELECT/.test(a.tagName))return;reload().then(render)},60000);
async function boot(){
  document.body.classList.add('authmode');
  $('#auth').innerHTML='<div class="aw"><section class="ar" style="grid-column:1/-1"><div class="acard"><p class="muted">Loading the portal…</p></div></section></div>';
  const lt=(/[#&]type=([a-z]+)/.exec(BOOT_HASH)||[])[1],le=/[#&]error(_code)?=/.test(BOOT_HASH);
  let sess=null;try{sess=(await sb.auth.getSession()).data.session}catch(_){}
  BOOTED=true;S.open=false;
  if(sess&&await startSession()){if(lt==='invite')location.replace('#accept-invite');else if(lt==='recovery')location.replace('#reset')}
  else if(le)location.replace('#'+(lt==='recovery'?'forgot':'accept-invite-expired'));
  render();
}
boot();''')

open(dst, 'w', encoding='utf-8').write(h)
print('ok', len(h), 'bytes')
