# Decomposition verification — `verification/`

Static verification that the server decomposition is intact — no runtime or MCP
dependency required.

**2 tracked file(s).**

## Contents

- `verify_refactor.py` — checks expected module files exist, tool registrations are present, every dispatched tool has a handler, the server inherits its mixins, and `memory.py` contains no live `eval()`
- `verify_refactor.out` — captured output of a past run

## Usage

```bash
python3 verification/verify_refactor.py
```

## Notes

`verify_refactor.out` is a captured record of one run, not a live result. Re-run
the script rather than quoting the `.out` file.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
