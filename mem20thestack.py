#!/usr/bin/env python3
"""mem20-thestack: discover, deconflict, boot, and test mem20 web surfaces."""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as _dt
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "bin" / "python"
PYTHON = str(VENV_PY if VENV_PY.exists() else Path(sys.executable))
STATE_DIR = Path(os.environ.get("MEM20_THESTACK_STATE", "/tmp/mem20-thestack"))
STATE_FILE = STATE_DIR / "state.json"
LOG_DIR = STATE_DIR / "logs"
DB_DIR = STATE_DIR / "db"


@dataclasses.dataclass
class Service:
    id: str
    name: str
    kind: str
    cwd: str
    cmd: List[str]
    env: Dict[str, str]
    desired_port: Optional[int]
    port: Optional[int]
    test_urls: List[str]
    cmd_variants: List[List[str]] = dataclasses.field(default_factory=list)
    meta: Dict[str, Any] = dataclasses.field(default_factory=dict)
    pid: Optional[int] = None
    log_file: Optional[str] = None
    status: str = "planned"
    error: Optional[str] = None
    test_result: Optional[Dict[str, Any]] = None


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _listen_ports_proc() -> set[int]:
    used: set[int] = set()
    for p in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(p) as f:
                next(f, None)
                for line in f:
                    parts = line.split()
                    if len(parts) > 3 and parts[3] == "0A":
                        used.add(int(parts[1].split(":")[1], 16))
        except Exception:
            pass
    return used


def _port_free(port: int, host: str = "127.0.0.1") -> bool:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _choose_port(desired: Optional[int], used: set[int], cursor: List[int], start: int = 20000) -> int:
    if desired and desired not in used and _port_free(desired):
        used.add(desired)
        return desired
    if desired:
        for off in range(1, 100):
            for cand in (desired + off, desired - off):
                if 1024 <= cand <= 65535 and cand not in used and _port_free(cand):
                    used.add(cand)
                    return cand
    p = cursor[0]
    while p in used or not _port_free(p):
        p += 1
        if p > 65000:
            p = start
    used.add(p)
    cursor[0] = p + 1
    return p


