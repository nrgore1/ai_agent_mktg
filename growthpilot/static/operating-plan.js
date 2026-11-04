/* Scheduled preparation and separately reviewed outcomes. */
const beforeOperatingPlan=render;
render=function(){
 beforeOperatingPlan();
 if(view!=='business'||!me||!businessData?.operating_plan)return;
 const d=businessData.operating_plan,bar=document.querySelector('[aria-label="Business workspace"]');
 if(bar){const b=document.createElement('button');b.textContent='90-day role plans';b.dataset.businessTab='plan';b.className=businessTab==='plan'?'active':'';b.onclick=()=>{businessTab='plan';render()};bar.append(b)}
 if(businessTab!=='plan')return;
 const unitIds=new Set(businessData.units.filter(u=>(!businessCompany||u.company_id===businessCompany)&&(!businessUnit||u.id===businessUnit)).map(u=>u.id));
 const plans=d.plans.filter(p=>unitIds.has(p.unit_id)&&(!businessRole||p.role===businessRole));
 const root=document.createElement('section');root.className='full operating-plan-panel';
 let html='<div class="card"><h2>90-day role plans</h2><p>'+esc(d.note)+'</p>';
 if(!d.program){
  html+='<p>No plan has been prepared.</p>'+(me.role==='founder'?'<form id="op-prepare" class="toolbar"><label>Start date<input name="start_date" type="date" required></label><button>Prepare 90-day plans</button></form>':'')+'</div>';root.innerHTML=html;$('#content').append(root);
  const f=$('#op-prepare');if(f)f.onsubmit=e=>{e.preventDefault();run(async()=>{await api('business/plan-prepare',Object.fromEntries(new FormData(f)));businessReload()})};return;
 }
 const program=d.program;
 html+='<p><b>'+esc(program.start_date)+' to '+esc(program.end_date)+'</b> - '+esc(program.timezone)+'</p><p>'+esc(program.scope)+'</p><p><b>Preparation worker: '+(program.enabled?'enabled':'paused')+'</b>. One evidence pack per role/unit each week; new phase packs also run at days 31 and 61. No catch-up business outcomes are invented.</p>';
 if(me.role==='founder')html+='<button id="op-control">'+(program.enabled?'Pause plan preparation':'Approve scope and enable preparation')+'</button>';
 html+='</div>';
 html+='<div class="metrics">'+[['Role plans in this view',plans.length],['Preparation complete',plans.flatMap(p=>p.tasks).filter(t=>t.kind==='preparation'&&t.status==='completed').length],['Business outcomes complete',plans.flatMap(p=>p.tasks).filter(t=>t.kind==='outcome'&&t.status==='completed').length]].map(([k,v])=>'<div class="card"><span class="muted">'+esc(k)+'</span><div class="metric">'+v+'</div></div>').join('')+'</div>';
 html+=plans.map(p=>{
  const reports=d.reports.filter(r=>r.plan_id===p.id);
  return '<details class="card op-plan"><summary><b>'+esc(p.name)+'</b> - '+esc(p.company_id)+'</summary><p>Accountable human: '+esc(p.accountable_human)+'. AI preparation does not replace owner verification.</p>'+p.tasks.map(t=>'<section><h3>Days '+((t.phase-1)*30+1)+'-'+(t.phase*30)+': '+esc(t.title)+'</h3><p>'+esc(t.kind)+' / '+esc(t.status)+' / due '+esc(t.due_date)+'</p><p>'+esc(t.acceptance)+'</p>'+t.evidence.map(e=>'<p class="muted">'+esc(e.note)+'<br>'+esc(e.source)+'</p>').join('')+(t.kind==='outcome'&&me.role!=='viewer'?'<form class="op-record form-grid" data-plan="'+esc(p.id)+'" data-task="'+esc(t.id)+'" data-version="'+t.version+'"><label>Status<select name="status"><option>in_progress</option><option>blocked</option><option>ready_for_review</option>'+(me.role==='founder'?'<option>completed</option>':'')+'</select></label><label>Evidence reference<input name="source" required minlength="10" maxlength="1000"></label><label>Outcome and limitations<textarea name="note" required minlength="30" maxlength="4000"></textarea></label><label><input name="attest" type="checkbox"> I verified the milestone acceptance evidence</label><button>Record milestone evidence</button></form>':'')+'</section>').join('')+'<h3>Latest evidence pack</h3>'+(reports.length?'<pre>'+esc(JSON.stringify(reports[0],null,2))+'</pre>':'<p>Scheduled preparation has not run yet.</p>')+'</details>';
 }).join('');
 const backlog=d.backlog.filter(t=>(!businessCompany||t.company_id===businessCompany)&&(!businessUnit||t.unit_id===businessUnit)&&(!businessRole||t.role===businessRole));
 html+='<div class="card"><h2>Existing backlog and next owners</h2><p>'+backlog.length+' unresolved tasks in this view. Product fixes stay on product backlogs. Unmapped products require founder scope mapping and are not silently assigned to a company.</p>'+backlog.map(t=>'<details><summary>P'+t.priority+' - '+esc(t.title)+' - '+esc(t.status)+' - '+esc(t.role)+'</summary><p>Product '+t.product_id+' / '+esc(t.unit_id||'Founder mapping queue')+'</p><p>'+esc(t.next_action)+'</p><p>'+esc(t.acceptance)+'</p><p class="muted">'+esc(t.source)+'</p><p>Human: '+esc(t.human_assignee||'not assigned')+' / AI: '+esc(t.ai_assignee||t.role)+'</p></details>').join('')+'</div>';
 root.innerHTML=html;$('#content').append(root);
 const control=$('#op-control');if(control)control.onclick=()=>run(async()=>{await api('business/plan-control',{enabled:!program.enabled,approve_scope:!program.enabled});businessReload()});
 document.querySelectorAll('.op-record').forEach(f=>f.onsubmit=e=>{e.preventDefault();run(async()=>{const values=new FormData(f);await api('business/plan-record',{plan_id:f.dataset.plan,task_id:f.dataset.task,version:Number(f.dataset.version),status:values.get('status'),source:values.get('source'),note:values.get('note'),attest:values.get('attest')==='on'});businessReload();notice('Milestone evidence recorded. Existing release gates are unchanged.')})});
};
