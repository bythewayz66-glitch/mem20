# mem20crewz - Upgrade Plan

**Date:** 2026-10-15 - **Scope:** `mem20crewz/` @ `main`
**Standing rule:** *features are never removed - they are fixed or completed.*

---

## 1. Current state assessment

`mem20crewz` is a **cleanroom rebuild** of the Crew/Agent/Task/Flow surface directly on mem20 primitives (memory self-model, `cog` reasoning, roadmap-backed runs, A2A fan-out to 22 peers, procedural skills, epistemic/plan guardrails). **27 files, ~4,162 Python LOC.**

Measured this session:

| Aspect | State | Evidence |
|---|---|---|
| Package import | OK (after declaring deps) | `import mem20crewz` OK once `pyyaml` installed |
| Test suite | **52/52 pass** | `pytest mem20crewz/tests` green **after** installing `aiohttp` |
| Declared deps | BROKEN - `dependencies = []` while code imports `yaml` + `aiohttp` | `pyproject.toml`; `a2a.py:28`, `a2a.py:254` |
| Feature parity pass | OK - Documented | `docs/PLAN.md` section 7: 22/22 feature tests, delegation gates, code-exec sandbox, hierarchical manager, cache, router |
| Base class ergonomics | PARTIAL - Bare `NotImplementedError`, not `abc.ABC` | `neural.py:33,37,40,43,53` |
| Runtime state | Committed demo output | `runtime/outputs/fountain-brief.md`, `fountain-research.md` |

**Verdict:** the healthiest of the three surfaces - it *works*. Its upgrade is about public trust and last-mile packaging, not repair.

---

## 2. Upgrade work items

### HIGH

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| K1 | **Declare runtime dependencies** in `mem20crewz/pyproject.toml` (`pyyaml`; `aiohttp` for A2A) so `pip install mem20crewz` yields a framework whose A2A path works. Split optional A2A transport into an extra if desired, but it must be installable. | `tooling`, `severity:high` | `dependencies = []` vs `a2a.py:28,254` |
| K2 | **Make the suite green from a clean install** - add a `[dev]` extra (pytest, ruff, aiohttp) and verify `pytest tests` passes without manual steps. This is the surface's strongest sales asset today. | `ci`, `tooling`, `severity:high` | 52/52 only after manual `pip install aiohttp` |

### MEDIUM

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| K3 | **Promote `Brain` to a real ABC** (`abc.ABC` + `@abstractmethod`) so a subclass missing `propose`/`plan` fails at construction, not at call time. Keeps `FakeBrain`, `CogBrain` intact. | `tech-debt`, `severity:medium` | `neural.py` bare `NotImplementedError` x5 |
| K4 | **Publish a runnable quickstart that proves the differentiator**: the README documents the surface and a VERIFY checklist with unchecked boxes. Ship a `demo_crew.py --fake` walkthrough plus a recorded real-key run, so the "roadmap-backed crew" story is reproducible by a buyer. | `documentation`, `severity:medium` | `README.md` VERIFY section (unchecked) |

### LOW

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| K5 | **Normalise README framing**: the file is titled "CLEANROOM BUILD MANIFEST (hypo-map-1 phase 01)" mixed with a "Managed members" list. Give it a product-facing header plus a repository-layout section, keeping the manifest content. | `documentation`, `severity:low` | `mem20crewz/README.md:1` |
| K6 | **Keep runtime state out of the shipped package**: ignore `runtime/outputs/*` (the demo artifacts) while leaving the `runtime/` scaffold and its `.gitignore` in place. | `tech-debt`, `severity:low` | `runtime/outputs/fountain-*.md` |
| K7 | **Document the A2A peer contract** (`peers.yaml`, ports 9901-9922, JSON-RPC v1.0) as a first-class doc so the 22-peer fan-out is inspectable without reading `a2a.py`. | `documentation`, `severity:low` | `mem20crewz/peers.yaml`, `a2a.py` |

---

## 3. Priority order

```
K1  -> declared deps             (clean install works)
K2  -> clean-install green suite (proof)
K3  -> Brain ABC                 (extensibility)
K4  -> runnable quickstart       (demo)
K5 -> K6 -> K7
```

## 4. Acceptance

1. `pip install -e mem20crewz` then `pytest tests` -> green with **no manual installs**.
2. `python -m mem20crewz run --fake` completes a crew + flow end-to-end from a fresh clone.
3. `Brain` subclass missing `propose()` raises `TypeError` at construction.
4. All 22 documented features in `docs/PLAN.md` section 7 remain present and tested - nothing removed.
