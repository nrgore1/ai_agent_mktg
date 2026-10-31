"use strict";
const statusBox=document.getElementById('status');
let token=location.hash.slice(1);history.replaceState(null,'',location.pathname);
async function submit(action,data,button){
 button.disabled=true;statusBox.textContent='Working…';
 try{
  const r=await fetch('/marketing-updates/api/'+action,{method:'POST',credentials:'omit',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const d=await r.json();if(!r.ok)throw Error(d.error||'Please try again later.');
  statusBox.textContent=d.message||(d.confirmed?'Your subscription is confirmed.':d.withdrawn?'You are unsubscribed.':d.export?'Your consent record is ready to download.':'Done.');
  if(d.export){const u=URL.createObjectURL(new Blob([JSON.stringify(d.export,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='my-marketing-consent.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}
  if(d.manage_url){const a=document.createElement('a');a.href=d.manage_url;a.textContent='Unsubscribe from these updates';document.getElementById('next').replaceChildren(a)}
  if(d.confirmed||d.withdrawn||d.erased){token='';button.hidden=true;if(d.erased)document.querySelectorAll('#rights-export,#rights-delete').forEach(b=>b.hidden=true)}
 }catch(e){statusBox.textContent=e.message||'The request could not be confirmed. Please try again.'}
 finally{button.disabled=false}
}
for(const action of ['subscribe','manage','rights-request']){
 const f=document.getElementById(action);if(f)f.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(f));if(action==='subscribe')data.consent=f.elements.consent.checked;submit(action,data,f.querySelector('button'))});
}
const buttons=[...document.querySelectorAll('#token-action,#rights-export,#rights-delete')];
if(buttons.length&&!token){buttons.forEach(b=>b.disabled=true);statusBox.textContent='Open the complete link from your email. Request a fresh link from Email preferences if it has expired.'}
for(const b of buttons)b.addEventListener('click',()=>{
 const action=b.dataset.action||b.id;
 if(action==='rights-delete'&&!document.getElementById('confirm-erasure').checked){statusBox.textContent='Choose the deletion checkbox to continue.';return}
 submit(action,{token,...(action==='rights-delete'?{confirm_erasure:true}:{})},b);
});
