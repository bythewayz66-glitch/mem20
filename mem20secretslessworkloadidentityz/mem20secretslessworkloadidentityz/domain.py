"""Secrets-less workload identity: OIDC/SPIFFE style identity."""
import hashlib, time


def issue_identity(workload, issuer="local"):
    return {"workload": workload, "issuer": issuer, "token": hashlib.sha256(f"{workload}{time.time()}".encode()).hexdigest(), "issued_at": time.time(), "expires_at": time.time()+3600}


def verify(identity, now=None):
    now = now or time.time()
    if now > identity.get("expires_at", 0):
        return {"valid": False, "reason": "expired"}
    return {"valid": True}


def rotate(identity):
    new = issue_identity(identity["workload"], identity["issuer"])
    return new


def identity_health(identities):
    now = time.time()
    valid = sum(1 for i in identities if verify(i, now)["valid"])
    return {"total": len(identities), "valid": valid}
