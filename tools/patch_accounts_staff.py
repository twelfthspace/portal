"""Accounts staff on the studio side, with owner-only actions hidden and guarded,
and a Studio team section in Settings.  python3 -I tools/patch_accounts_staff.py site/index.html"""
import sys
p = sys.argv[1]
h = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f'expected {count}, found {n}: {old[:100]!r}')
    h = h.replace(old, new)

# staff use the studio side of the portal
rep("ME=user.id;MEP=p;ROLE=p.role;", "ME=user.id;MEP=p;ROLE=p.role==='partner'?'partner':'admin';")

# staff list and invitations split by role
rep("D.invites=invites.map(i=>({id:i.id,name:i.full_name||i.email,email:i.email,link:null}));",
    "D.invites=invites.filter(i=>i.role!=='accounts').map(i=>({id:i.id,name:i.full_name||i.email,email:i.email,link:null}));\n"
    "  D.staffInvites=invites.filter(i=>i.role==='accounts').map(i=>({id:i.id,name:i.full_name||i.email,email:i.email}));\n"
    "  D.staff=profiles.filter(p=>p.role!=='partner').map(p=>({id:p.id,name:p.full_name||p.email,email:p.email,role:p.role,st:{active:'Active',suspended:'Suspended',removed:'Removed'}[p.status]||'Suspended'}));")
rep("const blankD=()=>({", "const blankD=()=>({staff:[],staffInvites:[],")

# chat: staff show as the studio, with their role
rep("const key=m.type+':'+m.id,mine=isMe(m.sid),adm=role()==='admin',isAdm=roleOfId(m.sid)==='admin';",
    "const key=m.type+':'+m.id,mine=isMe(m.sid),adm=role()==='admin',isAdm=isStaffRole(roleOfId(m.sid));")
rep("${isAdm?tag('Studio','sky'):''}", "${isAdm?tag(roleOfId(m.sid)==='accounts'?'Studio · Accounts':'Studio','sky'):''}")
rep("if(tk.includes('studio'))D.dir.filter(p=>p.role==='admin')", "if(tk.includes('studio'))D.dir.filter(p=>isStaffRole(p.role))")
rep("(tk.includes('everyone')&&roleOfId(m.sid)==='admin')", "(tk.includes('everyone')&&isStaffRole(roleOfId(m.sid)))")

# channels are managed by the owner
rep("${adm?`<button type=\"button\" data-act=\"chnew\"", "${adm&&isOwner()?`<button type=\"button\" data-act=\"chnew\"")
rep("${adm?`<button type=\"button\" class=\"ibtn\" data-act=\"chedit\"", "${adm&&isOwner()?`<button type=\"button\" class=\"ibtn\" data-act=\"chedit\"")

# settings: commission rules are owner-only; role shown correctly
rep("['Role','Administrator']", "['Role',MEP.role==='accounts'?'Accounts':'Owner']")
rep("${field('Hold before a commission can be paid out','hold',{opts:[0,3,5,7,10].map(n=>[String(n),n+' business days']),val:String(D.hold)})}<div class=\"hint\">Applies straight away to commission that is still on hold.</div>",
    "${isOwner()?field('Hold before a commission can be paid out','hold',{opts:[0,3,5,7,10].map(n=>[String(n),n+' business days']),val:String(D.hold)})+'<div class=\"hint\">Applies straight away to commission that is still on hold.</div>':ro('Hold before a commission can be paid out',D.hold+' business days')+'<div class=\"hint\">Only the owner can change this.</div>'}")
rep("if(adm&&f.hold!==undefined&&Number(f.hold)!==D.hold)", "if(adm&&isOwner()&&f.hold!==undefined&&Number(f.hold)!==D.hold)")
rep("PG['admin-settings']=()=>profilePage(true);", "PG['admin-settings']=()=>profilePage(true)+teamCard();")

# hide owner-only controls for staff (the database refuses them anyway)
rep("CUR_Q=null;if(!BOOTED)return;route=location.hash.slice(1);",
    "CUR_Q=null;if(!BOOTED)return;route=location.hash.slice(1);document.body.classList.toggle('not-owner',!!MEP&&MEP.role==='accounts');")

