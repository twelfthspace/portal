"""One messaging space: Activity, channels with threads, announcements and direct messages,
with emoji reactions, an emoji picker, files, voice notes, @mentions, edit/delete, unread counts,
live updates, typing and online indicators.  python3 -I tools/patch_messaging_hub.py site/index.html"""
import sys
p = sys.argv[1]
h = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f'expected {count}, found {n}: {old[:100]!r}')
    h = h.replace(old, new)

# ---------- icons ----------
rep('const I={megaphone:"', 'const I={'
    'smile:"M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8 14s1.5 2 4 2 4-2 4-2M9 9.5h.01M15 9.5h.01",'
    'clip:"M21.4 11.1l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5",'
    'mic:"M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3zM19 10v2a7 7 0 0 1-14 0v-2M12 19v3",'
    'file:"M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6",'
    'dl:"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3",'
    'reply:"M9 17l-5-5 5-5M4 12h11a5 5 0 0 1 5 5v2",'
    'trash:"M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6",'
    'lock:"M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4",'
    'at:"M16 12a4 4 0 1 0-1.2 2.8M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8",'
    'megaphone:"')

# ---------- state ----------
rep("const blankD=()=>({pay:{},", "const blankD=()=>({cm:[],dmByP:{},channels:[],allChannels:[],creads:{},reacts:{},furl:{},online:new Set(),pay:{},")
rep("const S={viewAs:null,realMe:null,tab:'All',", "const S={hub:null,hv:'list',thread:null,draft:{},att:{},editing:null,typing:{},viewAs:null,realMe:null,tab:'All',")

# ---------- loading ----------
rep("q(sb.from('community_messages').select('*').order('created_at',{ascending:false}).limit(300)),",
    "q(sb.from('community_messages').select('*').order('created_at',{ascending:false}).limit(1000)),")
rep("  if(adm&&!D.partners.some(p=>p.id===S.conv))S.conv=(D.partners[0]||{}).id;\n",
    "  if(adm&&!D.partners.some(p=>p.id===S.conv))S.conv=(D.partners[0]||{}).id;\n  await loadChat({chatm,msgs});\n")

# ---------- navigation: one Messages entry ----------
rep("['community','Community','megaphone'],", "")
rep(",['community','Community','megaphone']]", "]")
rep("messages:um,community:(r==='partner'?D.ann.filter(a=>!D.read[a.id]).length:0)+cunread(r)}", "messages:hubUnreadTotal()}")

# ---------- routes into the hub ----------
rep("  if(/^(admin|partner)-announcements$/.test(route)){S.ctab='news';location.replace('#'+route.split('-')[0]+'-community');return}",
    "  if(hubRoute(route))return;")
rep("if(!S.viewAs&&route===ROLE+'-messages'){const cid=ROLE==='admin'?S.conv:ME,un=(D.msgs[cid]||[]).filter(x=>!x.read&&x.sid!==ME);if(un.length){un.forEach(x=>x.read=true);sb.from('messages').update({read_at:nowIso()}).in('id',un.map(x=>x.id)).then(()=>{})}}",
    "if(!S.viewAs&&/^(admin|partner)-messages$/.test(route))hubMarkRead();")
rep("const ch=t.closest('[data-chat]');if(ch){S.conv=ch.dataset.chat;if(location.hash==='#admin-messages'){S.open=true;render()}else{S.goChat=true;location.hash='admin-messages'}return}",
    "const ch=t.closest('[data-chat]');if(ch){S.hub={t:'dm',id:ch.dataset.chat};S.thread=null;S.hv='conv';if(location.hash==='#admin-messages')render();else location.hash='admin-messages';return}")
rep("function render(){try{render_()}", "function render(){const _hs=hubSnap();try{render_();hubRestore(_hs)}")
rep("  startAlerts();\n  return true}", "  startAlerts();startChatLive();\n  return true}")
rep("sb.auth.onAuthStateChange(ev=>{if(ev==='SIGNED_OUT'&&ME){stopAlerts();", "sb.auth.onAuthStateChange(ev=>{if(ev==='SIGNED_OUT'&&ME){stopAlerts();stopChatLive();")