def _http_get(url: str, timeout: float = 2.5) -> Tuple[bool, int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "mem20-thestack/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(512)
            ct = r.headers.get("Content-Type", "")
            text = body.decode("utf-8", errors="replace")
            return True, int(r.status), f"{ct} {text[:120]!r}"
    except urllib.error.HTTPError as e:
        try:
            body = e.read(256).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return False, int(e.code), body[:160]
    except Exception as e:
        return False, 0, str(e)[:200]


def _discover_docs_app_modules() -> List[Dict[str, Any]]:
    readme = ROOT / "docs" / "app" / "README.md"
    txt = _read_text(readme)
    pat = re.compile(r"^\-\s+\[(?P<name>[^\]]+)\]\((?P<link>[^\)]+)\)\s+—\s+`(?P<cmd>[^`]+)`", re.M)
    items = []
    seen = set()
    for m in pat.finditer(txt):
        cmd = m.group("cmd")
        mm = re.search(r"-m\s+(\S+)\s+serve\s+--port\s+(\d+)", cmd)
        if not mm:
            continue
        key = (m.group("name"), mm.group(1), int(mm.group(2)))
        if key in seen:
            continue
        seen.add(key)
        items.append({"name": m.group("name"), "link": m.group("link"), "module": mm.group(1), "port": int(mm.group(2))})
    return items


def _discover_runtime_serve_modules() -> List[Dict[str, Any]]:
    out = []
    seen_mods = set()
    for rp in sorted(ROOT.rglob("runtime.py")):
        if any(p in {".venv", "node_modules", ".git", "site-packages", "tests", "mem20corez"} for p in rp.parts):
            continue
        txt = _read_text(rp)
        if "serve" not in txt or "argparse" not in txt:
            continue
        if "add_parser('serve')" not in txt and 'add_parser("serve")' not in txt and "'serve'" not in txt:
            # still maybe serve handled differently
            if "serve" not in txt:
                continue
        parts = rp.relative_to(ROOT).parts
        if not parts or not parts[0].startswith("mem20"):
            continue
        mod = parts[0]
        if mod in seen_mods:
            continue
        # skip modules that are clearly not runnable as top-level serve in usual way? keep them.
        m = re.search(r"add_argument\(['\"]--port['\"].*?default\s*=\s*(\d+)", txt)
        port = int(m.group(1)) if m else None
        if port == 0:
            port = None
        seen_mods.add(mod)
        out.append({"module": mod, "port": port, "runtime": str(rp.relative_to(ROOT))})
    return out


def _discover_runpy_serve() -> List[Path]:
    out = []
    for runpy in sorted(ROOT.rglob("run.py")):
        if any(part in {".venv", "node_modules", ".git", "site-packages"} for part in runpy.parts):
            continue
        txt = _read_text(runpy)
        if "cli" in txt or "serve" in txt or "mem20core" in txt:
            out.append(runpy)
    return out


def _discover_braid_examples() -> List[Dict[str, Any]]:
    ex_dir = ROOT / "braid" / "braid_ui_bridge" / "examples"
    if not ex_dir.exists():
        return []
    exs = []
    for rs in sorted(ex_dir.glob("*.rs")):
        txt = _read_text(rs)
        if "fn main" not in txt:
            continue
        if any(k in rs.name for k in ("shell", "walk_in", "console", "wire", "gate", "door", "terminal", "intent", "audio", "drive", "godmode")):
            exs.append({"name": rs.stem, "path": str(rs)})
    return exs


def _service_variants_for_module(mod: str, port: int, dbpath: str) -> Tuple[List[str], List[List[str]]]:
    base_serve = [PYTHON, "-m", mod, "serve", "--host", "127.0.0.1", "--port", str(port)]
    variants = [
        [PYTHON, "-m", mod, "serve", "--host", "127.0.0.1", "--port", str(port)],
        [PYTHON, "-m", mod, "--db", dbpath, "serve", "--host", "127.0.0.1", "--port", str(port)],
        [PYTHON, "-m", mod, "--store", dbpath, "serve", "--host", "127.0.0.1", "--port", str(port)],
        [PYTHON, "-m", mod, "serve", "--port", str(port)],
    ]
    # unique
    uniq = []
    seen = set()
    for v in variants:
        k = tuple(v)
        if k not in seen:
            seen.add(k); uniq.append(v)
    return uniq[0], uniq[1:]


def build_inventory() -> List[Service]:
    services: List[Service] = []

    # Static surfaces
    for sid, name, port, path in [
        ("static-docs-root", "docs (static root)", 8088, ROOT / "docs"),
        ("static-docs-app", "docs/app (main shell + monitors)", 8090, ROOT / "docs" / "app"),
        ("static-dashboard", "dashboard (static/source)", 8091, ROOT / "dashboard"),
        ("static-published", "published (static artifacts)", 8092, ROOT / "published"),
    ]:
        if not path.exists():
            continue
        services.append(Service(
            id=sid, name=name, kind="static-http", cwd=str(ROOT),
            cmd=[PYTHON, "-m", "http.server", "{port}", "--bind", "127.0.0.1", "--directory", str(path)],
            env={}, desired_port=port, port=None,
            test_urls=["http://127.0.0.1:{port}/", "http://127.0.0.1:{port}/index.html"],
            meta={"path": str(path)},
        ))

    # mem20controlz
    services.append(Service(
        id="mem20controlz", name="mem20controlz (control plane)", kind="controlz", cwd=str(ROOT),
        cmd=[PYTHON, "-m", "mem20controlz", "--host", "127.0.0.1", "--port", "{port}"],
        env={"PYTHONPATH": str(ROOT)}, desired_port=8890, port=None,
        test_urls=["http://127.0.0.1:{port}/api/health", "http://127.0.0.1:{port}/api/auth/status", "http://127.0.0.1:{port}/"],
    ))

    # bridge
    services.append(Service(
        id="mem20-bridge", name="mem20 bridge (dashboard HTTP bridge)", kind="bridge", cwd=str(ROOT),
        cmd=[PYTHON, str(ROOT / "bridge" / "server.py")],
        env={"PYTHONPATH": str(ROOT), "MEM20_BRIDGE_LISTEN": "127.0.0.1:{port}", "MEM20_BRIDGE_HOST": "127.0.0.1", "MEM20_BRIDGE_PORT": "8080"},
        desired_port=8000, port=None,
        test_urls=["http://127.0.0.1:{port}/", "http://127.0.0.1:{port}/api/status"],
    ))

    # mem20agentz web (Vite dev)
    agentz_web = ROOT / "mem20agentz" / "web"
    if agentz_web.exists() and (agentz_web / "package.json").exists() and shutil.which("npx"):
        services.append(Service(
            id="mem20agentz-web",
            name="mem20agentz web (vite dev)",
            kind="vite-dev",
            cwd=str(agentz_web),
            cmd=["npx", "--yes", "vite", "--host", "127.0.0.1", "--port", "{port}"],
            env={},
            desired_port=5173,
            port=None,
            test_urls=["http://127.0.0.1:{port}/"],
            meta={"path": str(agentz_web)},
        ))

    # docs/app README subsystem monitors (72 entries) - keep each as separate instance
    for item in _discover_docs_app_modules():
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "-", item["name"]).strip("-").lower()
        sid = f"mod-{safe}-{item['port']}"
        dbpath = str(DB_DIR / f"{sid}.sqlite3")
        cmd, variants = _service_variants_for_module(item["module"], 0, dbpath)  # port filled later
        services.append(Service(
            id=sid, name=item["name"], kind="subsystem-module", cwd=str(ROOT),
            cmd=cmd, cmd_variants=variants, env={"PYTHONPATH": str(ROOT)},
            desired_port=int(item["port"]), port=None,
            test_urls=["http://127.0.0.1:{port}/api/health", "http://127.0.0.1:{port}/api/status", "http://127.0.0.1:{port}/health", "http://127.0.0.1:{port}/"],
            meta={**item, "dbpath": dbpath},
        ))

    # extra runtime serve modules not already represented as same (module,desired_port)
    existing_mod_ports = {(s.meta.get("module"), s.desired_port) for s in services if s.kind == "subsystem-module"}
    existing_mods_any = {s.meta.get("module") for s in services if s.kind == "subsystem-module"}
    for item in _discover_runtime_serve_modules():
        mod = item["module"]
        # skip if already covered by docs/app monitor entries for same module (instances run separately) - but include at least one if missing
        if mod in existing_mods_any:
            continue
        sid = f"rtmod-{mod}"
        dbpath = str(DB_DIR / f"{sid}.sqlite3")
        cmd, variants = _service_variants_for_module(mod, 0, dbpath)
        services.append(Service(
            id=sid, name=f"runtime module: {mod}", kind="subsystem-module", cwd=str(ROOT),
            cmd=cmd, cmd_variants=variants, env={"PYTHONPATH": str(ROOT)},
            desired_port=item.get("port"), port=None,
            test_urls=["http://127.0.0.1:{port}/api/health", "http://127.0.0.1:{port}/api/status", "http://127.0.0.1:{port}/"],
            meta={**item, "dbpath": dbpath},
        ))

    # run.py RM packages
    for rp in _discover_runpy_serve():
        try:
            rel = rp.parent.relative_to(ROOT)
        except Exception:
            continue
        sid = "runpy-" + re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(rel)).strip("-")
        services.append(Service(
            id=sid, name=f"run.py serve: {rel}", kind="runpy", cwd=str(rp.parent),
            cmd=[PYTHON, "run.py", "--data-dir", str(DB_DIR / sid), "serve", "--host", "127.0.0.1", "--port", "{port}"],
            cmd_variants=[[PYTHON, "run.py", "serve", "--host", "127.0.0.1", "--port", "{port}"]],
            env={"PYTHONPATH": str(ROOT)}, desired_port=8765, port=None,
            test_urls=["http://127.0.0.1:{port}/", "http://127.0.0.1:{port}/api/status", "http://127.0.0.1:{port}/api/health"],
            meta={"run_py": str(rp)},
        ))

    # braid examples
    cargo = shutil.which("cargo")
    if cargo and (ROOT / "braid" / "Cargo.toml").exists():
        for ex in _discover_braid_examples():
            sid = "braid-ex-" + ex["name"]
            services.append(Service(
                id=sid, name=f"braid example: {ex['name']}", kind="braid-example", cwd=str(ROOT / "braid"),
                cmd=[cargo, "run", "-q", "-p", "braid_ui_bridge", "--example", ex["name"]],
                env={}, desired_port=None, port=None, test_urls=[],
                meta=ex,
            ))

    # de-dup by id
    uniq: Dict[str, Service] = {}
    for s in services:
        if s.id not in uniq:
            uniq[s.id] = s
    return list(uniq.values())


