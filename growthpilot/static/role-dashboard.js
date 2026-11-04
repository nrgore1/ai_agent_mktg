/* Human role dashboard. Server authorization is authoritative. */
const beforeRoleRender=render;
let roleSession=null;
const beforeRoleLogin=loginScreen;
loginScreen=function(){roleSession=null;document.querySelectorAll('nav [data-view]').forEach(b=>b.hidden=false);return beforeRoleLogin()};
const rolePassword=()=>`<div class="card"><h2>Change your password</h2><p>Use a unique password of at least 14 characters. Temporary passwords must be changed before accessing business data.</p><form id="role-password" class="form-grid"><label>Current password<input name="old" type="password" autocomplete="current-password" required></label><label>New password<input name="new" type="password" autocomplete="new-password" minlength="14" required></label><button>Change and sign out</button></form></div>`;
function bindRolePassword(){const f=$('#role-password');if(f)f.onsubmit=e=>{e.preventDefault();run(async()=>{await api('password',Object.fromEntries(new FormData(f)));state=null;loginScreen();notice('Password changed. Sign in with your new password.')})}}
render=function(){
 const scoped=me?.role==='business';
 if(scoped&&roleSession!==me.username){roleSession=me.username;view='business';businessTab='work'}
 document.querySelectorAll('nav [data-view]').forEach(b=>b.hidden=scoped&&!['business','settings',...(me?.can_manage_users?['users']:[])].includes(b.dataset.view));
 if(me?.must_change){
  header();$('#pause')?.remove();$('#title').textContent='Set your personal password';$('#content').innerHTML=rolePassword();bindRolePassword();return;
 }
 if(scoped){
  if(!['settings','users'].includes(view))view='business';
  if(view==='business'&&businessData&&!businessData.dashboard_tabs.includes(businessTab))businessTab='work';
  if(view==='settings'){header();$('#pause')?.remove();$('#title').textContent='Your account';$('#content').innerHTML=rolePassword();bindRolePassword();return}
 }
 beforeRoleRender();
 if(scoped){
  $('#pause')?.remove();
  document.querySelector('header > span').textContent=businessData?.companies.map(c=>c.name).join(' / ')||'ASSIGNED WORKSPACE';
  $('#title').textContent=businessData?Object.keys(businessData.roles).join(' / ')+' dashboard':'Your role dashboard';
  const names={Portfolio:'overview','Work queues':'work','Decision inbox':'decisions','Process library':'processes','People & roles':'roles',Connections:'connections','Vanguard opportunities':'opportunities','Finance evidence':'finance','AI work results':'workers','90-day role plans':'plan','Human + AI workspace':'counterparts'};
  document.querySelectorAll('[aria-label="Business workspace"] button').forEach(b=>b.hidden=!businessData?.dashboard_tabs.includes(names[b.textContent]));
  $('#business-export')?.remove();
  if($('#business-company'))$('#business-company').options[0].textContent='All assigned companies';
  return;
 }
 if(me?.role==='founder'&&view==='settings'){
  const box=document.createElement('section');box.className='card full';box.innerHTML='<h2>User administration</h2><p>Your President account has full user management across both companies.</p><button id="open-user-management">Open User management</button>';$('#content').prepend(box);$('#open-user-management').onclick=()=>{view='users';render()};
 }
};
