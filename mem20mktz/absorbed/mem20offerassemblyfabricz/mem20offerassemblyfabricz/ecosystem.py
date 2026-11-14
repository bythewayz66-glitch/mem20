"""Cross-subsystem wiring for mem20offerassemblyfabricz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["deal_desk","bundle_engine","plg_sim","revenue_check","offer_events","offer_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomousdealdeskz","mem20servicebundlingenginez","mem20simz","mem20revenueleakhunterz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def deal_desk()->dict:
    try:
        from mem20autonomousdealdeskz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20autonomousdealdeskz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousdealdeskz","error":f"{type(exc).__name__}: {exc}"}
def bundle_engine()->dict:
    try:
        from mem20servicebundlingenginez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20servicebundlingenginez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20servicebundlingenginez","error":f"{type(exc).__name__}: {exc}"}
def plg_sim()->dict:
    try:
        from mem20simz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20simz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def revenue_check()->dict:
    try:
        from mem20revenueleakhunterz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20revenueleakhunterz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20revenueleakhunterz","error":f"{type(exc).__name__}: {exc}"}
def offer_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish as es_publish,throughput
        s=create_stream("offers"); es_publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def offer_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["offer"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"deal_desk":deal_desk(),"bundle_engine":bundle_engine(),"plg_sim":plg_sim(),"revenue_check":revenue_check(),"offer_events":offer_events("o",{}),"offer_routing":offer_routing("k",["o"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
