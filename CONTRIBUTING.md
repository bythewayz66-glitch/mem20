# Contributing to mem20

mem20 is a large multi-package Python monorepo. Small, verifiable changes beat large clever ones.

## Before you start

- **Python >= 3.10** (see `pyproject.toml`). CI runs 3.11.
- **pip install -e '.[dev]'** for pytest.
- **pre-commit** (optional): `pip install pre-commit && pre-commit install`
- Agents: read `docs/handoff/AGENT-OPERATING-PROTOCOL.md` and `docs/INDEX.md` first.

## Tests (issue #5)

```bash
pip install -e '.[dev]'
pytest -m unit -q          # CI-safe; no optional native deps
pytest -m integration -q   # needs torch/blender/network as applicable
pytest <package> -q        # one package
```

Markers are registered in `pytest.ini`. CI runs the green package set with `-m "not integration"`.

## Paths (issues #14 / #15)

Never hardcode `/home/jayson/...`. Use `specs/`, `Path.home()`, or env vars
(`MEM20_ENGINE_PATH`, `MEM20_SPEC_SOURCE`, `UNITY_EDITOR`, …). See `docs/hygiene/spec-authority-paths.md`.

## What gets a PR rejected

- Fails `python3 -m compileall`
- Committed generated state (`.sqlite3`, harness JSON, `ledger.jsonl`)
- Docs that contradict the code

## Security

Do **not** open a public issue for a vulnerability. See `SECURITY.md`.
Secret scanning is a repository setting (issue #11).