def _materialize(s: Service) -> None:
    def sub(v: Any) -> Any:
        if isinstance(v, str):
            return v.replace("{port}", str(s.port))
        if isinstance(v, list):
            return [sub(x) for x in v]
        if isinstance(v, dict):
            return {k: sub(val) for k, val in v.items()}
        return v
    s.cmd = sub(s.cmd)
    s.cmd_variants = [sub(v) for v in s.cmd_variants]
    s.env = sub(s.env)
    s.test_urls = sub(s.test_urls)


def assign_ports(services: List[Service]) -> List[Dict[str, Any]]:
    used = _listen_ports_proc()
    cursor = [20000]
    order = {"static-http": 0, "controlz": 1, "bridge": 2, "vite-dev": 3, "subsystem-module": 4, "runpy": 5, "braid-example": 6}
    graph = []
    for s in sorted(services, key=lambda x: (order.get(x.kind, 9), x.desired_port or 99999, x.id)):
        if s.kind == "braid-example":
            s.port = _choose_port(None, used, cursor, start=39000)
        else:
            s.port = _choose_port(s.desired_port, used, cursor)
        _materialize(s)
        graph.append({
            "id": s.id, "name": s.name, "kind": s.kind,
            "desired_port": s.desired_port, "assigned_port": s.port,
            "reassigned": s.desired_port is not None and s.port != s.desired_port,
            "cwd": s.cwd, "cmd": s.cmd, "tests": s.test_urls,
        })
    return graph


