const o=document.getElementById('o'), sh=x=>o.textContent=JSON.stringify(x,null,2);
document.getElementById('doc').onclick=async()=>{try{sh(await (await fetch('/doctor')).json())}catch(e){o.textContent=String(e)}};
document.getElementById('st').onclick=async()=>{try{sh(await (await fetch('/status')).json())}catch(e){o.textContent=String(e)}};
