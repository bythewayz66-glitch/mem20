# Perl SDK surface audit — mem20 3.0.0 @ d99ab5d8 (2026-11-01)

Scope: `sdk/perl/` only. Target surface **272 tools across 27 domains**.

Everything below was observed by running the server, not by reading its docs.
Reproduce with the commands quoted in each section.

## 1. The surface: 272 tools, 27 domains

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

**Wire count.** Instantiating the registry and reading `tools/list` both give 272:

```
$ python -c 'from server import Mem20MCPServer; print(len(Mem20MCPServer().tools))'
TOOL_COUNT: 272
PREFIX_BUCKETS: 38
BARE: ['reflexion']
```

```
initialize -> {"protocolVersion":"2025-06-18","serverInfo":{"name":"mem20-mcp","version":""}}
tools/list -> TOOL_COUNT: 272   UNIQUE: 272
```

`serverInfo.version` is the empty string, so the SDK does not assert on it.

**Why 38 != 27.** Bucketing the 272 tool *names* by their first `_` component
yields 38 buckets, for three reasons — none of them the domain split:

1. Several domain modules expose tools under a **shortened prefix**, so one
   domain becomes one bucket: `versioncontrol` -> `vcs_`, `filesystem` -> `fs_`,
   `productivity` -> `prod_`, `database` -> `db_`, `cloudservice` -> `cloud_`,
   `marketing` -> `mkt_`, `finance` -> `fin_`, `communication` -> `comm_`,
   `webscraping` -> `scrape_`.
2. Seven tools are **bare or singleton** names whose first component is not a
   family at all: `reflexion`, `react_reason`, `least_to_most`, `beam_search`,
   `cognitive_substrate`, `get_cognitive_tree_state`, `graph_execute_reversible_plan`.
3. The rest are ordinary `family_*` prefixes (`memory_` 52, `lie_` 10, `prod_` 10,
   `imagination_` 9, `braid_` 9, ...).

There is **no `vault_` prefix** on this surface (`grep -c '^vault' ` -> 0); an
earlier revision of this file claimed one and that claim was wrong. The domain
count must come from registration; the prefix count is a different measurement.
`Mem20::Version` records both meanings explicitly.

`memory_` is the single largest bucket (52 tools) and is the only prefix that
maps one-to-one onto a domain, which is why it is the family the SDK gives
named accessors to.

**Local `mcp/tools/` has 26 files, not 27**: `memory_tools.py`,
`cognitive_tools.py` and `roadmap_tools.py` live directly in `mcp/`. The 27
modules are the 27 `register_*_tools()` mixins, which is what the domain figure
counts.

## 1a. The two tools added since the previous audit

`d99ab5d` ("ci(mcp): bump expected tool count 270 -> 272 after wave-1 merges")
documents the delta, and the wire confirms both:

```
$ grep -n 'vcs_asset_release_audit\|graph_execute_reversible_plan' /tmp/live_tools.txt
114:graph_execute_reversible_plan
253:vcs_asset_release_audit
```

| tool | origin | registered by |
|---|---|---|
| `vcs_asset_release_audit` | PR #157 (RM-239) | `mcp/tools/rm239_tools.py` |
| `graph_execute_reversible_plan` | PR #158 (RM-052) | `mcp/tools/rm052_tools.py` |

Both landed inside the **existing** `register_versioncontrol_tools()` call site,
so the domain count stayed 27 while the tool count moved to 272. That is the
ordinary case: the tool count drifts on almost every merge, the domain count
only moves when a new `register_*_tools()` call site appears. A guard that only
tracked domains would have missed this entirely — which is why
`t/90-live-server.t` asserts the exact tool count.

**How they attach matters, and it is not a plain mixin.** Neither file defines a
new `register_*_tools()` that `_setup_tools()` calls. Each one *wraps* the
existing method on the class:

```python
# mcp/tools/rm052_tools.py:104-115
original = VersionControlToolsMixin.register_versioncontrol_tools
if getattr(original, "_rm052_installed", False):
    return True

def register_versioncontrol_tools(self):
    original(self)
    self.tools["graph_execute_reversible_plan"] = _tool_spec()
    self._graph_execute_reversible_plan = _handle

register_versioncontrol_tools._rm052_installed = True
VersionControlToolsMixin.register_versioncontrol_tools = register_versioncontrol_tools
```

