"""Reality-to-software compiler: ingest real-world specs into code, with estate report."""
from __future__ import annotations
import re
from . import ecosystem
__all__=["ingest","compile_to_code","validate_spec","diff_spec","compile_health","compiler_report","probe","estate_context"]

def ingest(spec_text):
    out={}
    for line in spec_text.splitlines():
        if ":" in line:
            k,v=line.split(":",1); out[k.strip()]=v.strip()
    return out

def compile_to_code(spec, lang="python"):
    name = spec.get("name", "app")
    if lang == "python": return f"class {name.title()}:\n    pass\n"
    return f"// {name}"

def validate_spec(spec):
    required=["name"]; missing=[r for r in required if r not in spec]
    return {"valid": not missing, "missing": missing}

def diff_spec(old, new):
    changes={}
    for k in set(old)|set(new):
        if old.get(k)!=new.get(k): changes[k]={"from": old.get(k), "to": new.get(k)}
    return changes

def compile_health(spec):
    return {"fields": len(spec), "valid": "name" in spec}

def compiler_report(spec_text=None):
    spec_text = spec_text if spec_text is not None else "name: demo\nkind: service"
    spec=ingest(spec_text); val=validate_spec(spec); code=compile_to_code(spec); health=compile_health(spec)
    peers={
        "software_foundry": ecosystem.software_foundry(spec),
        "config_validation": ecosystem.config_validation(spec),
        "compile_events": ecosystem.compile_events("compile.report", {"name":spec.get("name"),"valid":val.get("valid")}),
        "causal_routing": ecosystem.causal_routing({"complexity":len(spec)}, {"complexity":0.5}),
        "compile_containment": ecosystem.compile_containment(spec.get("name","app")),
        "capability_routing": ecosystem.capability_routing("compiler", ["ingest","validate","codegen"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and val.get("valid",False),"spec_fields":len(spec),"valid":val.get("valid"),"code_len":len(code),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=compiler_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
