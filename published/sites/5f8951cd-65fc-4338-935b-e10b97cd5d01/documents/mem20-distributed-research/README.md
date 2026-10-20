# mem20 — Distributed Research: Canonical Repo Rebase

**As of:** 2026-10-14 · prepared by Experiment Tracker · published via gabe
**Source of truth:** https://github.com/bythewayz66-glitch/mem20 (branch `main`, MIT)

---

## What this is

The distributed-research leg of the mem20 canonical-repository rebase. It
delivers the deterministic engine that runs one research corpus across four
independent mem20 nodes and merges their results without centralising the source
data — the machine-executable core behind the *Federated Research Grid*
capability. Every figure below is produced by `distributed_research.py` on a
real run; none is written by hand.

## Publish record

The artifact was published through **gabe**, the sole publish authority on the
Sidney host.

| Field | Value |
|---|---|
| Manifest seq | **222** |
| Action | **publish** |
| Verdict | **pass — "No non-conformance found"** |
| Judge | `gabe-judge-1527286` (nvidia/nemotron-3-super-120b, `real-llm-call`) |
| Live path | `/opt/mem20/live/distributed_research.py` |
| Artifact sha256 | `67a9e56edd58d7f9a07642d998b46f61af64bf74f728adce61fdf34567e8af02` |
| Chain | **chain ok (223 entries)**, halted=false |

The live file is byte-identical to the staged artifact (same sha256), so the
published surface is traceable to the reviewed source.

## What changed

The retired reference `github.com/JaysonAIOnline/mem20` returns HTTP 404. The
canonical repository is now `github.com/bythewayz66-glitch/mem20` at `main`, and
the engine fetches its repository fields from real repository state at run time
rather than from a remembered answer:

| Field | Value | Source |
|---|---|---|
| Canonical repository | `https://github.com/bythewayz66-glitch/mem20` | fetched `CANONICAL.md` |
| Branch / license | `main` / MIT | fetched `CANONICAL.md` |
| Tracked files | 9,882 | fetched `CANONICAL.md` |
| `mem20*z` subsystems | 293 | fetched `CANONICAL.md` |
| Live tool count | 257 | real `tools/list` on each node |
| Protocol | `2025-06-18` | real `initialize` handshake |

## How the federation works

1. **Plan.** The researcher supplies a research-plan file on the command line;
   the engine hard-codes no corpus, slice, protocol, path or timeout, and
   assumes no default plan path.
2. **Split.** The corpus is partitioned across four headless mem20 nodes
   (`node-a`…`node-d`); each node is a real stdio MCP server with its own
   private store.
3. **Plant.** Each node stores only its declared slice of the corpus.
4. **Probe.** The whole corpus is recalled back from every node, and the engine
   records which findings each node actually returns (the echoed-query header is
   dropped, so a finding counts only when the node really returns it).
5. **Consolidate.** The per-node result sets are merged into one research set;
   the engine reports the union coverage and the redundancy factor.

### Real run (on the target host)

```
nodes joined: 4
live tool count per node: {'node-a': 257, 'node-b': 257, 'node-c': 257, 'node-d': 257}
negotiated protocol: ['2025-06-18']
corpus findings: 6
union coverage: 6/6 = 1.0
redundancy factor: 2.5
canonical repository: https://github.com/bythewayz66-glitch/mem20
canonical tracked files: 9882
canonical subsystems: 293
exit rc=0
```

The engine enforces its own invariants — every node returns exactly its declared
slice; the nodes agree on server id, negotiated protocol and tool count; every
tool descriptor carries a distinct name — and exits non-zero rather than report a
drifted or unmeasured figure. Invariants are enforced with explicit exceptions,
never `assert`, so they survive an optimised interpreter (`python3.14 -O`); the
captured evidence includes that second run.

## Contents

| Path | What |
|---|---|
| `distributed_research.py` | Deterministic merge engine (the published artifact) |
| `research_plan.txt` | The run-time plan: corpus, node slices, protocol, timeouts |
| `requirement.txt` | The written requirement the artifact was gated against |

Regenerate all numbers with:

```bash
python3 distributed_research.py research_plan.txt
```

## Gate

Publishing is routed through gabe. The artifact passed gabe's full gate — the L1
deterministic floor (including all sealed ban detectors), the L2 adversarial LLM
judge, and the judge's signature over the append-only, hash-chained manifest —
before it reached the live surface.
