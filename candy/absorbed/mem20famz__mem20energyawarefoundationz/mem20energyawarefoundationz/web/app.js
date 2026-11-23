async function api(p,o){const r=await fetch(p,Object.assign({headers:{'Content-Type':'application/json'}},o||{}));return r.json()}
function v(i){return document.getElementById(i).value} function sh(i,x){document.getElementById(i).textContent=JSON.stringify(x,null,2)}
async function ref(){const s=await api('/api/status'); sh('st',s.evaluation?.result||s); sh('dev', (await api('/api/devices')).devices)}
document.getElementById('r').onclick=ref; document.getElementById('d').onclick=async()=>sh('out',await api('/api/doctor')); document.getElementById('s').onclick=async()=>sh('out',await api('/api/simulate',{method:'POST',body:'{}'}));
document.getElementById('ad').onclick=async()=>{sh('out',await api('/api/devices',{method:'POST',body:JSON.stringify({device_id:v('id'),power_watts:Number(v('w'))})})); ref()};
document.getElementById('pol').onclick=async()=>sh('out',await api('/api/policies',{method:'POST',body:JSON.stringify({policy_id:'default',budget_watts:Number(v('b')),default_threshold_watts:Number(v('th'))})}));
document.getElementById('ev').onclick=async()=>sh('out',await api('/api/evaluate',{method:'POST',body:'{}'}));
ref().catch(e=>sh('st',String(e)));
