#!/usr/bin/env python3
"""Regenerate the vendored MCP server implementation.

``mcp/server.py`` normally loads the implementation from
``mem20liez/_server_impl.py`` (committed, so shallow clones work). That file is
a build artefact of one upstream commit plus an in-memory patch. This script
rebuilds it.

Usage
-----
    python mem20liez/regen_server_impl.py            # write the file
    python mem20liez/regen_server_impl.py --check    # verify it is current
    python mem20liez/regen_server_impl.py --sha <sha>

Requires git history containing the source commit (a full clone, or a shallow
clone plus ``git fetch --depth=1 origin <sha>``).
"""
from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_TARGET = os.path.join(_HERE, "_server_impl.py")
_SERVER_PY = os.path.join(_ROOT, "mcp", "server.py")


def _load_helpers():
    """Import the patch helpers from mcp/server.py without running bootstrap."""
    with open(_SERVER_PY, "r", encoding="utf-8") as f:
        source = f.read()
    head = source.partition("def _bootstrap(")[0]
    if not head.strip():
        raise SystemExit(f"could not find the helper block in {_SERVER_PY}")
    ns = {"__file__": _SERVER_PY, "__name__": "mem20_server_helpers"}
    exec(compile(head, _SERVER_PY, "exec"), ns)
    return ns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify without writing")
    ap.add_argument("--sha", default=None, help="source commit (default: pinned)")
    args = ap.parse_args()

    ns = _load_helpers()
    sha = args.sha or ns.get("_GOOD_COMMIT")
    if not sha:
        raise SystemExit("no source commit: pass --sha")

    raw = ns["_read_from_git"](sha)
    if not raw:
        raise SystemExit(
            f"could not read {sha}:mcp/server.py from git.\n"
            f"Try: git fetch --depth=1 origin {sha}"
        )

    built = ns["_apply_lie_patch"](raw)

    if args.check:
        if not os.path.isfile(_TARGET):
            print(f"MISSING: {_TARGET}")
            return 1
        with open(_TARGET, "r", encoding="utf-8") as f:
            current = f.read()
        if current == built:
            print(f"OK: {_TARGET} is current ({len(built)} bytes)")
            return 0
        print(f"STALE: {_TARGET} differs from a fresh build ({len(current)} vs {len(built)} bytes)")
        return 1

    with open(_TARGET, "w", encoding="utf-8") as f:
        f.write(built)
    print(f"wrote {_TARGET} ({len(built)} bytes) from {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