def fix_broken_editable_pths() -> List[str]:
    fixed = []
    site = ROOT / ".venv" / "lib"
    if not site.exists():
        return fixed
    for pth in site.rglob("__editable__.*.pth"):
        try:
            txt = pth.read_text(errors="replace")
        except Exception:
            continue
        m = re.search(r"__editable___[A-Za-z0-9_]+_finder", txt)
        if not m:
            continue
        finder = m.group(0) + ".py"
        if not (pth.parent / finder).exists():
            try:
                bak = pth.with_suffix(pth.suffix + ".thestack.bak")
                if not bak.exists():
                    pth.rename(bak)
                    fixed.append(f"disabled broken editable pth: {pth.name}")
            except Exception as e:
                fixed.append(f"failed to disable {pth.name}: {e}")
    return fixed


def _popen(s: Service, cmd: List[str]) -> subprocess.Popen:
    log_path = LOG_DIR / f"{s.id}.log"
    s.log_file = str(log_path)
    env = os.environ.copy()
    for k, v in (s.env or {}).items():
        env[str(k)] = str(v)
    pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + pp if pp else "")
    env.setdefault("PYTHONUNBUFFERED", "1")
    lf = open(log_path, "ab", buffering=0)
    lf.write(f"\n=== START {_now()} ===\n".encode())
    lf.write(("CMD: " + " ".join(shlex.quote(c) for c in cmd) + "\n").encode())
    lf.write(("CWD: " + s.cwd + "\n").encode())
    lf.flush()
    return subprocess.Popen(cmd, cwd=s.cwd or str(ROOT), env=env, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)


