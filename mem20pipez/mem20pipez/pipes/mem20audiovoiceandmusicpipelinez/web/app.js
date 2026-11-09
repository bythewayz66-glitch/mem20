const $ = (s) => document.querySelector(s);
const state = { base: localStorage.getItem('avmp_api_base') || '' };
$('#api-base').value = state.base;
function baseUrl(){ const b = state.base.trim().replace(/\/$/, ''); return b; }
async function api(path, opts={}){
  const url = baseUrl() + path;
  const r = await fetch(url, {headers:{'Content-Type':'application/json'}, ...opts});
  const txt = await r.text();
  let data; try{ data = JSON.parse(txt); } catch { data = {raw: txt}; }
  if(!r.ok) throw new Error(data.error || data.message || r.statusText);
  return data;
}
function toast(msg, bad=false){ const t=$('#toast'); t.textContent=msg; t.hidden=false; t.style.borderColor=bad?'#ff7b8a':'#243554'; setTimeout(()=>t.hidden=true, 2600); }
function stat(k,v){ return `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`; }
function renderPeers(peers){
  const el = $('#peers'); el.innerHTML='';
  if(!peers){ el.innerHTML='<div class="card"><p>No report yet.</p></div>'; return; }
  Object.entries(peers).forEach(([k,p])=>{
    const ok = p && p.ok;
    const d = document.createElement('div'); d.className='card';
    d.innerHTML = `<h3>${k} <span class="${ok?'ok':'bad'}">${ok?'ok':'error'}</span></h3><p>${JSON.stringify(p,null,2)}</p>`;
    el.appendChild(d);
  });
}
async function runReport(){
  const fd = new FormData($('#report-form'));
  try{
    const data = await api('/api/status', {method:'POST', body: JSON.stringify({prompt: fd.get('prompt'), bpm: Number(fd.get('bpm')||120)})});
    $('#report').textContent = JSON.stringify(data, null, 2);
    renderPeers(data.peers);
    const peers = data.peers || {};
    const ok = Object.values(peers).filter(p=>p&&p.ok).length;
    $('#stats').innerHTML = stat('overall', data.ok?'<span class="ok">ok</span>':'<span class="warn">degraded</span>') + stat('peers', `${ok}/6`) + stat('export', (data.export&&data.export.format)||'-') + stat('beats', (data.sync&&data.sync.beats)||0);
    toast('Report updated');
  }catch(e){ $('#report').textContent=String(e); toast(String(e), true); }
}
async function runDoctor(){
  try{ const d = await api('/api/doctor'); $('#doctor').hidden=false; $('#doctor').textContent=JSON.stringify(d,null,2); toast(d.ok?'All peers reachable':'Some peers unavailable', !d.ok); }
  catch(e){ toast(String(e), true); }
}
async function runSim(){
  try{ const d = await api('/api/simulate', {method:'POST'}); $('#sim').textContent=JSON.stringify(d,null,2); toast('Simulation complete'); }
  catch(e){ toast(String(e), true); }
}
async function loadEvents(){
  try{ const d = await api('/api/events?limit=50'); const ev=(d.events||d||[]); const ol=$('#events'); ol.innerHTML='';
    (Array.isArray(ev)?ev:[]).slice().reverse().forEach(e=>{ const li=document.createElement('li'); li.textContent=typeof e==='string'?e:JSON.stringify(e); ol.appendChild(li); });
  }catch(e){ /* ignore */ }
}
$('#api-save').addEventListener('click', ()=>{ state.base=$('#api-base').value.trim(); localStorage.setItem('avmp_api_base', state.base); toast('API base set'); runReport(); });
$('#run-report').addEventListener('click', (e)=>{ e.preventDefault(); runReport(); });
$('#run-doctor').addEventListener('click', runDoctor);
$('#run-sim').addEventListener('click', runSim);
$('#refresh-events').addEventListener('click', loadEvents);
$('#mix-form').addEventListener('submit', async (e)=>{
  e.preventDefault();
  try{ const tracks = JSON.parse(new FormData(e.target).get('tracks')); const d = await api('/api/mix',{method:'POST', body: JSON.stringify({tracks})}); $('#ops').textContent=JSON.stringify(d,null,2); toast('Mixed'); }
  catch(err){ toast(String(err), true); }
});
$('#master-form').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const fd=new FormData(e.target);
  try{ const stages=String(fd.get('stages')||'').split(',').map(s=>s.trim()).filter(Boolean); const samples=String(fd.get('samples')||'').split(',').map(Number).filter(n=>!Number.isNaN(n));
    const d=await api('/api/master',{method:'POST', body: JSON.stringify({stages,audio:samples})}); $('#ops').textContent=JSON.stringify(d,null,2); toast('Mastered'); }
  catch(err){ toast(String(err), true); }
});
runReport(); loadEvents(); setInterval(loadEvents, 10000);
