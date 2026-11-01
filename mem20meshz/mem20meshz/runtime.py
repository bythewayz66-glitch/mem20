from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

from . import governance
from .meshes import crisis as m_crisis
from .meshes import crossdevice as m_cross
from .meshes import federated as m_fed
from .meshes import nearby as m_nearby
from .meshes import offline as m_offline
from .meshes import selfhealing as m_heal

MESHES = {
    "crisis": m_crisis,
    "crossdevice": m_cross,
    "federated": m_fed,
    "nearby": m_nearby,
    "offline": m_offline,
    "selfhealing": m_heal,
}

def _mesh_dir(mod):
    return Path(mod.__file__).resolve().parent

#: Request keys that belong to admission control, not to a mesh. Stripped before
#: dispatch so a mesh never treats a policy field as domain input.
GOVERNANCE_KEYS = frozenset({"tool", "intended_uses", "at", "wire", "my_nicks"})

def _load_engine(mod):
    cfg = mod.load_config(str(_mesh_dir(mod) / "CAPABILITY.json"))
    return mod.Engine(cfg)

class MasterEngine:
    def __init__(self):
        self.engines = {name: _load_engine(mod) for name, mod in MESHES.items()}
        self.configs = {name: mod.load_config(str(_mesh_dir(mod) / "CAPABILITY.json")) for name, mod in MESHES.items()}
        self.admissions = {}
        self.provenance = {}

    def inspect(self):
        return {name: eng.metrics_snapshot() if hasattr(eng, "metrics_snapshot") else {"ok": True} for name, eng in self.engines.items()}

    def execute(self, request, only=None):
        """Dispatch a request to one or all meshes, through admission control.

        Every mesh execution passes ``governance.admit`` first: naming, the
        prohibited-use gate, the stub linter over the mesh's own source, the
        operating window, and the wire filter. A refusal is reported per mesh
        and that mesh does not run -- it is never silently skipped, and it is
        never dispatched anyway.
        """
        targets = [only] if only else list(self.engines)
        out = {}
        for name in targets:
            try:
                admission, wire = governance.admit(
                    name, self.configs[name], dict(request), _mesh_dir(MESHES[name])
                )
            except governance.MeshRefused as exc:
                out[name] = exc.as_dict()
                continue
            self.admissions[name] = admission
            # Governance-only keys are consumed here; a mesh must not see them,
            # or a mesh that echoes its input would report policy as data.
            payload = {k: v for k, v in request.items() if k not in GOVERNANCE_KEYS}
            if wire:
                payload["wire"] = [line.text for line in wire]
            try:
                result = self.engines[name].execute(payload)
            except Exception as e:
                result = {"error": type(e).__name__, "message": str(e)}
            self.provenance[name] = governance.record_provenance(name, request, result)
            out[name] = result
        return {"mesh": "mem20meshz", "results": out}

    def admission_report(self):
        """What admission control decided for the last execution of each mesh."""
        return {name: adm.as_dict() for name, adm in self.admissions.items()}

    def provenance_report(self):
        """Where each mesh execution was recorded, and whether it was committed."""
        return dict(self.provenance)

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
    ap = argparse.ArgumentParser(prog="mem20meshz", description="mem20 mesh gold runtime \u2014 orchestrates all 6 mesh runtimes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    # delegate subcommands
    p = sub.add_parser("list", help="list sub-meshes")
    p = sub.add_parser("simulate", help="run all simulators")
    p = sub.add_parser("benchmark", help="benchmark all"); p.add_argument("--runs", type=int, default=50)
    p = sub.add_parser("execute"); p.add_argument("json", nargs="?", default="{}"); p.add_argument("--only", default=None)
    p = sub.add_parser("signatures", help="enable all signature modes")
    p = sub.add_parser("admission", help="show what admission control decided for the last execute")
    p = sub.add_parser("provenance", help="show where each mesh execution was recorded")
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
    elif args.cmd == "admission":
        print(json.dumps(eng.admission_report(), indent=2))
    elif args.cmd == "provenance":
        print(json.dumps(eng.provenance_report(), indent=2))
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
