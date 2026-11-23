"""CLI for mem20prez."""
from __future__ import annotations
import argparse, json, sys
from . import domain

def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem20prez")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--topic")
    p.add_argument("--history", nargs="*", default=[])
    p.add_argument("-k", type=int, default=8)
    sub.add_parser("status")
    sub.add_parser("doctor")
    r = sub.add_parser("record")
    r.add_argument("--topic", required=True)
    r.add_argument("--returned", nargs="*", default=[])
    o = sub.add_parser("outcome")
    o.add_argument("--id", required=True)
    o.add_argument("--useful", type=int, choices=[0, 1], required=True)
    o.add_argument("--facts", nargs="*", default=[])
    args = ap.parse_args(argv)
    eng = domain.get_engine()
    if args.cmd == "predict":
        preds = eng.predict_next(context_topic=args.topic, history=args.history or None, k=args.k)
        print(json.dumps([{"topic": p.topic, "score": p.score, "reason": p.reason} for p in preds], indent=2))
    elif args.cmd == "status":
        print(json.dumps(domain.recall_report(), indent=2, default=str))
    elif args.cmd == "doctor":
        print(json.dumps(domain.probe(), indent=2, default=str))
    elif args.cmd == "record":
        facts = [{"id": f"auto-{i}", "topic": t} for i, t in enumerate(args.returned)]
        eid = eng.record_recall_event(context_topic=args.topic, returned_facts=facts)
        print(json.dumps({"ok": True, "event_id": eid}))
    elif args.cmd == "outcome":
        oid = eng.record_outcome(args.id, args.facts, bool(args.useful))
        print(json.dumps({"ok": True, "outcome_id": oid}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
