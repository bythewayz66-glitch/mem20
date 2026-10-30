from __future__ import annotations
import argparse, json, sys, tempfile, pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
# Engine-based adaptive modules
for sub in [
    "mem20adaptiveachievementenginez",
    "mem20adaptiveforgettingenginez",
    "mem20adaptiveinferencemarketplacez",
    "mem20adaptivepersonalityruntimez",
    "mem20adaptivepricingbrainz",
]:
    p = ROOT / sub
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))
# interfacecomposer uses src/ layout
ic = ROOT / "mem20adaptiveinterfacecomposerz"
ic_src = ic / "src"
if ic_src.is_dir() and str(ic_src) not in sys.path:
    sys.path.insert(0, str(ic_src))

import mem20adaptiveachievementenginez as m_ach
import mem20adaptiveforgettingenginez as m_forget
import mem20adaptiveinferencemarketplacez as m_infer
import mem20adaptivepersonalityruntimez as m_pers
import mem20adaptivepricingbrainz as m_price
import mem20adaptiveinterfacecomposerz as m_ic

ADAPTIVES = {
    "achievement": m_ach,
    "forgetting": m_forget,
    "inferencemarketplace": m_infer,
    "personality": m_pers,
    "pricingbrainz": m_price,
}


def _load_engine(mod):
    cfg_path = Path(mod.__file__).resolve().parent.parent / "CAPABILITY.json"
    cfg = mod.load_config(str(cfg_path))
    return mod.Engine(cfg)


class InterfaceComposerAdapter:
    """Adapter exposing Engine-like interface for interfacecomposer."""
    def __init__(self):
        self.mod = m_ic

    def execute(self, request):
        from mem20adaptiveinterfacecomposerz.model import UserIntent
        from mem20adaptiveinterfacecomposerz.runtime import InterfaceComposerRuntime, RuntimeConfig
        with tempfile.TemporaryDirectory() as d:
            rt = InterfaceComposerRuntime(RuntimeConfig(db_path=str(pathlib.Path(d)/"db.sqlite")))
            try:
                intent = UserIntent(request.get("text") or request.get("task") or "search my files")
                res = rt.compose(intent)
                return {"composed": res, "ok": True}
            finally:
                rt.close()

    def simulator(self):
        from mem20adaptiveinterfacecomposerz.simulator import run_scenario
        out = {}
        for name in ["success","malformed_input","disconnection","overload","provider_loss","restart_recovery"]:
            try:
                out[name] = run_scenario(name)
                if not isinstance(out[name], dict):
                    out[name] = {"ok": True}
                else:
                    out[name].setdefault("ok", True)
            except Exception as e:
                out[name] = {"ok": False, "error": str(e)}
        return out

    def benchmark(self, n=20):
        from mem20adaptiveinterfacecomposerz.benchmark import benchmark as _b
        return _b(runs=n)

    def signature_mode(self, enabled=False):
        if not enabled:
            return {"enabled": False, "note": "opt-in only"}
        return {"enabled": True, "behavior": "Adaptive interfaces compose themselves to the user and task", "formed_in_seconds": 1, "opt_in": True}


class MasterEngine:
    def __init__(self):
        self.engines = {name: _load_engine(mod) for name, mod in ADAPTIVES.items()}
        self.engines["interfacecomposer"] = InterfaceComposerAdapter()

    def inspect(self):
        return {name: (eng.metrics_snapshot() if hasattr(eng, "metrics_snapshot") else {"ok": True}) for name, eng in self.engines.items()}

    def execute(self, request, only=None):
        targets = [only] if only else list(self.engines)
        out = {}
        for name in targets:
            try:
                out[name] = self.engines[name].execute(dict(request))
            except Exception as e:
                out[name] = {"error": type(e).__name__, "message": str(e)}
        return {"adapt": "mem20adaptz", "results": out}

    def simulate(self):
        out = {}
        for name, eng in self.engines.items():
            try:
                out[name] = eng.simulator()
            except Exception as e:
                out[name] = {"error": type(e).__name__, "message": str(e)}
        return out

    def benchmark(self, n=20):
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


def load_config(path=None):
    if path is None:
        path = str(Path(__file__).resolve().parent.parent / "CAPABILITY.json")
    return json.loads(Path(path).read_text())


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem20adaptz", description="mem20 adapt gold runtime — orchestrates all 6 adaptive runtimes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("simulate")
    p = sub.add_parser("benchmark"); p.add_argument("--runs", type=int, default=20)
    p = sub.add_parser("execute"); p.add_argument("json", nargs="?", default="{}"); p.add_argument("--only", default=None)
    sub.add_parser("signatures")
    for name in list(ADAPTIVES) + ["interfacecomposer"]:
        pp = sub.add_parser(name)
        pp.add_argument("args", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    eng = MasterEngine()
    if args.cmd == "list":
        print(json.dumps(list(eng.engines), indent=2))
    elif args.cmd == "simulate":
        print(json.dumps(eng.simulate(), indent=2))
    elif args.cmd == "benchmark":
        print(json.dumps(eng.benchmark(args.runs), indent=2))
    elif args.cmd == "execute":
        print(json.dumps(eng.execute(json.loads(args.json), args.only), indent=2))
    elif args.cmd == "signatures":
        print(json.dumps(eng.signature_modes(), indent=2))
    elif args.cmd in eng.engines:
        # delegate to module main if available
        mod = ADAPTIVES.get(args.cmd)
        if mod is not None and hasattr(mod, "main"):
            mod.main(list(args.args))
        else:
            print(json.dumps({"error": "no delegate for " + args.cmd}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
