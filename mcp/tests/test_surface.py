"""Tests for mcp/surface.py — tool-surface admission control.

The point of these tests is not that the checks return booleans. It is that each
check is *delegated* to the estate module that owns that rule, and that the
delegation actually fires: a prohibited use is refused because
``mem20liez.gates.check_prohibited_uses`` raised, a stub body is refused because
``mem20verify.linters.noop_bodies`` found it, and so on. So the tests assert on
the estate module's own behaviour, not on a re-implementation of it.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

MCP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MCP_ROOT.parent


def _load_surface():
    """Load mcp/surface.py by path.

    ``import mcp.surface`` is not usable here: the repo's own ``mcp/`` directory
    shadows the installed MCP SDK as a namespace package, and the SDK is what
    ``mcp/server.py`` needs. Loading the file directly keeps this test about
    surface.py and nothing else.
    """
    path = MCP_ROOT / "surface.py"
    spec = importlib.util.spec_from_file_location("mem20_mcp_surface", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["mem20_mcp_surface"] = module
    spec.loader.exec_module(module)
    return module


def _load_irc():
    """Load mem20botz's irc module by path.

    ``mem20botz/__init__.py`` pulls in the crew, which pulls in the kanban bot,
    which needs a fully installed ``mem20kanbanz``. The IRC ``Message`` dataclass
    has no such dependency, and it is the only thing the wire check needs.
    """
    path = REPO_ROOT / "mem20botz" / "mem20botz" / "irc.py"
    spec = importlib.util.spec_from_file_location("mem20botz_irc_standalone", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["mem20botz_irc_standalone"] = module
    spec.loader.exec_module(module)
    return module


surface = _load_surface()
irc = _load_irc()

GOOD_SOURCE = "def handler(x):\n    return x + 1\n"
STUB_SOURCE = "def handler(x):\n    pass\n"
AT = "2026-11-01T12:00:00+00:00"


def _msg(command, text="", target="#mem20", prefix="alice!u@h"):
    return irc.Message(
        raw=f":{prefix} {command} {target} :{text}",
        prefix=prefix,
        command=command,
        params=[target],
        text=text,
    )


# --- criterion 6: the estate modules are imported AND called -----------------

def test_surface_imports_five_estate_modules():
    """The module must import >= 5 other mem20 modules (conformance criterion 6)."""
    tree = ast.parse((MCP_ROOT / "surface.py").read_text(encoding="utf-8"))
    tops = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            tops.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            tops.update(a.name.split(".")[0] for a in node.names)
    estate = {t for t in tops if t.startswith("mem20")}
    assert len(estate) >= 5, f"only {sorted(estate)}"


def test_each_estate_function_is_reachable_from_surface():
    """Every wired function is the real object from the estate module."""
    from mem20ops.clicheck import classify_naming
    from mem20verify.linters import noop_bodies
    from mem20liez.gates import check_prohibited_uses
    from mem20ircz.filter import classify as classify_wire_line
    from mem20temporaldatabasefabricz.temporal.interval import contains as interval_contains

    assert surface.classify_naming is classify_naming
    assert surface.noop_bodies is noop_bodies
    assert surface.check_prohibited_uses is check_prohibited_uses
    assert surface.classify_wire_line is classify_wire_line
    assert surface.interval_contains is interval_contains


# --- naming (mem20ops.clicheck) ---------------------------------------------

def test_mem20_native_name_is_admitted():
    check = surface.check_name("mem20_search")
    assert check.ok
    assert check.reason == "mem20-native"


def test_fs_standard_name_is_admitted():
    assert surface.check_name("fs-metrics").ok


def test_generic_name_is_refused():
    check = surface.check_name("helper")
    assert not check.ok
    assert "generic" in check.reason


def test_foreign_name_is_refused_by_clicheck():
    """A name clicheck classifies as 'other' is refused, and says so."""
    check = surface.check_name("SomeRandomTool")
    assert not check.ok
    assert "other" in check.reason


# --- body (mem20verify.linters) ---------------------------------------------

def test_real_body_passes():
    assert surface.check_body("mem20_x", GOOD_SOURCE).ok


def test_stub_body_is_refused_by_linter():
    check = surface.check_body("mem20_x", STUB_SOURCE)
    assert not check.ok
    assert "noop" in check.reason


def test_missing_source_is_refused():
    """An unverifiable handler is refused, not waved through."""
    check = surface.check_body("mem20_x", None)
    assert not check.ok
    assert "cannot be verified" in check.reason


def test_unparseable_source_is_refused():
    check = surface.check_body("mem20_x", "def broken(:\n")
    assert not check.ok
    assert "does not parse" in check.reason


# --- uses (mem20liez.gates) -------------------------------------------------

def test_permitted_use_passes():
    assert surface.check_uses(["retrieval"]).ok


def test_prohibited_use_is_refused_by_gate():
    check = surface.check_uses(["clinical_diagnosis"])
    assert not check.ok
    assert "prohibited_use" in check.reason


def test_prohibited_use_normalises_spacing_and_case():
    """The gate normalises 'Clinical Diagnosis' to clinical_diagnosis."""
    assert not surface.check_uses(["Clinical Diagnosis"]).ok


def test_no_declared_uses_passes():
    assert surface.check_uses(None).ok


# --- validity (temporal fabric interval.contains) ---------------------------

def test_instant_inside_window_passes():
    check = surface.check_validity("2026-01-01T00:00:00+00:00",
                                   "2027-01-01T00:00:00+00:00", AT)
    assert check.ok


def test_instant_after_window_is_refused():
    check = surface.check_validity("2026-01-01T00:00:00+00:00",
                                   "2026-06-01T00:00:00+00:00", AT)
    assert not check.ok
    assert "outside" in check.reason


def test_open_ended_window_passes():
    assert surface.check_validity("2026-01-01T00:00:00+00:00", None, AT).ok


def test_unparseable_window_is_refused():
    check = surface.check_validity("not-a-date", None, AT)
    assert not check.ok
    assert "unparseable" in check.reason


# --- wire signal (mem20ircz.filter) -----------------------------------------

def test_human_channel_message_carries_signal():
    check = surface.check_wire_noise([_msg("PRIVMSG", "hello")])
    assert check.ok
    assert "1/1" in check.reason


def test_motd_numeric_is_noise():
    check = surface.check_wire_noise([_msg("372", "- motd", target="alice")])
    assert not check.ok
    assert "protocol noise" in check.reason


def test_notice_is_noise():
    assert not surface.check_wire_noise([_msg("NOTICE", "hi")]).ok


def test_mixed_lines_pass_when_one_carries_signal():
    check = surface.check_wire_noise([
        _msg("372", "- motd", target="alice"),
        _msg("PRIVMSG", "real question"),
    ])
    assert check.ok
    assert "1/2" in check.reason


def test_no_declared_lines_passes():
    assert surface.check_wire_noise([]).ok


# --- the whole verdict ------------------------------------------------------

def test_clean_tool_is_admitted():
    admission = surface.admit_tool(
        "mem20_search", source=GOOD_SOURCE, intended_uses=["retrieval"], at=AT,
    )
    assert admission.admitted
    assert admission.reasons == []
    assert len(admission.checks) == 5


def test_every_failure_is_reported_at_once():
    """A refusal lists all reasons, not just the first."""
    admission = surface.admit_tool(
        "helper",
        source=STUB_SOURCE,
        intended_uses=["clinical_diagnosis"],
        valid_from="2026-01-01T00:00:00+00:00",
        valid_to="2026-06-01T00:00:00+00:00",
        at=AT,
        wire_lines=[_msg("372", "- motd", target="alice")],
    )
    assert not admission.admitted
    assert len(admission.reasons) == 5


def test_admission_serialises():
    payload = surface.admit_tool("mem20_x", source=GOOD_SOURCE, at=AT).as_dict()
    assert payload["admitted"] is True
    assert payload["tool"] == "mem20_x"
    assert len(payload["checks"]) == 5


def test_audit_registry_splits_admitted_from_refused():
    report = surface.audit_registry(
        ["mem20_a", "mem20_b"],
        sources={"mem20_a": GOOD_SOURCE},
        at=AT,
    )
    assert report["total"] == 2
    assert report["admitted_tools"] == ["mem20_a"]
    assert [r["tool"] for r in report["refusals"]] == ["mem20_b"]
    assert report["admitted"] == 1 and report["refused"] == 1
    assert report["clean"] is False


def test_audit_registry_clean_when_all_admitted():
    report = surface.audit_registry(
        ["mem20_a"], sources={"mem20_a": GOOD_SOURCE}, at=AT,
    )
    assert report["clean"] is True
