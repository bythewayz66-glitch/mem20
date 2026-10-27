# README install block + repo header — publish-ready (v3, canonical-repo-corrected)

**Use:** paste into the canonical repo README (github.com/bythewayz66-glitch/mem20), under the H1.
**Verified:** repo 200, MIT, Python, default branch main, pyproject version 2.1.0rc2.
**Supersedes:** v2, which pointed at a dead repo and carried an install pin that does not work on this tree.

---

## Why v3 exists (a substantive fix, not a relabel)

v2 told readers to pin an old SDK major. That instruction is wrong for the canonical repo. Two facts from the tree:

| Source | Fact |
|---|---|
| requirements.txt | mcp>=2.1.1 |
| pyproject.toml [project].dependencies | mcp>=2.1.1 |
| README Installation, pip | pip install . then mem20-mcp |

The canonical tree requires mcp 2.1.1 or newer. A reader following v2's old pin would install an SDK the tree does not use. v3 replaces the pin with pip install -r requirements.txt, the command the repo's own README and install.sh actually use.

Also corrected: the run command. v2 published python -m mcp_cognitive_substrate.cli, a module from the older, non-canonical repo. The canonical entry point is mcp/mcp_server.py, plus the mem20-mcp console script which wraps it via launcher.py.

---

## README H1 + intro

```markdown
# mem20

### Auditable agent memory — the memory layer you can prove.

mem20 is a persistent memory + cognition substrate for AI agents, exposed over the
Model Context Protocol as a JSON-RPC 2.0 service on stdio. It keeps *grounded*
memory (real observations, user statements, events) strictly separate from
*simulated* memory (hypotheticals, counterfactuals, model output), audits
contamination between the two, promotes content only on attached evidence, and
records every operation in an append-only, origin-tagged ledger.

**270 tools across 27 domains.** MIT licensed. Python. Self-hosted. Zero lock-in.
```

Badge note: static status badges are fine. The only actionable links (clone URL, install commands, client registration) point at the canonical repo.

---

## Install

mem20 installs from source. It is not yet published to PyPI, under any name.

The sequence is: clone the repo, cd into it, create a venv, install from requirements.txt (mcp, pydantic, anyio, numpy, faiss-cpu, sentence-transformers), then run the server as a script with MEM20_STORE_PATH set.

A bare registry install is not a valid install path today. Use the clone path above.

---

## Install as a package (console script)

`pip install .` builds the wheel and installs the mem20-mcp command; running mem20-mcp starts the MCP server plus the health endpoint on 8080. It is a thin launcher that locates the bundled mcp/ directory and runs it as a script, so the upstream MCP SDK import is never shadowed by the repo's local mcp/ directory.

---

## Install as an always-on service (systemd)

Clone to /opt/mem20, then run install.sh with your user and target dir. Verify with the health and metrics endpoints on port 8080.

What install.sh does: creates a venv, installs core deps from requirements.txt, generates the systemd unit from the template and enables plus starts it, defaults the store path to /opt/mem20/store, and supports a no-systemd mode for a manual run.

---

## Other install channels

Docker: build the image, run it publishing 8080 and mounting a named volume for the store. apt: make deb, dpkg the package, then check the service status and run the health probe.

---

## Register mem20 with an MCP client

For Claude Code or Cursor: add an stdio server pointing at <repo>/mcp/mcp_server.py, with MEM20_STORE_PATH in the env block. The equivalent JSON config uses command python3, args pointing at that same script, and an env object carrying the store path. Hermes uses the same script path in its mcp.servers setting.

---

## Benchmarks section (paste under Install)

Self-reported, measured on our own internal harness: hit rate 1.000 direct, 0.800 multi-hop, 0.000 adversarial, leak rate 0.000 on clean stores.

Read the 0.000 adversarial row honestly: hard adversarial queries defeat the retrieval path today. It is a known weakness and it is on the roadmap, not a smudge. These figures are self-reported on our own harness; they have not been independently audited and they are not reproducible from a script in this repository.

We also publish no LoCoMo or LongMemEval result comparable to Mem0 or Zep, and we do not claim one.

---

## Provenance / limits section (paste near the bottom)

### What auditable means here, and what it does not

mem20 gives you a grounded/simulated partition enforced at the storage layer, contamination auditing, evidence-based promotion, and an append-only origin-tagged ledger.

It is not tamper-proof and it is not unfakeable. The promotion gate requires prediction_error_evidence, either a linked prior prediction resolved in the item's favour or a registered external verifier, but that attestation is self-reported rather than cryptographically enforced. A prior internal audit flagged the gap.

The accurate claim is evidence-based promotion with an append-only audit trail.

---

## Guardrail check

- [x] No LoCoMo or LongMemEval claim; explicit disclaimer present
- [x] Adversarial 0.000 disclosed, framed as a known weakness, labelled self-reported
- [x] Promotion described as evidence-based with an append-only audit trail, never tamper-proof
- [x] Install commands match the tree (requirements.txt, mcp/mcp_server.py)
- [x] No bare registry install; canonical repo only
- [x] No stale old-org reference
- [x] No retired SDK pin
