const $=(s)=>document.querySelector(s); const state={base:localStorage.getItem('lc_api_base')||''}; $('#api-base').value=state.base; const base=()=>state.base.trim().replace(/\/$/,'');
async function api(path,opts={}){const r=await fetch(base()+path,{headers:{'Content-Type':'application/json'},...opts}); const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.error||r.statusText); return d;}
function toast(m){const t=$('#toast'); t.textContent=m; t.hidden=false; setTimeout(()=>t.hidden=true,2200);}
function stat(k,v){return `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`;}
function renderPeers(peers){$('#peers').innerHTML=Object.entries(peers||{}).map(([k,p])=>`<div class="card"><h3>${k} <span class="${p&&p.ok?'ok':'bad'}">${p&&p.ok?'ok':'err'}</span></h3><p>${JSON.stringify(p,null,2)}</p></div>`).join('')||'<div class="card"><p>No report.</p></div>';}
async function runReport(){try{const d=await api('/api/status',{method:'POST',body:'{}'}); $('#report').textContent=JSON.stringify(d,null,2); renderPeers(d.peers); const ok=Object.values(d.peers||{}).filter(p=>p&&p.ok).length; $('#stats').innerHTML=stat('ok',d.ok)+stat('peers',`${ok}/6`)+stat('stage',d.stage)+stat('ltv',d.ltv);}catch(e){$('#report').textContent=String(e); toast(String(e));}}
async function runDoctor(){try{const d=await api('/api/doctor'); $('#doctor').hidden=false; $('#doctor').textContent=JSON.stringify(d,null,2); toast(d.ok?'Peers reachable':'Degraded');}catch(e){toast(String(e));}}
async function runSim(){try{$('#sim').textContent=JSON.stringify(await api('/api/simulate',{method:'POST'}),null,2); toast('Simulation complete');}catch(e){toast(String(e));}}
async function loadEvents(){try{const d=await api('/api/events'); $('#events').innerHTML=(d.events||[]).map(e=>`<li>${JSON.stringify(e)}</li>`).reverse().join('');}catch(e){}}
$('#api-save').onclick=()=>{state.base=$('#api-base').value.trim(); localStorage.setItem('lc_api_base',state.base); runReport();};
$('#run-report').onclick=runReport; $('#run-doctor').onclick=runDoctor; $('#run-sim').onclick=runSim; $('#refresh-events').onclick=loadEvents;
runReport(); loadEvents();