# helpers, guards, Studio team
rep("const studioId=()=>", r'''const isStaffRole=r=>r==='admin'||r==='accounts';
const isOwner=()=>!!MEP&&MEP.role==='admin'&&!S.viewAs;
const OWNER_ACTS=['invite','revoke','suspend','remove','rate','reassign','chnew','chedit','staffadd','staffsus','staffrem'];
OWNER_ACTS.forEach(k=>{const f=ACT[k];if(f)ACT[k]=function(...a){if(!isOwner()){toast('Only the owner can do this.');return}return f.apply(this,a)}});
function teamCard(){const own=isOwner(),L=D.staff.filter(x=>x.st!=='Removed').sort((a,b)=>(a.role==='admin'?0:1)-(b.role==='admin'?0:1));
  const row=x=>`<div>${who(x.name,x.email,pIdx(x.id))}<span class="grow"></span><div class="acts">${tag(x.role==='admin'?'Owner':'Accounts',x.role==='admin'?'sun':'sky')}${x.st!=='Active'?stTag(x.st):''}${own&&x.role==='accounts'?act(x.st==='Active'?'Suspend':'Reactivate','staffsus',x.id,'line')+act('Remove','staffrem',x.id,'line'):''}</div></div>`;
  return `<section class="pcard"><h2 class="ptitle2">Studio team</h2><div class="prow"><div class="pl"><h3>Who runs the portal</h3><p>The owner has full control. Accounts staff handle payments, payouts, clients, projects, referrals and messages, but can't manage people, rates or settings.</p></div>
  <div class="pf"><div class="list">${L.map(row).join('')}${D.staffInvites.map(i=>`<div>${who(i.name,i.email,3)}<span class="grow"></span><div class="acts">${tag('Invited','sun')}${own?act('Revoke','revoke',i.id,'line'):''}</div></div>`).join('')}</div>
  ${own?`<div class="mact" style="justify-content:flex-start;margin-top:14px"><button type="button" class="btn" data-act="staffadd">${ic('plus',16)} Add staff member</button></div>`:''}</div></div></section>`}
ACT.staffadd=function(){if(!isOwner()){toast('Only the owner can do this.');return}
  modal('Add an Accounts staff member','They can handle payments, payouts, clients, projects, referrals and messages. They cannot manage people, rates or settings.',field('Full name','name')+field('Email address','email',{type:'email'})+field('How to send it','how',{opts:[['email','Email the invitation for me'],['link','Give me a link to send myself']]}),'Send invitation',async f=>{
  const n=f.name.trim(),m=f.email.trim().toLowerCase();if(!n)return'Enter their name.';if(!MAIL.test(m))return'Enter a valid email address.';
  if(D.staff.some(x=>x.email===m)||D.partners.some(x=>x.email===m)||D.invites.some(x=>x.email===m)||D.staffInvites.some(x=>x.email===m))return'This email already has an account or a pending invitation.';
  let d;try{d=await callAdmin({action:'invite',role:'accounts',email:m,full_name:n,send_email:f.how!=='link'})}catch(e){return nice(e)}
  await reload();
  if(d&&d.link){D.newlink=d.link;info('Invitation ready',`<p class="muted">Copy this link and send it to ${esc(n)} yourself. It works once and expires in 24 hours. When they accept, they join as Accounts staff.</p><div class="fld"><textarea id="linkbox" rows="3" readonly>${esc(d.link)}</textarea></div><div class="mact" style="justify-content:flex-start"><button type="button" class="btn soft" data-act="copylink" data-id="new">Copy link</button></div>`);render();return{keep:true}}
  toast('Invitation emailed to '+m);return''})};
ACT.staffsus=function(id){const x=D.staff.find(s=>s.id===id);if(!x)return;const on=x.st==='Active';
  modal((on?'Suspend ':'Reactivate ')+esc(x.name),on?'They will be signed out and cannot sign in until reactivated.':'They will be able to sign in again.',reasonField(),on?'Suspend':'Reactivate',f=>{const e=needReason(f);if(e)return e;return doit(()=>callAdmin({action:on?'suspend':'reactivate',user_id:id,reason:f.reason.trim()}),x.name+' is now '+(on?'suspended':'active'))})};
ACT.staffrem=function(id){const x=D.staff.find(s=>s.id===id);if(!x)return;
  modal('Remove '+esc(x.name),'For a staff member who has left. Their login is closed for good; everything they recorded stays in the books and the audit log.',reasonField()+field('Type REMOVE to confirm','confirm',{ph:'REMOVE'}),'Remove',f=>{const e=needReason(f);if(e)return e;if((f.confirm||'').trim().toUpperCase()!=='REMOVE')return'Type REMOVE to confirm.';
    return doit(()=>callAdmin({action:'remove',user_id:id,reason:f.reason.trim()}),x.name+' has been removed')},'pink')};
const studioId=()=>''')

rep('.pop .pall{display:block;', '''body.not-owner [data-act="invite"],body.not-owner [data-act="revoke"],body.not-owner [data-act="suspend"],body.not-owner [data-act="remove"],body.not-owner [data-act="rate"],body.not-owner [data-act="reassign"],body.not-owner [data-act="chnew"],body.not-owner [data-act="chedit"],body.not-owner [data-act="staffadd"],body.not-owner [data-act="staffsus"],body.not-owner [data-act="staffrem"]{display:none!important}
.pop .pall{display:block;''')

open(p, 'w', encoding='utf-8').write(h)
print('ok', len(h))
