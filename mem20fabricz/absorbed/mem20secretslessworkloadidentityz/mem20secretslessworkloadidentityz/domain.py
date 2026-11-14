"""Secrets-less workload identity: OIDC/SPIFFE style identity, with estate report."""
from __future__ import annotations
import hashlib, time
from . import ecosystem
__all__=["issue_identity","verify","rotate","identity_health","identity_report","probe","estate_context"]

def issue_identity(workload, issuer="local"):
    return {"workload": workload, "issuer": issuer, "token": hashlib.sha256(f"{workload}{time.time()}".encode()).hexdigest(), "issued_at": time.time(), "expires_at": time.time()+3600}

def verify(identity, now=None):
    now = now or time.time()
    if now > identity.get("expires_at", 0): return {"valid": False, "reason": "expired"}
    return {"valid": True}

def rotate(identity):
    return issue_identity(identity["workload"], identity["issuer"])

def identity_health(identities):
    now=time.time(); valid=sum(1 for i in identities if verify(i, now)["valid"])
    return {"total": len(identities), "valid": valid}

def identity_report():
    i1=issue_identity("api"); i2=issue_identity("worker"); v=verify(i1); rot=rotate(i1); h=identity_health([i1,i2])
    peers={
        "identity_events": ecosystem.identity_events("identity.issued", {"workload":"api","valid":v.get("valid")}),
        "identity_routing": ecosystem.identity_routing("api", ["issue","verify","rotate"]),
        "identity_health_check": ecosystem.identity_health_check(["api","worker"]),
        "verify_containment": ecosystem.verify_containment("api"),
        "rotation_plans": ecosystem.rotation_plans(["issue_new","revoke_old"]),
        "policy_config": ecosystem.policy_config({"issuer":"local","ttl":3600}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and v.get("valid",False),"valid":h["valid"],"rotated":rot["workload"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=identity_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
