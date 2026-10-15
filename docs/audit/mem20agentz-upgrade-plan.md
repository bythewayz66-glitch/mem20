# mem20agentz - Upgrade Plan

**Date:** 2026-10-15 - **Scope:** `mem20agentz/` @ `main`
**Standing rule:** *features are never removed - they are fixed or completed.* Every item below repairs or finishes an existing capability.

---

## 1. Current state assessment

`mem20agentz` is the largest and most ambitious of the three surfaces: **81 files, ~15,124 Python LOC**, with a documented phase ladder (`docs/PLAN.md`) from profiles -> agent loop -> skills/plugins/pets/hooks -> cron/kanban/projects/webhooks -> gateway bridges -> webgateway/MCP/ACP/computer-use -> secrets/egress/security -> auth/MoA -> frontend unification -> backup/import, plus four absorption phases (OREO, Open WebUI, office, OpenAI Agents SDK, Google ADK).

Measured this session:

| Aspect | State | Evidence |
|---|---|---|
| Package import | OK (after declaring deps) | `import mem20agentz` OK once `pyyaml` installed |
| `gateway_web.py` | BROKEN - does not parse | `py_compile` -> `SyntaxError: unterminated string literal` @ line 213 |
| CLI | BROKEN on clean hosts | `cli.py:20-32` -> `NameError: name '_exc' is not defined` |
| Office/desktop surface | CANNOT START | `desktop.py` imports the broken `gateway_web` |
| Test suite | 30 failed / 119 passed | 22 in `test_mem20agentz.py`, 6 in `test_oreditor.py`, 2 in `test_oreo.py` |
| OREO integration | DARK | `ModuleNotFoundError: mem20oreo` (8 occurrences) |
| Runtime deps | UNDECLARED | `pyyaml`, `httpx`, `aiohttp` needed but not declared |
| Absolute paths | HOST-BOUND | `desktop.py:33-34` `CREWZ_ROOT`/`GAMEZ_ROOT` hardcode `/opt/mem20/...` |

**Verdict:** the architecture is sound and largely built; the *shippable* subset is blocked by two small defects (B1, B2) that each take the whole surface down, plus an install-time dependency gap.

---

## 2. Findings -> work items

### BLOCKERS (fix first - each restores the whole surface)

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| A1 | **Repair the `gateway_web.py` f-string** so the module parses. Extract the cron-row label into a small local helper (behaviour-identical) rather than inlining the conditional. Verify `py_compile` and that `desktop.py` can import it. | `bug`, `severity:critical` | `gateway_web.py:213` unterminated string literal |
| A2 | **Fix the `mem20cliz` fallback `NameError`**: bind the exception into a module-level name (or capture it per-call) so the wrapper closure can reference it. Add a regression test that runs the CLI with `mem20cliz` absent. | `bug`, `severity:critical` | `cli.py:20-32` `NameError: name '_exc' is not defined` |

### HIGH

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| A3 | **Declare runtime dependencies** (`pyyaml`, `httpx`, `aiohttp`, `pydantic`) in `mem20agentz/pyproject.toml` so a clean install runs. | `tooling`, `severity:high` | Import fails without `yaml` |
| A4 | **Complete the OREO integration** so `mem20oreo` is resolvable where `mem20agentz` consumes it (path/entry-point/extra), unblocking `test_oreo.py`, `test_oreditor.py`, `test_graphstore.py`. Do **not** drop the capability - finish wiring it. | `tech-debt`, `severity:high` | 8 x `ModuleNotFoundError: mem20oreo` |
| A5 | **Make the suite green**: after A1-A4, drive `test_mem20agentz.py` from 22 failures to 0 (remaining failures are CLI/WebGateway/Desktop/Parity/Acceptance, all downstream of B1/B2). | `tech-debt`, `ci`, `severity:high` | 30 failed / 119 passed |

### MEDIUM

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| A6 | **De-hardcode host paths** in `desktop.py`: resolve `CREWZ_ROOT`/`GAMEZ_ROOT` from env with a repo-relative fallback, so the office surface works off the author's machine. | `tooling`, `severity:medium` | `desktop.py:33-34` |
| A7 | **Replace silent `except Exception` with honest states** in the dashboard builders: surface the failure reason (or a `degraded` marker) instead of a silent `(sealed)` placeholder. | `tech-debt`, `severity:medium` | `gateway_web.py:215-218` |
| A8 | **Bridge the live turnstile gap**: `docs/PLAN.md` records the Telegram turnstile as "NOT LIVE" pending a real bot token. Add a documented, token-free acceptance proof (the loopback bridge already exists) and record the outcome in the PLAN. | `documentation`, `ci`, `severity:medium` | `docs/PLAN.md` |

### LOW

| ID | Work item | Labels | Evidence |
|---|---|---|---|
| A9 | **Trim committed build output** under `mem20agentz/built/` (21 generated `app_*.py` + editor bundles) from tracking so the tree reflects source, not artifacts. | `tech-debt`, `severity:low` | `find mem20agentz/built` |

---

## 3. Priority order

```
A1  -> restore gateway_web import        (unblocks web + office)
A2  -> restore CLI on clean hosts
A3  -> declared deps                     (unblocks clean install)
A4  -> mem20oreo wiring                  (unblocks OREO demos)
A5  -> green suite                       (proves A1-A4)
A6 -> A7 -> A8 -> A9
```

## 4. Acceptance

1. `python3 -m py_compile mem20agentz/mem20agentz/gateway_web.py` passes.
2. `python -m mem20agentz --version` and `profiles list` succeed with no `mem20cliz` installed.
3. `pytest mem20agentz/tests` -> 0 failures.
4. `desktop serve` opens the office surface and `/office` returns a live bundle.
5. Every capability in `docs/PLAN.md` remains present - nothing removed.
