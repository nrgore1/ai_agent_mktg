/* President and company-scoped user administration; every operation is authorized on the server. */
let userDirectory=null,userDirectoryOwner=null,userEdit=null,userRequest=0;
const userManagementNav=document.createElement('button');userManagementNav.dataset.view='users';userManagementNav.textContent='User management';document.querySelector('nav').append(userManagementNav);
userManagementNav.onclick=()=>{view='users';userDirectory=null;userEdit=null;render()};
const beforeUserLogin=loginScreen;
loginScreen=function(){userDirectory=null;userDirectoryOwner=null;userEdit=null;userRequest++;userManagementNav.hidden=true;return beforeUserLogin()};
const beforeUserRender=render;
render=function(){
 const allowed=me&&(me.role==='founder'||me.can_manage_users)&&!me.must_change;
 userManagementNav.hidden=!allowed;
 if(view!=='users'||!me||me.must_change){beforeUserRender();userManagementNav.hidden=!allowed;return}
 if(!allowed){view='business';return beforeUserRender()}
 if(userDirectoryOwner!==me.username){userDirectoryOwner=me.username;userDirectory=null;userEdit=null;userRequest++}
 header();if(me.role==='business')$('#pause')?.remove();
 $('#title').textContent='User management';document.querySelector('.heading p:not(.eyebrow)').textContent='Manage people, roles and access for Atmakosh LLC and Vireoka LLC.';
 document.querySelectorAll('nav [data-view]').forEach(b=>{if(me.role==='business')b.hidden=!['business','settings','users'].includes(b.dataset.view);b.classList.toggle('active',b.dataset.view==='users')});
 if(!userDirectory){
  $('#content').textContent='Loading authorized users and role permissions…';const seq=++userRequest,owner=me.username;
  api('user-management').then(d=>{if(seq===userRequest&&me?.username===owner){userDirectory=d;render()}}).catch(e=>{if(seq===userRequest){$('#content').textContent=e.message;notice(e.message,true)}});
  return;
 }
 const d=userDirectory,selected=d.users.find(u=>u.username===userEdit),editing=!!selected;
 const companies=[...new Set(d.units.map(u=>u.company_id))];
 const company=selected?.grants[0]?.company||companies[0];
 const assignedRoles=new Set(selected?.grants.map(g=>g.role)||[]),assignedUnits=new Set(selected?.grants.map(g=>g.unit)||[]);
 let html='<div class="card full"><h2>'+(d.is_president?'President and full user administrator':'Delegated company user administrator')+'</h2><p>Signed in as <b>'+esc(me.username)+'</b>. '+esc(d.note)+'</p><p>Passwords are never displayed from storage. Give each person a unique temporary password privately; first sign-in requires a change.</p><button id="users-refresh">Refresh users</button></div>';
 html+='<div class="card full"><h2>Account directory</h2><div class="user-directory">'+d.users.map(u=>'<details><summary><b>'+esc(u.username)+'</b> · '+esc(u.display_name)+' · '+(u.deleted?'deleted':u.enabled?'enabled':'disabled')+(u.must_change?' · password change required':'')+'</summary><p>'+esc(u.system_role)+(u.protected?' · protected account':'')+'</p><ul>'+u.grants.map(g=>'<li>'+esc(g.company)+' / '+esc(d.units.find(x=>x.id===g.unit)?.name||g.unit)+' / '+esc(g.role)+'</li>').join('')+'</ul>'+(u.can_edit?'<button data-user-edit="'+esc(u.username)+'">Edit roles and units</button>':'')+'</details>').join('')+'</div></div>';
 html+='<div class="card full"><h2>'+(editing?'Edit account '+esc(selected.username):'Create a user')+'</h2><p>Choose only the roles and units this person needs. Saving replaces the complete selected access set and signs out existing sessions. Usernames remain stable for audit history.</p><form id="users-profile" class="form-grid">';
 if(!editing)html+='<label>User ID<input name="username" pattern="[a-zA-Z0-9_.@-]{1,80}" maxlength="80" required autocomplete="off"></label><label>Temporary password<input name="password" type="password" minlength="14" maxlength="1024" required autocomplete="new-password"></label>';
 html+='<label>Person or role name<input name="display_name" maxlength="160" required value="'+esc(selected?.display_name||'')+'"></label><label>Company<select name="company">'+companies.map(c=>'<option value="'+c+'" '+(c===company?'selected':'')+'>'+esc(c==='atmakosh'?'Atmakosh LLC':'Vireoka LLC')+'</option>').join('')+'</select></label>';
 html+='<fieldset class="user-role-options"><legend>Assignable roles</legend>'+d.assignable_roles.map(r=>'<label><input name="roles" type="checkbox" value="'+esc(r)+'" '+(assignedRoles.has(r)?'checked':'')+'> '+esc(r)+' — '+esc(d.roles[r].description)+'</label>').join('')+'</fieldset>';
 html+='<fieldset class="user-unit-options"><legend>Business units</legend></fieldset><label>Reason for this access<textarea name="note" minlength="20" maxlength="2000" required></textarea></label><button>'+(editing?'Save user access':'Create user')+'</button></form>'+(editing?'<button id="users-new">Cancel edit and create another user</button>':'')+'</div>';
 const manageable=d.users.filter(u=>u.can_edit);
 html+='<div class="card full"><h2>Reset disable or delete access</h2><p>Delete removes login access and active grants while retaining the account ID in historical evidence. It does not delete customer data, financial records or case history. President accounts and your own account are protected.</p><form id="users-action" class="form-grid"><label>User<select name="username" required>'+manageable.map(u=>'<option value="'+esc(u.username)+'">'+esc(u.username)+'</option>').join('')+'</select></label><label>Action<select name="action"><option value="reset_password">Set temporary password</option><option value="disable">Disable access</option><option value="enable">Enable access</option><option value="delete">Delete user access</option></select></label><label>New temporary password<input name="password" type="password" minlength="14" maxlength="1024" autocomplete="new-password"></label><label>Type user ID to confirm deletion<input name="confirm_username" autocomplete="off"></label><label>Reason<textarea name="note" minlength="20" maxlength="2000" required></textarea></label><button '+(!manageable.length?'disabled':'')+'>Apply account action</button></form></div>';
 html+='<div class="card full"><h2>Role permissions</h2><p>Department roles receive only their assigned-unit workflow steps and manual tasks. Billing and invoicing record drafts, reconciliation and provider receipts; they do not charge cards or issue invoices automatically. New departments have human workflows, not newly qualified autonomous AI workers. Auditors can read assigned-unit case and finance evidence but cannot change it. Combining an auditor role with another role adds that other role’s write permissions.</p><ul>'+Object.entries(d.roles).map(([r,v])=>'<li><b>'+esc(r)+'</b>: '+esc(v.description)+(v.ai_preparation?' · existing bounded AI preparation':v.read_only?' · read only':' · human workflow')+'</li>').join('')+'</ul></div>';
 $('#content').innerHTML=html;
 const reload=()=>{userDirectory=null;render()};
 $('#users-refresh').onclick=reload;
 document.querySelectorAll('[data-user-edit]').forEach(b=>b.onclick=()=>{userEdit=b.dataset.userEdit;render();$('#users-profile').scrollIntoView({block:'start'})});
 $('#users-new')?.addEventListener('click',()=>{userEdit=null;render()});
 const form=$('#users-profile');
 const fillUnits=()=>{form.querySelector('.user-unit-options').innerHTML='<legend>Business units</legend>'+d.units.filter(u=>u.company_id===form.elements.company.value).map(u=>'<label><input name="units" type="checkbox" value="'+esc(u.id)+'" '+(assignedUnits.has(u.id)?'checked':'')+'> '+esc(u.name)+'</label>').join('')};
 fillUnits();form.elements.company.onchange=()=>{assignedUnits.clear();fillUnits()};
 form.onsubmit=e=>{e.preventDefault();run(async()=>{
  const fd=new FormData(form),data={display_name:fd.get('display_name'),company:fd.get('company'),roles:fd.getAll('roles'),units:fd.getAll('units'),note:fd.get('note')};
  if(editing){data.username=selected.username;data.version=selected.version}else{data.username=fd.get('username');data.password=fd.get('password')}
  if(!data.roles.length||!data.units.length)throw Error('Select at least one role and one business unit.');
  await api('user-management/'+(editing?'update':'create'),data);
  if(form.elements.password)form.elements.password.value='';userEdit=null;notice('User access saved. Existing sessions were revoked; new users must change their password.');reload();
 })};
 const af=$('#users-action');const actionFields=()=>{const action=af.elements.action.value;af.elements.password.disabled=action!=='reset_password';af.elements.password.required=action==='reset_password';af.elements.confirm_username.disabled=action!=='delete';af.elements.confirm_username.required=action==='delete'};
 af.elements.action.onchange=actionFields;actionFields();
 af.onsubmit=e=>{e.preventDefault();run(async()=>{
  const fd=new FormData(af),u=d.users.find(u=>u.username===fd.get('username')),action=fd.get('action');if(!u?.can_edit)throw Error('Select an editable account.');
  const data={username:u.username,version:u.version,note:fd.get('note')};
  if(action==='reset_password')data.password=fd.get('password');
  if(action==='delete')data.confirm_username=fd.get('confirm_username');
  await api('user-management/'+action,data);af.elements.password.value='';userEdit=null;notice('Account action recorded and previous sessions signed out.');reload();
 })};
};

