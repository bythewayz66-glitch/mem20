"""The aggregate estate installer (issue #227).

`toolchest` calls a subsystem degraded when its distribution is missing from
the interpreter that ran `refresh`. One command must install them all, and it
must only pick real PEP-621 projects, not build artefacts or non-Python SDKs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "scripts" / "install_estate.py"

_spec = importlib.util.spec_from_file_location("mem20_install_estate", _SCRIPT)
installer = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = installer
_spec.loader.exec_module(installer)


def _project(root: Path, name: str) -> Path:
    project = root / name
    (project / name).mkdir(parents=True)
    (project / name / "__init__.py").write_text("", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    return project


def test_discover_only_pep621_mem20_projects(tmp_path: Path) -> None:
    a = _project(tmp_path, "mem20alphaz")
    b = _project(tmp_path, "mem20betaz")
    _project(tmp_path, "mem20-sdk-ignored")
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "mem20artefact.egg-info").mkdir()

    assert installer.discover_projects(tmp_path) == [a, b]


def test_install_command_is_editable_and_dependency_free_by_default(tmp_path: Path) -> None:
    project = tmp_path / "mem20alphaz"
    assert installer.install_command("python3", project, editable=True, with_deps=False) == [
        "python3", "-m", "pip", "install", "--editable", "--no-deps", str(project)
    ]
    assert installer.install_command("python3", project, editable=False, with_deps=True) == [
        "python3", "-m", "pip", "install", str(project)
    ]


def test_dry_run_prints_every_command(tmp_path: Path, capsys) -> None:
    _project(tmp_path, "mem20alphaz")
    _project(tmp_path, "mem20betaz")

    assert installer.main(["--root", str(tmp_path), "--python", "python3", "--dry-run"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 2
    assert all(line.startswith("python3 -m pip install --editable --no-deps ") for line in out)
    assert "mem20alphaz" in out[0] and "mem20betaz" in out[1]


def test_only_filters_projects(tmp_path: Path, capsys) -> None:
    _project(tmp_path, "mem20alphaz")
    _project(tmp_path, "mem20betaz")

    assert installer.main(
        ["--root", str(tmp_path), "--python", "python3", "--only", "mem20betaz", "--dry-run"]
    ) == 0
    out = capsys.readouterr().out
    assert "mem20betaz" in out
    assert "mem20alphaz" not in out
