# Troubleshooting the mem20 MCP Server Startup

> Practical, reproduction-based guide to the failure modes that actually occur when
> starting the mem20 MCP server. Every symptom below was reproduced against
> `bythewayz66-glitch/mem20` — the error strings, log lines and JSON bodies are copied
> from real runs, not paraphrased.
>
> For install/configuration basics see [Installation Guide](03-installation.md). For the
> tool surface see [Tools Reference](02-tools-reference.md).

---

## Contents

1. [Quick triage checklist](#quick-triage-checklist)
2. [Symptom A — "mem20 MCP server implementation not found" (shallow clone)](#symptom-a--mem20-mcp-server-implementation-not-found-shallow-clone)
3. [Symptom B — missing Python dependencies](#symptom-b--missing-python-dependencies)
4. [Symptom C — `conftest.py` / `mcp` SDK namespace shadowing](#symptom-c--conftestpy--mcp-sdk-namespace-shadowing)
5. [Symptom D — stdio transport vs the `:8080` health port](#symptom-d--stdio-transport-vs-the-8080-health-port)
6. [Symptom E — retrieving empty or degraded results](#symptom-e--retrieving-empty-or-degraded-results)
7. [Verifying the server: the MCP handshake](#verifying-the-server-the-mcp-handshake)
8. [MCP client registration formats](#mcp-client-registration-formats)
9. [One-shot repair script](#one-shot-repair-script)

---

## Quick triage checklist

Run these in order; the first one that fails tells you which section to read.

```bash
# 0. Start from the repo root of the checkout you are actually running.
cd /path/to/mem20

# 1. Is this a full clone? (shallow clones break startup — Symptom A)
git rev-parse --is-shallow-repository        # must print: false
git cat-file -t 6a2bdaab2434611a2edee5d26b93bcc500edb87b   # must print: commit

# 2. Is the real mcp SDK importable as a package (not a namespace dir)? — Symptom C
python3 -c "import mcp; print(getattr(mcp, '__file__', None))"
#   prints /usr/local/lib/python3.11/site-packages/mcp/__init__.py  -> good
#   prints None                                                     -> shadowed, see Symptom C

# 3. Are required deps present? — Symptom B
python3 -c "import mcp, pydantic, anyio; print('core ok')"

# 4. Does the server boot and answer a handshake? — see "Verifying the server"
python3 ./launcher.py        # expect a health log line on stderr, then it waits on stdin

# 5. Is the health endpoint live? (server must already be running)
curl -s http://127.0.0.1:8080/health
```

Expected healthy output for steps 4–5:

```
2026-10-23 00:41:21,546 INFO mem20.mcp health endpoint listening on :8080 (/health /ready /metrics)
```

```json
{"status": "ok", "service": "mem20-mcp", "uptime_seconds": 8.189}
```

---

## Symptom A — "mem20 MCP server implementation not found" (shallow clone)

### What you see

```
$ git clone --depth 1 --branch copilot/setup https://github.com/bythewayz66-glitch/mem20.git
$ cd mem20
$ git rev-parse --is-shallow-repository
true
$ python3 ./launcher.py
mem20 MCP server implementation not found.
Ensure this is a git checkout that contains commit 6a2bdaab2434611a2edee5d26b93bcc500edb87b (a normal clone does).
Or place the full server at mem20liez/_server_impl.py.
```

Exit code is **1**. No health log line is printed, nothing listens on `:8080`, and every
MCP client that spawns this command reports a dead server.

### Why it happens

`mcp/server.py` is a thin bootstrap loader, not the server itself. It resolves the real
implementation in this order:

1. `mem20liez/_server_impl.py` — an optional vendored copy (**not** in the repo).
2. `git show 6a2bdaab2434611a2edee5d26b93bcc500edb87b:mcp/server.py` — the last
   known-good implementation, read out of the object database and patched in memory.
3. Clear error.

A `--depth 1` clone only contains the tip commit's tree, so the object for `6a2bdaa…`
is not in `.git`. `git show` fails, rule 1 has nothing to read, and you get the error
above. The message is accurate — the checkout genuinely lacks the commit, it is not a
missing-file bug.

Note this is independent of which branch you cloned: the commit must be present as an
*object*, and a depth-1 fetch never brings it.

### Fix — one of three

**A1. Fetch just that commit into the shallow clone (fastest, keeps the clone shallow):**

```bash
git fetch --depth 1 origin 6a2bdaab2434611a2edee5d26b93bcc500edb87b
git cat-file -t 6a2bdaab2434611a2edee5d26b93bcc500edb87b   # -> commit
python3 ./launcher.py
```

**A2. Deepen the clone:**

```bash
git fetch --unshallow          # full history, guaranteed to contain the commit
# or, cheaper, deepen until the commit appears:
git fetch --deepen 200
```

**A3. Clone without `--depth` in the first place:**

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
```

**A4 (no git history at all — tarball, vendored copy, container export):** drop a full
implementation at `mem20liez/_server_impl.py`. The loader accepts it if the file exists
and is larger than 10 KB:

```bash
mkdir -p mem20liez
curl -fsSL "https://raw.githubusercontent.com/bythewayz66-glitch/mem20/6a2bdaab2434611a2edee5d26b93bcc500edb87b/mcp/server.py" \
  -o mem20liez/_server_impl.py
python3 ./launcher.py
```

### Prevent it

Anything that builds a mem20 environment must not use `--depth 1` — including VS Code
dev containers, Docker `ADD` of a shallow checkout, and CI setup steps. In CI, at minimum
append the A1 `git fetch` before running the server.

---

## Symptom B — missing Python dependencies

### What you see

`mcp/memory_tools.py` fails fast (`sys.exit(1)`) when the `mcp` SDK is absent:

```
Error: mcp package not installed. Please install with: pip install mcp
```

Exit code **1**, and in a pytest session this aborts the *whole* run rather than
skipping one test — one missing dep looks like a total suite failure.

Other modules fail lazily and less visibly: an `ImportError` is caught and the
corresponding tool returns a degraded message at call time (see Symptom E).

### What is required

| Package | Required? | Needed for | Declared in |
|---|---|---|---|
| `mcp>=2.1.1` | **Yes** | The MCP SDK itself — `from mcp.server import Server`. Without it the process exits 1 | `pyproject.toml`, `requirements.txt` |
| `pydantic>=2.13.4` | **Yes** | SDK/request models | `pyproject.toml`, `requirements.txt` |
| `anyio>=4.14.2` | **Yes** | `mcp.server.stdio` transport | `pyproject.toml`, `requirements.txt` |
| `aiohttp` | Yes for `a2a_*` tools | Agent-to-agent transport (`mcp/tools/a2a_tools.py`) | `copilot-setup-steps.yml` |
| `PyYAML` | Yes for YAML-driven tools | Lazy `import yaml` in `a2a_tools.py`, `enhanced_memory_tools.py` | `copilot-setup-steps.yml` |
| `httpx` | Yes for bridge/LLM paths | `bridge/server.py`, `llm.py`, agentz modules | `copilot-setup-steps.yml` |
| `cryptography` | Yes for signing/attestation | `braid_keyz/binding.py` (ChaCha20Poly1305), `mem20mktz`/`mem20sensorz` attestation | `copilot-setup-steps.yml` |
| `numpy>=1.24` | Optional* | Vector math | `pyproject.toml`, `requirements.txt` |
| `faiss-cpu>=1.7.4` | Optional* | Vector index — real hybrid retrieval | `pyproject.toml`, `requirements.txt` |
| `sentence-transformers>=2.2.0` | Optional* | Embeddings / cross-encoder rerank | `pyproject.toml`, `requirements.txt` |
| `pytest>=7` | Dev | Test suite | `[project.optional-dependencies].dev` |

\* Optional for *startup*, mandatory for *real* retrieval. Without them the store, ledger
and status tools work, but `memory_recall_hybrid` returns
`Error: No search dependencies installed`. Do not treat a green startup as a working
retrieval stack.

### Fix

```bash
# Core runtime (declared in requirements.txt)
python3 -m pip install -r requirements.txt

# The extras the server imports ad hoc
python3 -m pip install aiohttp httpx PyYAML cryptography

# Full retrieval stack — large (torch). Skip only if you accept degraded recall.
python3 -m pip install numpy faiss-cpu sentence-transformers

# Editable install: provides the `mem20-mcp` console script and package data
python3 -m pip install -e .
```

Verify each independently rather than assuming the aggregate worked:

```bash
python3 -c "import mcp, pydantic, anyio; print('core ok')"
python3 -c "import aiohttp, httpx, yaml, cryptography; print('extras ok')"
python3 -c "import numpy, faiss, sentence_transformers; print('retrieval ok')" \
  || echo "retrieval stack absent - recall_hybrid will be degraded"
```

A virtualenv is strongly recommended — the module `mcp` collides with the repo's `mcp/`
directory (Symptom C), and a venv keeps system Pythons from contributing stale copies:

```bash
python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install -U pip
```

---

## Symptom C — `conftest.py` / `mcp` SDK namespace shadowing

### What you see

Worst case, from the repo root:

```
Error: mcp package not installed. Please install with: pip install mcp
```
…even though `pip show mcp` reports it installed. Exit code 1.

The underlying state is visible with a one-liner — `__file__` is `None` because the name
resolved to a *directory*, not the SDK package:

```python
$ python3 -c "import mcp; print(mcp.__file__, mcp.__path__)"
None _NamespacePath(['/workspace/mem20/mcp'])
```

The same mechanism produces, for the nested packages, collection errors such as:

```
ImportError: cannot import name 'ActionSpec' from 'mem20unitiz' (unknown location)
```

### Why it happens

The repo contains a top-level `mcp/` *project directory with no `__init__.py`* — it is
the server's source folder, not a Python package. But the repo root is on `sys.path`
(it is the cwd), so Python matches `import mcp` against that directory first and treats
it as an **implicit namespace package**. It wins over the installed SDK, has no
`__file__`, and exports nothing. `from mcp.server import Server` then fails, and
`memory_tools.py` responds to that ImportError with `sys.exit(1)`.

The same shadowing hits every `<project>/<name>/` pair in the estate (e.g. the outer
`mem20unitiz/` directory shadowing the real `mem20unitiz` package), because the outer
directory has no `__init__.py` either.

This is why `launcher.py` runs `mcp/mcp_server.py` **as a script** via `runpy` instead of
importing it as `mcp.mcp_server` — importing it as a package would need the shadowing
`mcp` name to resolve correctly, which it cannot.

### Fix

**C1. Keep the SDK pre-bound before anything can shadow it (what `conftest.py` does).**
`conftest.py` at the repo root removes `""`, `"."` and the repo root from `sys.path`,
puts each real project root on the path instead, purges namespace-package entries, and
pre-imports the real `mcp` SDK while `sys.path` is still clean so the later `import mcp`
is a cache hit:

```python
try:
    import mcp as _real_mcp
    if getattr(_real_mcp, "__file__", None) is None:
        raise ImportError("mcp resolved to a namespace package, not the SDK")
except ImportError:
    pass  # SDK genuinely absent: say so per-test rather than aborting the session
```

With `conftest.py` in place, `pytest` from the repo root is safe. Use it:

```bash
pytest                       # conftest.py auto-loads
mem20verify tests            # canonical runner; honours per-package venvs + timeouts
```

**C2. Never invoke the server as a module.** These are correct:

```bash
python3 ./launcher.py            # recommended — resolves mcp/ and runpy-executes it
python3 mcp/mcp_server.py        # equivalent, path-absolute inside the script
cd mcp && python3 mcp_server.py  # also works
```

This is **wrong** and will re-trigger the shadow:

```bash
python3 -m mcp.mcp_server        # the repo dir is NOT a package
```

**C3. Don't `pip install` the repo's own `mcp/` directory.** Only
`pip install -e .` from the root, or `pip install mcp` (the SDK from PyPI).

**C4. Verify the fix:**

```bash
python3 -c "import mcp; print(mcp.__file__)"
# -> /usr/local/lib/python3.11/site-packages/mcp/__init__.py
```

If it prints `None`, the shadowing is still active — check that you are not running the
server as a module and that `conftest.py` has not been deleted.

**Why not add `__init__.py` to `mcp/`?** It would turn the server directory into a real
package named `mcp`, which is *worse* — it would permanently shadow the SDK. The
directory must stay an unimportable plain folder; every entry point avoids the collision
instead.

---

## Symptom D — stdio transport vs the `:8080` health port

### How it is supposed to behave

The default transport is **stdio JSON-RPC**: the client spawns the process and talks over
its stdin/stdout. Separately, and best-effort, the server starts a threaded HTTP health
endpoint so probes and dashboards have something to hit.

| Setting | Default | Meaning |
|---|---|---|
| `MEM20_TRANSPORT` | `stdio` | `stdio` (client-spawned) or `http` (long-lived server) |
| `MEM20_HEALTH_PORT` | `8080` | Port for `/health`, `/ready`, `/metrics` |
| `MEM20_HEALTH_DISABLE` | unset | Set to `1`/`true`/`yes` to skip the health server entirely |
| `MEM20_MCP_PORT` | `8082` | Only used when `MEM20_TRANSPORT=http` |
| `MEM20_LOG_LEVEL` | `INFO` | `DEBUG` for verbose startup tracing |

On a healthy boot, **stderr** carries exactly one line (stdout is reserved for JSON-RPC —
never write logs there):

```
2026-10-23 00:41:21,546 INFO mem20.mcp health endpoint listening on :8080 (/health /ready /metrics)
```

### Trap 1 — the server exits immediately and looks "broken"

```bash
$ echo '' | python3 mcp/mcp_server.py
2026-10-23 00:43:39,445 INFO mem20.mcp health endpoint listening on :8080 (/health /ready /metrics)
$ echo $?
0
```

Exit code 0 with no error. That is **correct stdio behaviour**: stdin reached EOF, so the
transport closed and the process exited. Under systemd with `StandardInput=null` this
becomes a restart loop.

Consequences and fixes:

- Manually smoke-testing with `< /dev/null` will always "fail" this way. Pipe something
  that stays open instead:
  ```bash
  sleep 300 | python3 ./launcher.py    # keeps stdin alive for 5 minutes
  ```
- For a durable systemd instance, use the supervisor that holds the stdin pipe open for
  the unit's lifetime:
  ```bash
  python3 mcp/stdio_guardian.py
  ```
- For an always-on server with a real HTTP port, switch transports instead:
  ```bash
  MEM20_TRANSPORT=http MEM20_MCP_PORT=8082 MEM20_HEALTH_PORT=8080 python3 ./launcher.py
  ```

### Trap 2 — `curl :8080` fails even though the server is running

The health server is started *before* the MCP transport handshake and binds on
`0.0.0.0`. Three real causes, in order of likelihood:

1. **You curled too early.** Bind + first response takes a moment after spawn:
   ```bash
   until curl -sf http://127.0.0.1:8080/health >/dev/null; do sleep 1; done
   ```
2. **The port is taken.** A bind failure is **non-fatal by design** — the MCP transport
   keeps working and you get a warning, not a crash:
   ```
   2026-10-23 00:43:12,222 WARNING mem20.mcp health endpoint disabled (could not bind :8080): [Errno 98] Address already in use
   ```
   Find the squatter and either stop it or move mem20:
   ```bash
   lsof -i :8080            # or: ss -lntp | grep 8080
   MEM20_HEALTH_PORT=9090 python3 ./launcher.py
   ```
3. **The health server was disabled** (`MEM20_HEALTH_DISABLE=1`) or you are running the
   guardian/supervisor variant that does not enable it.

A client-spawned stdio instance also means **one process per client**. Two editors each
spawn their own server; the second one loses the `:8080` bind and warns. That is expected,
not a misconfiguration — the transport is unaffected.

### The three endpoints

```bash
# Liveness — always cheap
curl -s http://127.0.0.1:8080/health
# {"status": "ok", "service": "mem20-mcp", "uptime_seconds": 8.189}

# Readiness — confirms the tool table is populated
curl -s http://127.0.0.1:8080/ready
# {"ready": true, "tools": 270}

# Metrics — counters, contamination rate, event taxonomy
curl -s http://127.0.0.1:8080/metrics
# {"service": "mem20-mcp", "uptime_seconds": 8.213, "tools_registered": 270,
#  "request_count": 0, "request_errors": 0, "memory_system_available": true,
#  "event_taxonomy": ["tool.call", "tool.success", ...]}

# Anything else is a 404, which is a useful "is this really mem20?" probe
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/nope   # -> 404
```

Two things worth reading closely:

- **`"ready": true` requires a non-empty tool table**, so `/ready` is a stronger signal
  than "the process didn't crash".
- **`"memory_system_available"`** in `/metrics` tells you whether the store engine loaded.
  `false` means memory tools will return errors even though the server is up.

---

## Symptom E — retrieving empty or degraded results

Server starts, handshake succeeds, tools list fine — but `memory_recall_hybrid` returns
`Error: No search dependencies installed`.

That is the graceful-degradation path: `memory_tools.py` sets
`MEMORY_SYSTEM_AVAILABLE = True` from the pure-Python store, so the server boots without
`faiss`/`sentence-transformers`, but the vector + cross-encoder half of hybrid retrieval
needs them.

```bash
python3 -c "import faiss, sentence_transformers" || \
  python3 -m pip install faiss-cpu sentence-transformers
```

To confirm what loaded:

```bash
curl -s http://127.0.0.1:8080/metrics | python3 -m json.tool | grep memory_system_available
```

Store-side empties are separate — a fresh install legitimately has zero entries:

```bash
curl -s http://127.0.0.1:8080/metrics    # request_count: 0 is normal on a new instance
ls -la ~/.mem20/store/                   # MEM20_STORE_PATH overrides the location
```

---

## Verifying the server: the MCP handshake

A process that stays alive is not a working MCP server. Verify the protocol end to end:
`initialize` → `notifications/initialized` → `tools/list`.

Save as `verify_mcp.py` in the repo root and run `python3 verify_mcp.py`:

```python
import json, subprocess, sys

p = subprocess.Popen([sys.executable, "./launcher.py"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, text=True, bufsize=1)

def send(obj):
    p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()

def recv():
    line = p.stdout.readline()
    return json.loads(line) if line.strip() else None

send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                 "clientInfo": {"name": "verify", "version": "1.0"}}})
init = recv()
print("INIT:", json.dumps(init)[:300])

send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
listed = recv()

count = len(listed["result"]["tools"]) if listed and "result" in listed else 0
print("TOOL_COUNT:", count)
if count:
    print("FIRST_5:", [t["name"] for t in listed["result"]["tools"][:5]])

p.terminate(); p.wait(timeout=5)
print("STDERR:", p.stderr.read()[:400])
sys.exit(0 if count else 1)
```

### Expected output

```
INIT: {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {"tools": {"listChanged": false}},
      "protocolVersion": "2025-06-18", "serverInfo": {"name": "mem20-mcp", "version": ""}}}
TOOL_COUNT: 270
FIRST_5: ['memory_store', 'memory_recall', 'memory_probe', 'memory_reason', 'memory_status']
STDERR: 2026-10-23 00:41:51,154 INFO mem20.mcp health endpoint listening on :8080 (/health /ready /metrics)
```

### Reading the result

| Observation | Meaning |
|---|---|
| `serverInfo.name == "mem20-mcp"` | You reached mem20, not some other MCP server |
| `protocolVersion: "2025-06-18"` | Negotiated with the installed SDK |
| **`TOOL_COUNT: 270`** | Full tool table registered — the healthy target |
| Count lower than 270 | A tool module failed to import; raise `MEM20_LOG_LEVEL=DEBUG` and check stderr |
| `TOOL_COUNT: 0` | Transport up but registration broken — almost always Symptom C |
| Count of 257 | You are reading stale docs, not a broken server — see below |

Note: `docs/README.md` advertises **257 tools across 26 domains**, while a live instance
registers **270**. The handshake number is authoritative. If you are debugging a
"missing tools" report, always quote the handshake count, not the README table.

A functional smoke test on the same connection (after `tools/list`):

```python
send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
      "params": {"name": "memory_status", "arguments": {}}})
print("STATUS:", recv()["result"]["content"][0]["text"])
```

Healthy output:

```
ledger events : 0
deep entries  : 0
MEMORY.md     : 0/2200 chars OK
USER.md       : 0/1375 chars OK
last event    : none
```

---

## MCP client registration formats

mem20 **is** an MCP server, so the integration point is server registration — not a
`gh` CLI extension and not a GitHub App. Register it in the client configuration.

### `.mcp.json` — portable (repo root)

This is the format the Copilot Agent Host reads natively. Keep it at the repository root:

```json
{
  "mcpServers": {
    "mem20": {
      "type": "stdio",
      "command": "python3",
      "args": ["./launcher.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### `.vscode/mcp.json` — VS Code format

VS Code uses a top-level `servers` key and supports `${workspaceFolder}`. This file is
provided so VS Code users keep IntelliSense; it is the VS Code-specific variant of the
same registration:

```json
{
  // Registers the mem20 MCP server for GitHub Copilot agent mode in VS Code.
  //
  // mem20 IS an MCP server, so this is the extension point that lets Copilot
  // agent mode call its memory, retrieval and cognitive tools directly.
  //
  // The launcher resolves mcp/ relative to the workspace and runs mcp_server.py
  // exactly as `python mcp/mcp_server.py` would. Transport is stdio.
  "servers": {
    "mem20": {
      "type": "stdio",
      "command": "python3",
      "args": ["${workspaceFolder}/launcher.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

`PYTHONUNBUFFERED=1` matters: a buffered stdout can delay JSON-RPC frames and make the
client time out on `initialize`.

Always point `command` at `launcher.py` (or at `mcp/mcp_server.py`) — never at
`-m mcp.mcp_server` (Symptom C).

### Other hosts

```bash
# Claude Code
claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py

# Hermes Agent
hermes config set mcp.servers.mem20 '["python3", "/path/to/mem20/mcp/mcp_server.py"]'
```

---

## One-shot repair script

For a checkout that refuses to start, run all the fixes in order:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/5 git history =="
if [ "$(git rev-parse --is-shallow-repository)" = "true" ]; then
  echo "shallow clone detected - fetching known-good commit"
  git fetch --depth 1 origin 6a2bdaab2434611a2edee5d26b93bcc500edb87b || git fetch --unshallow
fi
git cat-file -t 6a2bdaab2434611a2edee5d26b93bcc500edb87b >/dev/null \
  && echo "OK: implementation commit present" \
  || { echo "WARN: commit missing - falling back to vendored copy"; \
       mkdir -p mem20liez; \
       curl -fsSL "https://raw.githubusercontent.com/bythewayz66-glitch/mem20/6a2bdaab2434611a2edee5d26b93bcc500edb87b/mcp/server.py" -o mem20liez/_server_impl.py; }

echo "== 2/5 core deps =="
python3 -m pip install -q -r requirements.txt aiohttp httpx PyYAML cryptography

echo "== 3/5 SDK not shadowed =="
python3 -c "import mcp; assert getattr(mcp,'__file__',None), 'mcp is shadowed by ./mcp - do not run as a module'"
echo "OK: mcp SDK resolves to a real package"

echo "== 4/5 handshake =="
python3 verify_mcp.py

echo "== 5/5 health =="
(sleep 60 | python3 ./launcher.py >/tmp/mem20-health.log 2>&1 &)
until curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; do sleep 1; done
curl -s http://127.0.0.1:8080/ready; echo
pkill -f launcher.py || true
echo "All checks passed."
```

---

## Summary table

| Symptom | Root cause | One-line fix |
|---|---|---|
| `mem20 MCP server implementation not found` | `--depth 1` clone lacks commit `6a2bdaa…` | `git fetch --depth 1 origin 6a2bdaab2434611a2edee5d26b93bcc500edb87b` |
| `Error: mcp package not installed` + exit 1 | SDK genuinely absent, or shadowed by `./mcp` | `pip install mcp`; never run `python3 -m mcp.mcp_server` |
| `mcp.__file__ is None` | `./mcp/` namespace package wins over the SDK | Use `./launcher.py`; keep root `conftest.py` |
| `ImportError: cannot import name … (unknown location)` | Same shadowing on `<project>/<name>/` dirs | `conftest.py` + `mem20verify tests` |
| Health endpoint unreachable | Curled too early, port taken, or disabled | `MEM20_HEALTH_PORT=9090`; check the `WARNING … could not bind` line |
| Server exits 0 immediately | stdin EOF under stdio transport | `mcp/stdio_guardian.py`, or `MEM20_TRANSPORT=http` |
| `Error: No search dependencies installed` | `faiss`/`sentence-transformers` absent | `pip install faiss-cpu sentence-transformers` |
| Fewer than 270 tools | A tool module failed to import | `MEM20_LOG_LEVEL=DEBUG python3 ./launcher.py` |
