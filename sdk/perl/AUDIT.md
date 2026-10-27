# Perl SDK surface audit — mem20 3.0.0 @ 7c0b3e8 (2026-10-26)

Scope: `sdk/perl/` only. Target surface **270 tools across 27 domains**.

Everything below was observed by running the server, not by reading its docs.
Reproduce with the commands quoted in each section.

## 1. The surface: 270 tools, 27 domains

Two independent probes agree.

**Registration count.** `mcp/server.py::_setup_tools()` invokes 27
`register_*_tools()` domain modules (memory, cognitive, roadmap, world,
procedural, blender, unity, integration, a2a, thought_process, cloudservice,
cloudstorage, communication, database, design, dev, enhanced_memory,
filesystem, finance, marketing, productivity, search, versioncontrol,
webscraping, braid, irc, lie). An inline `register_job_tools()` in `server.py`
adds `job_status`/`job_wait` but is not an `mcp/tools/` domain module.

```
$ ls mcp/tools/*.py | grep -v __init__ | wc -l
26                      # + mcp/{memory,cognitive,roadmap}_tools.py = 27 modules
```

**Wire count.** Instantiating the registry and reading `tools/list` both give 270:

```
$ python -c 'from server import Mem20MCPServer; print(len(Mem20MCPServer().tools))'
TOOL_COUNT: 270
PREFIX_BUCKETS: 37
BARE: ['reflexion']
```

```
initialize -> {"protocolVersion":"2025-06-18","serverInfo":{"name":"mem20-mcp","version":""}}
tools/list -> TOOL_COUNT: 270   UNIQUE: 270
```

`serverInfo.version` is the empty string, so the SDK does not assert on it.

**Why 37 != 27.** Bucketing the 270 tool *names* by their first `_` component
yields 37 buckets, because `memory_*` and `vault_*` are separate prefixes inside
one domain, `cloud_*`/`cloudstorage_*` likewise, and the bare `reflexion` has no
underscore. The domain count must come from registration; the prefix count is a
different measurement. `Mem20::Version` records both meanings explicitly.

**Local `mcp/tools/` has 26 files, not 27**: `memory_tools.py`,
`cognitive_tools.py` and `roadmap_tools.py` live directly in `mcp/`. The 27
modules are the 27 `register_*_tools()` mixins, which is what the domain figure
counts.

## 2. `initialize` will not accept an empty `clientInfo`

```
{"protocolVersion":"2025-06-18","capabilities":{}}                        -> -32602
{"protocolVersion":"2025-06-18","capabilities":{}, "clientInfo":{...}}     -> result
```

`capabilities: {}` is fine; omitting `clientInfo` is not.

## 3. Three different failure shapes

| Probe | Wire response | Meaning |
|---|---|---|
| unknown **method** | `{"error":{"code":-32601,...}}` | JSON-RPC error object |
| unknown **tool** | `{"result":{"content":[{"text":"Error: Unknown tool 'x'"}],"isError":true}}` | **protocol success** |
| `memory_store` with no `epistemic_status` | `isError:false`, text `"Error: epistemic_status is required. ..."` | **protocol success** |
| `memory_store` with `epistemic_status:"totally_made_up"` | `isError:false`, text `"Error storing memory: Invalid epistemic_status ..."` | **protocol success** |
| `memory_store` with `content:""` | `isError:false`, text `"Stored in mem20 memory: [general]  ..."` | stored an empty fact |

The transport already turned a JSON-RPC error object into `Mem20::ToolError`.
The other three arrived as *successful* responses, so a caller's `eval {}` never
fired: a rejected write was indistinguishable from a stored fact. Fixed by
normalising both `isError` shapes into `Mem20::ToolError`, with `soft_error`
flagging the `isError:false`-but-`Error`-prefixed case.

## 4. `memory_store` requires `epistemic_status` at the schema level only

```json
"required": ["content", "epistemic_status"]
```

The server does not enforce it: a call without it stores nothing useful and
reports `isError:false`, and a call with `content:""` stores an empty record.
Both are silent data loss. The SDK refuses both locally
(`Mem20::ValidationError`) rather than forwarding them.

`epistemic_status:"unlabeled"` and `"imagined"` are both **accepted by the
server and written into grounded memory**, even though the tool's own
description says invented content belongs in the simulated partition and that
`unlabeled` is refused by the epistemic veto. Neither refusal happens. The SDK
therefore rejects `imagined` on `memory_store` and points the caller at
`memory_simulate_store`.

`category` is a closed enum in the schema (`user_pref|project|tool|general`)
but the server accepts anything:

