# mem20 Ruby SDK — verification evidence

This is the raw output behind the results summarised in the README. It was captured on
the **Sidney** host (now retired) against the mem20 server; nothing here is estimated.

- Host: the former `sidney` host — **retired**, no longer exists. Kali Linux
  (7.1.5+kali-amd64), `ruby 3.3.8 (2025-04-09)` at capture time
- Canonical repo: `github.com/bythewayz66-glitch/mem20` @ `main` (MIT)
- Server: mem20-mcp, release `v2.1.0rc2`, protocol `2025-06-18`, 270 tools

> **Surface re-verified 2026-11-01: the live surface is now 272 tools.** The
> capture below is kept verbatim as the historical record of the 0.2.0 run
> (270 tools). The current count and its measurement are in section 0.

## 0. Surface re-verification (2026-11-01)

Measured on `main` @ `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110` with
`MEM20_EXPECTED_TOOLS=272 python3 verify_mcp.py` (real `initialize` +
`tools/list` over stdio, not a source grep):

```
INIT: {"capabilities": {"tools": {"listChanged": false}}, "protocolVersion": "2025-06-18", "serverInfo": {"name": "mem20-mcp", "version": ""}}
TOOL_COUNT: 272
FIRST_8: ['memory_store', 'memory_recall', 'memory_probe', 'memory_reason', 'memory_status', 'memory_contradict', 'memory_related', 'memory_feedback']
LIE_TOOLS: 10 ['lie_acknowledge_cue', 'lie_dual_acknowledge', 'lie_feed_audio', 'lie_feed_transcript', 'lie_get_cues', 'lie_list_sessions', 'lie_seal_session', 'lie_set_baseline', 'lie_start_session', 'lie_status']
RESULT: PASS
```

The two tools added since the 0.2.0 capture are `vcs_asset_release_audit`
(RM-239) and `graph_execute_reversible_plan` (RM-052). Both are registered by
monkeypatching `VersionControlToolsMixin#register_versioncontrol_tools`, so the
domain-module count stays 27 while the domain-tool count rises 268 -> 270.

A static `grep` of `self.tools["..."] =` reports 282, which is **wrong**: each of
those two names is assigned twice (once in the installer, once in the patched
method). Only the live `tools/list` is authoritative here.

## 1. Syntax check

```
lib/mem20/client.rb            Syntax OK
lib/mem20/config.rb            Syntax OK
lib/mem20/errors.rb            Syntax OK
lib/mem20.rb                   Syntax OK
lib/mem20/transport/stdio.rb   Syntax OK
lib/mem20/version.rb           Syntax OK
```

## 2. RSpec suite

```
Finished in 0.32609 seconds (files took 0.155 seconds to load)
33 examples, 0 failures
```

The suite covers the config object, the module entry points, the error hierarchy, the
version constants, the client facade (argument stringification, the memory primitives,
the text extraction), and the stdio transport against a **real child process** (`initialize`
handshake, tool round-trip, the `ToolError` path, notification skipping and child reaping).

## 3. RuboCop

```
19 files inspected, no offenses detected
```

## 4. Gem build

```
Successfully built RubyGem
  Name: mem20-sdk
  Version: 0.2.0
  File: mem20-sdk-0.2.0.gem
```

## 5. Load smoke checks

```
# from the source tree
VERSION=0.2.0
SERVER_VERSION=2.1.0rc2
PROTOCOL_VERSION=2025-06-18
config_frozen_after_client=true

# from the installed gem
loaded_from=/var/lib/gems/3.3.0/gems/mem20-sdk-0.2.0/lib/mem20.rb
VERSION=0.2.0
```

## 6. Live store → recall round-trip

Run with `ruby -Ilib examples/quickstart.rb` against the real server
(`MEM20_CWD=/opt/mem20/mem20`). This is the **0.2.0 capture, kept verbatim**; the
surface has since grown to 272 (see section 0), so the `tools:` line below is
historical, not current.

```
server:       mem20-mcp (reported version "")
protocol:     2025-06-18
tools:        270   # historical: 0.2.0 capture, current surface is 272
sdk version:  0.2.0

store -> Stored in mem20 memory: [project] quickstart token ruby-quickstart-1791998110 (tags: quickstart,ruby)
recall -> Memory recall results for 'ruby-quickstart-1791998110' (category: , limit: 5):

round-trip: 5.805 ms
token 'ruby-quickstart-1791998110' recovered: true
```

The script exits `0` only when the distinctive token it stored is actually returned by
`memory_recall`; the run above exited `0`.

## What is deliberately not claimed

No memory-quality, retrieval-accuracy or cognition benchmark figures appear anywhere in
this SDK — none were measured. The numbers above describe this client's build, tests and
transport, not the quality of the memory engine it talks to.
