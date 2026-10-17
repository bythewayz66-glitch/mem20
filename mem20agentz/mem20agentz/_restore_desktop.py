"""One-shot restore for truncated desktop.py.

Recovers the full module from git blob 83450f57 (last known-good version)
and applies the CREWZ_ROOT / GAMEZ_ROOT path de-hardcode (#32).

Usage (from repo root or this directory):
    python3 mem20agentz/mem20agentz/_restore_desktop.py
"""
from __future__ import annotations

import pathlib
import urllib.request

TARGET = pathlib.Path(__file__).resolve().parent / "desktop.py"
GOOD_BLOB = "83450f57f10a8b47da5f6d4e1e9ad35d2012acc7"
URL = f"https://api.github.com/repos/bythewayz66-glitch/mem20/git/blobs/{GOOD_BLOB}"

OLD = (
    'FRONTEND_DIR = pathlib.Path(__file__).parent / "frontend"\n'
    'CREWZ_ROOT = "/opt/mem20/mem20crewz"\n'
    'GAMEZ_ROOT = "/opt/mem20/mem20gamez"\n'
    'RUNTIME_ROOT = pathlib.Path(os.path.expanduser(\n'
    '    os.environ.get("MEM20_RUNTIME", "/root/.mem20agentz")))\n'
)

NEW = (
    'FRONTEND_DIR = pathlib.Path(__file__).parent / "frontend"\n'
    '\n'
    '# Resolve sibling package roots from env, then fall back to the monorepo\n'
    '# layout (…/mem20/mem20agentz/mem20agentz/desktop.py → parents[2] is mem20/).\n'
    '_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]\n'
    'CREWZ_ROOT = os.environ.get("MEM20_CREWZ_ROOT") or str(_REPO_ROOT / "mem20crewz")\n'
    'GAMEZ_ROOT = os.environ.get("MEM20_GAMEZ_ROOT") or str(_REPO_ROOT / "mem20gamez")\n'
    'RUNTIME_ROOT = pathlib.Path(os.path.expanduser(\n'
    '    os.environ.get("MEM20_RUNTIME", "~/.mem20agentz")))\n'
)


def main() -> None:
    current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
    if "class Frontend" in current and len(current) > 10000:
        print(f"desktop.py already healthy ({len(current)} bytes)")
        return
    print(f"fetching blob {GOOD_BLOB}…")
    req = urllib.request.Request(
        URL,
        headers={
            "Accept": "application/vnd.github.raw",
            "User-Agent": "mem20-restore-desktop",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        src = resp.read().decode("utf-8")
    if OLD not in src:
        raise SystemExit("unexpected source shape from blob — aborting")
    fixed = src.replace(OLD, NEW, 1)
    TARGET.write_text(fixed, encoding="utf-8")
    print(f"restored {TARGET} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
