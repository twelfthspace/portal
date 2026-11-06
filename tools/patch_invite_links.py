"""Invitations that survive WhatsApp and mail scanners: links open an Accept page that only redeems
the token on a button press, pending people show as Invited, and the owner can make a fresh link.
python3 -I tools/patch_invite_links.py site/index.html"""
import sys
p = sys.argv[1]
h = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f'expected {count}, found {n}: {old[:100]!r}')
    h = h.replace(old, new)

# ---------- the Accept invitation screen (#join=<token hash>) ----------
rep("const BOOT_HASH=location.hash,BASE=location.origin+location.pathname;",
    "const BOOT_HASH=location.hash,BASE=location.origin+location.pathname;let JOIN=null;")
rep("'accept-invite':'Accept invitation',", "'accept-invite':'Accept invitation','join':'Accept invitation',")
rep(" 'accept-invite':{h:'Get started with us',",
    " 'join':{h:'Get started with us',d:'Complete these easy steps to register your account.',s:['Accept your invitation','Complete your profile','Submit your first client'],a:0},\n 'accept-invite':{h:'Get started with us',")
rep("const OPEN_ROUTES=['signin','forgot','suspended','accept-invite-expired'];",
    "const OPEN_ROUTES=['signin','forgot','suspended','accept-invite-expired','join'];")
rep("if(!(route.startsWith(role()+'-')||route==='reset'||route==='accept-invite')){",
    "if(!(route.startsWith(role()+'-')||route==='reset'||route==='accept-invite'||route==='join')){")
rep("  else if(r==='accept-invite-expired')h=authCard('This invitation is no longer valid','The link has expired or was already used. Invitation links work once and expire after 24 hours. Ask the studio to send you a new one.',toSignin);",
    "  else if(r==='join')h=JOIN?authCard('You are invited','Press the button to accept your invitation to the Twelfth Space portal. Next you choose a password.',`${ME?`<p class=\"small muted\">This device is signed in as ${escE(MEP.email)}. Accepting signs that account out here first.</p>`:''}<div class=\"err\" id=\"aerr\" role=\"alert\"></div><button type=\"button\" class=\"btn wide\" data-act=\"joinnow\" style=\"margin-top:16px\">Accept invitation</button>`):authCard('This invitation is no longer valid','The link has expired or was already used. Ask the studio to send you a new one.',toSignin);\n"
    "  else if(r==='accept-invite-expired')h=authCard('This invitation is no longer valid','The link has expired or was already used. Invitation links work once and expire after a short time. Ask the studio to send you a new one.',toSignin);")
rep("  const lt=(/[#&]type=([a-z]+)/.exec(BOOT_HASH)||[])[1],le=/[#&]error(_code)?=/.test(BOOT_HASH);",
    "  const jm=/^#join=([A-Za-z0-9_-]{16,256})$/.exec(BOOT_HASH);if(jm){JOIN=jm[1];history.replaceState(null,'',BASE+'#join')}\n"
    "  const lt=(/[#&]type=([a-z]+)/.exec(BOOT_HASH)||[])[1],le=/[#&]error(_code)?=/.test(BOOT_HASH);")

# ---------- pending people show as Invited ----------
rep("D.invites=invites.filter(i=>i.role!=='accounts').map(i=>({id:i.id,name:i.full_name||i.email,email:i.email,link:null}));",
    "D.invites=invites.filter(i=>i.role!=='accounts').map(i=>({id:i.id,name:i.full_name||i.email,email:i.email,at:i.invited_at,link:null}));")
rep("D.staffInvites=invites.filter(i=>i.role==='accounts').map(i=>({id:i.id,name:i.full_name||i.email,email:i.email}));",
    "D.staffInvites=invites.filter(i=>i.role==='accounts').map(i=>({id:i.id,name:i.full_name||i.email,email:i.email,at:i.invited_at}));")
rep("Suspended:'pink',Completed:'mint'", "Suspended:'pink',Invited:'sun',Completed:'mint'")
rep("who(p.name,p.email,pIdx(p.id)),stTag(p.st),", "who(p.name,p.email,pIdx(p.id)),stTag(pSt(p)),")
rep("<div class=\"acts\">${act('Revoke','revoke',i.id,'line')}</div>",
    "<div class=\"acts\"><span class=\"small muted\">Sent ${sentD(i.at)}</span>${act('New link','relink',i.id,'soft')}${act('Revoke','revoke',i.id,'line')}</div>")
rep("${tag('Invited','sun')}${own?act('Revoke','revoke',i.id,'line'):''}",
    "${tag('Invited','sun')}${own?act('New link','relink',i.id,'soft')+act('Revoke','revoke',i.id,'line'):''}")

# partner page: an invitation that was never accepted
rep("const pic=D.avById&&D.avById[id],tel=ghTel(p.phone)",
    "const inv=D.invites.find(x=>x.id===id),pic=D.avById&&D.avById[id],tel=ghTel(p.phone)")
rep("<div class=\"ph-tags\">${stTag(p.st)}", "<div class=\"ph-tags\">${stTag(pSt(p))}")
rep("  const ready=rem?",
    "  const ready=inv?`<div class=\"ph-ready inv\"><span class=\"ph-ic\">${ic('mail',20)}</span><div class=\"ptx\"><b>Invitation not accepted yet</b><p>Sent ${sentD(inv.at)}. If ${first} can't find it, send a fresh link on WhatsApp.</p></div><button type=\"button\" class=\"btn sm\" data-act=\"relink\" data-id=\"${id}\">${ic('refresh',15)} New invite link</button></div>`:rem?")
