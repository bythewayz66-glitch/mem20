async function api(p,o){const r=await fetch(p,Object.assign({headers:{'Content-Type':'application/json'}},o||{}));const t=await r.text();try{return JSON.parse(t)}catch{return {raw:t}}}
const v=i=>document.getElementById(i).value, sh=(i,x)=>document.getElementById(i).textContent=JSON.stringify(x,null,2);
async function ref(){sh('st',await api('/api/status')); sh('eps',(await api('/api/episodes')).episodes)}
document.getElementById('r').onclick=ref; document.getElementById('d').onclick=async()=>sh('out',await api('/api/doctor'));
document.getElementById('g').onclick=async()=>sh('out',await api('/api/graph'));
document.getElementById('s').onclick=async()=>sh('out',await api('/api/simulate',{method:'POST',body:'{}'}));
document.getElementById('c').onclick=async()=>{sh('out',await api('/api/episodes',{method:'POST',body:JSON.stringify({title:v('t')})})); ref()};
document.getElementById('rec').onclick=async()=>sh('out',await api('/api/recall',{method:'POST',body:JSON.stringify({query:v('q')})}));
ref().catch(e=>sh('st',String(e)));
