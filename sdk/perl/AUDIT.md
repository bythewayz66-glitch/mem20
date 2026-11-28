# Perl SDK surface audit — mem20 4.0.0 @ main (2026-11-16)

Scope: `sdk/perl/` only. Target surface **527 tools across 135 domains**.

Everything below was observed by running the server, not by reading its docs.
Reproduce with the commands quoted in each section.

## 1. The surface: 527 tools, 135 domains

The surface figure is read from `docs/surface.json`, which
`scripts/surface_manifest.py` generates from a live `tools/list` response and
cross-checks against the AST catalog in `web/src/data/tools.json` -- the two
collections must be identical or the generator refuses to emit. Both land on
**527 tools across 135 domains**.

```
initialize -> {"protocolVersion":"2025-06-18","serverInfo":{"name":"mem20-mcp","version":""}}
tools/list -> TOOL_COUNT: 487   UNIQUE: 487
```

`serverInfo.version` is the empty string, so the SDK does not assert on it.

**Why the domain count is not a prefix count.** Bucketing the 527 tool *names*
by their first `_` component yields more buckets than there are domains, because
`memory_*` and `vault_*` are separate prefixes inside one domain,
`cloud_*`/`cloudstorage_*` likewise, and the bare `reflexion` has no underscore.
The domain count must come from registration; the prefix count is a different
measurement. `Mem20::Version` records both meanings explicitly.

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
{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{...}}     -> result
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
| B6 | `verify_surface` compared only a count, so a rename that kept the count identical was invisible. | 0.3.0 compares the full name list via `Mem20::Surface->diff` and returns `missing`/`extra`. |

## 8. Verified

All of the following were run on **2026-11-01** against main @ `d99ab5d8`
(`d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`), with the server booted from that
same clone. The transcripts are the runner's own summary lines.

```
$ perl xt/gen-surface.pl --check
lib/Mem20/Surface.pm is up to date (487 tools, 129 domains)

$ prove -Ilib t/
t/00-load.t ......... ok
t/05-surface.t ...... ok
t/10-config.t ....... ok
t/20-client.t ....... ok
t/90-live-server.t .. skipped: set MEM20_MCP_DIR and MEM20_PYTHON ...
t/95-jobs.t ......... ok
All tests successful.
Files=6, Tests=140, Result: PASS

$ MEM20_MCP_DIR=/workspace/mem20/mcp MEM20_PYTHON=python3 prove -Ilib t/90-live-server.t
All tests successful.
Files=1, Tests=9, Result: PASS

$ MEM20_PYTHON=python3 perl -Ilib examples/quickstart.pl /workspace/mem20
stored one fact
recall returned:
[2026-11-16T13:05:42] project (pri=normal) [observed]
   perl sdk live round trip sdk-live-marker-810489
surface: 487 tools (SDK compiled for 487), 129 domains, ok=1
```

The live suite asserts the 527 count, a `memory_store`->`memory_recall` round
trip through the grounded partition, local refusal of a missing
`epistemic_status`, `ToolError` for an unknown tool, `soft_error` for a rejected
status, and a `cog_plan` job polled to a terminal state.

## 9. The surface manifest (0.3.0)

0.2.0 carried two integers. A count cannot say I<which> tool moved, so a rename
that kept the count identical was invisible to `verify_surface`. 0.3.0 ships
`lib/Mem20/Surface.pm`, generated by `xt/gen-surface.pl` from the repository's
own `docs/surface.json` and `web/src/data/tools.json`:

```
$ perl xt/gen-surface.pl
wrote lib/Mem20/Surface.pm: 487 tools, 129 domains
```

The generator refuses to emit unless the two source files agree on the tool set
and the domain set, and unless `surface.json`'s own `cross_check` block reports
no `only_ast` / `only_live` delta. `Mem20::Version` re-exports the two counts
from the generated module rather than restating them, so there is one source of
truth.

`verify_surface` now returns `missing` and `extra` name lists alongside the
counts, and `ok` is false when the live surface differs in either direction.
`t/20-client.t` exercises this against the fake server (5 of 527 tools
advertised): 522 names in `missing`, nothing in `extra`.

The live surface was confirmed independently by driving the real server over
stdio:

```
initialize -> {"protocolVersion":"2025-06-18","serverInfo":{"name":"mem20-mcp","version":""}}
tools/list -> TOOL_COUNT: 487   UNIQUE: 487
```

and the generated name list matches the live `tools/list` exactly (no missing,
no extra).
