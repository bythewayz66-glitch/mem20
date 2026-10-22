# Top-level `test/` scratch (issue #18)

## Status

`pytest.ini` lists `test` in `norecursedirs`, so a plain `pytest` no longer
collects the top-level scratch directory. Real suites live under each package's
`tests/` directory.

If a top-level `test/` directory is re-introduced:

1. Do **not** name files `test_*.py` unless they are real pytest modules.
2. Prefer `scripts/` for one-off system scripts.
3. Keep `norecursedirs` including `test`.

Related: issue #5 (unit vs integration markers).
