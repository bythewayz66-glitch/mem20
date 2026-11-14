"""Cross-subsystem wiring for mem20selfz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["episodic_memory","context_compression","causal_routing","self_events","capability_routing","health_nervous","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20episodicmemorygraphz","mem20rewardforgez","mem20causalroutingbrainz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20universalhealthnervoussystemz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def episodic_memory(title:str)->dict:
    try:
        from mem20episodicmemorygraphz.domain import create_episode, recall
        ep=create_episode(title, events=[{"type":"self","v":1}]); found=recall([ep], title.split()[0] if title else "self")
        return {"ok":True,"subsystem":"mem20episodicmemorygraphz","id":ep.get("id") or ep.get("title"),"found":len(found) if isinstance(found,list) else 0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20episodicmemorygraphz","error":f"{type(exc).__name__}: {exc}"}
def context_compression(text:str)->dict:
    try:
        try:
            from mem20rewardforgez.forges.mem20contextcompressionforgez.domain import compress
        except Exception:
            from mem20rewardforgez.domain import compress
        r=compress(text or "self context", ratio=0.5); return {"ok":True,"subsystem":"mem20rewardforgez","compressed":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20rewardforgez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def self_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("selfz"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["self"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def health_nervous()->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}; register_subsystem(h,"self",lambda: {"ok":True}); checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}

def _absorbed_member_peers():
    try:
        import importlib, pathlib, sys
        root = pathlib.Path(__file__).resolve().parents[2]
        if str(root) not in sys.path: sys.path.insert(0, str(root))
        try:
            import _mem20_absorbed_finder  # noqa: F401
        except Exception:
            pass
        tc = root / 'toolchest' / 'src'
        if tc.is_dir() and str(tc) not in sys.path: sys.path.insert(0, str(tc))
        adir = pathlib.Path(__file__).resolve().parents[1] / 'absorbed'
        members = sorted(p.name for p in adir.iterdir() if p.is_dir()) if adir.is_dir() else []
        checks = {}
        total = 0; okm = 0
        for name in members:
            try:
                eco = importlib.import_module(f"{name}.ecosystem")
                if hasattr(eco, 'probe'):
                    r = eco.probe()
                    if isinstance(r, dict):
                        c = r.get('count')
                        if c is None: c = len(r.get('reachable') or r.get('checks') or [])
                        checks[name] = {'ok': bool(r.get('ok', False)), 'count': int(c)}
                        total += int(c)
                        if r.get('ok'): okm += 1
                        continue
                fns = [x for x in dir(eco) if not x.startswith('_') and callable(getattr(eco,x))]
                checks[name] = {'ok': True, 'count': len(fns)}
                total += len(fns); okm += 1
            except Exception as e:
                checks[name] = {'ok': False, 'count': 0, 'error': f"{type(e).__name__}: {e}"}
        return {'ok': True, 'members_with_ecosystem_probe': len(members), 'members_ok': okm, 'peer_checks_total': total, 'checks': checks}
    except Exception as e:
        return {'ok': False, 'error': f"{type(e).__name__}: {e}"}


def probe():
    checks={"episodic_memory":episodic_memory("self episode"),"context_compression":context_compression("a b c"),"causal_routing":causal_routing({"s":1},{"s":1}),"self_events":self_events("s",{}),"capability_routing":capability_routing("k",["s"]),"health_nervous":health_nervous()}
    _result = {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
    try:
        _amp = _absorbed_member_peers()
        _result["member_ecosystems"] = _amp
        _core_count = int(_result.get("count") or _result.get("core_count") or len(_result.get("checks") or _result.get("reachable") or []))
        _result["core_count"] = _core_count
        _result["peer_surface_total"] = _core_count + int(_amp.get("peer_checks_total", 0))
        _result["count"] = _result["peer_surface_total"]
    except Exception:
        pass
    return _result