rep("${p.st==='Removed'?'':`<button type=\"button\" class=\"btn sm\" data-chat=\"${id}\">${ic('chat',15)} Ask ${first} to add it</button>`}",
    "${p.st==='Removed'||D.invites.some(x=>x.id===id)?'':`<button type=\"button\" class=\"btn sm\" data-chat=\"${id}\">${ic('chat',15)} Ask ${first} to add it</button>`}")

# ---------- one place that shows a fresh link, with WhatsApp sharing ----------
rep("if(d&&d.link){D.newlink=d.link;info('Invitation ready',`<p class=\"muted\">Copy this link and send it to ${esc(n)} yourself. It works once and expires in 24 hours.</p><div class=\"fld\"><textarea id=\"linkbox\" rows=\"3\" readonly>${esc(d.link)}</textarea></div><div class=\"mact\" style=\"justify-content:flex-start\"><button type=\"button\" class=\"btn soft\" data-act=\"copylink\" data-id=\"new\">Copy link</button></div>`);render();return{keep:true}}",
    "if(d&&d.link){linkReady(n,d.link);render();return{keep:true}}")
rep("if(d&&d.link){D.newlink=d.link;info('Invitation ready',`<p class=\"muted\">Copy this link and send it to ${esc(n)} yourself. It works once and expires in 24 hours. When they accept, they join as Accounts staff.</p><div class=\"fld\"><textarea id=\"linkbox\" rows=\"3\" readonly>${esc(d.link)}</textarea></div><div class=\"mact\" style=\"justify-content:flex-start\"><button type=\"button\" class=\"btn soft\" data-act=\"copylink\" data-id=\"new\">Copy link</button></div>`);render();return{keep:true}}",
    "if(d&&d.link){linkReady(n,d.link,' When they accept, they join as Accounts staff.');render();return{keep:true}}")
rep("else toast('Links are only shown when created. Revoke and invite again for a new one.')",
    "else toast('Links are only shown when created. Use New link to make a fresh one.')")

rep("const OWNER_ACTS=['invite','revoke',", "const OWNER_ACTS=['invite','relink','revoke',")
rep("body.not-owner [data-act=\"revoke\"],", "body.not-owner [data-act=\"revoke\"],body.not-owner [data-act=\"relink\"],")

rep("const studioId=()=>", r'''const sentD=t=>t?new Date(t).toLocaleDateString('en-GB',{day:'numeric',month:'short'}):'earlier';
const pSt=p=>p.st==='Active'&&D.invites.some(i=>i.id===p.id)?'Invited':p.st;
function linkReady(name,link,extra){D.newlink=link;const fn=String(name||'').trim().split(/\s+/)[0]||'there';
  const msg='Hi '+fn+', here is your invitation to the Twelfth Space portal:\n'+link+'\n\nOpen it and press "Accept invitation", then choose a password. The link works once, so please use it soon.';
  info('Invitation link ready',`<p class="muted">Send this to ${esc(name)} on WhatsApp or by email. It works once and expires soon, so send it straight away.${extra||''}</p><p class="small muted">It opens an <b>Accept invitation</b> button, so WhatsApp link previews can't use it up.</p><div class="fld"><textarea id="linkbox" rows="3" readonly>${esc(link)}</textarea></div><div class="mact" style="justify-content:flex-start;flex-wrap:wrap"><button type="button" class="btn soft" data-act="copylink" data-id="new">${ic('copy',15)} Copy link</button><a class="btn" href="https://wa.me/?text=${encodeURIComponent(msg)}" target="_blank" rel="noopener">${ic('wa',15)} Send on WhatsApp</a></div>`)}
ACT.relink=function(id){if(!isOwner()){toast('Only the owner can do this.');return}
  const i=D.invites.find(x=>x.id===id)||D.staffInvites.find(x=>x.id===id);if(!i){toast('This invitation was already accepted or revoked.');return}
  modal('New invitation for '+esc(i.name),`${fmtEmail(i.email)} · first sent ${sentD(i.at)}. A new link replaces the old one, which stops working.`,field('How to send it','how',{opts:[['link','Give me a link to send on WhatsApp (recommended)'],['email','Email it again']]}),'Make new link',async f=>{
    let d;try{d=await callAdmin({action:'invite_link',user_id:id,send_email:f.how==='email'})}catch(e){return nice(e)}
    await reload();
    if(d&&d.link){linkReady(i.name,d.link,D.staffInvites.some(x=>x.id===id)?' When they accept, they join as Accounts staff.':'');render();return{keep:true}}
    toast('Invitation emailed again to '+i.email+'. Ask them to check Spam and Promotions.');render();return''})};
ACT.joinnow=async function(){const tok=JOIN;if(!tok){location.replace('#accept-invite-expired');return}
  const b=document.querySelector('[data-act=joinnow]');if(b){b.disabled=true;b.textContent='Checking your invitation…'}
  try{if(ME)await sb.auth.signOut({scope:'local'})}catch(_){}
  const {error}=await sb.auth.verifyOtp({token_hash:tok,type:'invite'});JOIN=null;
  if(error){location.replace('#accept-invite-expired');return}
  if(await startSession()){location.replace('#accept-invite');render()}else if(location.hash==='#join')location.replace('#signin')};
const studioId=()=>''')

rep('.pop .pall{display:block;', '''.ph-ready.inv{background:var(--sand-2);border-color:#E3E79B}.ph-ic{width:44px;height:44px;border-radius:50%;background:#fff;border:1px solid var(--line);display:grid;place-items:center;flex:none}
.pop .pall{display:block;''')

open(p, 'w', encoding='utf-8').write(h)
print('ok', len(h))
