#!/usr/bin/env python3
"""Settling command for the partition / audit / promotion-gate rows (A1-A8, PG1-PG6)
in docs/gtm/claim-ledger.md.

Runs against a throwaway store. Requires the repo root on sys.path and the
engine importable (`pip install -r requirements.txt`).

Usage:
    MEM20_STORE_PATH=/tmp/mem20-gtm-$(date +%s) python3 docs/gtm/verify/partition.py
"""
import inspect
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)

from memory_engine import memory as M  # noqa: E402


def main():
    print("=== signatures (the harness must match these) ===")
    for name in ("remember", "remember_simulated", "recall",
                 "audit_contamination", "promote_simulated_to_grounded"):
        print("%s%s" % (name, inspect.signature(getattr(M, name))))
    print()

    g = M.remember("gtm", "grounded fact: the sky was blue on day one",
                   epistemic_status="observed")
    print("A1 grounded write -> origin=%s store=%s action=%s"
          % (g.get("origin"), g.get("store"), g.get("action")))

    try:
        M.remember("gtm", "should be refused", epistemic_status="observed",
                   _allow_simulated=True)
        print("A2 -> NO REFUSAL (unexpected)")
    except Exception as e:
        print("A2 -> %s: %s" % (type(e).__name__, e))

    s = M.remember_simulated("gtm", "simulated hypothesis: the sky is green")
    print("A3 simulated write -> origin=%s store=%s epistemic_status=%s"
          % (s.get("origin"), s.get("store"), s.get("epistemic_status")))
    sid = s.get("id")

    r4 = M.recall(topic="gtm", k=10)
    print("A4 recall() -> %s n=%d origins=%s stores=%s"
          % (type(r4).__name__, len(r4),
             sorted({x.get("origin") for x in r4}),
             sorted({x.get("store") for x in r4})))
    r5 = M.recall(topic="gtm", k=10, include_simulated=True)
    print("A5 recall(include_simulated=True) -> n=%d origins=%s stores=%s"
          % (len(r5), sorted({x.get("origin") for x in r5}),
             sorted({x.get("store") for x in r5})))

    a = M.audit_contamination(actor="gtm")
    vkeys = [k for k in a if k.startswith("violations_")]
    print("A6 audit -> contamination_rate=%s status=%s violation_classes=%d"
          % (a.get("contamination_rate"), a.get("status"), len(vkeys)))
    for k in vkeys:
        print("     %s => %s" % (k, a[k]))

    try:
        M.remember("gtm", "no status given")
        print("A7 -> ACCEPTED (unexpected)")
    except Exception as e:
        print("A7 -> %s: %s" % (type(e).__name__, e))

    print()
    print("=== promotion gate ===")

    def pg(label, **kw):
        try:
            r = M.promote_simulated_to_grounded(sid, **kw)
            print("%s -> PROMOTED: %s" % (label, json.dumps(r, default=str)[:300]))
        except Exception as e:
            print("%s -> REFUSED: %s: %s" % (label, type(e).__name__, e))

    pg("PG1 bare sim_id")
    pg("PG2 bool+note", resolved_via_prediction_error=True,
       resolution_note="the model predicted rain, it was sunny")
    pg("PG3 structured unrecorded ref", resolved_via_prediction_error=True,
       resolution_note="prediction error noted",
       prediction_error_evidence={"prediction_ref": "pred-does-not-exist",
                                  "observed_outcome": "sunny"})
    pg("PG4 free-text confirmation alone", confirmation="I confirm this is true")
    pg("PG5 whitespace confirmation", confirmation="   ")
    pg("PG6 resolution_note alone", resolution_note="just a note")

    a2 = M.audit_contamination(actor="gtm")
    print()
    print("A8 audit after gate -> contamination_rate=%s status=%s"
          % (a2.get("contamination_rate"), a2.get("status")))


if __name__ == "__main__":
    main()
