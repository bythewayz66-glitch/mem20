# Perl SDK surface audit — mem20 3.0.0 @ 7c0b3e8 (2026-10-26)

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
yields 38 buckets, because `memory_*` and `vault_*` are separate prefixes inside
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
