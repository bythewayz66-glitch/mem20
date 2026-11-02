"""The signer gate must fail at the boundary, not deep inside signer creation.

`_load_or_create_signer()` used to guard on `import braid_python` alone. With the
repo root on `sys.path`, that import resolves to the Rust *source* directory as
an empty namespace package: it succeeds, so the `except ImportError` never fired
and the real failure surfaced much later as

    AttributeError: module 'braid_python' has no attribute 'PyBraidEngine'

from inside `_create_signer()`. That is a confusing error at the wrong layer, and
it is what made the braid-dependent tests report a seeding failure instead of
"braid is not built here".

These tests pin both branches: unavailable -> BraidUnavailable naming the real
cause; available -> the signer path is reached unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import braid_bridge  # noqa: E402


def test_unavailable_braid_raises_braidunavailable_not_attributeerror(monkeypatch):
    """The namespace-package case: import succeeds, the symbol does not exist."""
    monkeypatch.setattr(braid_bridge, "available", lambda: False)

    with pytest.raises(braid_bridge.BraidUnavailable) as exc:
        braid_bridge._load_or_create_signer()

    msg = str(exc.value)
    assert "braid_python is not installed" in msg
    assert "maturin develop" in msg, "the error must name the fix"


def test_the_gate_does_not_rely_on_import_succeeding(monkeypatch):
    """A namespace package imports fine; the gate must still refuse it.

    This is the regression itself: `import braid_python` succeeding is not
    evidence that the engine exists.
    """
    import types

    shell = types.ModuleType("braid_python")  # importable, but no PyBraidEngine
    monkeypatch.setitem(sys.modules, "braid_python", shell)
    monkeypatch.setattr(braid_bridge, "available", braid_bridge.available)

    assert braid_bridge.available() is False, "a symbol-less module is not available"

    with pytest.raises(braid_bridge.BraidUnavailable):
        braid_bridge._load_or_create_signer()


def test_available_braid_reaches_the_signer_path(monkeypatch):
    """When braid really is available, behaviour is unchanged."""
    monkeypatch.setattr(braid_bridge, "available", lambda: True)
    monkeypatch.setattr(braid_bridge, "_resolve_signer", lambda load: "deadbeef")

    assert braid_bridge._load_or_create_signer() == "deadbeef"


def test_available_requires_both_symbols(monkeypatch):
    """available() must check PyPolicySnapshot too, not just PyBraidEngine."""
    import types

    only_engine = types.ModuleType("braid_python")
    only_engine.PyBraidEngine = object()
    monkeypatch.setitem(sys.modules, "braid_python", only_engine)

    assert braid_bridge.available() is False, "PyPolicySnapshot is also required"
