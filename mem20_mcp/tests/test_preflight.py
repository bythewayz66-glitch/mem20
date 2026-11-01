"""Preflight must actually run before the canonical tree is loaded.

``mem20_mcp`` is a forwarder, and its one failure mode is quiet: if the
canonical tree is stubbed or stale, the package boots it anyway and the estate
runs the wrong logic while looking healthy. These tests drive the real load path
(``_forward.canonical_root``) against a fixture tree and assert on what the
estate modules decided, not on a mock of them.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

# ``mem20_mcp/__init__.py`` resolves the canonical root at import time, so the
# env var has to be set before the package is imported -- a fixture is too late.
# This module-level tree exists only to make the import succeed; every test that
# cares about the tree builds its own and points the env at it.
_BOOTSTRAP = Path(tempfile.mkdtemp(prefix="mem20_mcp_bootstrap_"))
(_BOOTSTRAP / "tools").mkdir(parents=True, exist_ok=True)
(_BOOTSTRAP / "server.py").write_text("TOOLS = []\n")
os.environ.setdefault("MEM20_CANONICAL_MCP_ROOT", str(_BOOTSTRAP))

from mem20_mcp import _forward, preflight  # noqa: E402


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A minimal canonical tree with one real tool."""
    root = tmp_path / "canonical"
    (root / "tools").mkdir(parents=True)
    (root / "server.py").write_text("TOOLS = ['alpha']\n")
    (root / "tools" / "alpha_tools.py").write_text(
        "def alpha():\n    return 'real'\n"
    )
    monkeypatch.setenv("MEM20_CANONICAL_MCP_ROOT", str(root))
    monkeypatch.delenv(_forward.PREFLIGHT_ENV, raising=False)
    return root


# ---------------------------------------------------------------------------
# The wiring itself: six estate modules, imported and called.
# ---------------------------------------------------------------------------


def test_preflight_imports_six_estate_modules():
    from mem20liez.gates import check_prohibited_uses
    from mem20ops.clicheck import classify_naming
    from mem20verify.linters import noop_bodies
    from mem20ircz.filter import NoiseMeter, classify
    from mem20temporaldatabasefabricz.temporal.interval import contains
    from mem20dreamz import ledger

    assert preflight.check_prohibited_uses is check_prohibited_uses
    assert preflight.classify_naming is classify_naming
    assert preflight.noop_bodies is noop_bodies
    assert preflight.classify_wire_line is classify
    assert preflight.NoiseMeter is NoiseMeter
    assert preflight.interval_contains is contains
    assert preflight.dreamz_ledger is ledger


# ---------------------------------------------------------------------------
# The load path runs the preflight.
# ---------------------------------------------------------------------------


def test_canonical_root_admits_a_clean_tree(tree):
    assert _forward.canonical_root() == str(tree)


def test_canonical_root_refuses_a_stubbed_tool(tree):
    """The quiet failure: a stubbed tool returns a well-formed nothing."""
    (tree / "tools" / "stub_tools.py").write_text(
        "def stub_tool(payload):\n    pass\n"
    )
    with pytest.raises(ImportError) as exc:
        _forward.canonical_root()
    assert "stub_body" in str(exc.value)


def test_preflight_can_be_skipped_explicitly(tree, monkeypatch):
    (tree / "tools" / "stub_tools.py").write_text("def s():\n    pass\n")
    monkeypatch.setenv(_forward.PREFLIGHT_ENV, "0")
    assert _forward.canonical_root() == str(tree)


def test_missing_layout_still_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.setenv("MEM20_CANONICAL_MCP_ROOT", str(tmp_path / "nope"))
    with pytest.raises(ImportError) as exc:
        _forward.canonical_root()
    assert "server.py/tools layout" in str(exc.value)


# ---------------------------------------------------------------------------
# Naming: mem20ops.clicheck.classify_naming
# ---------------------------------------------------------------------------


def test_estate_tool_name_is_admitted():
    assert preflight.check_tool_name("mem20_alpha") == "mem20-native"


def test_fs_tool_name_is_admitted():
    assert preflight.check_tool_name("fs-alpha") == "fs-standard"


def test_foreign_tool_name_is_refused():
    with pytest.raises(preflight.PreflightRefused) as exc:
        preflight.check_tool_name("helper")
    assert exc.value.check == "naming"


def test_preflight_reports_naming_for_every_tool(tree):
    report = preflight.preflight(tree)
    assert report.tool_count == 1
    assert report.naming == {"alpha_tools": "mem20-native"}


