"""Admission control for the MCP tool surface.

These tests exercise the real checks against real estate modules: the linters
parse real source, the IRC filter classifies real protocol lines, the lie gates
run their real prohibited-use policy, and the temporal interval does real
timestamp comparison. Nothing here is mocked, because the point of the module is
that the estate's own rules decide admission.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

MCP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MCP_ROOT.parent
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

import surface  # noqa: E402
import estate  # noqa: E402


# --- naming ------------------------------------------------------------------


@pytest.mark.unit
def test_a_snake_case_tool_name_is_admitted():
    check = surface.check_naming("memory_store")
    assert check.ok, check.reason


@pytest.mark.unit
def test_a_namespaced_tool_name_is_admitted():
    assert surface.check_naming("memory.recall").ok


@pytest.mark.unit
@pytest.mark.parametrize("bad", ["Bad Tool!", "Memory-Store", "9lives", "", "a b"])
def test_a_malformed_tool_name_is_refused(bad):
    check = surface.check_naming(bad)
    assert not check.ok
    assert "not a valid MCP tool name" in check.reason


@pytest.mark.unit
def test_a_server_that_is_not_a_fleet_binary_is_refused():
    """The binary convention is applied to the server, and it must bite."""
    check = surface.check_naming("memory_store", server_name="random-thing")
    assert not check.ok
    assert "random-thing" in check.reason


@pytest.mark.unit
def test_the_real_server_identity_passes_the_binary_convention():
    assert surface.check_naming("memory_store", server_name="mem20-mcp").ok


# --- body: the stub shapes ---------------------------------------------------


@pytest.mark.unit
def test_a_real_handler_body_passes():
    source = "def handler(args):\n    return {'ok': True, 'n': len(args)}\n"
    assert surface.check_handler_source("t", source).ok


@pytest.mark.unit
def test_a_pass_only_body_is_refused():
    source = "def handler(args):\n    pass\n"
    check = surface.check_handler_source("t", source, "t.py")
    assert not check.ok
    assert "stub-shaped" in check.reason


@pytest.mark.unit
def test_identical_branches_are_refused():
    """An if/else returning the same value is a placeholder with a schema."""
    source = (
        "def handler(args):\n"
        "    if args:\n"
        "        return 'same'\n"
        "    else:\n"
        "        return 'same'\n"
    )
    check = surface.check_handler_source("t", source, "t.py")
    assert not check.ok


@pytest.mark.unit
def test_unparseable_source_is_refused_not_crashed():
    check = surface.check_handler_source("t", "def broken(:\n", "t.py")
    assert not check.ok
    assert "does not parse" in check.reason


@pytest.mark.unit
def test_the_real_health_module_has_no_stub_shaped_body():
    """A real module in this package must pass the same check tools face."""
    path = MCP_ROOT / "health.py"
    check = surface.check_handler_source("health", path.read_text(), str(path))
    assert check.ok, check.reason


# --- intended use ------------------------------------------------------------


@pytest.mark.unit
def test_no_declared_use_passes():
    assert surface.check_intended_uses(None).ok


@pytest.mark.unit
def test_an_ordinary_use_passes():
    assert surface.check_intended_uses(["summarise a meeting"]).ok


@pytest.mark.unit
def test_a_prohibited_use_is_refused():
    """The lie gate's policy must actually reach admission."""
    check = surface.check_intended_uses(["employment_screening_without_notice"])
    assert not check.ok
    assert "intended-use" == check.name


@pytest.mark.unit
def test_a_prohibited_use_written_as_prose_is_still_refused():
    """A caller writing the policy key as words must not slip past the gate."""
    check = surface.check_intended_uses(["Employment Screening Without Notice"])
    assert not check.ok


# --- notification: the wire filter ------------------------------------------


@pytest.mark.unit
def test_a_channel_message_is_worth_forwarding():
    check = surface.check_notification(":alice!u@h PRIVMSG #mem20 :hello there")
    assert check.ok, check.reason


@pytest.mark.unit
def test_motd_noise_is_not_forwarded():
    check = surface.check_notification(":server 372 nick :- welcome to the network")
    assert not check.ok
    assert "numeric.motd" in check.reason