def _wait_listen(s: Service, proc: subprocess.Popen, timeout: float) -> None:
    deadline = time.time() + timeout
    if s.port and s.kind != "braid-example":
        while time.time() < deadline:
            if proc.poll() is not None:
                s.status = "exited"; s.error = f"exit {proc.returncode}"; return
            if not _port_free(s.port):
                s.status = "running"; return
            time.sleep(0.2)
        if proc.poll() is None:
            s.status = "running-no-listen-yet"
        else:
            s.status = "exited"; s.error = f"exit {proc.returncode}"
    else:
        time.sleep(min(1.5, timeout))
        s.status = "running" if proc.poll() is None else "exited"
        if proc.poll() is not None:
            s.error = f"exit {proc.returncode}"


def start_service(s: Service, timeout: float = 8.0) -> None:
    _ensure_dirs()
    try:
        proc = _popen(s, s.cmd)
        s.pid = proc.pid
        s.status = "starting"
        _wait_listen(s, proc, timeout)
    except Exception as e:
        s.status = "failed-start"; s.error = str(e)


def test_service(s: Service) -> Dict[str, Any]:
    result = {"id": s.id, "name": s.name, "ok": False, "checks": [], "status": s.status, "port": s.port}
    if s.kind == "braid-example":
        alive = False
        if s.pid:
            try:
                os.kill(s.pid, 0); alive = True
            except Exception:
                alive = False
        result["ok"] = alive
        result["checks"].append({"kind": "process", "ok": alive, "detail": "alive" if alive else "not running"})
        s.test_result = result
        return result
    urls = s.test_urls or ([f"http://127.0.0.1:{s.port}/"] if s.port else [])
    any_ok = False
    for url in urls:
        ok, code, detail = _http_get(url, timeout=3.0)
        passed = ok and 200 <= code < 400
        auth_ok = code in (401, 403)
        result["checks"].append({"url": url, "code": code, "pass": passed or auth_ok, "detail": detail})
        if passed or auth_ok:
            any_ok = True
            break
    if not any_ok and s.pid and s.port:
        try:
            os.kill(s.pid, 0); alive = True
        except Exception:
            alive = False
        if alive and not _port_free(s.port):
            result["checks"].append({"kind": "listen", "ok": True, "detail": f"port {s.port} listening"})
            any_ok = True
    result["ok"] = any_ok
    s.test_result = result
    return result


def try_fix_and_retest(s: Service) -> Dict[str, Any]:
    # try command variants if process exited or test failed
    for variant in s.cmd_variants:
        try:
            if s.pid:
                with contextlib.suppress(Exception):
                    os.killpg(s.pid, signal.SIGTERM)
                time.sleep(0.3)
        except Exception:
            pass
        try:
            proc = _popen(s, variant)
            s.pid = proc.pid
            s.cmd = variant
            s.status = "starting-retry"
            s.error = None
            _wait_listen(s, proc, 6.0)
            time.sleep(0.5)
            r = test_service(s)
            if r.get("ok"):
                r["fixed_with"] = " ".join(shlex.quote(c) for c in variant)
                s.test_result = r
                return r
        except Exception as e:
            s.error = str(e)
    r = test_service(s)
    s.test_result = r
    return r


