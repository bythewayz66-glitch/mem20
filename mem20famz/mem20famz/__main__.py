"""CLI: inspect the family registry."""
import argparse, json, sys
from . import families, members, purpose, family_of, spec, stats, orphans, unmapped


def main(argv=None):
    p = argparse.ArgumentParser(prog="mem20famz")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    sub.add_parser("families")
    f = sub.add_parser("members"); f.add_argument("family")
    q = sub.add_parser("which"); q.add_argument("package")
    s = sub.add_parser("spec"); s.add_argument("package")
    sub.add_parser("orphans")
    sub.add_parser("unmapped")
    sub.add_parser("json")
    a = p.parse_args(argv)

    if a.cmd == "stats": out = stats()
    elif a.cmd == "families": out = families()
    elif a.cmd == "members": out = members(a.family)
    elif a.cmd == "which": out = family_of(a.package)
    elif a.cmd == "spec": out = spec(a.package)
    elif a.cmd == "orphans": out = orphans()
    elif a.cmd == "unmapped": out = unmapped()
    else: out = {"families": {f: {"purpose": purpose(f), "members": members(f)} for f in families()},
                 "stats": stats()}
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
