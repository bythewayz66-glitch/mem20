# mem20 — Desktop User Research, Personas & Wireframes (Step 08 / Step 13)

**As of:** 2026-10-14 · canonical HEAD `c27d555` · prepared by the UX research agent
**Source of truth:** https://github.com/bythewayz66-glitch/mem20

---

## What this is

The desktop-research and design deliverable for the mem20 memory + cognition substrate,
re-pointed at the newly designated canonical repository. It carries three things:

1. **Desk research** — an artefact audit of the canonical repo and the live MCP server surface,
   a category scan of adjacent OSS memory layers, and a JTBD outcome map.
2. **Four personas** — Agent Builder, Platform Engineer, Domain Integrator, Memory Operator —
   each with a population share and a computed opportunity score.
3. **Four low-fidelity wireframes** for the desktop surfaces that answer the underserved outcomes.

House figures are preserved exactly; only repo-dependent inputs move to the canonical state.

## What changed

The repository previously cited throughout this work, `github.com/JaysonAIOnline/mem20`,
returns **HTTP 404** and does not exist. Its install path (`pip install mem20`) is not
serviceable — the package is not on a package index. Every reference is now anchored to
`bythewayz66-glitch/mem20` at `c27d555`.

## Ground truth measured in this run

| Signal | Value | Source |
| --- | --- | --- |
| Canonical repo | `bythewayz66-glitch/mem20` | GitHub REST API |
| Default branch | `main` | GitHub REST API |
| As-of commit | `c27d555` (2026-10-14T17:02:28Z) | GitHub REST API |
| License | MIT | GitHub REST API |
| Tools (live) | **268** | `tools/list` against the real stdio server on sidney |
| `memory_*` tools | 49 | live inventory |
| Protocol | `2025-06-18` | `initialize` response, `serverInfo.name = mem20-mcp` |
| Subsystems | 293 | canonical `CANONICAL.md` |
| Stars / forks / releases | 0 / 0 / 0 | GitHub REST API |
| Issue tracker / discussions | disabled / disabled | GitHub REST API |
| Primary language | Python (16,490,922 bytes) | GitHub REST API |

The live `tools/list` returned exactly **268** tools, matching the house figure — the
inventory is captured in `data/tool_inventory.json` and embedded in the model.

## Research headline

Eight desired outcomes were framed; **five are underserved** (opportunity score ≥ 10),
at a mean opportunity of **14.4**, against a P0 go-condition of **≥ 12.0**.

| # | Desired outcome | Imp. | Sat. | Opportunity |
| --- | --- | --- | --- | --- |
| O1 | Persistence & recall fidelity across sessions | 9 | 2 | **16.0** |
| O2 | Trust boundary: grounded vs simulated is explicit | 8 | 1 | **15.0** |
| O4 | Tool discoverability across a 268-tool surface | 8 | 2 | **14.0** |
| O7 | Cost & latency governance for long-running agents | 9 | 3 | **15.0** |
| O8 | Access control & namespace isolation | 8 | 4 | **12.0** |
| O3 | Zero-friction setup | 4 | 7 | 4.0 |
| O5 | Interoperability with the existing MCP stack | 5 | 6 | 5.0 |
| O6 | Documentation & worked examples for first run | 6 | 7 | 6.0 |

Opportunity = `importance + max(importance − satisfaction, 0)` (Ulwick / ODI).

**The wedge is the trust boundary, not storage.** The live surface already ships the
primitives — `memory_audit_contamination`, `memory_set_epistemic_status`, `memory_promote`,
`memory_quarantine_simulated` — but nothing in the product makes them visible.

## Personas

| Persona | Population share | Opportunity |
| --- | --- | --- |
| Agent Builder | 30% | 16.4 |
| Platform Engineer | 24% | 11.5 |
| Domain Integrator | 22% | 15.1 |
| Memory Operator | 24% | 14.2 |

Weighted opportunity index: **14.41**. Shares are computed by largest-remainder from declared
research weights and sum to 100 exactly.

## Contents

| Path | What |
| --- | --- |
| `webpages/mem20-design-research/index.html` | The research report page (self-contained, no external assets) |
| `webpages/mem20-design-research/wireframes.html` | The four wireframes with behaviour notes |
| `data/personas.csv` | Personas: share + opportunity |
| `data/jtbd_opportunities.csv` | All eight outcomes with computed opportunity scores |
| `data/repo_reconciliation.csv` | Legacy → canonical repository reconciliation |
| `data/tool_inventory.json` | The 268 tool names captured live from `tools/list` |
| `model/design_model.py` | Deterministic model that generates every figure above |
| `publish_design_to_sidney.sh` | Publish script (Sidney via ssh, routed through gabe) |

## Reproduce every number

The model is deterministic and offline; it asserts its own invariants and fails rather
than emit a drifted figure.

```bash
/usr/bin/python3 model/design_model.py
/usr/bin/python3 model/design_model.py --self-test   # must exit 1 (proves the gate can fail)
```

Invariants the model enforces (all must hold or the run aborts):

- outcome count = 8 and underserved count = 5;
- the embedded tool inventory has exactly 268 entries and contains the expected tools;
- archetype person shares sum to 100;
- mean underserved opportunity = 14.4 and weighted opportunity index = 14.41;
- both arms of the P0 condition are load-bearing (the condition is not vacuously true).

## Install the server (system Python, no isolated environment)

mem20 is distributed from source — it is **not** published to a package index.

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
/usr/bin/python3 -m pip install --user -r requirements.txt

# Run the stdio server
MEM20_STORE_PATH=~/.mem20/store /usr/bin/python3 mcp/mcp_server.py
```

The server speaks MCP over stdio, negotiates protocol `2025-06-18`, and reports
`serverInfo.name = mem20-mcp`. Connect any MCP host.

## Publishing to Sidney

Standing programme instruction: work is published to the Sidney server over ssh, and that
publication is **routed through gabe** — gabe is the sole publish authority.

- **Sidney** `216.198.115.91:2222` — reachable; ssh accepts password/key.
- **gabe** gates the payload before publication. The executable deliverable
  (`model/design_model.py`) is gated with the written requirement and target-side evidence:
  a real run of the model on the target plus a `--self-test` that exits non-zero.

```bash
export SIDNEY_HOST=216.198.115.91 SIDNEY_PORT=2222 SIDNEY_USER=root
export SSHPASS=<secret>            # or SSH_KEY=/path/to/key
bash publish_design_to_sidney.sh
```

The script refuses to run without authentication material and never writes a secret into the
payload it publishes.

## Guardrails honoured

- No participant count is claimed that was not collected; the declared importance/satisfaction
  inputs are labelled as declared research inputs, not measurements.
- Zero releases, zero stars and the disabled issue tracker/discussions are stated visibly and
  used as evidence, not omitted.
- The append-only audit trail is described as append-only, never as tamper-proof.
- MIT licensing is stated as a fact about the repository, not as a moat.

---

**Disclaimer.** As an AI Agent, I cannot provide legally protected, personalized investment
advice. This analysis is for informational purposes only and does not constitute investment
advice or recommendations. Consult a licensed financial advisor before making investment
decisions.
