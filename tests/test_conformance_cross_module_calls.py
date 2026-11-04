"""Criterion 6 counts a called symbol, not a decorative import.

Issue #220: the Python path of the conformance gate used to count import
statements. A bare, dead-code, or ``TYPE_CHECKING`` import passed. The gate now
binds each imported name to its source module and only counts a ``Call`` whose
callee resolves to that binding; coverage then decides whether the call ran.
These tests pin the binding/call-resolution half of that rule.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONFORMANCE = os.path.join(
    os.path.dirname(_HERE), "scripts", "renovation", "conformance.py"
)

_spec = importlib.util.spec_from_file_location("mem20_conformance_c6", _CONFORMANCE)
conformance = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = conformance
_spec.loader.exec_module(conformance)


def _sites(source: str) -> list:
    tree = ast.parse(source)
    return conformance._call_sites(tree, conformance._bound_names(tree))


def test_bare_import_is_not_a_call_site() -> None:
    assert _sites("import mem20verify\n") == []


def test_imported_function_call_is_a_site() -> None:
    sites = _sites("from memory_engine import remember\nremember('x')\n")
    assert sites == [("memory_engine", 2)]


def test_attribute_call_through_imported_module_is_a_site() -> None:
    sites = _sites("from mem20verify import linters\nlinters.run()\n")
    assert sites == [("mem20verify", 2)]


def test_alias_of_bound_module_is_resolved() -> None:
    source = (
        "from memory_engine import memory\n"
        "engine = memory\n"
        "engine.recall('x')\n"
    )
    assert _sites(source) == [("memory_engine", 3)]


def test_import_under_type_checking_without_call_is_not_a_site() -> None:
    source = (
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from mem20verify import linters\n"
        "value = 1\n"
    )
    assert _sites(source) == []
