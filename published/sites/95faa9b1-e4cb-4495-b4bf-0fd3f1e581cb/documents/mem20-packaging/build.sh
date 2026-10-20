#!/usr/bin/env bash
# Build a correct mem20 wheel from the canonical tree.
#
# Why a script instead of a bare `python -m build`: the server tree has to be
# staged into the `mem20_runtime` package first. Skipping the staging step is
# what produced a 13-entry wheel with no server in it.
#
# Usage:
#   bash build.sh [path-to-checkout]     # default: ./mem20_canon
set -euo pipefail

SRC="${1:-mem20_canon}"
[ -d "${SRC}" ] || { echo "FATAL: no checkout at ${SRC}" >&2; exit 2; }
cd "${SRC}"

echo "==> source: $(pwd) @ $(git rev-parse --short HEAD 2>/dev/null || echo 'not a git tree')"

# Remove every artifact that could mask a broken build.
rm -rf build dist ./*.egg-info mem20_runtime

./scripts/stage_runtime.sh stage
./scripts/stage_runtime.sh verify
python3 -m build --wheel --no-isolation . 2>&1 | tail -2

echo "==> auditing wheel"
python3 - <<'PY'
import glob, sys, zipfile
w = sorted(glob.glob("dist/mem20-*.whl"))[-1]
n = zipfile.ZipFile(w).namelist()
server = any(x == "mem20_runtime/mcp/mcp_server.py" for x in n)
pyc = sum(1 for x in n if x.endswith(".pyc") or "__pycache__" in x)
print(f"    {w}")
print(f"    entries={len(n)}  server={server}  pyc={pyc}")
if not server or pyc:
    print("    FAIL: wheel is malformed", file=sys.stderr)
    sys.exit(1)
print("    OK")
PY

# Leave the tree clean for the next build.
./scripts/stage_runtime.sh unstage
echo "==> done: ${SRC}/dist"
