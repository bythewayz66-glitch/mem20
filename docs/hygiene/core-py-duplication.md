# core.py duplication (issue #17)

## Status
**Landed.** Every `mem20*z/*/core.py` is now a thin re-export of `mem20core.core`; no package
carries its own implementation copy any more.

## Completion plan (do not delete packages) — done
1. The shared body lives in `mem20core/mem20core/core.py`; the behaviour the two
   formerly-divergent packages added on top lives in `mem20core/mem20core/fixes.py`.
2. Each `core.py` is a 6-line shim:
   ```python
   from mem20core.fixes import *  # noqa: F401,F403
   from mem20core.fixes import patch as _patch; _patch()
   ```
3. The two formerly divergent copies (`mem20wasmz`, `mem20webgpuz`) were **folded in**, not kept
   as-is: their unique work — free-text credential redaction, redaction on the events write path,
   redaction of job results, and hardware-probed GPU detection reporting `not_measured` instead of
   a fabricated speedup — now lives in `mem20core` and both packages inherit it.
4. Enforced by the `Syntax gate` job in `.github/workflows/ci.yml`: any `core.py` outside
   `mem20core/` longer than 10 lines fails the gate.
