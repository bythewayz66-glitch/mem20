# Bare `except:` policy (issue #13)

## Problem
A repo-wide scan found hundreds of bare `except:` clauses. They catch
`BaseException` (including `KeyboardInterrupt` / `SystemExit`) and often
swallow failures with `pass` or `return None`.

## Policy (going forward)
1. **Never** write new bare `except:`.
2. Prefer `except Exception as exc:` and **log** before fallback.
3. For expected cases, catch the specific type (`ImportError`, `OSError`, …).
4. CI / pre-commit: ruff rule `E722` (do not use bare `except`) should be
   enabled package-by-package as each package is cleaned.

## Mechanical cleanup
Full replacement of every site is a multi-PR effort (hundreds of files).
Track remaining count with:

```bash
git grep -nE '^[[:space:]]*except[[:space:]]*:' -- '*.py' | grep -v __pycache__ | wc -l
```

Priority order: `mcp/`, `mem20agentz/`, `mem20controlz/`, then the rest of the estate.
