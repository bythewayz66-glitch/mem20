"""The agent-facing MCP surface must ask for, and show, epistemic labels.

The engine refuses an unlabeled grounded write, but an agent reaches memory
through these tools, not through the engine. If the tool schema does not require
a label, or the recall renderers do not print one, every guarantee the engine
provides is lost at the exact boundary where an agent would read or write a fact.

These tests exercise the tool methods directly. They need no MCP SDK and no live
transport: `_memory_store` and friends are plain async methods that return the
string an agent would see, and `register_memory_tools` only assigns into a dict.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

MCP_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = MCP_ROOT.parent / "memory_engine"

# The repo-root conftest pre-binds the installed mcp SDK, because this repo's
# mcp/ directory shadows the `mcp` name during pytest's collection walk and
# memory_tools.py answers that ImportError with sys.exit(1) - which aborts the
# whole session. Skip loudly rather than crash if the SDK is genuinely absent.
pytest.importorskip("mcp.server", reason="mcp SDK not installed")
pytest.importorskip("mcp_types", reason="mcp_types not installed")

EPISTEMIC_STATUSES = ["observed", "inferred", "imagined", "user_stated",
                      "hypothesis", "agent_generated", "unlabeled"]


def _load_by_path(name: str, path: Path):
    """Load a module by explicit file path.

    Deliberately not `importlib.import_module`: putting this repo's mcp/ on
    sys.path shadows the installed `mcp` SDK with this repo's own server.py,
    which then fails to import itself. Loading the canonical file directly makes
    the module under test the same object the running server executes.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Recorder(dict):
    """A dict that also keeps every value assigned into it, for later lookup."""

    def __setitem__(self, key, value):
        super().__setitem__(key, value)


@pytest.fixture()
def tools(tmp_path, monkeypatch):
    """(memory_tools module, bound mixin server, registered tools dict)."""
    store = tmp_path / "store"
    store.mkdir()
    monkeypatch.setenv("MEM20_STORE_PATH", str(store))
    monkeypatch.syspath_prepend(str(ENGINE_ROOT))
    sys.modules.pop("memory", None)
    importlib.import_module("memory")  # engine, isolated by MEM20_STORE_PATH

    module = _load_by_path("memory_tools", MCP_ROOT / "memory_tools.py")

    registered = Recorder()

    class Server(module.MemoryToolsMixin):
        def __init__(self):
            self.tools = registered

    server = Server()
    server.register_memory_tools()
    yield module, server, registered
    sys.modules.pop("memory_tools", None)
    sys.modules.pop("memory", None)


def _run(coro):
    return asyncio.run(coro)


class TestStoreToolRequiresALabel:
    """An agent must be told what kind of claim it is making."""

    def test_missing_label_is_refused_with_guidance(self, tools):
        _, server, _ = tools
        out = _run(server._memory_store(
            {"content": "a claim", "category": "general", "tags": ""}))
        assert "epistemic_status" in out
        assert "Error" in out

    def test_refusal_names_every_valid_status(self, tools):
        _, server, _ = tools
        out = _run(server._memory_store({"content": "a claim"}))
        for status in EPISTEMIC_STATUSES:
            assert status in out, f"refusal did not mention {status}"

    def test_refusal_points_at_the_simulated_tool(self, tools):
        # An agent reaching for the wrong door should be redirected, not stuck.
        _, server, _ = tools
        out = _run(server._memory_store({"content": "invented"}))
        assert "memory_simulate_store" in out

    def test_labeled_write_succeeds_and_echoes_the_label(self, tools):
        _, server, _ = tools
        out = _run(server._memory_store(
            {"content": "a verified claim", "epistemic_status": "observed"}))
        assert "Record ID:" in out
        assert "observed" in out

    def test_schema_declares_the_label_required(self, tools):
        _, _, registered = tools
        schema = registered["memory_store"].input_schema
        assert schema["required"] == ["content", "epistemic_status"]
        enum = schema["properties"]["epistemic_status"]["enum"]
        assert set(enum) == set(EPISTEMIC_STATUSES)


class TestRecallRendersTheLabel:
    """A label the agent never sees is a label that does not exist."""

    BASE = {"ts": "2026-01-01T00:00:00+00:00", "topic": "t",
            "priority": "normal", "content": "c"}

    @staticmethod
    def _mark(line: str) -> str:
        """The bracketed epistemic tag is the LAST bracket group on the header."""
        header = line.split("\n")[0]
        return header[header.rindex("[") + 1:header.rindex("]")]

    def test_fact_line_marks_each_status_distinctly(self, tools):
        module, _, _ = tools
        marks = {s: self._mark(module._fact_line({**self.BASE, "epistemic_status": s}))
                 for s in EPISTEMIC_STATUSES}
        assert len(set(marks.values())) == len(EPISTEMIC_STATUSES), (
            f"marks collide: {marks}")

    def test_fact_line_defaults_a_missing_label_to_unlabeled(self, tools):
        module, _, _ = tools
        line = module._fact_line(dict(self.BASE))
        assert "UNLABELED" in line

    def test_untrusted_statuses_are_visually_louder(self, tools):
        # A hypothesis must not read like an observation in a wall of text.
        module, _, _ = tools
        observed = module._fact_line({**self.BASE, "epistemic_status": "observed"})
        hypothesis = module._fact_line({**self.BASE, "epistemic_status": "hypothesis"})
        assert observed != hypothesis
        assert "HYPOTHESIS" in hypothesis


class TestSetEpistemicStatusToolAcceptsUnlabeled:
    """There must be a way to say 'unknown' through the tool surface too."""

    def test_schema_includes_unlabeled(self, tools):
        _, _, registered = tools
        schema = registered["memory_set_epistemic_status"].input_schema
        assert "unlabeled" in schema["properties"]["status"]["enum"]


class TestSharedStoreAlsoRequiresALabel:
    """A namespace is not a loophole for storing unlabeled claims."""

    def test_schema_requires_the_label(self, tools):
        _, _, registered = tools
        schema = registered["memory_shared_store"].input_schema
        assert "epistemic_status" in schema["required"]

    def test_missing_label_is_refused(self, tools):
        _, server, _ = tools
        out = _run(server._memory_shared_store(
            {"namespace": "ns", "content": "a claim"}))
        assert "epistemic_status" in out
        assert "Error" in out


class TestCoverageToolsAreRegistered:
    """The numbers have to be reachable, or the guarantee is unmeasurable."""

    def test_coverage_and_backfill_tools_exist(self, tools):
        _, _, registered = tools
        assert "memory_label_coverage" in registered
        assert "memory_backfill_labels" in registered

    def test_coverage_tool_reports_a_denominator_on_an_empty_store(self, tools):
        # An empty store must not report "100% coverage"; that is the same
        # divide-by-zero silence the contamination audit was fixed for.
        _, server, _ = tools
        out = _run(server._memory_label_coverage({}))
        assert "coverage" in out.lower()
        assert "0/0" in out
        assert "100.0%" not in out

    def test_backfill_tool_on_a_fresh_store_changes_nothing(self, tools):
        _, server, _ = tools
        out = _run(server._memory_backfill_labels({}))
        assert "Backfilled 0" in out