`rm239_tools.py` does the same with its own `_rm239_installed` sentinel. So
`grep -rn 'def register_versioncontrol_tools'` returns **three** definitions
(`versioncontrol_tools.py:36`, `rm052_tools.py:107`, `rm239_tools.py:110`) while
`_setup_tools()` calls it **once**. Consequences worth knowing:

- The "27 domains" figure counts **call sites**, not modules. The module count
  behind those call sites is higher (29 here: 27 + the two RM wrappers).
- The `_rmNNN_installed` sentinels make the patch idempotent, so importing the
  module twice does not double-register. Verified: `TOOL_COUNT: 272` and
  `UNIQUE: 272` — no duplicates.
- A tool count derived by grepping `def register_*_tools` would be wrong in both
  directions, which is why the count here comes from instantiating the registry.

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

All of the following were run on **2026-11-01** against main @ `d99ab5d8`
(`d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`), with the server booted from that
same clone. The transcripts are the runner's own summary lines.

```
$ prove -Ilib t/00-load.t t/05-surface.t t/10-config.t t/20-client.t t/95-jobs.t
t/00-load.t ......... ok
t/05-surface.t ...... ok
t/10-config.t ....... ok
t/20-client.t ....... ok
t/95-jobs.t ......... ok
All tests successful.
Files=5, Tests=109, Result: PASS
```

```
$ PYTHONPATH=<repo> MEM20_CANONICAL_MCP_ROOT=<repo>/mcp \
  MEM20_MCP_DIR=<repo>/mcp MEM20_PYTHON=python3 prove -Ilib t/90-live-server.t
t/90-live-server.t .. ok
All tests successful.
Files=1, Tests=8, Result: PASS
```

```
$ PYTHONPATH=<repo> MEM20_CANONICAL_MCP_ROOT=<repo>/mcp \
  MEM20_MCP_DIR=<repo>/mcp MEM20_PYTHON=python3 \
  perl -Ilib examples/quickstart.pl <repo>
stored one fact
recall returned:
Memory recall results for 'what build is prod on' (category: , limit: 5):

[2026-11-01T22:27:11] project (pri=normal) [observed]
   prod runs build 4127

[2026-11-01T22:25:00] project (pri=normal) [observed]
   perl sdk live round trip sdk-live-marker-188676


surface: 272 tools (SDK compiled for 272), 27 domains, ok=1
```

Note the argument to `quickstart.pl` is the **repo root**, not `mcp/`: the
example appends `mcp/` itself. Passing `mcp/` produces
`can't open file '<repo>/mcp/mcp/mcp_server.py'`.

The live suite asserts the 272 count, a `memory_store`->`memory_recall` round
trip through the grounded partition, local refusal of a missing
`epistemic_status`, `ToolError` for an unknown tool, `soft_error` for a rejected
status, and a `cog_plan` job polled to a terminal state.

## 9. The 0.2.0 -> 0.2.1 drift, and why the guard missed it

This is the most useful entry in this file, because the failure was in the
guard rather than in the SDK.

`d99ab5d` bumped the **CI** expectation to 272. `sdk/perl/` was not touched, so
it kept asserting 270 in four places. The hermetic suite stayed green (it never
contacts a server) and the live suite failed:

```
#   Failed test 'tools/list returns 270 tools'
#   at t/90-live-server.t line 67.
#          got: '272'
#     expected: '270'
```

`t/05-surface.t` exists precisely to catch this and did not, for two reasons:

1. **`270` was not in `@RETIRED`.** The list held 257/268/269/271 — every
   neighbour *except* the one that was actually live. A retired-count list has
   to include the count you are retiring.
2. **The literal check only matched `=>`.** `t/90-live-server.t` wrote
   `is( $surface->{expected_tools}, 270, ... )` — a comma, not a fat arrow — so
   the regex `expected_tools\s*=>\s*\d+` never fired.

Both are fixed: `270` is retired, the regex accepts `=>` or `,`, and the guard
now also asserts the live test *reads* the constants so the assertions cannot
simply be deleted. Verified by mutation — with the old `270` transcript still in
this file, `t/05-surface.t` fails at subtest 9:

```
#           matches '(?^:\b270\b(?=[^\n]{0,40}\b(?:tools?|tool surface)\b))'
# Looks like you failed 1 test of 44.
```

That is the guard doing its job on the exact text that used to pass it.