```
category="deploys" -> "Stored in mem20 memory: [deploys] ..." isError=false
```

Because rejecting that locally would refuse calls the server honours, enum
enforcement is opt-in (`strict => 1`) while the `epistemic_status` rules above
are always applied.

## 5. Long-running tools return a job envelope

25 tools are listed in `Mem20MCPServer.LONG_RUNNING_TOOLS`. They answer
immediately with:

```json
{"job_id":"1d68a688ff44","status":"running","tool":"cog_plan","poll":"job_status","wait":"job_wait"}
```

as the *text payload of a successful result*. A caller that assumes one
response carries the answer silently gets that JSON. `job_status`/`job_wait`
are the poll primitives; `Mem20::Client` adds `job_from`, `wait_for_job` and
`call_tool_await`.

## 6. Server-start preconditions that bite

- `requirements.txt` omits **`aiohttp`**, which `mcp/tools/a2a_tools.py` imports
  at module scope. Without it the server dies with
  `ModuleNotFoundError: No module named 'aiohttp'` before serving anything.
  Install it alongside the pinned set.
- The server must run with the **repo root** as cwd when invoked as
  `python mcp/mcp_server.py`, or `mcp/` as cwd when invoked as
  `python mcp_server.py`. `Config->cwd` was documented but never applied by the
  transport, so the child inherited the caller's directory and died with
  `can't open file '<caller>/mcp_server.py'`. Fixed.
- A missing `mcp` package is reported **on stdout, not stderr**
  (`Error: mcp package not installed...`). The transport correctly rejects that
  as `invalid JSON from mem20 server` rather than hanging.

## 7. Bugs found and fixed in the SDK

| # | Symptom | Fix |
|---|---|---|
| T1 | Timeout path **hung forever**: `_drain_stderr` did a blocking `sysread` on stderr while composing the timeout message. Reproduced as `timeout 12` exit 124. | stderr put in `O_NONBLOCK`; the drain is bounded and cannot block. Now throws at 2.00s with the stderr tail. |
| T2 | No lazy handshake: `tool()` sent `tools/call` before `initialize`, and the server answered `-32602 Invalid request parameters`. | `request()` performs `initialize_session` for any method except `initialize`. |
| T3 | `Config->cwd` never applied. | `chdir` before `open3`, restored after the spawn; a clear `TransportError` if the directory is missing. |
| T4 | One `sysread` could deliver several responses; only the first was consumed. | Complete lines are buffered in `pending`; a single unterminated frame is capped at 8 MiB. |
| B1 | `tool($name, {})` (the README's own example) built `{"HASH(0x...)": undef}` as `arguments`. | `_params_from` accepts a hashref **or** a flat pair list, refuses odd-length and mixed forms. |
| B2 | `Mem20::Client::text($hits)` returned `''` — the documented call consumed the envelope as its invocant. | `text` works as both function and method. |
| B3 | `memory_store` did not require `epistemic_status`, and let `imagined` into grounded memory. | Required locally; grounded statuses enumerated; `imagined` redirected to `memory_simulate_store`. |
| B4 | `isError:true` / `Error`-prefixed payloads looked like success. | Normalised to `ToolError` (`is_error` / `soft_error`). |
| B5 | No job polling; no surface assertion. | `job_from`, `wait_for_job`, `call_tool_await`, `verify_surface`, `tool_schema(s)`. |

## 8. Verified

All of the following were run against a **clean clone of this branch**, so they
describe the tree the PR actually ships.

```
$ prove -Ilib t/*.t
t/00-load.t ......... ok
t/10-config.t ....... ok
t/20-client.t ....... ok
t/90-live-server.t .. skipped: set MEM20_MCP_DIR and MEM20_PYTHON ...
All tests successful.
Files=4, Tests=57, Result: PASS

$ MEM20_MCP_DIR=/opt/mem20/mcp MEM20_PYTHON=python3 prove -Ilib t/90-live-server.t
All tests successful.
Files=1, Tests=8, Result: PASS

$ MEM20_PYTHON=/opt/mem20/.venv/bin/python perl -Ilib examples/quickstart.pl /opt/mem20
stored one fact
recall returned:
[2026-10-27T02:02:51] project (pri=normal) [observed]
   prod runs build 4127
surface: 270 tools (SDK compiled for 270), 27 domains, ok=1
```

The live suite asserts the 270 count, a `memory_store`->`memory_recall` round
trip through the grounded partition, local refusal of a missing
`epistemic_status`, `ToolError` for an unknown tool, `soft_error` for a rejected
status, and a `cog_plan` job polled to a terminal state.
