# Generated master plan set — `plans/`

The generated 100-plan master todo and the data modules that build it.

**15 tracked file(s).**

## Contents

- `master/MASTER_TODO.md` — the rendered plan set (100 plans, 2305 roadmap items, generated 2026-10-11)
- `master/master_todo.json` — machine-readable form
- `master/build_master.py` — renderer
- `master/plans_data_*.py`, `plans_extra*.py` — the plan data modules
- `master/fix_epistemic_tests.py` — test fixups referenced by the plan set

## Usage

```bash
python3 plans/master/build_master.py
```

## Notes

`MASTER_TODO.md` is **generated** — edit the `plans_data_*.py` / `plans_extra*.py`
modules and re-render, never the Markdown by hand. The baseline measurements in it
are dated 2026-10-11 and are historical.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
