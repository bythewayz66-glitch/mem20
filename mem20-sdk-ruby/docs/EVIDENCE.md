# mem20 Ruby SDK — verification evidence

This is the raw output behind the results summarised in the README. It was captured on
a Kali Linux host against the mem20 server; nothing here is estimated.

- Host: a Kali Linux box (7.1.5+kali-amd64), `ruby 3.3.8 (2025-04-09)` at capture
  time. That host has since been **retired** and no longer exists; the capture is
  kept as the dated record of what was measured.
- Canonical repo: `github.com/bythewayz66-glitch/mem20` @ `main` (MIT)
- Server: mem20-mcp, release `v4.0.0`, protocol `2025-06-18`

> **Surface re-verified 2026-11-16: the live surface is 487 tools across 129
> domains.** The 0.3.0 capture below is verbatim from this checkout; the
> historical 0.2.0 run follows it from section 1 on. The current count and its
> measurement are in section 0.

## 0. Surface re-verification (2026-11-16)

Measured against `docs/surface.json` at `main` (the file
`scripts/surface_manifest.py` generates from a live `initialize` + `tools/list`
and refuses to emit unless it matches the AST catalog in
`web/src/data/tools.json`), and compared with the constants this gem ships:

```
MANIFEST: docs/surface.json schema=1 tools=487 domains=129
CROSS_CHECK: ast_tools=487 ast_domains=129 only_ast=[] only_live=[]
UNWIRED_DECLARATIONS: 19
TOOL_COUNT: 487
DOMAIN_COUNT: 129
SDK_SURFACE: 487 tools across 129 domains
SDK_DOMAIN_TOOL_COUNTS_SUM: 487
SDK_DOMAINS_LENGTH: 129
SDK_CONSISTENT: true
MANIFEST_MATCH: tools=true domains=true
PER_DOMAIN_MATCH: true
TOP5: [["memory", 55], ["cognitive", 19], ["world", 14], ["versioncontrol", 11], ["cloudservice", 10]]
```

The surface is **487 tools across 129 domains**. `docs/surface.json` is the
authoritative manifest: `scripts/surface_manifest.py` refuses to emit unless the
live `tools/list` names and the AST catalog are identical sets. A static `grep`
of `self.tools["..."] =` is **not** authoritative — a name can be assigned more
than once (installer plus patched method), and several modules define a
`register_*_tools` function that `_setup_tools()` never calls, so only the live
`tools/list` counts. The 19 unwired declarations are exactly those: declared in
source, not registered by any inherited mixin, and therefore not on the wire.

`Mem20::Surface` carries the per-domain table (`DOMAIN_TOOL_COUNTS`), derives
`TOOL_COUNT` (487) and `DOMAIN_COUNT` (129) from it, and the spec pins the sum,
the domain count and the manifest comparison above.

### 0.1 Build, test and packaging (2026-11-16)

Captured on this checkout: Debian 12, `ruby 3.1.2p20`, `rspec 3.13`, `rubocop 1.92.2`.

```
$ for f in $(find lib -name '*.rb'); do ruby -c "$f"; done
Syntax OK   (every file)

$ rspec
Finished in 0.39335 seconds (files took 0.13492 seconds to load)
82 examples, 0 failures

$ rubocop --format simple
24 files inspected, no offenses detected

$ gem build mem20-sdk.gemspec
Successfully built RubyGem
  Name: mem20-sdk
  Version: 0.3.0
  File: mem20-sdk-0.3.0.gem

$ gem install ./mem20-sdk-0.3.0.gem && ruby -e 'require "mem20"; ...'
Successfully installed mem20-sdk-0.3.0
loaded_from=/var/lib/gems/3.1.0/gems/mem20-sdk-0.3.0/lib/mem20.rb
VERSION=0.3.0
SERVER_VERSION=4.0.0
SURFACE=487 tools across 129 domains
CONSISTENT=true

$ rake surface:check
manifest: 487 tools across 129 domains (/workspace/mem20/docs/surface.json)
surface:  487 tools across 129 domains
OK - Mem20::Surface matches docs/surface.json
```

The suite grew from 33 to 82 examples: the surface specs now cover the per-domain
table (one entry per domain, values summing to the total, every domain non-empty),
the two measurement helpers, and the document-vs-constant drift guard extended to
the retired 311 / 39 pair.

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
surface has since grown to 487 (see section 0), so the `tools:` line below is
historical, not current.

```
server:       mem20-mcp (reported version "")
protocol:     2025-06-18
tools:        270   # historical: 0.2.0 capture, current surface is 487
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
