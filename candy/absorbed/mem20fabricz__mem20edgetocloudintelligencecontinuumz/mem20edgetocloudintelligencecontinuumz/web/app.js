async function api(path, opts={}) {
  const res = await fetch(path, {headers: {'Content-Type':'application/json'}, ...opts});
  const text = await res.text();
  let data; try { data = JSON.parse(text); } catch { data = {raw:text}; }
  if (!res.ok) throw Object.assign(new Error(data.error || res.statusText), {data, status:res.status});
  return data;
}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]))}
function show(data){document.getElementById('output').textContent = typeof data==='string'?data:JSON.stringify(data,null,2)}
function formObj(form){const o={}; for(const [k,v] of new FormData(form).entries()) if(v!=='') o[k]=v; for(const k of ['cpu','memory_gb','latency_ms','cost_per_cpu_hour','egress_cost_per_gb','reliability','duration_s','size_mb','max_latency_ms','max_cost','priority']) if(o[k]!=null) o[k]=Number(o[k]); return o}
async function refresh(){
  try{
    const [status, targets, workloads, events] = await Promise.all([
      api('/api/status'), api('/api/targets'), api('/api/workloads'), api('/api/events?limit=50')]);
    const h=status.health||{};
    document.getElementById('healthCards').innerHTML = [
      ['Health', h.health], ['Targets', `${h.online||0}/${h.targets||0} online`], ['Util', h.cpu_utilisation],
      ['Queued', h.queued], ['Running', h.running], ['Migrating', h.migrating], ['Failed', h.failed]
    ].map(([k,v])=>`<div class="card"><div class="k">${esc(k)}</div><div class="v">${esc(typeof v==='number'?v.toFixed? (Number.isInteger(v)?v:v.toFixed(3)):v:v)}</div></div>`).join('');
    renderTargets(targets.targets||[]);
    renderWorkloads(workloads.workloads||[]);
    document.getElementById('events').textContent = JSON.stringify(events.events||[],null,2);
  }catch(e){show({ok:false,error:e.message,data:e.data})}
}
function renderTargets(rows){
  if(!rows.length){document.getElementById('targets').innerHTML='<p class="sub">No targets.</p>';return}
  document.getElementById('targets').innerHTML = `<table><thead><tr><th>id</th><th>tier</th><th>status</th><th>cpu</th><th>lat/cost</th><th>caps</th><th></th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.target_id)}</td><td>${esc(r.tier)}</td><td><span class="pill ${r.status==='online'?'ok':r.status==='offline'?'bad':'warn'}">${esc(r.status)}</span></td><td>${esc(r.used_cpu)}/${esc(r.cpu)}</td><td>${esc(r.latency_ms)}ms / ${esc(r.cost_per_cpu_hour)}</td><td>${esc((r.capabilities||[]).join(','))}</td><td><button data-act="offline" data-id="${esc(r.target_id)}">offline</button> <button data-act="online" data-id="${esc(r.target_id)}">online</button> <button data-act="del" data-id="${esc(r.target_id)}">del</button></td></tr>`).join('')}</tbody></table>`;
  document.querySelectorAll('#targets button').forEach(b=>b.onclick=async()=>{
    try{ if(b.dataset.act==='del') show(await api('/api/targets/'+b.dataset.id,{method:'DELETE'})); else show(await api(`/api/targets/${b.dataset.id}/status`,{method:'POST',body:JSON.stringify({status:b.dataset.act})})); refresh(); }catch(e){show(e.data||e.message)}
  });
}
function renderWorkloads(rows){
  if(!rows.length){document.getElementById('workloads').innerHTML='<p class="sub">No workloads.</p>';return}
  document.getElementById('workloads').innerHTML = `<table><thead><tr><th>id</th><th>state</th><th>target</th><th>cpu/pri</th><th>constraints</th><th></th></tr></thead><tbody>${rows.map(r=>`<tr><td>${esc(r.workload_id)}</td><td>${esc(r.state)}</td><td>${esc(r.assigned_target||'')}</td><td>${esc(r.cpu)}/${esc(r.priority)}</td><td>${esc(r.privacy_zone)} ${r.max_latency_ms??''} ${r.max_cost??''}</td><td><button data-act="dispatch" data-id="${esc(r.workload_id)}">dispatch</button> <button data-act="failover" data-id="${esc(r.workload_id)}">failover</button> <button data-act="complete" data-id="${esc(r.workload_id)}">done</button></td></tr>`).join('')}</tbody></table>`;
  document.querySelectorAll('#workloads button').forEach(b=>b.onclick=async()=>{
    try{
      if(b.dataset.act==='dispatch') show(await api('/api/dispatch',{method:'POST',body:JSON.stringify({workload_id:b.dataset.id})}));
      else if(b.dataset.act==='failover') show(await api('/api/failover',{method:'POST',body:JSON.stringify({workload_id:b.dataset.id})}));
      else show(await api('/api/complete',{method:'POST',body:JSON.stringify({workload_id:b.dataset.id,success:true,reason:'ui'})}));
      refresh();
    }catch(e){show(e.data||e.message)}
  });
}
document.getElementById('refresh').onclick=refresh;
document.getElementById('runSim').onclick=async()=>{try{show(await api('/api/simulate',{method:'POST',body:'{}'}));refresh()}catch(e){show(e.data||e.message)}};
document.getElementById('runDoctor').onclick=async()=>{try{show(await api('/api/doctor'))}catch(e){show(e.data||e.message)}};
document.getElementById('dispatchAll').onclick=async()=>{try{show(await api('/api/dispatch',{method:'POST',body:'{}'}));refresh()}catch(e){show(e.data||e.message)}};
document.getElementById('targetForm').onsubmit=async e=>{e.preventDefault(); try{show(await api('/api/targets',{method:'POST',body:JSON.stringify(formObj(e.target))})); e.target.reset(); refresh()}catch(err){show(err.data||err.message)}};
document.getElementById('workloadForm').onsubmit=async e=>{e.preventDefault(); try{show(await api('/api/workloads',{method:'POST',body:JSON.stringify(formObj(e.target))})); e.target.reset(); refresh()}catch(err){show(err.data||err.message)}};
refresh();
