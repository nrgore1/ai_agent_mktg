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
 document.querySelectorAll('nav [data-view]').forEach(b=>b.hidden=scoped&&!['business','settings'].includes(b.dataset.view));
 if(me?.must_change){
  header();$('#pause')?.remove();$('#title').textContent='Set your personal password';$('#content').innerHTML=rolePassword();bindRolePassword();return;
 }
 if(scoped){
  if(view!=='settings')view='business';
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
 if(me?.role==='founder'&&view==='settings'&&!$('#role-account-create')){
  const box=document.createElement('section');box.className='card full';box.innerHTML=`<h2>Create a company role login</h2><p>CEO, CFO, CMO, CTO and COO accounts receive only their assigned company and unit views. They cannot approve founder decisions, publish campaigns, change prices or access integration secrets. Create a named account for each person; do not share credentials.</p><form id="role-account-create" class="form-grid"><label>Username<input name="username" pattern="[a-zA-Z0-9_.@-]{1,80}" autocomplete="off" required></label><label>Temporary password<input name="password" type="password" minlength="14" autocomplete="new-password" required></label><label>Company<select name="company"><option value="atmakosh">Atmakosh LLC</option><option value="vireoka">Vireoka LLC</option></select></label><label>Business role<select name="business_role">${['CEO','CFO','CMO','CTO','COO'].map(r=>'<option>'+r+'</option>').join('')}</select></label><fieldset id="role-units"><legend>Business units</legend><p>Loading available units&</p></fieldset><button disabled>Create role login</button></form><p id="role-account-result" role="status"></p>`;$('#content').prepend(box);
  const manager=document.createElement('section');manager.className='card full';manager.innerHTML='<h2>Manage role logins</h2><p>Set a private temporary password before handing over a role login. Password resets and access changes sign out every existing session for that account.</p><form id="role-account-manage" class="form-grid"><label>Role login<select name="username" required></select></label><label>Action<select name="action"><option value="password">Set temporary password</option><option value="disable">Disable account</option><option value="enable">Enable account</option></select></label><label>New temporary password<input name="password" type="password" minlength="14" autocomplete="new-password"></label><button>Save account change</button></form><p id="role-manage-result" role="status"></p>';$('#content').append(manager);
  const mf=$('#role-account-manage');
  const reloadRoleUsers=()=>api('users').then(users=>{if(!mf.isConnected)return;mf.elements.username.innerHTML=users.filter(u=>u.role==='business').map(u=>'<option value="'+esc(u.username)+'">'+esc(u.username)+(u.enabled?'':' (disabled)')+'</option>').join('')}).catch(e=>notice(e.message,true));reloadRoleUsers();
  mf.elements.action.onchange=()=>{mf.elements.password.required=mf.elements.action.value==='password';mf.elements.password.disabled=mf.elements.action.value!=='password'};mf.elements.action.onchange();
  mf.onsubmit=e=>{e.preventDefault();run(async()=>{const data={username:mf.elements.username.value};if(mf.elements.action.value==='password')data.password=mf.elements.password.value;else data.enabled=mf.elements.action.value==='enable';await api('role-accounts/manage',data);mf.elements.password.value='';$('#role-manage-result').textContent='Account updated. Previous sessions are signed out.';reloadRoleUsers()})};
  const f=$('#role-account-create');
  api('business').then(d=>{if(!f.isConnected)return;const fill=()=>{$('#role-units').innerHTML='<legend>Business units</legend>'+d.units.filter(u=>u.company_id===f.elements.company.value).map(u=>'<label><input type="checkbox" name="unit" value="'+esc(u.id)+'" checked> '+esc(u.name)+'</label>').join('')};fill();f.elements.company.onchange=fill;f.querySelector('button').disabled=false}).catch(e=>notice(e.message,true));
  f.onsubmit=e=>{e.preventDefault();run(async()=>{const values=new FormData(f),data=Object.fromEntries(values);delete data.unit;data.units=values.getAll('unit');await api('role-accounts',data);f.elements.password.value='';reloadRoleUsers();$('#role-account-result').textContent='Role account created. Share its temporary password through a private channel. First sign-in requires a password change.'})};
 }
};
