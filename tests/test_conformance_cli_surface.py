"""Criterion 4 must see a declared console script, not only a cli.py file.

Issue #218: eight subsystems ship a working ``[project.scripts]`` entry point
and no ``cli.py`` / ``__main__.py``. The gate's filename check reported "no CLI
surface" for a command that starts fine. These tests pin the rule in both
directions: a declared entry point whose module exists counts, and a stale
declaration whose module is gone does not.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONFORMANCE = os.path.join(
    os.path.dirname(_HERE), "scripts", "renovation", "conformance.py"
)

_spec = importlib.util.spec_from_file_location("mem20_conformance", _CONFORMANCE)
conformance = importlib.util.module_from_spec(_spec)
# dataclasses resolves type annotations through sys.modules[cls.__module__],
# so the module must be registered before it is executed.
sys.modules[_spec.name] = conformance
_spec.loader.exec_module(conformance)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _pyproject(name: str, target: str) -> str:
    return (
        "[project]\n"
        f'name = "{name}"\n'
        'version = "0.1.0"\n'
        "\n"
        "[project.scripts]\n"
        f'{name} = "{target}"\n'
    )


def test_declared_entry_point_with_module_is_a_cli(tmp_path: Path) -> None:
    subsystem = tmp_path / "mem20probez"
    _write(
        subsystem / "pyproject.toml",
        _pyproject("mem20probez", "mem20probez.core:cli"),
    )
    _write(subsystem / "mem20probez" / "__init__.py", "")
    _write(
        subsystem / "mem20probez" / "core.py",
        "def cli():\n"
        '    """Entry point installed for the console script."""\n'
        "    return 0\n",
    )

    assert conformance.declared_entry_points(subsystem) == [
        "mem20probez.core:cli"
    ]
    result = conformance.check_subsystem("mem20probez", root=tmp_path)
    assert result.cli is True
    assert "no CLI surface" not in result.failures


def test_stale_entry_point_without_module_does_not_count(tmp_path: Path) -> None:
    subsystem = tmp_path / "mem20stalez"
    _write(
        subsystem / "pyproject.toml",
        _pyproject("mem20stalez", "mem20stalez.core:cli"),
    )
    _write(subsystem / "mem20stalez" / "__init__.py", "")

    assert conformance.declared_entry_points(subsystem) == []
    result = conformance.check_subsystem("mem20stalez", root=tmp_path)
    assert result.cli is False
    assert "no CLI surface" in result.failures


def test_src_layout_entry_point_resolves(tmp_path: Path) -> None:
    subsystem = tmp_path / "mem20srcz"
    _write(
        subsystem / "pyproject.toml",
        _pyproject("mem20srcz", "mem20srcz.cli:main"),
    )
    _write(subsystem / "src" / "mem20srcz" / "__init__.py", "")
    _write(
        subsystem / "src" / "mem20srcz" / "cli.py",
        "def main():\n"
        '    """Entry point in an src layout."""\n'
        "    return 0\n",
    )

    assert conformance.declared_entry_points(subsystem) == [
        "mem20srcz.cli:main"
    ]


def test_no_pyproject_has_no_declared_entry_points(tmp_path: Path) -> None:
    subsystem = tmp_path / "mem20barez"
    _write(subsystem / "mem20barez" / "__init__.py", "")

    assert conformance.declared_entry_points(subsystem) == []
