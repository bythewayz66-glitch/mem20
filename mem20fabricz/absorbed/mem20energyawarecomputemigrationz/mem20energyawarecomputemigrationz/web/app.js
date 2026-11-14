async function api(p,o){const r=await fetch(p,Object.assign({headers:{'Content-Type':'application/json'}},o||{}));const t=await r.text();try{return JSON.parse(t)}catch{return {raw:t}}}
function v(id){return document.getElementById(id).value} function show(id,x){document.getElementById(id).textContent=typeof x==='string'?x:JSON.stringify(x,null,2)}
async function refresh(){const [s,n,w]=await Promise.all([api('/api/status'),api('/api/nodes'),api('/api/workloads')]); show('status',s.summary||s); show('nodes',n.nodes||n); show('wls',w.workloads||w)}
document.getElementById('refresh').onclick=refresh;
document.getElementById('doctor').onclick=async()=>show('out',await api('/api/doctor'));
document.getElementById('simulate').onclick=async()=>show('out',await api('/api/simulate',{method:'POST',body:'{}'}));
document.getElementById('addNode').onclick=async()=>{show('out',await api('/api/nodes',{method:'POST',body:JSON.stringify({node_id:v('nid'),power_watts:Number(v('np')),speed:Number(v('ns')),energy_rate:Number(v('nr')),carbon_g_per_kwh:Number(v('nc')),renewable_pct:Number(v('nre'))})})); refresh()};
document.getElementById('addWl').onclick=async()=>{show('out',await api('/api/workloads',{method:'POST',body:JSON.stringify({workload_id:v('wid'),size:Number(v('ws')),current_node:v('wcn')||null})})); refresh()};
document.getElementById('mig').onclick=async()=>{show('out',await api('/api/migrate',{method:'POST',body:JSON.stringify({workload_id:v('wid'),target_node:v('wto')||null})})); refresh()};
document.getElementById('plan').onclick=async()=>{show('out',await api('/api/plan',{method:'POST',body:'{}'}))};
refresh().catch(e=>show('status',String(e)));
