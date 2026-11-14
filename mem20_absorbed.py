"""Shared helpers for assimilated/absorbed mem20 subsystems.

Provides discovery and probing of absorbed member packages rehomed under
<runtime>/absorbed/<member>/.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def ensure_import_paths(root: Optional[Path] = None) -> None:
    root = root or repo_root()
    rs = str(root)
    if rs not in sys.path:
        sys.path.insert(0, rs)
    tc = root / "toolchest" / "src"
    tcs = str(tc)
    if tc.is_dir() and tcs not in sys.path:
        sys.path.insert(0, tcs)
    try:
        import _mem20_absorbed_finder  # noqa: F401
    except Exception:
        try:
            spec = importlib.util.spec_from_file_location("_mem20_absorbed_finder", root / "_mem20_absorbed_finder.py")
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                sys.modules.setdefault("_mem20_absorbed_finder", mod)
        except Exception:
            pass


def discover_absorbed(runtime_dir: Path) -> tuple[str, ...]:
    adir = runtime_dir / "absorbed"
    if not adir.is_dir():
        return ()
    names = []
    for p in sorted(adir.iterdir()):
        if p.is_dir() and p.name.startswith("mem20") and p.name.endswith("z"):
            names.append(p.name)
    return tuple(names)


def absorbed_map(root: Optional[Path] = None) -> Dict[str, List[str]]:
    root = root or repo_root()
    mp = root / ".mem20-absorbed-map.json"
    if not mp.exists():
        return {}
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
        return data.get("mapping", {}) or {}
    except Exception:
        return {}


def canonical_targets(root: Optional[Path] = None) -> Dict[str, str]:
    root = root or repo_root()
    cp = root / "tmp" / "absorbed_canonical.json"
    # also check /tmp
    if not cp.exists():
        cp = Path("/tmp/absorbed_canonical.json")
    if not cp.exists():
        return {}
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
        return data.get("canonical", {}) or {}
    except Exception:
        return {}


def probe_member_ecosystem(name: str, root: Optional[Path] = None) -> Dict[str, Any]:
    ensure_import_paths(root)
    try:
        eco = importlib.import_module(f"{name}.ecosystem")
    except Exception as e:
        return {"ok": False, "member": name, "error": f"no_ecosystem:{type(e).__name__}: {e}"}
    try:
        if hasattr(eco, "probe"):
            r = eco.probe()
            if isinstance(r, dict):
                count = r.get("count")
                if count is None:
                    count = len(r.get("reachable") or r.get("checks") or [])
                return {"ok": bool(r.get("ok", False)), "member": name, "count": int(count), "reachable": r.get("reachable")}
            return {"ok": True, "member": name, "count": 1}
        fns = [x for x in dir(eco) if not x.startswith("_") and callable(getattr(eco, x))]
        return {"ok": True, "member": name, "count": len(fns)}
    except Exception as e:
        return {"ok": False, "member": name, "error": f"{type(e).__name__}: {e}"}


def aggregate_member_peers(members: Sequence[str], root: Optional[Path] = None) -> Dict[str, Any]:
    checks = {}
    total = 0
    ok = 0
    for m in members:
        r = probe_member_ecosystem(m, root)
        checks[m] = r
        c = r.get("count")
        if isinstance(c, int):
            total += c
        if r.get("ok"):
            ok += 1
    return {"ok": True, "members": len(members), "members_ok": ok, "peer_checks_total": total, "checks": checks}


def probe_members_basic(members: Sequence[str], runtime_dir: Path, root: Optional[Path] = None) -> List[Dict[str, Any]]:
    ensure_import_paths(root)
    out = []
    for name in members:
        absorbed_dir = runtime_dir / "absorbed" / name
        present = absorbed_dir.is_dir()
        importable = False
        version = None
        error = None
        try:
            mod = importlib.import_module(name)
            importable = True
            version = getattr(mod, "__version__", None)
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        out.append({"name": name, "present": present, "absorbed": present, "importable": importable, "version": version, "error": error, "path": str(absorbed_dir) if present else None})
    return out
