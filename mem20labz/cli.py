"""mem20labz CLI — real lab runtime control surface."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from . import MEMBERS, __version__
from .runtime import LabRuntime


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mem20labz", description="mem20 laboratory runtime control plane.")
    p.add_argument("--version", action="store_true", help="Print the version and exit.")
    p.add_argument("--members", action="store_true", help="List member systems and exit.")
    p.add_argument("--db", help="SQLite DB path for durable run history.")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("status", help="Runtime status.")
    sub.add_parser("registry", help="Member registry.")

    pp = sub.add_parser("probe", help="Probe a member or all members.")
    pp.add_argument("member", nargs="?", help="Member name (omit for all).")

    sp = sub.add_parser("simulate", help="Run simulation/probe operation on member(s).")
    sp.add_argument("member", nargs="?", help="Member name (omit for all).")

    sub.add_parser("signals", help="Run 6-peer ecosystem signal checks.")

    hp = sub.add_parser("history", help="Show durable run history.")
    hp.add_argument("--limit", type=int, default=20)

    sv = sub.add_parser("serve", help="Serve HTTP/JSON API and web frontend.")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8841)

    return p


def _emit(obj):
    print(json.dumps(obj, indent=2, default=str))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    # backward-compatible flags
    if args.version and not args.cmd:
        print(f"mem20labz {__version__}")
        if not args.members:
            return 0
    if args.members and not args.cmd:
        if not args.version:
            pass
        for member in MEMBERS:
            print(member)
        return 0
    if args.version or args.members:
        return 0

    rt = LabRuntime(db_path=getattr(args, "db", None))
    cmd = args.cmd or "status"
    if cmd == "status":
        _emit(rt.status())
    elif cmd == "registry":
        _emit(rt.registry())
    elif cmd == "probe":
        _emit(rt.probe(getattr(args, "member", None)))
    elif cmd == "simulate":
        _emit(rt.simulate(getattr(args, "member", None)))
    elif cmd == "signals":
        _emit(rt.signals())
    elif cmd == "history":
        _emit(rt.history(getattr(args, "limit", 20)))
    elif cmd == "serve":
        from .server import serve
        httpd = serve(args.host, args.port, db_path=getattr(args, "db", None))
        print(f"http://{args.host}:{args.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
    else:
        build_parser().print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
