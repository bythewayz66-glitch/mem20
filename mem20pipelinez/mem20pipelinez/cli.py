"""Crew runtime CLI (legacy flags + depth subcommands)."""
from __future__ import annotations
import argparse, json, sys
from typing import Optional, Sequence
from . import MEMBERS, __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mem20pipelinez", description="mem20 production pipeline runtime for game-maker and software pipelines.")
    parser.add_argument("--version", action="store_true", help="Print the version and exit.")
    parser.add_argument("--members", action="store_true", help="List member systems and exit.")
    parser.add_argument("--store", help="Store path override.")
    sub = parser.add_subparsers(dest="cmd")
    s=sub.add_parser("serve"); s.add_argument("--host",default="127.0.0.1"); s.add_argument("--port",type=int,default=8855)
    sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("simulate")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Legacy behavior preserved
    if getattr(args,"version",False):
        print(f"mem20pipelinez {__version__}")
        if not getattr(args,"cmd",None) and not getattr(args,"members",False): return 0
    if getattr(args,"members",False):
        for member in MEMBERS: print(member)
        if not getattr(args,"cmd",None): return 0
    cmd = getattr(args,"cmd",None)
    if cmd is None:
        return 0
    from .runtime import Service, serve
    svc = Service(getattr(args,"store",None))
    if cmd=="serve": serve(args.host,args.port,getattr(args,"store",None))
    elif cmd=="status": print(json.dumps(svc.status(),indent=2,default=str))
    elif cmd=="doctor": print(json.dumps(svc.doctor(),indent=2,default=str))
    elif cmd=="simulate": print(json.dumps(svc.simulate(),indent=2,default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