# ---------- the hub ----------
rep("PG['partner-messages']=()=>chat('partner');", r'''PG['partner-messages']=()=>chat('partner');
/* ================= messaging hub ================= */
const HUB_QUICK=['👍','❤️','😂','🎉','🔥','👏','🙏','👀'];
const HUB_EMO={'Smileys':'😀 😃 😄 😁 😆 😅 😂 🙂 😉 😊 😍 🥳 😎 🤔 😮 😢 😭 🙄 😴 🤩','Gestures':'👍 👎 👏 🙌 🙏 💪 👋 🤝 ✌️ 👌 🫶 👀','Celebrate':'🎉 🔥 💯 ✅ ⭐ 🚀 💡 ❤️ 💚 💛 🏆 💰','Work':'📌 📎 📅 📈 📊 💼 📝 ⏰ 📞 ✉️ 🧾 🏁'};
const HUB_TYPES=['image/jpeg','image/png','image/webp','image/gif','application/pdf','text/plain','text/csv','audio/webm','audio/ogg','audio/mp4','audio/mpeg','audio/wav','audio/x-m4a','video/mp4','application/zip','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.ms-powerpoint','application/vnd.openxmlformats-officedocument.presentationml.presentation'];
const HUB_MAX=26214400;
const fmtSize=n=>n<1024?n+' B':n<1048576?(n/1024).toFixed(0)+' KB':(n/1048576).toFixed(1)+' MB';
const fmtDur=s=>{s=Math.max(0,Math.round(s||0));return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')};
const hhmm=t=>new Date(t).toTimeString().slice(0,5);
const dayLab=t=>{const d=new Date(t),n=new Date(),y=new Date();y.setDate(n.getDate()-1);if(d.toDateString()===n.toDateString())return'Today';if(d.toDateString()===y.toDateString())return'Yesterday';return d.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long'})};
const baseType=t=>String(t||'application/octet-stream').split(';')[0].trim().toLowerCase();
const roleOfId=id=>{const p=D.dir.find(x=>x.id===id);return p?p.role:(D.partners.some(x=>x.id===id)?'partner':null)};
const nameOfId=id=>P(id).name;
const isMe=id=>id===realMe();
const onHub=()=>/^(admin|partner)-messages$/.test(route);

async function loadChat(pre){
  pre=pre||{};
  const [channels,creads,reacts,chatm,msgs]=await Promise.all([
    q(sb.from('channels').select('*').order('position').order('created_at')),
    q(sb.from('channel_reads').select('*')),
    q(sb.from('message_reactions').select('*').order('created_at')),
    pre.chatm?Promise.resolve(pre.chatm):q(sb.from('community_messages').select('*').order('created_at',{ascending:false}).limit(1000)),
    pre.msgs?Promise.resolve(pre.msgs):q(sb.from('messages').select('*').order('created_at'))]);
  D.allChannels=channels;D.channels=channels.filter(c=>!c.archived);
  D.creads=Object.fromEntries(creads.map(r=>[r.channel_id,Date.parse(r.last_read_at)]));
  D.cm=chatm.slice().reverse().map(m=>({id:m.id,type:'community',ch:m.channel_id,parent:m.parent_id,sid:m.sender_id,body:m.body||'',atts:m.attachments||[],ments:m.mentions||[],at:Date.parse(m.created_at),edited:!!m.edited_at}));
  D.dmByP={};msgs.forEach(m=>{(D.dmByP[m.partner_id]=D.dmByP[m.partner_id]||[]).push({id:m.id,type:'dm',pid:m.partner_id,sid:m.sender_id,body:m.body||'',atts:m.attachments||[],at:Date.parse(m.created_at),read:!!m.read_at,edited:!!m.edited_at})});
  D.reacts={};reacts.forEach(r=>{(D.reacts[r.message_type+':'+r.message_id]=D.reacts[r.message_type+':'+r.message_id]||[]).push({e:r.emoji,u:r.user_id,at:Date.parse(r.created_at)})});
  D.msgs={};D.unreadA={};D.unreadP={};D.partners.forEach(p=>{D.msgs[p.id]=[];D.unreadA[p.id]=0;D.unreadP[p.id]=0});
  msgs.forEach(m=>{const k=m.partner_id;(D.msgs[k]=D.msgs[k]||[]).push({id:m.id,sid:m.sender_id,f:m.sender_id===k?'p':'a',t:m.body,at:mtime(m.created_at),read:!!m.read_at});if(!m.read_at){if(m.sender_id===k)D.unreadA[k]=(D.unreadA[k]||0)+1;else D.unreadP[k]=(D.unreadP[k]||0)+1}});
  // sign file links (kept for 50 minutes)
  const now=Date.now(),need=[];
  D.cm.concat(...Object.values(D.dmByP)).forEach(m=>m.atts.forEach(a=>{const f=D.furl[a.path];if(a.path&&(!f||now-f.t>3e6))need.push(a.path)}));
  for(let i=0;i<need.length;i+=100){try{const {data}=await sb.storage.from('chat-files').createSignedUrls(need.slice(i,i+100),3600);(data||[]).forEach(x=>{if(x&&x.signedUrl&&x.path)D.furl[x.path]={u:x.signedUrl,t:now}})}catch(_){}}
}
const furl=path=>(D.furl[path]||{}).u||'';

/* unread */
const chUnread=id=>{const t=D.creads[id]||0;return D.cm.filter(m=>m.ch===id&&!m.parent&&!isMe(m.sid)&&m.at>t).length};
const dmUnread=pid=>(D.dmByP[pid]||[]).filter(m=>!m.read&&!isMe(m.sid)).length;
const annUnread=()=>role()==='partner'?D.ann.filter(a=>!D.read[a.id]).length:0;
function actItems(){const me=realMe(),h=role()==='admin'?'studio':hOf(P(me)),out=[];
  D.cm.forEach(m=>{if(isMe(m.sid))return;const tk=toks(m.body);
    if(m.ments.includes(me)||tk.includes(h)||(tk.includes('everyone')&&roleOfId(m.sid)==='admin'))out.push({k:'mention',at:m.at,m});
    else if(m.parent){const pa=D.cm.find(x=>x.id===m.parent);if(pa&&isMe(pa.sid))out.push({k:'reply',at:m.at,m})}});
  Object.entries(D.reacts).forEach(([key,L])=>{const [ty,id]=key.split(':');const m=ty==='community'?D.cm.find(x=>x.id===id):(Object.values(D.dmByP).flat().find(x=>x.id===id));if(!m||!isMe(m.sid))return;L.forEach(r=>{if(!isMe(r.u))out.push({k:'react',at:r.at,m,r})})});
  return out.sort((a,b)=>b.at-a.at).slice(0,60)}
const actUnread=()=>{const t=+(lsGet('ts-act-'+realMe())||0);return actItems().filter(x=>x.at>t).length};
function hubUnreadTotal(){const chs=D.channels.reduce((s,c)=>s+chUnread(c.id),0);const dms=role()==='admin'?D.partners.reduce((s,p)=>s+dmUnread(p.id),0):dmUnread(ME);return chs+dms+annUnread()}
const cap=n=>n>99?'99+':String(n);

/* routes like admin-messages~general~t-<id>, partner-messages~dm, admin-messages~dm-<id>, ~ann, ~act */
function hubRoute(r){
  const m=/^(admin|partner)-(messages|community|announcements)(?:~(.+))?$/.exec(r);if(!m)return false;
  if(m[2]==='messages'&&!m[3])return false;
  if(m[2]==='community')S.hub={t:'ch',id:(D.channels[0]||{}).id};
  else if(m[2]==='announcements')S.hub={t:'ann'};
  else{const parts=m[3].split('~'),a=parts[0];S.thread=null;
    if(a==='dm')S.hub={t:'dm',id:ROLE==='admin'?((S.hub&&S.hub.t==='dm')?S.hub.id:(D.partners[0]||{}).id):ME};
    else if(a.startsWith('dm-'))S.hub={t:'dm',id:a.slice(3)};
    else if(a==='ann'||a==='act')S.hub={t:a};
    else{const c=D.allChannels.find(c=>c.slug===a);if(c)S.hub={t:'ch',id:c.id}}
    const th=parts.find(x=>x.startsWith('t-'));if(th)S.thread=th.slice(2)}
  S.hv=S.thread?'thread':'conv';location.replace('#'+m[1]+'-messages');return true}

/* keep the composer, focus and scroll position across re-renders */
const hubKey=()=>S.hub?(S.hub.t==='ch'?'ch:'+S.hub.id:S.hub.t==='dm'?'dm:'+S.hub.id:S.hub.t):'';
function hubSnap(){const ae=document.activeElement,b=$('#hmsgs'),t=$('#hthb');
  return {f:ae&&ae.classList&&ae.classList.contains('hin')?{c:ae.dataset.ctx,s:ae.selectionStart,e:ae.selectionEnd}:null,
    near:b?b.scrollHeight-b.scrollTop-b.clientHeight<90:true,st:b?b.scrollTop:0,tnear:t?t.scrollHeight-t.scrollTop-t.clientHeight<90:true,tst:t?t.scrollTop:0,key:S._hk,th:S._th}}
function hubRestore(s){const b=$('#hmsgs'),t=$('#hthb');
  if(b)b.scrollTop=(s.key!==hubKey()||s.near||S._stick)?b.scrollHeight:s.st;
  if(t)t.scrollTop=(s.th!==S.thread||s.tnear||S._stick)?t.scrollHeight:s.tst;
  S._hk=hubKey();S._th=S.thread;S._stick=false;
  document.querySelectorAll('.hin').forEach(grow);
  if(s.f){const n=document.querySelector(`.hin[data-ctx="${s.f.c}"]`);if(n){n.focus();try{n.setSelectionRange(s.f.s,s.f.e)}catch(_){}}}
  showTyping()}
const grow=ta=>{ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,180)+'px'};

/* text formatting: links, `code`, **bold**, _italic_, @mentions; applied to text only, never inside tags */
function fmtMsg(s){
  let x=esc(s).replace(/(https?:\/\/[^\s<]+[^\s<.,;:!?)\]'"])/g,u=>`<a href="${u}" target="_blank" rel="noopener noreferrer">${u}</a>`);
  x=x.split(/(<[^>]+>)/).map((seg,i)=>i%2?seg:seg.replace(/`([^`\n]+)`/g,'<code>$1</code>').replace(/\*\*([^*\n]+)\*\*/g,'<b>$1</b>').replace(/(^|[\s(])_([^_\n]+)_(?=$|[\s).,!?])/g,'$1<i>$2</i>')
    .replace(/@([A-Za-z]+)/g,(m,hd)=>{const l=hd.toLowerCase(),ok=l==='studio'||l==='everyone'||D.dir.some(p=>hOf(p)===l);return ok?`<span class="men ${l===vh()||l==='everyone'?'me':''}">@${hd}</span>`:m})).join('');
  return x.replace(/\n/g,'<br>')}

function hav(sid,small){const nm=nameOfId(sid),u=D.avById[sid];return `<span class="hava ${small?'sm':''}">${u?`<span class="av"><img src="${esc(u)}" alt=""></span>`:av(nm,pIdx(sid))}${D.online.has(sid)?'<i class="ondot" title="Online"></i>':''}</span>`}

function attsHtml(atts){if(!atts||!atts.length)return'';
  const imgs=atts.filter(a=>/^image\//.test(a.type)),aud=atts.filter(a=>/^audio\//.test(a.type)||a.voice),rest=atts.filter(a=>!imgs.includes(a)&&!aud.includes(a));
  return `<div class="hatts">${imgs.length?`<div class="himgs">${imgs.map(a=>{const u=furl(a.path);return u?`<a class="himg" href="${esc(u)}" target="_blank" rel="noopener"><img src="${esc(u)}" alt="${esc(a.name)}" loading="lazy"></a>`:`<span class="himg ph">${ic('file',18)}</span>`}).join('')}</div>`:''}
  ${aud.map(a=>{const u=furl(a.path);return `<div class="hvoice"><span class="hvi">${ic('mic',15)}</span>${u?`<audio controls preload="metadata" src="${esc(u)}"></audio>`:'<span class="muted small">Loading…</span>'}<span class="hvd">${a.duration?fmtDur(a.duration):''}</span></div>`}).join('')}
  ${rest.map(a=>{const u=furl(a.path),ext=(a.name.split('.').pop()||'file').toUpperCase().slice(0,5);return `<a class="hfile" ${u?`href="${esc(u)}&download=${encodeURIComponent(a.name)}"`:''} target="_blank" rel="noopener"><span class="hfi">${ext}</span><span class="hfn"><b>${esc(a.name)}</b><small>${fmtSize(a.size||0)}</small></span>${ic('dl',16)}</a>`}).join('')}</div>`}

function reactsHtml(key){const L=D.reacts[key]||[];if(!L.length)return'';const g={};L.forEach(r=>{(g[r.e]=g[r.e]||[]).push(r.u)});
  return `<div class="hreacts">${Object.entries(g).map(([e,us])=>`<button type="button" class="hre ${us.includes(realMe())?'me':''}" data-react="${key}|${e}" title="${esc(us.map(nameOfId).join(', '))}" aria-label="${e} ${us.length}, react">${e}<span>${us.length}</span></button>`).join('')}<button type="button" class="hre add" data-emopick="react|${key}" aria-label="Add a reaction">${ic('smile',15)}<span>+</span></button></div>`}

function msgHtml(m,ctx,compact){
  const key=m.type+':'+m.id,mine=isMe(m.sid),adm=role()==='admin',isAdm=roleOfId(m.sid)==='admin';
  const tk=toks(m.body),men=!mine&&((m.ments||[]).includes(realMe())||tk.includes(vh())||tk.includes('everyone'));
  const replies=ctx==='ch'?D.cm.filter(x=>x.parent===m.id):[];
  const ed=S.editing===key;
  const acts=`<div class="hacts" role="toolbar" aria-label="Message actions">${HUB_QUICK.slice(0,3).map(e=>`<button type="button" data-react="${key}|${e}" aria-label="React ${e}">${e}</button>`).join('')}<button type="button" data-emopick="react|${key}" aria-label="More reactions" title="React">${ic('smile',16)}</button>${ctx==='ch'?`<button type="button" data-thread="${m.id}" aria-label="Reply in thread" title="Reply in thread">${ic('reply',16)}</button>`:''}${mine&&m.body?`<button type="button" data-medit="${key}" aria-label="Edit message" title="Edit">${ic('pencil',15)}</button>`:''}${mine||adm?`<button type="button" data-mdel="${key}" aria-label="Delete message" title="Delete">${ic('trash',15)}</button>`:''}</div>`;
  return `<div class="hmsg ${compact?'cmp':''} ${men?'ment':''} ${ed?'editing':''}" id="m-${m.id}">
  <div class="hl">${compact?`<span class="hts">${hhmm(m.at)}</span>`:hav(m.sid)}</div>
  <div class="hb">${compact?'':`<div class="hh"><b>${esc(nameOfId(m.sid))}</b>${isAdm?tag('Studio','sky'):''}<time datetime="${new Date(m.at).toISOString()}">${hhmm(m.at)}</time>${m.edited?'<span class="hed">edited</span>':''}</div>`}
   ${ed?`<div class="hedit"><textarea class="hin hedt" data-ctx="edit:${key}" rows="2" aria-label="Edit message">${esc(S.draft['edit:'+key]!=null?S.draft['edit:'+key]:m.body)}</textarea><div class="hedit-b"><span class="muted small">Enter to save · Esc to cancel</span><button type="button" class="btn sm line" data-mcancel="1">Cancel</button><button type="button" class="btn sm" data-msave="${key}">Save</button></div></div>`
       :(m.body?`<div class="htx">${fmtMsg(m.body)}${compact&&m.edited?' <span class="hed">edited</span>':''}</div>`:'')}
   ${attsHtml(m.atts)}${reactsHtml(key)}
   ${replies.length?`<button type="button" class="hrep" data-thread="${m.id}"><span class="hrep-av">${[...new Set(replies.map(r=>r.sid))].slice(0,3).map(s=>hav(s,1)).join('')}</span><b>${replies.length} ${replies.length===1?'reply':'replies'}</b><span class="muted">Last reply ${dayLab(replies[replies.length-1].at).toLowerCase()==='today'?'today at '+hhmm(replies[replies.length-1].at):dayLab(replies[replies.length-1].at)}</span></button>`:''}
  </div>${ed?'':acts}</div>`}

function msgList(list,ctx){let out='',lastDay='',prev=null;
  list.forEach(m=>{const d=new Date(m.at).toDateString();if(d!==lastDay){out+=`<div class="hday"><span>${dayLab(m.at)}</span></div>`;lastDay=d;prev=null}
    const compact=prev&&prev.sid===m.sid&&m.at-prev.at<5*60e3&&!(ctx==='ch'&&D.cm.some(x=>x.parent===prev.id));
    out+=msgHtml(m,ctx,compact);prev=m});return out}

function composer(ctx,ph,can,why){
  if(!can)return `<div class="hcmp-off">${ic('lock',15)} ${why}</div>`;
  const att=S.att[ctx]||[],rec=S.rec&&S.rec.ctx===ctx;
  return `<form class="hcmp ${rec?'rec':''}" data-ctx="${ctx}" novalidate>
  <div class="sug hsug" role="listbox"></div>
  ${att.length?`<div class="hchips">${att.map((a,i)=>a.voice?`<span class="hchip v">${ic('mic',14)}<audio controls src="${a.url}"></audio><b>${fmtDur(a.duration)}</b><button type="button" data-attx="${ctx}|${i}" aria-label="Remove voice note">×</button></span>`
      :`<span class="hchip">${/^image\//.test(a.type)?`<img src="${a.url}" alt="">`:`<span class="hfi">${esc((a.name.split('.').pop()||'').toUpperCase().slice(0,4))}</span>`}<span class="nm"><b>${esc(a.name)}</b><small>${fmtSize(a.size)}</small></span><button type="button" data-attx="${ctx}|${i}" aria-label="Remove ${esc(a.name)}">×</button></span>`).join('')}</div>`:''}
  ${rec?`<div class="hrec"><span class="rdot"></span><b>Recording</b><span id="rectime">0:00</span><span class="grow"></span><button type="button" class="btn sm line" data-act="reccancel">Cancel</button><button type="button" class="btn sm" data-act="recstop">Done</button></div>`
       :`<textarea class="hin" data-ctx="${ctx}" rows="1" placeholder="${esc(ph)}" aria-label="${esc(ph)}" maxlength="4000">${esc(S.draft[ctx]||'')}</textarea>`}
  <div class="hbar">
   <button type="button" class="hib" data-emopick="compose|${ctx}" aria-label="Add an emoji" title="Emoji">${ic('smile',18)}</button>
   <label class="hib" title="Attach files" aria-label="Attach files">${ic('clip',18)}<input type="file" class="vh" data-attin="${ctx}" multiple></label>
   <button type="button" class="hib ${rec?'on':''}" data-act="recstart" data-id="${ctx}" aria-label="Record a voice note" title="Voice note">${ic('mic',18)}</button>
   <button type="button" class="hib" data-atins="${ctx}" aria-label="Mention someone" title="Mention">${ic('at',18)}</button>
   <span class="hhint">**bold** &nbsp;_italic_ &nbsp;\`code\` &nbsp;·&nbsp; Shift+Enter for a new line</span>
   <button type="submit" class="hsend" aria-label="Send">${ic('send',16)}</button>
  </div></form>`}

function hubSide(){const adm=role()==='admin',k=hubKey(),au=actUnread(),an=annUnread();
  const it=(key,inner,n,extra)=>`<button type="button" class="hsi ${k===key?'on':''} ${n?'un':''} ${extra||''}" data-hub="${key}">${inner}${n?`<span class="hcnt">${cap(n)}</span>`:''}</button>`;
  const dms=adm?D.partners.filter(p=>p.st!=='Removed'||(D.dmByP[p.id]||[]).length).map(p=>it('dm:'+p.id,`${hav(p.id,1)}<span class="nm">${esc(p.name)}</span>`,dmUnread(p.id),p.st!=='Active'?'dim':'')).join('')||'<div class="hs-empty">No partners yet.</div>'
             :it('dm:'+ME,`<span class="hava sm"><span class="av" style="background:var(--dark);color:var(--sand)">TS</span></span><span class="nm">Twelfth Space studio</span>`,dmUnread(ME));
  return `<div class="hs-top">${it('act',`<span class="hsi-i">${ic('bell',16)}</span><span class="nm">Activity</span>`,au)}${it('ann',`<span class="hsi-i">${ic('megaphone',16)}</span><span class="nm">Announcements</span>`,an)}</div>
  <div class="hs-h"><span>Channels</span>${adm?`<button type="button" data-act="chnew" aria-label="Add a channel" title="Add a channel">${ic('plus',15)}</button>`:''}</div>
  ${D.channels.map(c=>it('ch:'+c.id,`<span class="hsi-i hash">#</span><span class="nm">${esc(c.name)}</span>${c.admin_only?`<span class="hlk" title="Only the studio starts posts">${ic('lock',12)}</span>`:''}`,chUnread(c.id))).join('')}
  <div class="hs-h"><span>Direct messages</span></div>${dms}`}

function hubHead(title,sub,right){return `<div class="hhd"><button type="button" class="hback" data-hback="list" aria-label="Back to conversations">${ic('back',18)}</button><div class="hhd-t"><h2>${title}</h2>${sub?`<p>${sub}</p>`:''}</div><span class="grow"></span>${right||''}</div>`}

function hubMain(){const adm=role()==='admin',t=S.hub.t;
  const online=[...D.online].filter(id=>D.dir.some(p=>p.id===id)).length;
  if(t==='act'){const L=actItems();
    return hubHead('Activity','Mentions, replies to your posts and reactions')+`<div class="hscroll"><div class="hact">${L.map(x=>{const m=x.m,c=m.type==='community'?D.allChannels.find(c=>c.id===m.ch):null,where=c?'#'+c.name:'Direct message',key=m.type==='community'?'ch:'+m.ch+'|'+(m.parent||''):'dm:'+m.pid+'|';
      const what=x.k==='mention'?`${ic('at',14)} Mention in ${esc(where)}`:x.k==='reply'?`${ic('reply',14)} Reply in ${esc(where)}`:`${x.r.e} reaction in ${esc(where)}`;
      const who=x.k==='react'?x.r.u:m.sid;
      return `<button type="button" class="hai" data-goto="${key}|${m.id}"><span class="hai-w">${what}<time>${dayLab(x.at)} ${hhmm(x.at)}</time></span><span class="hai-b">${hav(who,1)}<span><b>${esc(nameOfId(who))}</b>${x.k==='react'?` reacted ${x.r.e} to your message`:''}<span class="hai-t">${esc((m.body||(m.atts.length?'Shared a file':'')).slice(0,180))}</span></span></span></button>`}).join('')||`<div class="hwel"><span class="hwel-i">${ic('bell',22)}</span><h3>Nothing here yet</h3><p>When someone mentions you, replies to your post or reacts to your message, it shows up here.</p></div>`}</div></div>`}
  if(t==='ann'){const body=(PG[(adm?'admin':'partner')+'-announcements'])();return hubHead('Announcements',adm?'Posts every partner sees. Replies come to you as direct messages.':'News from the studio')+`<div class="hscroll hann">${body}</div>`}
  if(t==='ch'){const c=D.allChannels.find(c=>c.id===S.hub.id);if(!c)return hubHead('Channel not found','')+'<div class="hscroll"></div>';
    const list=D.cm.filter(m=>m.ch===c.id&&!m.parent),can=!c.archived&&(!c.admin_only||adm);
    const right=`<span class="hmeta" title="Members">${ic('users',15)} ${D.dir.length}</span><span class="hmeta" title="Online now"><i class="ondot s"></i> ${online}</span>${adm?`<button type="button" class="ibtn" data-act="chedit" data-id="${c.id}" aria-label="Channel settings" title="Channel settings">${ic('gear',16)}</button>`:''}`;
    return hubHead(`# ${esc(c.name)}${c.admin_only?` <span class="hlk">${ic('lock',13)}</span>`:''}`,esc(c.description||''),right)+
     `<div class="hscroll" id="hmsgs"><div class="hwel"><span class="hwel-i hash">#</span><h3>Welcome to #${esc(c.name)}</h3><p>${esc(c.description||'')}${c.admin_only?' Only the studio starts posts here; everyone can reply in threads.':''} Be kind, and please don't share commission rates, client contracts or account details.</p></div>${msgList(list,'ch')}</div>
     <div class="htyping" data-ctx="ch:${c.id}" aria-live="polite"></div>${composer('ch:'+c.id,'Message #'+c.name,can,c.archived?'This channel is archived.':'Only the studio can start posts here. You can reply in threads.')}`}
  if(t==='dm'){const pid=S.hub.id,p=P(pid),list=D.dmByP[pid]||[],title=adm?esc(p.name):'Twelfth Space studio';
    const sub=adm?(p.st==='Active'?'Growth Partner':p.st+' partner')+(D.online.has(pid)?' · online now':''):'Private to you and the studio';
    const right=adm?`<a class="btn sm line" href="#admin-partner-${pid}">View partner</a>`:'';
    const can=adm?p.st!=='Removed':true;
    return hubHead(title,sub,right)+`<div class="hscroll" id="hmsgs"><div class="hwel">${adm?hav(pid):`<span class="hwel-i">${ic('chat',22)}</span>`}<h3>${adm?'Your conversation with '+esc(p.name):'Your conversation with the studio'}</h3><p>Only ${adm?esc(p.name.split(' ')[0])+' and the studio':'you and the studio'} can see these messages.</p></div>${msgList(list,'dm')}</div>
     <div class="htyping" data-ctx="dm:${pid}"></div>${composer('dm:'+pid,adm?'Message '+p.name.split(' ')[0]:'Message the studio',can,'This partner has left. Messages are kept for your records.')}`}
  return''}

function hubThread(){const pm=D.cm.find(m=>m.id===S.thread);if(!pm)return'';const c=D.allChannels.find(c=>c.id===pm.ch)||{name:''},reps=D.cm.filter(m=>m.parent===pm.id);
  return `<div class="hhd"><button type="button" class="hback" data-hback="conv" aria-label="Back to channel">${ic('back',18)}</button><div class="hhd-t"><h2>Thread</h2><p># ${esc(c.name)}</p></div><span class="grow"></span><button type="button" class="ibtn" data-act="thclose" aria-label="Close thread">${ic('x',16)}</button></div>
  <div class="hscroll" id="hthb">${msgHtml(pm,'thp',false)}<div class="hday thr"><span>${reps.length} ${reps.length===1?'reply':'replies'}</span></div>${msgList(reps,'th')}</div>
  <div class="htyping" data-ctx="th:${pm.id}"></div>${composer('th:'+pm.id,'Reply in thread',!c.archived,'This channel is archived.')}`}

function hubPage(){
  if(!S.hub||(S.hub.t==='ch'&&!D.channels.some(c=>c.id===S.hub.id)&&!D.allChannels.some(c=>c.id===S.hub.id)))S.hub=D.channels[0]?{t:'ch',id:D.channels[0].id}:{t:'act'};
  if(S.hub.t==='dm'&&role()==='partner')S.hub.id=ME;
  if(S.thread&&!D.cm.some(m=>m.id===S.thread))S.thread=null;
  return `<div class="hub v-${S.hv||'list'} ${S.thread?'th':''}"><aside class="hside" aria-label="Conversations">${hubSide()}</aside><section class="hmain" aria-label="Conversation">${hubMain()}</section>${S.thread?`<aside class="hthr" aria-label="Thread">${hubThread()}</aside>`:''}</div>`}
PG['admin-messages']=hubPage;PG['partner-messages']=hubPage;PG['admin-community']=hubPage;PG['partner-community']=hubPage;

function hubMarkRead(){if(!S.hub)return;const k=S.hub;
  if(k.t==='ch'){const id=k.id;if(chUnread(id)>0||!D.creads[id]){D.creads[id]=Date.now();sb.from('channel_reads').upsert({channel_id:id,last_read_at:nowIso()},{onConflict:'user_id,channel_id'}).then(()=>{})}}
  else if(k.t==='dm'){const un=(D.dmByP[k.id]||[]).filter(m=>!m.read&&!isMe(m.sid));if(un.length){un.forEach(m=>m.read=true);sb.from('messages').update({read_at:nowIso()}).in('id',un.map(m=>m.id)).then(()=>{})}}
  else if(k.t==='act')lsSet('ts-act-'+realMe(),String(Date.now()))}

/* ---------- sending ---------- */
function mentionIds(body){const tk=toks(body),ids=new Set();
  D.dir.forEach(p=>{if(tk.includes(hOf(p)))ids.add(p.id)});
  if(tk.includes('studio'))D.dir.filter(p=>p.role==='admin').forEach(p=>ids.add(p.id));
  if(tk.includes('everyone')&&role()==='admin')D.dir.forEach(p=>ids.add(p.id));
  ids.delete(realMe());return [...ids]}
function addFiles(ctx,files){if(S.viewAs){toast('Read-only while viewing as a partner.');return}
  const L=S.att[ctx]=S.att[ctx]||[];
  for(const f of files){if(L.length>=6){toast('You can attach up to 6 files to one message.');break}
    const ty=baseType(f.type);if(!HUB_TYPES.includes(ty)){toast(`${f.name}: that kind of file is not supported.`);continue}
    if(f.size>HUB_MAX){toast(`${f.name} is larger than 25 MB.`);continue}
    L.push({file:f,name:f.name||'file',size:f.size,type:ty,url:/^image\//.test(ty)?URL.createObjectURL(f):''})}
  render()}
async function hubSend(ctx){
  if(S.viewAs){toast('Read-only while viewing as a partner.');return}
  if(S.sending)return;
  const [kind,id]=ctx.split(':'),ta=document.querySelector(`.hin[data-ctx="${ctx}"]`),body=((ta?ta.value:S.draft[ctx])||'').trim(),att=S.att[ctx]||[];
  if(!body&&!att.length)return;
  const me=realMe();let table,row,prefix;
  if(kind==='ch'){table='community_messages';prefix='community/'+me+'/';row={channel_id:id,body,mentions:mentionIds(body)}}
  else if(kind==='th'){const pm=D.cm.find(m=>m.id===id);if(!pm)return;table='community_messages';prefix='community/'+me+'/';row={channel_id:pm.ch,parent_id:id,body,mentions:mentionIds(body)}}
  else{table='messages';prefix='dm/'+id+'/'+me+'/';row={partner_id:id,body}}
  S.sending=ctx;const btn=document.querySelector(`.hcmp[data-ctx="${ctx}"] .hsend`);if(btn)btn.disabled=true;
  const up=[];
  try{for(const a of att){const safe=a.name.replace(/[^A-Za-z0-9._-]+/g,'-').slice(-80)||'file',path=prefix+(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random().toString(36).slice(2))+'-'+safe;
      const {error}=await sb.storage.from('chat-files').upload(path,a.file,{contentType:a.type,upsert:false});if(error)throw error;
      up.push(Object.assign({path,name:a.name,size:a.size,type:a.type},a.voice?{voice:true,duration:a.duration}:{}))}
    row.attachments=up;
    await q(sb.from(table).insert(row));
    S.draft[ctx]='';(S.att[ctx]||[]).forEach(a=>a.url&&URL.revokeObjectURL(a.url));S.att[ctx]=[];S._stick=true;
    await loadChat();
  }catch(e){toast(nice(e));if(up.length)sb.storage.from('chat-files').remove(up.map(x=>x.path)).then(()=>{})}
  S.sending=null;render();const n=document.querySelector(`.hin[data-ctx="${ctx}"]`);if(n)n.focus()}

async function toggleReact(key,emoji){if(S.viewAs){toast('Read-only while viewing as a partner.');return}
  const [ty,id]=key.split(':'),me=realMe(),L=D.reacts[key]=D.reacts[key]||[],ex=L.find(r=>r.u===me&&r.e===emoji);
  if(ex)L.splice(L.indexOf(ex),1);else L.push({e:emoji,u:me,at:Date.now()});render();
  try{if(ex)await q(sb.from('message_reactions').delete().match({message_type:ty,message_id:id,user_id:me,emoji}));
      else await q(sb.from('message_reactions').insert({message_type:ty,message_id:id,emoji}))}catch(e){toast(nice(e));await loadChat();render()}}
const findMsg=key=>{const [ty,id]=key.split(':');return ty==='community'?D.cm.find(m=>m.id===id):Object.values(D.dmByP).flat().find(m=>m.id===id)};
async function saveEdit(key){const m=findMsg(key);if(!m)return;const n=document.querySelector(`.hin[data-ctx="edit:${key}"]`),v=(n?n.value:'').trim();
  if(!v&&!m.atts.length){toast('A message needs some text. Delete it instead.');return}
  if(v===m.body){S.editing=null;render();return}
  try{await q(sb.from(m.type==='community'?'community_messages':'messages').update({body:v}).eq('id',m.id));S.editing=null;delete S.draft['edit:'+key];await loadChat()}catch(e){toast(nice(e))}render()}
function delMsg(key){const m=findMsg(key);if(!m)return;const reps=m.type==='community'?D.cm.filter(x=>x.parent===m.id).length:0;
  modal('Delete message',reps?`This also deletes its ${reps} ${reps===1?'reply':'replies'}. It can't be undone.`:'It can\'t be undone.','','Delete',async()=>{
    try{await q(sb.from(m.type==='community'?'community_messages':'messages').delete().eq('id',m.id))}catch(e){return nice(e)}
    const paths=m.atts.map(a=>a.path).filter(Boolean);if(paths.length)sb.storage.from('chat-files').remove(paths).then(()=>{});
    if(S.thread===m.id)S.thread=null;await loadChat();return''},'pink')}

/* ---------- voice notes ---------- */
let REC_T=null;
ACT.recstart=async function(ctx){if(S.viewAs){toast('Read-only while viewing as a partner.');return}
  if(S.rec){toast('Finish the voice note you are recording first.');return}
  if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia||!window.MediaRecorder){toast('This browser cannot record voice notes.');return}
  let stream;try{stream=await navigator.mediaDevices.getUserMedia({audio:true})}catch(_){toast('Microphone access was blocked. Allow it in your browser settings to record voice notes.');return}
  const mt=['audio/webm;codecs=opus','audio/webm','audio/mp4','audio/ogg'].find(t=>MediaRecorder.isTypeSupported&&MediaRecorder.isTypeSupported(t))||'';
  const rec=new MediaRecorder(stream,mt?{mimeType:mt}:undefined),chunks=[];
  rec.ondataavailable=e=>{if(e.data&&e.data.size)chunks.push(e.data)};
  rec.onstop=()=>{stream.getTracks().forEach(t=>t.stop());clearInterval(REC_T);const r=S.rec;S.rec=null;
    if(r&&!r.cancel&&chunks.length){const ty=baseType(rec.mimeType||mt||'audio/webm'),blob=new Blob(chunks,{type:ty}),dur=(Date.now()-r.t0)/1000;
      if(dur>=1)(S.att[r.ctx]=S.att[r.ctx]||[]).push({file:blob,name:'Voice note '+fmtDur(dur)+'.'+(ty.includes('mp4')?'m4a':ty.split('/')[1]),size:blob.size,type:ty,duration:Math.round(dur),voice:true,url:URL.createObjectURL(blob)})}
    render()};
  S.rec={ctx,rec,t0:Date.now(),cancel:false};rec.start(250);render();
  REC_T=setInterval(()=>{if(!S.rec)return;const s=(Date.now()-S.rec.t0)/1000,el=$('#rectime');if(el)el.textContent=fmtDur(s);if(s>=300){toast('Voice notes can be up to 5 minutes.');S.rec.rec.stop()}},250)};
ACT.recstop=function(){if(S.rec)S.rec.rec.stop()};
ACT.reccancel=function(){if(S.rec){S.rec.cancel=true;S.rec.rec.stop()}};
ACT.thclose=function(){S.thread=null;S.hv='conv';render()};

/* ---------- channels (admin) ---------- */
const slugOf=s=>String(s).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,30);
ACT.chnew=function(){modal('Add a channel','Channels are open to every active partner.',field('Name','name',{ph:'e.g. leads'})+field('What it is for','desc',{ph:'Share new leads and ask for introductions'})+field('Who can start posts','who',{opts:[['all','Everyone'],['studio','Only the studio (everyone can reply)']]}),'Add channel',async f=>{
  const sl=slugOf(f.name);if(sl.length<2)return'Enter a name of at least 2 letters or numbers.';if(D.allChannels.some(c=>c.slug===sl))return'There is already a channel called #'+sl+'.';
  try{const r=await q(sb.from('channels').insert({slug:sl,name:sl,description:f.desc.trim()||null,admin_only:f.who==='studio',position:D.allChannels.length}).select('id').single());await loadChat();S.hub={t:'ch',id:r.id};S.hv='conv';toast('#'+sl+' added')}catch(e){return nice(e)}return''})};
ACT.chedit=function(id){const c=D.allChannels.find(c=>c.id===id);if(!c)return;modal('# '+esc(c.name),'Channel settings',field('What it is for','desc',{val:c.description||''})+field('Who can start posts','who',{opts:[['all','Everyone'],['studio','Only the studio (everyone can reply)']],val:c.admin_only?'studio':'all'})+field('Status','st',{opts:[['open','Open'],['archived','Archived (hidden, history kept)']],val:c.archived?'archived':'open'}),'Save',async f=>{
  try{await q(sb.from('channels').update({description:f.desc.trim()||null,admin_only:f.who==='studio',archived:f.st==='archived'}).eq('id',id));await loadChat();if(f.st==='archived'&&S.hub&&S.hub.id===id)S.hub=null;toast('Channel saved')}catch(e){return nice(e)}return''})};

/* ---------- emoji picker ---------- */
let EMO=null;
function closeEmo(){if(EMO){EMO.el.remove();EMO=null}}
function openEmo(btn,mode,key){closeEmo();const d=document.createElement('div');d.className='emopop';d.setAttribute('role','dialog');d.setAttribute('aria-label','Choose an emoji');
  d.innerHTML=`<div class="emo-q">${HUB_QUICK.map(e=>`<button type="button" data-emoji="${e}" aria-label="${e}">${e}</button>`).join('')}</div>`+Object.entries(HUB_EMO).map(([k,v])=>`<div class="emo-h">${k}</div><div class="emo-g">${v.split(' ').map(e=>`<button type="button" data-emoji="${e}" aria-label="${e}">${e}</button>`).join('')}</div>`).join('');
  document.body.appendChild(d);const r=btn.getBoundingClientRect(),w=d.offsetWidth,hh=d.offsetHeight;
  let top=r.top-hh-8;if(top<8)top=Math.min(innerHeight-hh-8,r.bottom+8);let left=Math.min(Math.max(8,r.right-w),innerWidth-w-8);
  d.style.top=Math.max(8,top)+'px';d.style.left=left+'px';EMO={el:d,mode,key};const f=d.querySelector('button');f&&f.focus()}
function insertAt(ctx,text){const n=document.querySelector(`.hin[data-ctx="${ctx}"]`);if(!n){S.draft[ctx]=(S.draft[ctx]||'')+text;render();return}
  const s=n.selectionStart==null?n.value.length:n.selectionStart,e=n.selectionEnd==null?s:n.selectionEnd;n.value=n.value.slice(0,s)+text+n.value.slice(e);S.draft[ctx]=n.value;n.focus();n.setSelectionRange(s+text.length,s+text.length);grow(n)}

/* ---------- live updates, online and typing ---------- */
let CHL=null,PRES=null,TYP=null,lastTyp=0;
function startChatLive(){if(CHL||!ME)return;let t=null;
  const go=()=>{clearTimeout(t);t=setTimeout(async()=>{try{await loadChat()}catch(_){return}
    const ae=document.activeElement,busy=$('#mbg').classList.contains('open')||(ae&&/INPUT|TEXTAREA|SELECT/.test(ae.tagName)&&!ae.classList.contains('hin'))||S.rec;
    if(!busy)render()},350)};
  CHL=sb.channel('chat-db').on('postgres_changes',{event:'*',schema:'public',table:'community_messages'},go).on('postgres_changes',{event:'*',schema:'public',table:'messages'},go).on('postgres_changes',{event:'*',schema:'public',table:'message_reactions'},go).subscribe();
  PRES=sb.channel('online',{config:{presence:{key:realMe()}}});
  PRES.on('presence',{event:'sync'},()=>{D.online=new Set(Object.keys(PRES.presenceState()));if(onHub()&&!S.rec&&!$('#mbg').classList.contains('open'))render()}).subscribe(st=>{if(st==='SUBSCRIBED')PRES.track({at:Date.now()})});
  TYP=sb.channel('typing');TYP.on('broadcast',{event:'t'},({payload:p})=>{if(!p||p.u===realMe()||String(p.c).startsWith('dm:'))return;(S.typing[p.c]=S.typing[p.c]||{})[p.u]={n:p.n,until:Date.now()+4500};showTyping()}).subscribe()}
function stopChatLive(){[CHL,PRES,TYP].forEach(c=>{if(c)try{sb.removeChannel(c)}catch(_){}});CHL=PRES=TYP=null;D.online=new Set()}
function sendTyping(ctx){if(!TYP||S.viewAs||ctx.startsWith('dm:')||ctx.startsWith('edit:')||Date.now()-lastTyp<2500)return;lastTyp=Date.now();try{TYP.send({type:'broadcast',event:'t',payload:{c:ctx,u:realMe(),n:((MEP&&MEP.full_name)||'Someone').split(' ')[0]}})}catch(_){}}
function showTyping(){const now=Date.now();document.querySelectorAll('.htyping').forEach(el=>{const m=S.typing[el.dataset.ctx]||{},ns=Object.values(m).filter(x=>x.until>now).map(x=>x.n);
  el.innerHTML=ns.length?`<span class="tdots"><i></i><i></i><i></i></span>${esc(ns.length>2?ns.length+' people are':ns.join(' and ')+(ns.length>1?' are':' is'))} typing…`:''})}
setInterval(showTyping,1500);

/* ---------- events ---------- */
document.addEventListener('click',e=>{const t=e.target;
  if(EMO&&!t.closest('.emopop')&&!t.closest('[data-emopick]'))closeEmo();
  const em=t.closest('[data-emoji]');if(em&&EMO){const {mode,key}=EMO;closeEmo();if(mode==='react')toggleReact(key,em.dataset.emoji);else insertAt(key,em.dataset.emoji);return}
  const ep=t.closest('[data-emopick]');if(ep){e.preventDefault();const [mode,key]=ep.dataset.emopick.split('|');if(EMO&&EMO.key===key&&EMO.mode===mode){closeEmo();return}openEmo(ep,mode,key);return}
  const hb=t.closest('[data-hub]');if(hb){const [ty,id]=hb.dataset.hub.split(':');S.hub=id?{t:ty,id}:{t:ty};S.thread=null;S.editing=null;S.hv='conv';render();return}
  const go=t.closest('[data-goto]');if(go){const [k,par,mid]=go.dataset.goto.split('|'),[ty,id]=k.split(':');
    S.hub={t:ty,id};S.thread=par||null;S.hv=S.thread?'thread':'conv';render();setTimeout(()=>{const n=document.getElementById('m-'+mid);if(n){n.scrollIntoView({block:'center'});n.classList.add('flash')}},60);return}
  const rc=t.closest('[data-react]');if(rc){const s=rc.dataset.react,i=s.lastIndexOf('|');toggleReact(s.slice(0,i),s.slice(i+1));return}
  const th=t.closest('[data-thread]');if(th){S.thread=th.dataset.thread;S.hv='thread';S._stick=true;render();const n=document.querySelector(`.hin[data-ctx="th:${S.thread}"]`);if(n)n.focus();return}
  const ax=t.closest('[data-attx]');if(ax){const [ctx,i]=ax.dataset.attx.split('|');const L=S.att[ctx]||[];const a=L.splice(+i,1)[0];if(a&&a.url)URL.revokeObjectURL(a.url);render();return}
  const me_=t.closest('[data-medit]');if(me_){if(S.viewAs){toast('Read-only while viewing as a partner.');return}S.editing=me_.dataset.medit;render();const n=document.querySelector(`.hin[data-ctx="edit:${S.editing}"]`);if(n){n.focus();n.setSelectionRange(n.value.length,n.value.length)}return}
  if(t.closest('[data-mcancel]')){delete S.draft['edit:'+S.editing];S.editing=null;render();return}
  const ms=t.closest('[data-msave]');if(ms){saveEdit(ms.dataset.msave);return}
  const md=t.closest('[data-mdel]');if(md){if(S.viewAs){toast('Read-only while viewing as a partner.');return}delMsg(md.dataset.mdel);return}
  const bk=t.closest('[data-hback]');if(bk){if(bk.dataset.hback==='conv'){S.thread=null;S.hv='conv'}else S.hv='list';render();return}
  const ins=t.closest('[data-atins]');if(ins){insertAt(ins.dataset.atins,'@');const n=document.querySelector(`.hin[data-ctx="${ins.dataset.atins}"]`);if(n)n.dispatchEvent(new Event('input',{bubbles:true}));return}
  const sg=t.closest('[data-hsug]');if(sg){const f=sg.closest('.hcmp'),n=f&&f.querySelector('.hin');if(n){const pos=n.selectionStart==null?n.value.length:n.selectionStart,bf=n.value.slice(0,pos).replace(/@([A-Za-z]*)$/,'@'+sg.dataset.hsug+' ');n.value=bf+n.value.slice(pos);S.draft[n.dataset.ctx]=n.value;f.querySelector('.hsug').classList.remove('open');n.focus();n.setSelectionRange(bf.length,bf.length)}return}
});
document.addEventListener('input',e=>{const n=e.target;if(!n.classList||!n.classList.contains('hin'))return;S.draft[n.dataset.ctx]=n.value;grow(n);sendTyping(n.dataset.ctx);
  const box=n.closest('.hcmp')&&n.closest('.hcmp').querySelector('.hsug');if(!box)return;const v=n.value.slice(0,n.selectionStart),m=v.match(/(?:^|\s)@([A-Za-z]*)$/);if(!m){box.classList.remove('open');return}
  const qq=m[1].toLowerCase(),o=D.dir.filter(p=>p.id!==realMe()).map(p=>({h:p.name.split(' ')[0],n:p.name,id:p.id})).concat([{h:'studio',n:'Studio team'}].concat(role()==='admin'?[{h:'everyone',n:'Everyone in the channel'}]:[])).filter(x=>x.h.toLowerCase().startsWith(qq)).slice(0,8);
  box.innerHTML=o.map(x=>`<button type="button" data-hsug="${esc(x.h)}">${x.id?hav(x.id,1):`<span class="hava sm"><span class="av">@</span></span>`}<span><b>@${esc(x.h)}</b><small class="muted"> ${esc(x.n)}</small></span></button>`).join('');box.classList.toggle('open',o.length>0)});
document.addEventListener('keydown',e=>{const n=e.target;
  if(e.key==='Escape'&&EMO){closeEmo();return}
  if(!n.classList||!n.classList.contains('hin'))return;const ctx=n.dataset.ctx;
  if(ctx.startsWith('edit:')){if(e.key==='Escape'){e.preventDefault();delete S.draft[ctx];S.editing=null;render()}else if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();saveEdit(ctx.slice(5))}return}
  const box=n.closest('.hcmp')&&n.closest('.hcmp').querySelector('.hsug.open');
  if(box&&e.key==='Enter'){const f=box.querySelector('[data-hsug]');if(f){e.preventDefault();f.click();return}}
  if(box&&e.key==='Escape'){box.classList.remove('open');return}
  if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();hubSend(ctx)}});
document.addEventListener('submit',e=>{const f=e.target.closest&&e.target.closest('.hcmp');if(!f)return;e.preventDefault();hubSend(f.dataset.ctx)});
document.addEventListener('change',e=>{const n=e.target.closest&&e.target.closest('[data-attin]');if(!n)return;addFiles(n.dataset.attin,[...n.files]);n.value=''});
document.addEventListener('paste',e=>{const n=e.target;if(!n.classList||!n.classList.contains('hin')||n.dataset.ctx.startsWith('edit:'))return;const fs=[...(e.clipboardData&&e.clipboardData.files||[])];if(fs.length){e.preventDefault();addFiles(n.dataset.ctx,fs)}});
document.addEventListener('dragover',e=>{const z=e.target.closest&&e.target.closest('.hmain,.hthr');if(z&&z.querySelector('.hcmp')&&[...(e.dataTransfer.types||[])].includes('Files')){e.preventDefault();z.classList.add('drop')}});
document.addEventListener('dragleave',e=>{const z=e.target.closest&&e.target.closest('.hmain,.hthr');if(z&&!z.contains(e.relatedTarget))z.classList.remove('drop')});
document.addEventListener('drop',e=>{const z=e.target.closest&&e.target.closest('.hmain,.hthr');if(!z)return;z.classList.remove('drop');const f=z.querySelector('.hcmp');if(!f||!e.dataTransfer.files.length)return;e.preventDefault();addFiles(f.dataset.ctx,[...e.dataTransfer.files])});
/* ================= end messaging hub ================= */''')

