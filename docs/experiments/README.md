# `docs/experiments/` — the 4.0 experiment register

The register of every **open hypothesis** for the mem20 4.0 release: what is being
tested, who owns it, which metric decides it, its measured baseline and its target.

| File | What it is |
|---|---|
| [`EXPERIMENT_REGISTER.md`](./EXPERIMENT_REGISTER.md) | The register, readable. Start here. |
| [`register.json`](./register.json) | The same register, machine-readable, built to be diffed. |
| [`build_register.py`](./build_register.py) | Regenerates both from committed artifacts. |
| [`verify_register.py`](./verify_register.py) | Checks the register still matches the tree. |

## Why this exists

The repo already had three separate documents that each carried part of the
picture — `docs/benchmarks/experiment-registry.md` (which retrieval modes are
scored), `docs/renovation/4.0/RENOVATION_PLAN.md` (per-subsystem owners and
acceptance criteria), and `docs/ops/program-scoreboard-2026-11-01.md` (release
signals). None of them answered the release question: **what is still open, who
owns it, and what number would close it.**

This register answers that in one place, and every row points at the artifact its
baseline came from.

## Sourcing rule

Every baseline is read from a committed file or produced by a documented command:

| Source | Feeds |
|---|---|
| `docs/surface.json` | tool/domain surface counts, unwired tool count |
| `benchmarks/results/latest.json` | retrieval hit rates and p50 latency |
| `docs/renovation/4.0/subsystem-assignments.csv` | the authoritative owner map |
| `scripts/renovation/conformance.py` | the 7-criterion conformance gate |

Nothing is hand-typed. Nothing is estimated. Nothing is carried over from a chat
message — the program's standing rule is that a deliverable exists only as a
commit SHA on a pushed branch or a file committed under `docs/`.

## Regenerate

```bash
python3 docs/experiments/build_register.py     # re-runs the gate, rebuilds both files
python3 docs/experiments/verify_register.py    # 235 assertions against the tree
```

Both exit non-zero if the tree and the register disagree. Reuse an existing gate
run with `--conf /tmp/conf.json` when you have just run the gate yourself.

## Status vocabulary

- **open** — no completed measurement against the target yet. All ten rows are here.
- **accepted** — the metric reached its target on a measurement that exists.
- **rejected** — the metric missed, or the framing was wrong.

`verify_register.py` **fails** any row marked accepted or rejected that does not
carry a completed measurement. A register cannot promote a hypothesis on
intent — the same rule `experiments.json` applies to `scored` flags.

## What this register deliberately does not do

- It does not claim a hypothesis is validated.
- It does not re-measure retrieval; it reads the benchmark of record.
- It does not resolve the 67-vs-211 subsystem count — `H-4.0-10` exists *because*
  that gap is open.
- It does not invent owners for unowned subsystems — `H-4.0-06` and `H-4.0-07`
  record the gap instead of papering over it.
