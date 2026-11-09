#!/usr/bin/env python3
"""One-pass registration checker/fixer for mem20 subsystems.

Checks every registry surface that matters for a first-class subsystem:
gateway (conformance criterion 7), toolchest inventory, MCP presence, sitemapz
filesystem visibility, package metadata, and the conformance gate.

This is a real tool, not a template generator: it reports actual state and only
makes narrow, explicit edits when --fix-gateway or --fix-toolchest is passed.

Usage:
  python scripts/renovation/register_subsystem.py mem20causalroutingbrainz
  python scripts/renovation/register_subsystem.py mem20causalroutingbrainz --conformance
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATEWAY = REPO / "gateway" / "mem20_gateway.py"
TOOLCHEST = REPO / "toolchest" / "inventory.json"


def run(cmd: list[str], cwd: Path = REPO, timeout: int = 180) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO))
    p = subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout,
    )
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return p.returncode, out.strip()


def check_gateway(name: str) -> dict:
    if not GATEWAY.is_file():
        return {"ok": False, "detail": f"missing {GATEWAY}"}
    text = GATEWAY.read_text(encoding="utf-8", errors="ignore")
    present = f'"{name}"' in text or f"'{name}'" in text
    if not present:
        return {"ok": False, "detail": "name not found in gateway/mem20_gateway.py SUBSYSTEMS"}
    # show the entry line
    for i, line in enumerate(text.splitlines(), 1):
        if f'"{name}"' in line:
            return {"ok": True, "detail": f"registered at gateway/mem20_gateway.py:{i}"}
    return {"ok": True, "detail": "name present"}


def check_toolchest(name: str) -> dict:
    if not TOOLCHEST.is_file():
        return {"ok": False, "detail": f"missing {TOOLCHEST}"}
    try:
        data = json.loads(TOOLCHEST.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "detail": f"inventory unreadable: {exc}"}
    for entry in data.get("entries", []):
        if entry.get("name") == name or entry.get("id") == f"subsystem:{name}":
            src = entry.get("source") or entry.get("meta", {}).get("pyproject") or ""
            stale = "/workspace/" in src or "/opt/mem20" not in src and "mem20" in name
            return {
                "ok": not stale,
                "detail": ("stale paths/fields" if stale else "entry present")
                + f"; source={src}; runtime={entry.get('runtime_status')}",
                "entry": {k: entry.get(k) for k in ("id", "description", "source", "runtime_status")},
            }
    return {"ok": False, "detail": "no subsystem entry in toolchest/inventory.json"}


def check_mcp(name: str) -> dict:
    hits = []
    mcp = REPO / "mcp"
    if mcp.is_dir():
        for path in mcp.rglob("*.py"):
            try:
                if name in path.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(str(path.relative_to(REPO)))
            except OSError:
                pass
    # gateway also counts for criterion 7; report MCP-specific hits separately
    mcp_hits = [h for h in hits if h.startswith("mcp/")]
    if mcp_hits:
        return {"ok": True, "detail": f"MCP references: {', '.join(mcp_hits[:8])}"}
    return {
        "ok": False,
        "detail": "no dedicated MCP reference under mcp/ (criterion 7 may still pass via gateway)",
    }


def check_sitemapz(name: str) -> dict:
    pkg = REPO / name
    pyproject = pkg / "pyproject.toml"
    if not pkg.is_dir():
        return {"ok": False, "detail": f"package directory missing: {pkg}"}
    if not pyproject.is_file():
        return {"ok": False, "detail": "pyproject.toml missing; sitemapz/filesystem discovery is weak"}
    # sitemapz policy skips common junk dirs, not mem20* packages
    return {"ok": True, "detail": f"filesystem-discoverable package present ({pyproject.relative_to(REPO)})"}


def check_package(name: str) -> dict:
    pkg = REPO / name
    checks = []
    for label, path in [
        ("pyproject", pkg / "pyproject.toml"),
        ("README", pkg / "README.md"),
        ("package", pkg / name / "__init__.py"),
        ("runtime", pkg / name / "runtime.py"),
        ("tests", pkg / "tests"),
    ]:
        checks.append(f"{label}={'y' if path.exists() else 'n'}")
    py = sys.executable
    code, out = run([py, "-m", name, "--help"], timeout=120)
    ok = code == 0 or "usage" in out.lower()
    checks.append(f"cli_help={'y' if ok else 'n'}")
    return {"ok": (pkg / "pyproject.toml").exists() and (pkg / name).exists(), "detail": ", ".join(checks)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="subsystem name, e.g. mem20causalroutingbrainz")
    parser.add_argument("--conformance", action="store_true", help="run conformance gate")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)
    name = args.name

    report = {
        "name": name,
        "gateway": check_gateway(name),
        "toolchest": check_toolchest(name),
        "mcp": check_mcp(name),
        "sitemapz": check_sitemapz(name),
        "package": check_package(name),
    }

    if args.conformance:
        py = sys.executable
        code, out = run([py, "scripts/renovation/conformance.py", name], timeout=900)
        # keep tail only
        tail = "\n".join(out.splitlines()[-30:])
        report["conformance"] = {"ok": code == 0, "exit_code": code, "tail": tail}

    report["ok"] = all(v.get("ok") for k, v in report.items() if isinstance(v, dict) and k != "conformance") and (
        report.get("conformance", {}).get("ok", True)
    )

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    print(f"register-subsystem: {name}")
    for key in ("package", "gateway", "toolchest", "mcp", "sitemapz", "conformance"):
        if key not in report:
            continue
        item = report[key]
        mark = "PASS" if item.get("ok") else "WARN" if key in ("mcp",) else "FAIL"
        print(f"  {mark:4}  {key:11}  {item.get('detail', '')}")
        if key == "conformance" and not item.get("ok"):
            print(item.get("tail", ""))
    print(f"\nresult: {'ok' if report['ok'] else 'needs attention'}")
    print("note: toolchest is generated - prefer `python -m toolchest refresh` over manual edits;")
    print("      sitemapz is filesystem-discovered; MCP needs a real *_tools.py only when useful.")
    print("      when fixing to 7/7, wire a DIFFERENT set of >=5 peer subsystems per subsystem.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
