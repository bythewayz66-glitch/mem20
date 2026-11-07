const o=document.getElementById('o'), sh=x=>o.textContent=JSON.stringify(x,null,2);
async function api(p,opt){return (await fetch(p,opt)).json()}
document.getElementById('st').onclick=async()=>sh(await api('/status'));
document.getElementById('doc').onclick=async()=>sh(await api('/doctor'));
document.getElementById('go').onclick=async()=>{try{sh(await api('/compose',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({intent:document.getElementById('intent').value,payload:JSON.parse(document.getElementById('p').value)})}))}catch(e){o.textContent=String(e)}};
