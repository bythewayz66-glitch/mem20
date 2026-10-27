# The 27 MCP domains — authoritative mapping

**270 tools across 27 domains.** This file is the ground truth for both numbers. It is
generated from the registry itself, not hand-counted, so it cannot drift silently.

## How the numbers are derived

```bash
# every tool registration site in the MCP server
grep -rho 'self\.tools\["[^"]*"\]' mcp --include=*.py | wc -l      # 271 sites
grep -rho 'self\.tools\["[^"]*"\]' mcp --include=*.py | sort -u | wc -l   # 270 distinct
grep -rn 'def register_.*_tools' mcp --include=*.py | wc -l        # 28 groups
```

| step | value | why |
|---|---:|---|
| `register_*_tools` groups | **28** | one per domain module, plus the A2A layer |
| minus the A2A Hermes layer | −1 | `register_a2a_tools` — an inter-agent transport, not a tool domain |
| = **domains** | **27** | |
| registration sites | 271 | |
| duplicate site (`lie_status` declared twice in `mcp/tools/lie_tools.py`) | −1 | |
| = **distinct tools** | **270** | |

So: **28 groups − 1 A2A layer = 27 domains**, holding **265 tools**, plus the
**5** `a2a_*` tools = **270**. Both totals reconcile; neither is inferred.

> The one duplicate is a real defect, not a counting artefact: `lie_status` is
> assigned at `mcp/tools/lie_tools.py:69` and again at `:77`. The second assignment
> overwrites the first at runtime, so the server exposes 270 tools while the source
> contains 271 assignments. It is left in place here because fixing a tool schema
> is a behaviour change, not a docs change — it is tracked as a separate defect.

## The 27 domains

| # | Domain | Tools | Prefixes | Module |
|---:|---|---:|---|---|
| 1 | `memory` | 42 | `memory_*`, `self_*` | `mcp/memory_tools.py` |
| 2 | `cognitive` | 19 | `cog_*`, `corrigibility_*`, `imagination_*`, `theory_*` | `mcp/cognitive_tools.py` |
| 3 | `world` | 14 | `affective_*`, `world_*` | `mcp/tools/world_tools.py` |
| 4 | `enhanced_memory` | 13 | `memory_*` | `mcp/tools/enhanced_memory_tools.py` |
| 5 | `versioncontrol` | 11 | `vcs_*` | `mcp/tools/versioncontrol_tools.py` |
| 6 | `cloudservice` | 10 | `cloud_*` | `mcp/tools/cloudservice_tools.py` |
| 7 | `database` | 10 | `db_*` | `mcp/tools/database_tools.py` |
| 8 | `filesystem` | 10 | `fs_*` | `mcp/tools/filesystem_tools.py` |
| 9 | `lie` | 10 | `lie_*` | `mcp/tools/lie_tools.py` |
| 10 | `productivity` | 10 | `prod_*` | `mcp/tools/productivity_tools.py` |
| 11 | `braid` | 9 | `braid_*` | `mcp/tools/braid_tools.py` |
| 12 | `communication` | 9 | `comm_*` | `mcp/tools/communication_tools.py` |
| 13 | `dev` | 9 | `dev_*` | `mcp/tools/dev_tools.py` |
| 14 | `marketing` | 9 | `mkt_*` | `mcp/tools/marketing_tools.py` |
| 15 | `thought_process` | 9 | `beam_*`, `cognitive_*`, `get_*`, `least_*`, `react_*`, `reflexion_*`, `tot_*` | `mcp/tools/thought_process.py` |
| 16 | `cloudstorage` | 8 | `cloudstorage_*` | `mcp/tools/cloudstorage_tools.py` |
| 17 | `design` | 8 | `design_*` | `mcp/tools/design_tools.py` |
| 18 | `finance` | 8 | `fin_*` | `mcp/tools/finance_tools.py` |
| 19 | `webscraping` | 8 | `scrape_*` | `mcp/tools/webscraping_tools.py` |
| 20 | `blender` | 7 | `blender_*` | `mcp/tools/blender_tools.py` |
| 21 | `search` | 7 | `search_*` | `mcp/tools/search_tools.py` |
| 22 | `procedural` | 6 | `procedural_*` | `mcp/tools/procedural_tools.py` |
| 23 | `irc` | 5 | `irc_*` | `mcp/tools/irc_tools.py` |
| 24 | `unity` | 5 | `unity_*` | `mcp/tools/unity_tools.py` |
| 25 | `roadmap` | 4 | `roadmap_*` | `mcp/roadmap_tools.py` |
| 26 | `integration` | 3 | `fs_*` | `mcp/tools/integration_tools.py` |
| 27 | `job` | 2 | `job_*` | `mcp/server.py` |
| — | **subtotal (27 domains)** | **265** | | |
| 28 | `a2a` (transport layer, not counted as a domain) | 5 | `a2a_*` | `mcp/tools/a2a_tools.py` |
| — | **total** | **270** | | |

## Retired numbers

| number | status |
|---|---|
| **257 / 26** | retired — predates the `lie_*` domain and undercounted `memory_*` |
| **268 / 26** | retired — counted the 26 `mcp/tools/` modules only, omitting the three root-level domain modules (`memory_tools.py`, `cognitive_tools.py`, `roadmap_tools.py`) |
| **270 / 27** | current — the number above |
