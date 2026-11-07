"""CLI tests: every subcommand returns real JSON and a correct exit code."""

from __future__ import annotations

import json

import pytest

from mem20edgefleetbrainz import runtime


def call(capsys, store: str, *args: str):
    code = runtime.main(["--store", store, *args])
    output = capsys.readouterr().out
    return code, json.loads(output)


def test_cli_full_lifecycle(tmp_path, capsys):
    store = str(tmp_path / "cli.db")

    code, payload = call(capsys, store, "status")
    assert code == 0
    assert payload["ok"] is True
    assert payload["metrics"]["nodes"] == 0

    code, payload = call(
        capsys, store, "node", "add", "--id", "a", "--kind", "server",
        "--cpu", "8", "--memory", "16", "--gpus", "1",
        "--capabilities", "cpu,gpu",
        "--reliability", "0.99", "--price", "0.2", "--region", "local",
    )
    assert code == 0
    assert payload["node"]["node_id"] == "a"
    assert payload["node"]["gpu_count"] == 1
    assert payload["device"]["can_render_3d"] is True
    assert payload["swarm"]["ok"] is True

    code, payload = call(capsys, store, "node", "add", "--id", "b",
                         "--cpu", "4", "--memory", "8", "--capabilities", "cpu")
    assert code == 0
    assert payload["version"] == 1

    code, payload = call(capsys, store, "node", "list")
    assert code == 0
    assert [node["node_id"] for node in payload["nodes"]] == ["a", "b"]

    code, payload = call(
        capsys, store, "workload", "submit", "--id", "w1", "--name", "demo",
        "--cpu", "2", "--memory", "2", "--capabilities", "cpu",
        "--priority", "80", "--duration", "60", "--deadline", "600",
        "--max-price", "1.0", "--energy-budget", "100",
        "--idempotency-key", "cli-w1",
    )
    assert code == 0
    assert payload["created"] is True
    assert payload["workload"]["workload_id"] == "w1"

    code, payload = call(capsys, store, "workload", "get", "w1")
    assert code == 0
    assert payload["workload"]["state"] == "queued"

    code, payload = call(capsys, store, "workload", "list")
    assert code == 0
    assert len(payload["workloads"]) == 1

    code, payload = call(capsys, store, "dispatch", "--id", "w1")
    assert code == 0
    assert payload["dispatched"] == 1

    code, payload = call(capsys, store, "workload", "complete", "w1")
    assert code == 0
    assert payload["workload"]["state"] == "completed"

    code, payload = call(capsys, store, "predict", "--horizon", "7200")
    assert code == 0
    assert len(payload["forecasts"]) == 2
    assert payload["forecasts"][0]["horizon_s"] == 7200.0

    code, payload = call(capsys, store, "energy", "--hours", "12")
    assert code == 0
    assert payload["energy"]["hours"] == 12.0

    code, payload = call(capsys, store, "events", "--since", "0", "--limit", "10")
    assert code == 0
    assert payload["events"]

    code, payload = call(capsys, store, "metrics")
    assert code == 0
    assert payload["nodes"] == 2
    assert payload["workloads"] == 1
    assert payload["placements"] == 1

    code, payload = call(capsys, store, "snapshot", "--label", "cli")
    assert code == 0
    snapshot_id = payload["snapshot_id"]

    code, payload = call(capsys, store, "restore", snapshot_id)
    assert code == 0
    assert payload["restored"] is True

    code, payload = call(capsys, store, "rebalance", "--threshold", "0.8")
    assert code == 0
    assert payload["ok"] is True

    code, payload = call(capsys, store, "benchmark", "--iterations", "3")
    assert code == 0
    assert payload["iterations"] == 3

    code, payload = call(capsys, store, "doctor")
    assert code == 0
    assert len(payload["ecosystem"]["reachable"]) == 6

    code, payload = call(capsys, store, "simulate")
    assert code == 0
    assert payload["ok"] is True

    code, payload = call(capsys, store, "node", "status", "b", "draining")
    assert code == 0
    assert payload["node"]["status"] == "draining"

    code, payload = call(capsys, store, "node", "drain", "b")
    assert code == 0
    assert payload["node"]["status"] == "draining"

    code, payload = call(capsys, store, "node", "evacuate", "b")
    assert code == 0
    assert payload["drained"] is True

    code, payload = call(capsys, store, "node", "delete", "b")
    assert code == 0
    assert payload["deleted"] is True


def test_cli_maps_errors_to_exit_code_and_json(tmp_path, capsys):
    store = str(tmp_path / "errors.db")

    code, payload = call(capsys, store, "workload", "submit", "--id", "bad",
                         "--cpu", "0")
    assert code == 1
    assert payload["ok"] is False
    assert payload["kind"] == "ValidationError"

    code, payload = call(capsys, store, "node", "add", "--id", "bad",
                         "--cpu", "0")
    assert code == 1
    assert payload["ok"] is False

    code, payload = call(capsys, store, "workload", "get", "missing")
    assert code == 1
    assert payload["kind"] == "NotFoundError"

    code, payload = call(capsys, store, "node", "delete", "missing")
    assert code == 1
    assert payload["kind"] == "NotFoundError"

    code, payload = call(capsys, store, "workload", "submit", "--json", "{not json")
    assert code == 1
    assert "not valid JSON" in payload["error"]


def test_cli_reads_json_from_a_file(tmp_path, capsys):
    store = str(tmp_path / "json.db")
    spec = tmp_path / "node.json"
    spec.write_text(json.dumps({
        "node_id": "from-file", "cpu_cores": 4, "memory_gb": 8,
        "capabilities": ["cpu"], "reliability": 0.95,
    }), encoding="utf-8")

    code, payload = call(capsys, store, "node", "add", "--json", f"@{spec}")
    assert code == 0
    assert payload["node"]["node_id"] == "from-file"
    assert payload["node"]["cpu_cores"] == 4


def test_default_store_path_honours_the_environment(tmp_path, monkeypatch):
    target = tmp_path / "custom.db"
    monkeypatch.setenv("MEM20_EDGEFLEET_STORE", str(target))
    assert runtime.default_store_path() == target

    monkeypatch.delenv("MEM20_EDGEFLEET_STORE")
    fallback = runtime.default_store_path()
    assert fallback.name == "fleet.db"
    assert ".mem20" in str(fallback)


def test_load_json_flag_rejects_non_objects(tmp_path):
    from mem20edgefleetbrainz.service import ValidationError

    assert runtime._load_json_flag(None) == {}
    assert runtime._load_json_flag('{"a": 1}') == {"a": 1}
    with pytest.raises(ValidationError):
        runtime._load_json_flag("[1, 2]")
