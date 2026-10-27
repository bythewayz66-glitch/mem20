# mem20 — tool count correction to 270 / 27

Design note for the `270 tools / 27 domains` correction. This file exists because
the correction itself has to be auditable, not asserted.

## What was wrong

| Number | Where it came from | Why it is wrong |
|---|---|---|
| **257 / 26** | An older reconciliation | Predates the `lie_*` domain entirely, and undercounted `memory_*` at 49 against 52 actually registered |
| **268 / 26** | The "house number" in `CHANGELOG.md` v3.0.0 | Counted only the 26 modules under `mcp/tools/`, silently omitting the three root-level domain modules: `mcp/memory_tools.py`, `mcp/cognitive_tools.py`, `mcp/roadmap_tools.py` |

## What is true

**270 tools across 27 domains.** Derivation, all reproducible from `main`:

```bash
grep -rho 'self\.tools\["[^"]*"\]' mcp --include=*.py | wc -l        # 271 registration sites
grep -rho 'self\.tools\["[^"]*"\]' mcp --include=*.py | sort -u | wc -l   # 270 distinct names
grep -rn 'def register_.*_tools' mcp --include=*.py | wc -l          # 28 registration groups
```

| Step | Value |
|---|---:|
| `register_*_tools` groups | 28 |
| − A2A Hermes transport layer (`register_a2a_tools`) | −1 |
| **= domains** | **27** |
| registration sites | 271 |
| − duplicate (`lie_status`, declared at `lie_tools.py:69` and `:77`) | −1 |
| **= distinct tools** | **270** |

Sub-totals reconcile: the 27 domains hold **265** tools, plus the **5** `a2a_*`
tools = **270**. The full per-domain mapping, with every tool name and its
source module, is in [`docs/TOOL-DOMAINS.md`](../TOOL-DOMAINS.md).

## The duplicate is a real defect

`lie_status` is assigned twice — `mcp/tools/lie_tools.py:69` and `:77`. The second
assignment overwrites the first, so the server exposes 270 tools while the source
contains 271 assignments. This run did **not** fix it: removing a tool
registration changes the exposed schema, which is a behaviour change and belongs
with the tests, not with a docs correction. It is recorded here so the next
person does not have to rediscover it.

## Files corrected

| File | Change |
|---|---|
| `README.md` | 6 sites: layer table, toolchest line, MCP-surface heading, architecture diagram, transport note, "Tool domains" heading + prose. Prefix table corrected: `memory_*` 49→52, `world_model_*` 9→8, `imagination_*` 8→9, `lie_*` row added (10 tools), `a2a_*` labelled as the transport layer |
| `docs/index.html` | 4 sites: hero lede, "MCP-native and broad" card, install checklist, footer stat |
| `docs/02-tools-reference.md` | 1 site: header claim |
| `docs/05-complete-tools-reference.md` | 6 sites: header claim, 3 roadmap entries, 1 target, and the `TOTAL` table row (268/26 domains → 270/27 domains) |
| `docs/TOOL-DOMAINS.md` | New — the generated 27-domain mapping |

## Deliberately not changed

`CHANGELOG.md` lines 17, 63 and 95 still contain 257 and 268. Those are
**historical release records** — line 63 is the v3.0.0 entry stating what was
believed at that release, and line 17 is the Unreleased entry that already
announces the 270/27 correction. Rewriting history to match today's number
would make the changelog lie about its own past. The open question for a human
is whether line 63 should gain an inline "superseded by 270/27" marker; that is
an editorial decision, not a factual correction, so it was left alone rather
than guessed at.
