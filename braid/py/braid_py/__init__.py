"""braid_py — the Python-side bridge to the braid Rust surface.

``braid`` is a Rust Cargo workspace. The native extension is built from
``braid_python/`` with maturin. This package is the Python surface over that
extension: it re-exports the top-level ``braid_bridge`` facade (one persistent
engine, one signer, one append-only ledger) and adds :mod:`braid_py.wiring`
(real calls into six other mem20 subsystems) and :mod:`braid_py.cli`.

When the native extension is not built, ``available()`` is ``False`` and every
ledger operation raises :class:`BraidUnavailable`. The bridge never fabricates
a receipt, a cid or a proof hop.

The ledger is append-only and origin-tagged. This package exposes no API that
mutates or deletes ledger history.
"""
from __future__ import annotations

from ._bootstrap import REPO_ROOT, ensure_paths

ensure_paths()

from braid_bridge import (  # noqa: E402  (path bootstrap must run first)
    BraidUnavailable,
    BraidWriteError,
    available,
    commit,
    commit_fact,
    engine_id,
    get_engine,
    hash_data,
    head,
    intent_submit,
    intent_view,
    prove,
    read,
    signer_hex,
    status,
    verify_signature,
)

from . import wiring  # noqa: E402

__version__ = "0.1.0"

__all__ = [
    "BraidUnavailable",
    "BraidWriteError",
    "REPO_ROOT",
    "available",
    "commit",
    "commit_fact",
    "engine_id",
    "get_engine",
    "hash_data",
    "head",
    "intent_submit",
    "intent_view",
    "prove",
    "read",
    "signer_hex",
    "status",
    "verify_signature",
    "wiring",
]
