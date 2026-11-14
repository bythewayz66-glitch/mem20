"""Estate calls this subsystem makes on its write and read paths.

Each function here calls a real API of another mem20 project and returns that
project's real result. The rule throughout: **a dependency is wired in at the
point where this subsystem cannot decide the answer alone.** That is why most of
these refuse rather than merely report.

================  ==========================================================
mem20 project      symbol used
================  ==========================================================
``memory_engine``  ``memory.validate_event_time``, ``memory._load_ledger``
``mem20verify``    ``dataintegrity.check``
``mem20ops``       ``memchecks.identity_check``
``mem20secretz``   ``sweep.classify``
``mem20liez``      ``gates.check_prohibited_uses``
================  ==========================================================

Imports are **symbol-level and module-level**: ``from mem20liez.gates import
check_prohibited_uses``, not ``import mem20liez``. Two reasons, both practical:

* a package ``__init__`` can re-export a *function* under a submodule's name
  (``mem20secretz/__init__.py`` does ``from .sweep import ... sweep ...``),
  which silently turns ``mem20secretz.sweep.classify`` into an AttributeError on
  a function object. Importing the symbol avoids the trap entirely.
* it makes "this is called, not merely imported" checkable by reading the
  module: the name cannot be present without being bound to the real callable.
"""

from __future__ import annotations

import os

from .estate import UNAVAILABLE, estate_path, need

__all__ = [
    "validate_event_time", "ledger_rows", "verify_ledger_integrity",
    "identity", "classify_secret", "check_belief_legality",
]

estate_path()

# -- static, symbol-level imports -------------------------------------------
# One block per project. A project that cannot be imported is recorded, not
# fatal: the rest of the seam still loads and the failure surfaces, naming the
# project, at the call that needs it.

try:
    from memory_engine.memory import validate_event_time as _validate_event_time
    from memory_engine.memory import _load_ledger as _ledger_load
