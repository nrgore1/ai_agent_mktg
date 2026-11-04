/* Role assignment visibility and source-linked execution packets. */
const beforeWorkAssignment=render;
render=function(){
 beforeWorkAssignment();
 if(!me||view!=='business'||businessTab!=='counterparts'||!businessData?.human_ai?.work_assignment)return;
 const w=businessData.human_ai.work_assignment,president=me.role==='founder',match=x=>(!businessCompany||x.company_id===businessCompany)&&(!businessUnit||x.unit_id===businessUnit)&&(!businessRole||x.role===businessRole);
 const units=new Map(businessData.units.map(u=>[u.id,u]));
 const assignments=w.assignments.filter(match),reports=w.reports.filter(r=>match({...r,company_id:units.get(r.unit_id)?.company_id}));
 const box=document.createElement('section');box.className='card full';box.id='assigned-work';
 const plans=assignments.filter(a=>a.kind==='plan'),backlog=assignments.filter(a=>a.kind==='backlog'||a.kind==='department_backlog');
 let html='<h2>Assigned work and next actions</h2><p>'+esc(w.note)+'</p><p><b>'+plans.length+'</b> plan activities / <b>'+backlog.length+'</b> remaining backlog assignments in this view. <b>'+reports.length+'</b> role work packets prepared.</p>';
 if(!w.assignments.length&&president)html+='<button id="assign-current-work">Assign and start the current plan</button>';
 html+='<p>Current outcome activities are in progress because assignment and preparation have started; human execution and verified outcomes are still outstanding. Future phases remain scheduled. Existing weekly preparation continues under the 90-day plan controls.</p>';
 if(president)html+='<p><b>Your action queue:</b> clear company/unit/role filters to see the President-owned tasks at the top of Manual work queue. Scope decisions do not automatically grant access. Existing commercial approval remains recorded; unmet evidence gates still hold execution.</p>';
 html+='<details><summary>All assignments in this view</summary>'+assignments.map(a=>'<p><b>'+esc(a.title)+'</b><br>'+esc(a.kind)+(a.oversight_role?' (executive oversight: '+esc(a.oversight_role)+')':'')+' / '+esc(a.source_status)+' / Human: '+esc(a.human_assignee)+' / AI: '+esc(a.ai_assignee)+(a.start_date?'<br>Scheduled '+esc(a.start_date)+' to '+esc(a.due_date):'')+'<br><span class="muted">'+esc(a.routing)+'</span></p>').join('')+'</details>';
 html+=reports.map(r=>'<details class="assigned-packet"><summary>'+esc(units.get(r.unit_id)?.name||r.unit_id)+' / '+esc(r.role)+' - prepared work packet</summary><p>Human: '+esc(r.human_assignee)+' / AI: '+esc(r.ai_assignee)+'<br>Prepared '+esc(r.created_at)+'. Source-based preparation; no outcome certified.</p><h3>Current phase</h3>'+r.active_activities.map(t=>'<p><b>'+esc(t.title)+'</b><br>'+esc(t.acceptance)+'<br>Due '+esc(t.due_date)+'</p>').join('')+'<h3>Active cases</h3>'+(r.case_queue||[]).map(c=>'<p><b>'+esc(c.title)+'</b> / '+esc(c.status)+'<br>Owner: '+esc(c.owner)+'<br>'+esc(c.next_action)+'</p>').join('')+'<h3>Prioritized backlog handoffs</h3>'+(r.prioritized_backlog.length?r.prioritized_backlog.map(t=>'<details><summary>P'+t.priority+' - '+esc(t.title)+' - '+esc(t.status)+'</summary><p>'+esc(t.acceptance)+'</p><p><b>Unmet prerequisites:</b> '+esc(t.unmet_dependencies.join('; ')||'None listed; acceptance evidence still required.')+'</p><p><b>Latest recorded observation:</b> '+esc(t.latest_observation)+'</p><p>'+t.evidence_sources.map(esc).join('<br>')+'</p></details>').join(''):'<p>No product readiness item maps to this role. Continue the current role objective using source-linked evidence.</p>')+'</details>').join('');
 box.innerHTML=html;
 const panel=document.querySelector('.human-ai-panel');panel.insertBefore(box,panel.children[1]||null);
 const start=$('#assign-current-work');if(start)start.onclick=()=>run(async()=>{await api('business/assign-work',{source:'President authorized paired assignment through Human + AI workspace'});businessReload()});
};
