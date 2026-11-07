async function api(p,o){const r=await fetch(p,Object.assign({headers:{'Content-Type':'application/json'}},o||{}));const t=await r.text();try{return JSON.parse(t)}catch{return {raw:t}}}
function v(id){return document.getElementById(id).value} function sh(id,x){document.getElementById(id).textContent=typeof x==='string'?x:JSON.stringify(x,null,2)}
async function refresh(){sh('status',await api('/api/status'))}
document.getElementById('refresh').onclick=refresh;
document.getElementById('doctor').onclick=async()=>sh('out',await api('/api/doctor'));
document.getElementById('members').onclick=async()=>sh('membersOut',await api('/api/members'));
document.getElementById('simulate').onclick=async()=>sh('out',await api('/api/simulate',{method:'POST',body:'{}'}));
document.getElementById('plan').onclick=async()=>sh('out',await api('/api/plan',{method:'POST',body:JSON.stringify({intent:v('intent')})}));
refresh().catch(e=>sh('status',String(e)));