def stop_from_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    stopped = []
    for rec in state.get("services", []):
        pid = rec.get("pid")
        if not pid:
            continue
        ok = False; err = None
        try:
            os.killpg(pid, signal.SIGTERM); ok = True
        except Exception as e:
            err = str(e)
            try:
                os.kill(pid, signal.SIGTERM); ok = True; err = None
            except Exception as e2:
                err = str(e2)
        stopped.append({"id": rec.get("id"), "pid": pid, "ok": ok, "error": err})
    time.sleep(1.0)
    for rec in state.get("services", []):
        pid = rec.get("pid")
        if not pid: continue
        with contextlib.suppress(Exception): os.killpg(pid, signal.SIGKILL)
        with contextlib.suppress(Exception): os.kill(pid, signal.SIGKILL)
    return stopped


def save_state(services: List[Service], graph: List[Dict[str, Any]], fixes: List[str], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    _ensure_dirs()
    state = {
        "timestamp": _now(), "root": str(ROOT), "python": PYTHON,
        "fixes": fixes, "port_graph": graph,
        "services": [dataclasses.asdict(s) for s in services],
        "tests": results,
        "summary": {
            "total": len(services),
            "booted_alive": sum(1 for s in services if s.pid and str(s.status).startswith("running")),
            "tests_passed": sum(1 for r in results if r.get("ok")),
            "tests_failed": sum(1 for r in results if not r.get("ok")),
        },
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def filter_services(services: List[Service], args: argparse.Namespace) -> List[Service]:
    out = services
    if getattr(args, "skip_rm", False):
        out = [s for s in out if s.kind != "runpy"]
    if getattr(args, "skip_braid", False):
        out = [s for s in out if s.kind != "braid-example"]
    only = getattr(args, "only", None)
    if only:
        rx = re.compile(only)
        out = [s for s in out if rx.search(s.id) or rx.search(s.name) or rx.search(s.kind)]
    skip = getattr(args, "skip", None)
    if skip:
        rx = re.compile(skip)
        out = [s for s in out if not (rx.search(s.id) or rx.search(s.name) or rx.search(s.kind))]
    limit = getattr(args, "limit", None)
    if limit:
        out = out[: int(limit)]
    return out


def cmd_plan(args: argparse.Namespace) -> int:
    fixes = fix_broken_editable_pths() if getattr(args, "apply_fixes", False) else []
    services = filter_services(build_inventory(), args)
    graph = assign_ports(services)
    out = {"count": len(graph), "fixes": fixes, "port_graph": graph}
    print(json.dumps(out, indent=2))
    return 0


def _boot_one(s: Service, timeout: float) -> Service:
    start_service(s, timeout=timeout)
    return s


def cmd_up(args: argparse.Namespace) -> int:
    _ensure_dirs()
    fixes = fix_broken_editable_pths()
    services = filter_services(build_inventory(), args)
    graph = assign_ports(services)
    print(f"[mem20-thestack] inventory={len(services)} fixes={len(fixes)} state={STATE_FILE}")
    for f in fixes:
        print(f"[fix] {f}")
    print("[port-graph]")
    for g in graph:
        flag = " (reassigned)" if g["reassigned"] else ""
        print(f"  - {g['assigned_port']:>5}  {g['kind']:<16}  {g['id']}{flag}")

    boot_timeout = float(getattr(args, "boot_timeout", 8.0))
    parallel = max(1, int(getattr(args, "parallel", 8)))
    # boot in parallel
    print(f"[boot] starting {len(services)} services with parallel={parallel}")
    with ThreadPoolExecutor(max_workers=parallel) as ex:
        futs = [ex.submit(_boot_one, s, boot_timeout) for s in services]
        for fut in as_completed(futs):
            s = fut.result()
            if s.error or s.status in ("exited", "failed-start"):
                print(f"[boot] WARN {s.id} status={s.status} err={s.error}")

    settle = float(getattr(args, "settle", 4.0))
    if settle > 0:
        print(f"[settle] waiting {settle}s")
        time.sleep(settle)

    # test and fix
    results: List[Dict[str, Any]] = []
    for s in services:
        r = test_service(s)
        if not r.get("ok") and s.kind not in ("braid-example",):
            print(f"[test] FAIL {s.id} (port {s.port}, status {s.status}) -> attempting fixes")
            r = try_fix_and_retest(s)
        else:
            mark = "PASS" if r.get("ok") else "FAIL"
            print(f"[test] {mark} {s.id} port={s.port}")
        results.append(r)

    state = save_state(services, graph, fixes, results)
    print(f"\n[mem20-thestack] done. passed={state['summary']['tests_passed']} failed={state['summary']['tests_failed']} total={state['summary']['total']}")
    print(f"[mem20-thestack] state: {STATE_FILE}")
    print(f"[mem20-thestack] logs:  {LOG_DIR}")
    # print compact port graph summary by kind
    by_kind: Dict[str, int] = {}
    for g in graph:
        by_kind[g['kind']] = by_kind.get(g['kind'], 0) + 1
    print(json.dumps({"summary": state["summary"], "by_kind": by_kind, "state_file": str(STATE_FILE)}, indent=2))
    return 0 if state['summary']['tests_failed'] == 0 else 2


def cmd_status(args: argparse.Namespace) -> int:
    if not STATE_FILE.exists():
        print(json.dumps({"ok": False, "error": f"no state file: {STATE_FILE}"}))
        return 1
    state = json.loads(STATE_FILE.read_text())
    for rec in state.get("services", []):
        pid = rec.get("pid"); alive = False
        if pid:
            try:
                os.kill(pid, 0); alive = True
            except Exception:
                alive = False
        rec["alive"] = alive
    print(json.dumps({"summary": state.get("summary", {}), "timestamp": state.get("timestamp")}, indent=2))
    return 0


def cmd_down(args: argparse.Namespace) -> int:
    if not STATE_FILE.exists():
        print("no state to stop")
        return 0
    state = json.loads(STATE_FILE.read_text())
    stopped = stop_from_state(state)
    print(json.dumps({"stopped": len(stopped)}, indent=2))
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    if not STATE_FILE.exists():
        print("no state")
        return 1
    state = json.loads(STATE_FILE.read_text())
    print(json.dumps(state.get("port_graph", []), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mem20-thestack", description="Boot, port-deconflict, and test the full mem20 web stack")
    sub = p.add_subparsers(dest="cmd")

    def add_filters(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--only", help="regex to include services by id/name/kind")
        sp.add_argument("--skip", help="regex to exclude services by id/name/kind")
        sp.add_argument("--skip-rm", action="store_true", help="skip run.py/RM packages")
        sp.add_argument("--skip-braid", action="store_true", help="skip braid examples")
        sp.add_argument("--limit", type=int, help="limit number of services (debug)")

    up = sub.add_parser("up", help="discover, assign ports, boot, and test all services")
    add_filters(up)
    up.add_argument("--dry-run", action="store_true", help="alias for plan")
    up.add_argument("--boot-timeout", type=float, default=8.0)
    up.add_argument("--settle", type=float, default=4.0)
    up.add_argument("--parallel", type=int, default=8)

    plan = sub.add_parser("plan", help="show inventory and port graph without booting")
    add_filters(plan)
    plan.add_argument("--apply-fixes", action="store_true")

    down = sub.add_parser("down", help="stop services started by the last up")
    status = sub.add_parser("status", help="show last run summary")
    sub.add_parser("graph", help="show last port graph")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    cmd = args.cmd or "up"
    if cmd == "up" and getattr(args, "dry_run", False):
        cmd = "plan"
    if cmd == "plan":
        return cmd_plan(args)
    if cmd == "up":
        return cmd_up(args)
    if cmd == "down":
        return cmd_down(args)
    if cmd == "status":
        return cmd_status(args)
    if cmd == "graph":
        return cmd_graph(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
