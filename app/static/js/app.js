const $ = (s, root=document) => root.querySelector(s);
const esc = (v='') => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateLabel = d => d ? new Date(`${d}T00:00:00`).toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'}) : 'Date to be confirmed';
async function api(url, options={}) {
  const response = await fetch(url, options);
  const body = await response.json().catch(()=>({detail:response.statusText}));
  if (!response.ok) throw new Error(body.detail || 'Something went wrong');
  return body;
}
async function loadDashboard() {
  const host = $('#applications'); if (!host) return;
  try {
    const apps = await api('/api/applications');
    const total = apps.length, active = apps.filter(a=>a.status==='active').length;
    const completed = apps.reduce((n,a)=>n+(a.timeline_completed||0),0);
    $('#total').textContent=total; $('#active').textContent=active; $('#completed').textContent=completed;
    $('#count-label').textContent=`${total} ${total===1?'application':'applications'}`;
    host.innerHTML = apps.length ? apps.map(a=>{
      const pct=a.timeline_total?Math.round(100*a.timeline_completed/a.timeline_total):0;
      return `<a class="app-card" href="/applications/${encodeURIComponent(a.id)}">
        <div class="card-top"><span class="status"><i></i>${esc(a.status||'active')}</span><span class="arrow">↗</span></div>
        <h3>${esc(a.university_name)}</h3><p class="program">${esc(a.program_name)}</p>
        <div class="card-meta"><span>APPLICATION DEADLINE</span><strong>${dateLabel(a.application_deadline)}</strong></div>
        <div class="progress-line"><i style="width:${pct}%"></i></div>
        <div class="progress-caption"><span>${a.timeline_completed||0} of ${a.timeline_total||0} tasks completed</span><b>${pct}%</b></div></a>`;
    }).join('') : `<div class="empty-state"><div class="empty-icon">✳</div><h3>Your next chapter starts here.</h3><p class="muted">Create your first application and turn its requirements into a practical checklist.</p><a class="button primary" href="/applications/new">Create your first application →</a></div>`;
  } catch(e) { host.innerHTML=`<div class="error">Could not load applications: ${esc(e.message)}<br><small>Check your Supabase configuration and database schema.</small></div>`; }
}
async function createApplication() {
  const form=$('#create-form'); if(!form)return;
  form.addEventListener('submit',async e=>{
    e.preventDefault(); const button=$('#submit-btn'), error=$('#form-error');
    button.disabled=true; button.textContent='Creating your plan…'; error.textContent='';
    try {
      const result=await api('/api/applications',{method:'POST',body:new FormData(form)});
      location.href=`/applications/${encodeURIComponent(result.id)}`;
    } catch(err) { error.textContent=err.message; button.disabled=false; button.textContent='Create & generate timeline →'; }
  });
}
async function loadDetail() {
  const host=$('#detail'); if(!host)return;
  const id=decodeURIComponent(location.pathname.split('/').pop());
  try {
    const app=await api(`/api/applications/${encodeURIComponent(id)}`);
    const pct=app.timeline_total?Math.round(100*app.timeline_completed/app.timeline_total):0;
    host.innerHTML=`<div class="detail-head"><div><p class="eyebrow">APPLICATION WORKSPACE</p><h1>${esc(app.university_name)}</h1><p class="program large">${esc(app.program_name)}</p></div><span class="status"><i></i>${esc(app.status||'active')}</span></div>
    <section class="detail-summary panel"><div><span>APPLICATION DEADLINE</span><strong>${dateLabel(app.application_deadline)}</strong></div><div><span>INTAKE</span><strong>${esc(app.intake||'Not specified')}</strong></div><div><span>PROGRESS</span><strong>${app.timeline_completed||0} / ${app.timeline_total||0} tasks</strong></div><div class="summary-progress"><div class="progress-line"><i style="width:${pct}%"></i></div><small>${pct}% complete</small></div>
    <div class="detail-links">${app.program_url?`<a href="${esc(app.program_url)}" target="_blank" rel="noopener">Program website ↗</a>`:''} ${app.admission_url?`<a href="${esc(app.admission_url)}" target="_blank" rel="noopener">Admission requirements ↗</a>`:''}</div></section>
    <div class="section-heading"><div><p class="eyebrow">YOUR NEXT STEPS</p><h2>Application timeline</h2></div><button class="button secondary" id="retry">↻ Generate / retry</button></div>
    <div id="timeline" class="timeline">${(app.timeline_items||[]).length?app.timeline_items.map(itemCard).join(''):`<div class="empty-state"><h3>No timeline yet</h3><p class="muted">Generate your checklist from the information available.</p><button class="button primary" id="retry-empty">Generate timeline →</button></div>`}</div>
    <div class="detail-foot"><span class="muted">Changes are saved automatically.</span><button class="text-button danger" id="delete-app">Delete application</button></div>`;
    host.querySelectorAll('.task-check').forEach(el=>el.addEventListener('change',()=>toggleTask(el)));
    host.querySelectorAll('.task-toggle').forEach(el=>el.addEventListener('click',()=>openTask(el.dataset.id)));
    host.querySelectorAll('.save-note').forEach(el=>el.addEventListener('click',()=>saveNote(el.dataset.id)));
    host.querySelectorAll('.upload-file').forEach(el=>el.addEventListener('change',()=>uploadAttachment(el)));
    host.querySelectorAll('.delete-attachment').forEach(el=>el.addEventListener('click',()=>deleteAttachment(el.dataset.id)));
    const retry=async()=>{const b=$('#retry')||$('#retry-empty'); if(b){b.disabled=true;b.textContent='Generating…';} try{await api(`/api/applications/${id}/generate-timeline`,{method:'POST'});await loadDetail();}catch(e){alert(e.message);if(b){b.disabled=false;b.textContent='↻ Generate / retry';}}};
    $('#retry')?.addEventListener('click',retry); $('#retry-empty')?.addEventListener('click',retry);
    $('#delete-app')?.addEventListener('click',async()=>{if(confirm('Delete this application and its timeline?')){await api(`/api/applications/${id}`,{method:'DELETE'});location.href='/';}});
  } catch(e) {host.innerHTML=`<div class="error">Could not load this application: ${esc(e.message)}</div>`;}
}
function itemCard(item) {
  const id=esc(item.id), completed=item.is_completed;
  return `<article class="task-card ${completed?'is-done':''}" id="task-${id}">
    <div class="task-main"><label class="check-wrap"><input class="task-check" type="checkbox" data-id="${id}" ${completed?'checked':''}><span class="custom-check"></span></label>
    <button class="task-toggle" data-id="${id}"><span class="task-date">${dateLabel(item.due_date)} <em>${esc(item.date_type||'unknown')}</em></span><strong>${esc(item.title)}</strong><span class="task-description">${esc(item.description)}</span></button><span class="task-chevron">⌄</span></div>
    <div class="task-workspace" id="workspace-${id}"><div class="workspace-inner"><label>YOUR NOTES<textarea id="note-${id}" rows="4" placeholder="Capture what you found, what is pending, or what you need to ask…"></textarea></label>
    <div class="workspace-actions"><button class="button secondary save-note" data-id="${id}">Save notes</button><label class="button secondary upload-label">＋ Add document<input class="upload-file" data-id="${id}" type="file" hidden></label></div>
    <div class="attachments" id="attachments-${id}"></div><p class="save-status" id="save-status-${id}"></p></div></div></article>`;
}
async function openTask(id) {
  const workspace=$(`#workspace-${CSS.escape(id)}`), card=$(`#task-${CSS.escape(id)}`);
  const isOpen=workspace.classList.toggle('open'); card.classList.toggle('expanded',isOpen);
  if(!isOpen)return;
  try {
    const data=await api(`/api/timeline/${id}`);
    $(`#note-${CSS.escape(id)}`).value=data.workspace?.note||'';
    const attachments=await api(`/api/timeline/${id}/attachments`);
    $(`#attachments-${CSS.escape(id)}`).innerHTML=attachments.map(a=>`<div class="attachment"><a href="${esc(a.url)}" target="_blank" rel="noopener">↗ ${esc(a.filename)}</a><button class="delete-attachment" data-id="${esc(a.id)}">Remove</button></div>`).join('');
    $(`#attachments-${CSS.escape(id)}`).querySelectorAll('.delete-attachment').forEach(b=>b.addEventListener('click',()=>deleteAttachment(b.dataset.id)));
  } catch(e) {$(`#save-status-${CSS.escape(id)}`).textContent=e.message;}
}
async function toggleTask(el) {
  try {await api(`/api/timeline/${el.dataset.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({is_completed:el.checked})});$(`#task-${CSS.escape(el.dataset.id)}`).classList.toggle('is-done',el.checked);}
  catch(e){el.checked=!el.checked;alert(e.message);}
}
async function saveNote(id) {
  const status=$(`#save-status-${CSS.escape(id)}`);
  try {await api(`/api/timeline/${id}/notes`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({note:$(`#note-${CSS.escape(id)}`).value})});status.textContent='Saved.';}
  catch(e){status.textContent=e.message;}
}
async function uploadAttachment(el) {
  if(!el.files.length)return; const id=el.dataset.id, data=new FormData();data.append('file',el.files[0]);
  try {await api(`/api/timeline/${id}/attachments`,{method:'POST',body:data});await openTask(id);$(`#workspace-${CSS.escape(id)}`).classList.add('open');}
  catch(e){alert(e.message);} finally{el.value='';}
}
async function deleteAttachment(id) {
  if(!confirm('Remove this document?'))return;
  try {await api(`/api/attachments/${id}`,{method:'DELETE'});await loadDetail();}
  catch(e){alert(e.message);}
}
loadDashboard();createApplication();loadDetail();
