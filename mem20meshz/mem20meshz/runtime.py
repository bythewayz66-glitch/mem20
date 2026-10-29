from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

# Ensure sub-runtimes importable
ROOT = Path(__file__).resolve().parent.parent.parent
for sub in [
    "mem20crisisresponsemeshz",
    "mem20crossdevicememorymeshz",
    "mem20federatedmodellearningmeshz",
    "mem20nearbydevicemeshz",
    "mem20offlineresiliencemeshz",
    "mem20selfhealingconnectormeshz",
]:
    p = ROOT / sub
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import mem20crisisresponsemeshz as m_crisis
import mem20crossdevicememorymeshz as m_cross
import mem20federatedmodellearningmeshz as m_fed
import mem20nearbydevicemeshz as m_nearby
import mem20offlineresiliencemeshz as m_offline
import mem20selfhealingconnectormeshz as m_heal

MESHES = {
    "crisis": m_crisis,
    "crossdevice": m_cross,
    "federated": m_fed,
    "nearby": m_nearby,
    "offline": m_offline,
    "selfhealing": m_heal,
}

def _load_engine(mod):
    cfg = mod.load_config(str(Path(mod.__file__).resolve().parent.parent / "CAPABILITY.json"))
    return mod.Engine(cfg)

class MasterEngine:
    def __init__(self):
        self.engines = {name: _load_engine(mod) for name, mod in MESHES.items()}

    def inspect(self):
        return {name: eng.metrics_snapshot() if hasattr(eng, "metrics_snapshot") else {"ok": True} for name, eng in self.engines.items()}

    def execute(self, request, only=None):
        targets = [only] if only else list(self.engines)
        out = {}
        for name in targets:
            try:
                out[name] = self.engines[name].execute(dict(request))
            except Exception as e:
                out[name] = {"error": type(e).__name__, "message": str(e)}
        return {"mesh": "mem20meshz", "results": out}

    def simulate(self):
        out = {}
        for name, eng in self.engines.items():
            try:
                out[name] = eng.simulator()
            except Exception as e:
                out[name] = {"error": type(e).__name__, "message": str(e)}
        return out

    def benchmark(self, n=50):
        out = {}
        for name, eng in self.engines.items():
            try:
                out[name] = eng.benchmark(n)
            except Exception as e:
                out[name] = {"error": type(e).__name__, "message": str(e)}
        return out

    def signature_modes(self):
        out = {}
        for name, eng in self.engines.items():
            try:
                if hasattr(eng, "signature_mode"):
                    out[name] = eng.signature_mode(enabled=True)
                else:
                    out[name] = {"enabled": False}
            except Exception as e:
                out[name] = {"error": str(e)}
        return out

def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem20meshz", description="mem20 mesh gold runtime — orchestrates all 6 mesh runtimes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    # delegate subcommands
    p = sub.add_parser("list", help="list sub-meshes")
    p = sub.add_parser("simulate", help="run all simulators")
    p = sub.add_parser("benchmark", help="benchmark all"); p.add_argument("--runs", type=int, default=50)
    p = sub.add_parser("execute"); p.add_argument("json", nargs="?", default="{}"); p.add_argument("--only", default=None)
    p = sub.add_parser("signatures", help="enable all signature modes")
    # per-mesh passthrough
    for name in MESHES:
        pp = sub.add_parser(name, help=f"run {name} mesh CLI")
        pp.add_argument("args", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    eng = MasterEngine()
    if args.cmd == "list":
        print(json.dumps(list(MESHES), indent=2))
    elif args.cmd == "simulate":
        print(json.dumps(eng.simulate(), indent=2))
    elif args.cmd == "benchmark":
        print(json.dumps(eng.benchmark(args.runs), indent=2))
    elif args.cmd == "execute":
        print(json.dumps(eng.execute(json.loads(args.json), args.only), indent=2))
    elif args.cmd == "signatures":
        print(json.dumps(eng.signature_modes(), indent=2))
    elif args.cmd in MESHES:
        mod = MESHES[args.cmd]
        # delegate
        mod.main(list(args.args))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

def load_config(path=None):
    if path is None:
        path = str(Path(__file__).resolve().parent.parent / "CAPABILITY.json")
    return json.loads(Path(path).read_text())
