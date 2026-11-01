"""Cross-subsystem wiring tests for mem20corez.

Every test calls the real function in the other subsystem and checks the value
it actually returned. A subsystem absent from the environment is skipped with
the real reason, never silently passed.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mem20corez import integrations  # noqa: E402

ESTATE = integrations.estate_root()


def _require(name):
    if not integrations.available().get(name):
        pytest.skip(f"{name} not importable in this environment")


def test_estate_root_contains_corez():
    assert (ESTATE / "mem20corez").is_dir()
    assert (ESTATE / "toolchest").is_dir()


def test_available_reports_every_wired_subsystem():
    assert set(integrations.available()) == {
        "toolchest", "memory_engine", "mem20kanbanz",
        "mem20ops", "mem20cliz", "mem20verify",
    }


def test_toolchest_catalog_returns_real_model_serving_entries():
    _require("toolchest")
    hits = integrations.model_serving_tools(ESTATE)
    assert hits, "registry reported no model-serving tools"
    for hit in hits:
        assert hit["id"] and hit["name"]
        assert hit["kind"] in {"mcp", "cli", "subsystem"}
    # the registry is the source of truth, so every hit must exist in it
    from toolchest import catalog
    inv = catalog.load_inventory(ESTATE / "toolchest" / "inventory.json")
    known = {e["id"] for e in inv["entries"]}
    assert {h["id"] for h in hits} <= known


def test_artifact_digest_matches_hashlib():
    _require("mem20kanbanz")
    target = Path(__file__).resolve()
    assert integrations.artifact_digest(target) == hashlib.sha256(
        target.read_bytes()).hexdigest()


def test_pin_evaluation_roundtrip():
    _require("memory_engine")
    result = integrations.pin_evaluation(
        "wiring-test-model", {"accuracy": 0.75, "latency_ms": 12.5},
        block_id="mem20corez:test-eval")
    assert result["pinned"] is True

    from memory_engine.memory import get_pinned_block
    stored = get_pinned_block("mem20corez:test-eval")
    assert "accuracy=0.75" in stored["content"]
    assert "wiring-test-model" in stored["content"]


def test_pin_evaluation_replaces_previous_result():
    _require("memory_engine")
    integrations.pin_evaluation("m", {"accuracy": 0.1}, block_id="mem20corez:test-repin")
    integrations.pin_evaluation("m", {"accuracy": 0.9}, block_id="mem20corez:test-repin")

    from memory_engine.memory import get_pinned_block
    assert "accuracy=0.9" in get_pinned_block("mem20corez:test-repin")["content"]


def test_ops_declared_scripts_reads_this_estate():
    _require("mem20ops")
    rows = integrations.declared_console_scripts(ESTATE)
    assert rows
    assert "mem20corez" in {r["name"] for r in rows}
    for row in rows:
        assert row["package_dir"].startswith(str(ESTATE))


def test_cliz_envelope_shape():
    _require("mem20cliz")
    env = integrations.cli_envelope("mem20corez", ["wiring"], 0, "ok", "")
    assert env["schema"] == "mem20.cli/1"
    assert env["ok"] is True
    assert env["command"] == "mem20corez"


def test_verify_discovers_test_bearing_packages():
    _require("mem20verify")
    packages = integrations.test_bearing_packages(ESTATE)
    assert "mem20corez" in packages
    assert "mem20verify" in packages


def test_wiring_report_all_edges_live():
    report = integrations.wiring_report(ESTATE)
    assert report["edges_total"] == 6
    assert report["ok"] is True, json.dumps(report, indent=2, default=str)
    assert report["edges_ok"] == 6


def test_wiring_cli_exits_zero(capsys):
    from mem20corez.cli import main
    code = main(["wiring", "--root", str(ESTATE)])
    out = capsys.readouterr().out
    assert code == 0
    assert "6/6 edges live" in out


def test_wiring_cli_json_is_parseable(capsys):
    from mem20corez.cli import main
    code = main(["wiring", "--root", str(ESTATE), "--json"])
    out = capsys.readouterr().out
    assert code == 0
    # ``--json`` is provided by mem20cliz's ``@json_main``. When mem20cliz is
    # importable the output is the estate envelope (report in ``stdout``);
    # when it is not, the CLI warns and falls back to human output. Both are
    # real, supported modes -- assert on whichever one actually ran.
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        assert "6/6 edges live" in out
        return
    if "schema" in payload:
        assert payload["schema"] == "mem20.cli/1"
        assert payload["ok"] is True
        # ``@json_main`` strips the flag before calling the command, so the
        # command itself emits human output and the envelope carries it.
        try:
            report = json.loads(payload["stdout"])
        except json.JSONDecodeError:
            assert "6/6 edges live" in payload["stdout"]
            return
    else:
        report = payload
    assert report["ok"] is True
    assert len(report["edges"]) == 6