@pytest.mark.unit
def test_a_roster_event_is_not_forwarded():
    check = surface.check_notification(":bob!u@h JOIN #mem20")
    assert not check.ok
    assert "roster" in check.reason


@pytest.mark.unit
def test_an_empty_line_is_refused():
    assert not surface.check_notification("   ").ok


# --- temporal window ---------------------------------------------------------


@pytest.mark.unit
def test_no_window_always_passes():
    assert surface.check_temporal_window(None, None, "2026-11-01T00:00:00Z").ok


@pytest.mark.unit
def test_an_instant_inside_the_window_passes():
    check = surface.check_temporal_window(
        "2026-01-01T00:00:00Z", "2026-12-31T00:00:00Z", "2026-11-01T00:00:00Z")
    assert check.ok, check.reason


@pytest.mark.unit
def test_an_instant_after_the_window_is_refused():
    check = surface.check_temporal_window(
        "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z", "2026-11-01T00:00:00Z")
    assert not check.ok
    assert "outside" in check.reason


# --- the combined verdict ----------------------------------------------------


@pytest.mark.unit
def test_a_clean_tool_is_admitted_with_every_check_recorded():
    admission = surface.admit_tool(
        "memory_store",
        source="def handler(a):\n    return len(a)\n",
        path="handler.py",
    )
    assert admission.admitted
    assert [c.name for c in admission.checks] == ["naming", "body", "intended-use"]
    assert "admitted" in admission.explain()


@pytest.mark.unit
def test_a_refusal_names_every_failing_check():
    admission = surface.admit_tool(
        "Bad Name",
        source="def handler(a):\n    pass\n",
        path="handler.py",
        intended_uses=["employment_screening_without_notice"],
    )
    assert not admission.admitted
    names = {c.name for c in admission.refusals}
    assert names == {"naming", "body", "intended-use"}
    assert "refused" in admission.explain()


@pytest.mark.unit
def test_a_missing_source_is_reported_not_silently_passed():
    admission = surface.admit_tool("memory_store")
    body = next(c for c in admission.checks if c.name == "body")
    assert body.ok
    assert "not linted" in body.reason


@pytest.mark.unit
def test_the_temporal_check_only_runs_when_a_window_is_given():
    without = surface.admit_tool("memory_store")
    assert "temporal" not in {c.name for c in without.checks}
    with_window = surface.admit_tool(
        "memory_store", valid_from="2026-01-01T00:00:00Z",
        valid_to="2026-12-31T00:00:00Z", at="2026-11-01T00:00:00Z")
    assert "temporal" in {c.name for c in with_window.checks}


# --- registry audit ----------------------------------------------------------


@pytest.mark.unit
def test_auditing_a_clean_registry_reports_no_refusals():
    summary = surface.audit_registry({"memory_store": object(), "memory_recall": object()})
    assert summary == {"total": 2, "admitted": 2, "refused": 0, "refusals": []}


@pytest.mark.unit
def test_auditing_a_registry_with_a_bad_name_reports_it():
    summary = surface.audit_registry({"memory_store": object(), "Bad Tool": object()})
    assert summary["refused"] == 1
    assert summary["refusals"][0]["tool"] == "Bad Tool"


# --- the estate wiring is real ----------------------------------------------


@pytest.mark.unit
def test_every_estate_module_this_surface_depends_on_is_importable():
    """Criterion 6 is only real if the imports resolve to actual modules."""
    for name in ("mem20ircz.filter", "mem20liez.gates", "mem20ops.clicheck",
                 "mem20temporaldatabasefabricz.temporal.interval",
                 "mem20verify.linters"):
        module = __import__(name, fromlist=["*"])
        assert module.__file__, f"{name} resolved to a namespace package"


@pytest.mark.unit
def test_the_estate_roots_are_repo_relative():
    roots = estate.estate_roots()
    assert roots, "no sibling project roots discovered"
    for root in roots:
        assert root.startswith(str(REPO_ROOT)), f"{root} is outside the repo"
