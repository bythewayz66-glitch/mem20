const o=document.getElementById('o'); const sh=x=>o.textContent=JSON.stringify(x,null,2);
async function api(p,opt){const r=await fetch(p,opt);return r.json()}
document.getElementById('go').onclick=async()=>{try{sh(await api('/execute',{method:'POST',headers:{'content-type':'application/json'},body:document.getElementById('p').value}))}catch(e){o.textContent=String(e)}};
document.getElementById('spec').onclick=async()=>sh(await api('/spec'));
document.getElementById('met').onclick=async()=>sh(await api('/metrics'));
document.getElementById('sim').onclick=async()=>sh(await api('/execute',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({xp:10,agents:[{value:5,effort:3,ethical_score:0.8}],rounds:3})}));