rep("new Set(['exitview','signout',", "new Set(['exitview','signout','thclose',")

# ---------- CSS ----------
rep('.pop .pall{display:block;', '''/* ---------- messaging hub ---------- */
.hub{display:grid;grid-template-columns:270px minmax(0,1fr);height:calc(100dvh - 156px);min-height:560px;background:var(--card);border:1px solid var(--line);border-radius:24px;overflow:hidden}
.hub.th{grid-template-columns:270px minmax(0,1fr) minmax(300px,380px)}
.hside{background:#F7F7EC;border-right:1px solid var(--line);overflow-y:auto;padding:12px 10px 16px;display:flex;flex-direction:column;gap:2px;min-width:0}
.hs-top{display:flex;flex-direction:column;gap:2px;padding-bottom:8px;margin-bottom:6px;border-bottom:1px solid var(--line)}
.hs-h{display:flex;align-items:center;justify-content:space-between;padding:12px 10px 6px;font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.hs-h button{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;color:var(--ink)}.hs-h button:hover{background:#EBECDF}
.hsi{display:flex;align-items:center;gap:10px;width:100%;min-height:38px;padding:6px 10px;border-radius:12px;color:#3d4437;font-size:14px;text-align:left}
.hsi:hover{background:#EDEEE2}.hsi.on{background:var(--dark);color:#fff}.hsi.on .hsi-i,.hsi.on .hlk{color:var(--sand)}
.hsi .nm{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.hsi.un .nm{font-weight:700;color:var(--ink)}.hsi.on.un .nm{color:#fff}
.hsi.dim .nm{opacity:.6}.hsi-i{width:22px;display:grid;place-items:center;color:var(--muted);flex:none}.hsi-i.hash{font-weight:700;font-size:16px}
.hcnt{min-width:22px;height:20px;padding:0 6px;border-radius:999px;background:var(--sand);color:var(--ink);font-size:11.5px;font-weight:700;display:grid;place-items:center;flex:none}
.hlk{color:var(--muted);display:inline-grid;place-items:center}.hs-empty{padding:6px 12px;color:var(--muted);font-size:13px}
.hava{position:relative;display:inline-grid;flex:none}.hava .av{width:36px;height:36px;font-size:12px}.hava.sm .av{width:24px;height:24px;font-size:9.5px}
.ondot{position:absolute;right:-1px;bottom:-1px;width:11px;height:11px;border-radius:50%;background:#3fb24f;border:2px solid #fff}.hava.sm .ondot{width:9px;height:9px}
.ondot.s{position:static;display:inline-block;width:8px;height:8px;border:0;margin-right:2px}
.hmain,.hthr{display:flex;flex-direction:column;min-width:0;min-height:0;position:relative}.hthr{border-left:1px solid var(--line);background:#FCFCF7}
.hmain.drop:after,.hthr.drop:after{content:'Drop files to attach';position:absolute;inset:10px;border:2px dashed var(--dark);border-radius:18px;background:rgba(250,255,126,.35);display:grid;place-items:center;font-weight:700;color:var(--dark);z-index:5}
.hhd{display:flex;align-items:center;gap:12px;min-height:64px;padding:10px 20px;border-bottom:1px solid var(--line)}.hhd-t{min-width:0}
.hhd h2{font-size:16px;font-weight:700;display:flex;align-items:center;gap:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hhd p{font-size:12.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:60ch}
.hmeta{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;color:var(--muted);padding:0 6px;white-space:nowrap}
.hback{display:none;width:36px;height:36px;border-radius:50%;place-items:center;flex:none}.hback:hover{background:#EEEFE3}
.hscroll{flex:1;overflow-y:auto;min-height:0;padding:8px 0 10px;overscroll-behavior:contain}
.hann{padding:16px 20px}.hann .pha{display:flex!important}
.hwel{padding:22px 20px 14px;display:flex;flex-direction:column;align-items:flex-start;gap:6px}.hwel h3{font-size:18px;font-weight:700}.hwel p{color:var(--muted);font-size:13.5px;max-width:64ch}
.hwel-i{width:44px;height:44px;border-radius:14px;background:var(--sand-2);display:grid;place-items:center;color:var(--dark);font-size:22px;font-weight:700}
.hday{display:flex;align-items:center;gap:10px;margin:10px 20px;color:var(--muted);font-size:12px;font-weight:600}.hday:before,.hday:after{content:'';flex:1;height:1px;background:var(--line)}
.hday span{padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:#fff}
.hmsg{position:relative;display:grid;grid-template-columns:40px minmax(0,1fr);gap:12px;padding:6px 20px}
.hmsg.cmp{padding-top:1px;padding-bottom:1px}.hmsg:hover{background:#FAFAF2}.hmsg.ment{background:#FEFFE6;box-shadow:inset 3px 0 0 var(--sand)}.hmsg.flash{animation:hflash 1.6s ease}
@keyframes hflash{0%{background:#FAFF7E}100%{background:transparent}}
.hl{display:flex;justify-content:center}.hts{font-size:10.5px;color:var(--muted);opacity:0;padding-top:4px;white-space:nowrap}.hmsg:hover .hts{opacity:1}
.hb{min-width:0}.hh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;line-height:1.3}.hh b{font-size:14px}.hh time{font-size:11.5px;color:var(--muted)}.hh .tag{transform:translateY(-1px)}
.hed{font-size:11px;color:var(--muted)}
.htx{font-size:14px;line-height:1.5;overflow-wrap:anywhere;color:#2b302a}.htx a{color:var(--info);text-decoration:underline}.htx code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;background:#EFF0E4;border-radius:6px;padding:1px 5px}
.hacts{position:absolute;top:-14px;right:18px;display:none;align-items:center;gap:2px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:3px}
.hmsg:hover .hacts,.hmsg:focus-within .hacts{display:flex}.hacts button{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;font-size:15px;color:var(--ink)}.hacts button:hover{background:#EEEFE3}
@media (hover:none){.hacts{position:static;display:flex;margin:4px 0 0 52px;grid-column:1/-1;width:max-content;background:transparent;border:0;padding:0}.hacts button{width:34px;height:34px}}
.hreacts{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.hre{display:inline-flex;align-items:center;gap:5px;height:28px;padding:0 9px;border-radius:999px;border:1px solid var(--line);background:#fff;font-size:14px}
.hre span{font-size:12px;font-weight:600;color:var(--muted)}.hre.me{background:#EEF6E2;border-color:#9cc07a}.hre.me span{color:var(--up)}.hre:hover{border-color:var(--dark)}.hre.add{color:var(--muted)}
.hrep{display:flex;align-items:center;gap:8px;margin-top:6px;padding:4px 10px 4px 4px;border-radius:10px;font-size:12.5px;max-width:100%}.hrep:hover{background:#fff;box-shadow:inset 0 0 0 1px var(--line)}
.hrep b{color:var(--info)}.hrep-av{display:flex}.hrep-av .hava{margin-right:-4px}.hrep .muted{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hatts{display:flex;flex-direction:column;gap:8px;margin-top:6px;align-items:flex-start}
.himgs{display:flex;flex-wrap:wrap;gap:8px}.himg{display:block;border-radius:14px;overflow:hidden;border:1px solid var(--line);max-width:min(320px,100%)}.himg img{display:block;max-height:240px;width:auto;max-width:100%;object-fit:cover}
.himg.ph{width:120px;height:90px;display:grid;place-items:center;color:var(--muted);background:#F3F3E7}
.hvoice{display:flex;align-items:center;gap:10px;padding:6px 12px 6px 6px;border:1px solid var(--line);border-radius:999px;background:#fff;max-width:100%}
.hvi{width:32px;height:32px;border-radius:50%;background:var(--dark);color:var(--sand);display:grid;place-items:center;flex:none}.hvoice audio{height:32px;max-width:240px;min-width:0}.hvd{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.hfile{display:flex;align-items:center;gap:12px;padding:10px 12px;border:1px solid var(--line);border-radius:14px;background:#fff;max-width:min(360px,100%);color:var(--ink)}.hfile:hover{border-color:var(--dark)}
.hfi{width:40px;height:40px;border-radius:10px;background:var(--sand-2);color:var(--dark);display:grid;place-items:center;font-size:10.5px;font-weight:800;flex:none}
.hfn{min-width:0;display:flex;flex-direction:column}.hfn b{font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hfn small{color:var(--muted);font-size:12px}
.htyping{min-height:20px;padding:0 22px;font-size:12px;color:var(--muted);display:flex;align-items:center;gap:6px}
.tdots{display:inline-flex;gap:3px}.tdots i{width:5px;height:5px;border-radius:50%;background:var(--muted);animation:tdot 1.2s infinite}.tdots i:nth-child(2){animation-delay:.15s}.tdots i:nth-child(3){animation-delay:.3s}
@keyframes tdot{0%,60%,100%{opacity:.3;transform:none}30%{opacity:1;transform:translateY(-3px)}}
.hcmp{position:relative;margin:0 16px 16px;border:1px solid var(--grey-1);border-radius:18px;background:#fff;transition:border-color .15s}.hcmp:focus-within{border-color:var(--dark)}
.hcmp-off{margin:0 16px 16px;padding:14px 16px;border:1px dashed var(--grey-1);border-radius:18px;color:var(--muted);font-size:13.5px;display:flex;align-items:center;gap:8px}
.hin{display:block;width:100%;border:0;outline:0;resize:none;background:transparent;padding:12px 16px 4px;font:inherit;font-size:14.5px;line-height:1.45;max-height:180px;color:var(--ink)}
.hbar{display:flex;align-items:center;gap:2px;padding:6px 8px 8px}
.hib{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;color:#4e5646;cursor:pointer;flex:none}.hib:hover{background:#EEEFE3;color:var(--ink)}.hib.on{background:#fde7e4;color:var(--dn)}
.hhint{flex:1;min-width:0;font-size:11.5px;color:var(--muted);padding:0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hsend{width:38px;height:38px;border-radius:12px;background:var(--dark);color:#fff;display:grid;place-items:center;flex:none;margin-left:auto}.hsend:hover{background:var(--ink)}.hsend:disabled{opacity:.5}
.hchips{display:flex;flex-wrap:wrap;gap:8px;padding:10px 12px 0}
.hchip{display:flex;align-items:center;gap:8px;padding:6px 6px 6px 6px;border:1px solid var(--line);border-radius:12px;background:#F8F8EE;max-width:100%;min-width:0}
.hchip img{width:40px;height:40px;object-fit:cover;border-radius:8px}.hchip .nm{display:flex;flex-direction:column;min-width:0;max-width:200px}.hchip .nm b{font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hchip .nm small{font-size:11px;color:var(--muted)}
.hchip button{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;color:var(--muted);font-size:16px;flex:none}.hchip button:hover{background:#E6E7D8;color:var(--ink)}
.hchip.v{padding-left:10px}.hchip.v audio{height:30px;max-width:200px}.hchip.v b{font-size:12px;font-variant-numeric:tabular-nums}
.hrec{display:flex;align-items:center;gap:10px;padding:12px 14px 4px;font-size:14px}.rdot{width:10px;height:10px;border-radius:50%;background:var(--dn);animation:rpulse 1s infinite}#rectime{font-variant-numeric:tabular-nums;color:var(--muted)}
@keyframes rpulse{50%{opacity:.35}}
.hsug{position:absolute;left:12px;right:12px;bottom:calc(100% + 6px);background:#fff;border:1px solid var(--line);border-radius:14px;padding:6px;display:none;flex-direction:column;gap:2px;max-height:260px;overflow-y:auto;z-index:6}
.hsug.open{display:flex}.hsug button{display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:10px;text-align:left}.hsug button:hover,.hsug button:focus{background:#F1F2E6}
.hai{display:flex;flex-direction:column;gap:8px;width:calc(100% - 32px);margin:8px 16px;padding:12px 14px;border:1px solid var(--line);border-radius:16px;background:#fff;text-align:left}.hai:hover{border-color:var(--dark)}
.hai-w{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);font-weight:600}.hai-w time{margin-left:auto;font-weight:500}
.hai-b{display:flex;gap:10px;align-items:flex-start}.hai-b>span:last-child{min-width:0;display:flex;flex-direction:column;gap:2px;font-size:13.5px}.hai-t{color:#3d4437;overflow-wrap:anywhere}
.hedit{margin-top:4px;border:1px solid var(--dark);border-radius:14px;background:#fff}.hedit .hin{padding:10px 12px 4px}.hedit-b{display:flex;align-items:center;gap:8px;justify-content:flex-end;padding:6px 8px 8px}.hedit-b .muted{margin-right:auto;padding-left:6px}
.emopop{position:fixed;z-index:120;width:min(320px,calc(100vw - 16px));max-height:min(380px,calc(100vh - 16px));overflow-y:auto;background:#fff;border:1px solid var(--line);border-radius:18px;padding:10px}
.emo-q{display:flex;gap:2px;padding-bottom:8px;border-bottom:1px solid var(--line);margin-bottom:4px}.emo-h{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;padding:8px 4px 4px}
.emo-g{display:grid;grid-template-columns:repeat(8,1fr);gap:2px}.emopop button{height:34px;border-radius:9px;font-size:19px;display:grid;place-items:center}.emo-q button{flex:1}.emopop button:hover,.emopop button:focus{background:#F1F2E6;outline:none}
@media (max-width:1100px){.hub.th{grid-template-columns:230px minmax(0,1fr) 320px}.hub{grid-template-columns:230px minmax(0,1fr)}.hhint{display:none}}
@media (max-width:899px){.hub,.hub.th{grid-template-columns:minmax(0,1fr);height:calc(100dvh - 150px);min-height:480px;border-radius:20px}
 .hub .hside,.hub .hmain,.hub .hthr{display:none}.hub.v-list .hside,.hub.v-conv .hmain,.hub.v-thread .hthr{display:flex}.hub.v-thread:not(.th) .hmain{display:flex}
 .hside{border-right:0}.hthr{border-left:0}.hback{display:grid}.hmsg{padding:6px 14px;grid-template-columns:36px minmax(0,1fr);gap:10px}.hday{margin:10px 14px}.hcmp,.hcmp-off{margin:0 10px 10px}.hhd{padding:8px 12px;gap:8px}.hmeta{display:none}.hwel{padding:18px 14px 10px}.hvoice audio{max-width:160px}}
.pop .pall{display:block;''')

open(p, 'w', encoding='utf-8').write(h)
print('ok', len(h))