def test_module_filename_is_not_the_mcp_address():
    """The canonical modules are named health/world_tools; the tools are mem20_*."""
    assert preflight.exposed_tool_name("health") == "mem20_health"
    assert preflight.exposed_tool_name("world_tools") == "mem20_world_tools"
    assert preflight.check_tool_name(preflight.exposed_tool_name("health")) == "mem20-native"


# ---------------------------------------------------------------------------
# Exposure: mem20liez.gates.check_prohibited_uses
# ---------------------------------------------------------------------------


def test_permitted_exposure_passes():
    assert preflight.check_exposure(["tool_serving"]) == ("tool_serving",)


def test_prohibited_exposure_is_refused():
    with pytest.raises(preflight.PreflightRefused) as exc:
        preflight.check_exposure(["automated_detention"])
    assert exc.value.check == "prohibited_use"


def test_preflight_refuses_a_prohibited_exposure(tree):
    with pytest.raises(preflight.PreflightRefused):
        preflight.preflight(tree, intended_uses=["automated_detention"])


# ---------------------------------------------------------------------------
# Stub bodies: mem20verify.linters.noop_bodies
# ---------------------------------------------------------------------------


def test_clean_tree_has_no_stub_bodies(tree):
    assert preflight.audit_canonical_tools(tree) == []


def test_stub_body_is_refused(tree):
    (tree / "tools" / "stub_tools.py").write_text("def s():\n    pass\n")
    with pytest.raises(preflight.PreflightRefused) as exc:
        preflight.check_no_stubs(tree)
    assert exc.value.check == "stub_body"


# ---------------------------------------------------------------------------
# Release window: mem20temporaldatabasefabricz.temporal.interval.contains
# ---------------------------------------------------------------------------


def test_instant_inside_window_passes():
    assert preflight.check_release_window(
        "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2026-06-01T00:00:00Z"
    ) is True


def test_instant_outside_window_is_refused():
    with pytest.raises(preflight.PreflightRefused) as exc:
        preflight.check_release_window(
            "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", "2026-06-01T00:00:00Z"
        )
    assert exc.value.check == "outside_window"


def test_open_window_passes():
    assert preflight.check_release_window(None, None, "2030-01-01T00:00:00Z") is True


# ---------------------------------------------------------------------------
# Log filter: mem20ircz.filter.classify + NoiseMeter
# ---------------------------------------------------------------------------


def test_banner_noise_is_dropped():
    kept, meter = preflight.filter_log([{"command": "372", "text": "- banner"}])
    assert kept == []
    assert meter.by_reason["numeric.motd"] == 1


def test_real_log_line_is_kept():
    kept, meter = preflight.filter_log(
        [{"command": "PRIVMSG", "text": "tool alpha served", "prefix": "a!u@h",
          "params": ("#ops",)}]
    )
    assert len(kept) == 1
    assert meter.kept == 1


def test_preflight_reports_log_savings(tree):
    report = preflight.preflight(tree, log=[
        {"command": "372", "text": "- banner"},
        {"command": "PRIVMSG", "text": "served", "prefix": "a!u@h", "params": ("#ops",)},
    ])
    assert report.log_kept == 1
    assert report.log_swallowed == 1
    assert report.log_reasons == {"numeric.motd": 1}


# ---------------------------------------------------------------------------
# Provenance: mem20dreamz.ledger.commit_raw
# ---------------------------------------------------------------------------


def test_boot_provenance_reports_durability_honestly(tree):
    report = preflight.preflight(tree)
    record = preflight.record_boot(str(tree), report)
    assert "committed" in record
    if record["committed"]:
        assert record["cid"]
    else:
        assert record["reason"]


# ---------------------------------------------------------------------------
# The CLI is a real surface, not a stub.
# ---------------------------------------------------------------------------


def test_cli_preflight_exits_zero_on_a_clean_tree(tree, capsys):
    from mem20_mcp import cli

    assert cli.main(["preflight"]) == 0
    assert '"admitted": true' in capsys.readouterr().out


def test_cli_preflight_exits_one_on_a_stubbed_tree(tree, capsys):
    from mem20_mcp import cli

    (tree / "tools" / "stub_tools.py").write_text("def s():\n    pass\n")
    assert cli.main(["preflight"]) == 1
    assert "stub_body" in capsys.readouterr().out


def test_cli_tools_lists_the_canonical_tools(tree, capsys):
    from mem20_mcp import cli

    assert cli.main(["tools"]) == 0
    assert "alpha_tools" in capsys.readouterr().out