except ImportError as _exc:  # pragma: no cover - only on a broken checkout
    _validate_event_time = None
    _ledger_load = None
    UNAVAILABLE["memory_engine.memory"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20verify.dataintegrity import check as _integrity_check
except ImportError as _exc:  # pragma: no cover
    _integrity_check = None
    UNAVAILABLE["mem20verify.dataintegrity"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20ops.memchecks import identity_check as _identity_check
except ImportError as _exc:  # pragma: no cover
    _identity_check = None
    UNAVAILABLE["mem20ops.memchecks"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20secretz.sweep import classify as _classify_secret_value
except ImportError as _exc:  # pragma: no cover
    _classify_secret_value = None
    UNAVAILABLE["mem20secretz.sweep"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20liez.gates import check_prohibited_uses as _check_prohibited_uses
except ImportError as _exc:  # pragma: no cover
    _check_prohibited_uses = None
    UNAVAILABLE["mem20liez.gates"] = f"{type(_exc).__name__}: {_exc}"


# -- 1. memory_engine: is this timestamp a legal event time? ----------------

def validate_event_time(valid_from: str, now: str | None = None) -> str:
    """Validate a caller-supplied event time through the ledger's own rules.

    This subsystem can check that a string parses. It cannot know what the
    memory ledger considers a *legal* event time - the bounds that reject a typo
    like ``"2026"`` while still allowing a fact from years ago live in
    ``memory_engine.memory``, and they must stay in one place. Re-implementing
    them here would let the two drift, and the failure mode of that drift is a
    wrong timestamp landing on the valid axis permanently.

    Raises ValueError from the engine's validator; returns what it normalised.
    """
    return need(_validate_event_time, "validate_event_time", "memory_engine")(
        valid_from, now=now
    )


def ledger_rows(path: str | None = None) -> list[dict]:
    """The memory ledger's rows, read by the module that owns the ledger.

    ``memory_engine.memory`` is the single authority for where the ledger is and
    what shape its rows take. Reading the file directly here is what the previous
    generated version of this package did, and it went wrong the first time the
    ledger path moved: the temporal store silently ingests nothing and then
    reports a confident empty answer.

    ``path`` overrides the location for tests. Without it the engine's own
    ``LEDGER`` is used, which honours ``MEM20_LEDGER_PATH`` and
    ``MEM20_STORE_PATH``.
    """
    load = need(_ledger_load, "_load_ledger", "memory_engine")
    if path is None:
        return list(load())

    import json

    if not os.path.exists(path):
        raise FileNotFoundError(f"ledger not found at {path}")
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


# -- 2. mem20verify: is the ledger this store derives from intact? ----------

def verify_ledger_integrity(engine_dir: str | None = None) -> dict:
    """Prove the memory engine can still round-trip a write.

    A temporal store whose source ledger is corrupt derives plausible intervals
    from damaged rows and cannot tell. ``mem20verify.dataintegrity.check`` writes
    known payloads into a throwaway store and reads them back through the real
    engine - the only evidence available here about whether the authority this
    package derives from can be trusted.

    Returns the checker's own ``as_dict()``, so a caller cannot mistake a
    paraphrase for the result.
    """
    from .estate import REPO_ROOT

    checker = need(_integrity_check, "dataintegrity.check", "mem20verify")
    return checker(engine_dir or str(REPO_ROOT / "memory_engine")).as_dict()


# -- 3. mem20ops: which store, whose blocks, which namespaces --------------

def identity(store_path: str | None = None) -> dict:
    """Identify the store the temporal engine is about to write into.

    ``mem20ops.memchecks.identity_check`` reports the store path, pinned blocks
    and namespaces actually registered on disk. Recording ``value_ref``s into an
    unidentified store is how a temporal layer ends up answering questions about
    someone else's facts: the intervals are right and the subject is wrong.
    Callers stamp this into ``provenance`` so the answer stays attributable.
    """
    return need(_identity_check, "identity_check", "mem20ops")(store_path)


# -- 4. mem20secretz: is the value safe to keep forever? -------------------

def classify_secret(name: str, value: str) -> dict:
    """Classify a belief through the estate's own secret sweep, on both halves.

    A temporal store records *what was believed*. If the thing believed is a
    credential, the store becomes a durable, hash-chained, immutable archive of
    it - the worst place for a leak, because the design guarantees it can never
    be deleted.

    ``mem20secretz.sweep.classify`` decides from the **variable name** as much as
    the value: a key called ``TOKEN`` is critical whatever it holds, while a
    high-entropy value under a neutral name is only ``high``. So both halves of
    the belief are classified and the more severe answer wins. Classifying only
    the value let a credential through whenever the attribute was named
    neutrally - e.g. ``svc.creds / value`` holding a real token - which is
    precisely the case that matters.

    ``safe`` follows the *store's* policy, which is stricter than "not critical":
    an append-only, hash-chained store cannot delete a row, so both a
    credential-named belief (``critical``) and an opaque high-entropy value that
    looks like one (``high``/``opaque``) are refused. Prose is unaffected - the
    only values that reach here through ``assert_belief`` are short references.
    """
    classify = need(_classify_secret_value, "sweep.classify", "mem20secretz")
    order = {"critical": 0, "high": 1, "info": 2}

    by_value = classify(name, value)
    # The name half is asked with an empty value: a key called TOKEN is critical
    # whatever it holds, and asking that separately is what catches a credential
    # stored under a neutral attribute name.
    by_name = classify(name, "")
    severity, kind = (by_value if order.get(by_value[0], 9) <= order.get(by_name[0], 9)
                      else by_name)

    undeletable_risk = severity == "critical" or (
        severity == "high" and kind == "opaque")
    return {
        "safe": not undeletable_risk,
        "severity": severity,
        "kind": kind,
        "by_value": {"severity": by_value[0], "kind": by_value[1]},
        "by_name": {"severity": by_name[0], "kind": by_name[1]},
        "policy": "critical and high/opaque are refused: an append-only store "
                  "cannot delete a credential once written",
        "classifier": "mem20secretz.sweep.classify",
    }


# -- 5. mem20liez: was this belief legal to hold at all? -------------------

def check_belief_legality(intended_uses=None) -> dict:
    """Refuse prohibited uses before any interval is written.

    ``mem20liez.gates.check_prohibited_uses`` is an estate-wide refusal list:
    detention, charging, clinical diagnosis, covert surveillance and the rest. It
    raises ``GateError``. A temporal store that records such a judgement and
    keeps it forever is participating in the prohibited use, so the gate is
    checked at the seam rather than left to the caller to remember.
    """
    gate = need(_check_prohibited_uses, "gates.check_prohibited_uses", "mem20liez")
    uses = list(intended_uses) if intended_uses is not None else ["memory_search"]
    gate(uses)
    return {"permitted": True, "uses": uses,
            "gate": "mem20liez.gates.check_prohibited_uses"}
