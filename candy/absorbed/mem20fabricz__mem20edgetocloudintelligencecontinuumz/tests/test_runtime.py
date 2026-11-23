from __future__ import annotations

import json

from mem20edgetocloudintelligencecontinuumz.runtime import main


def run(argv, capsys):
    code = main(argv)
    out = capsys.readouterr().out.strip()
    return code, json.loads(out) if out else None


def test_cli_status_doctor_simulate(tmp_path, capsys):
    store = str(tmp_path / "c.db")
    code, data = run(["--store", store, "status"], capsys)
    assert code == 0 and data["ok"]
    code, data = run(["--store", store, "doctor"], capsys)
    assert code == 0 and data["ok"] and data["count"] == 6
    code, data = run(["--store", store, "simulate"], capsys)
    assert code == 0 and data["ok"]


def test_cli_target_workload_dispatch(tmp_path, capsys):
    store = str(tmp_path / "c.db")
    code, data = run(["--store", store, "target", "add", "--id", "t1", "--tier", "local", "--capabilities", "compute", "--cpu", "8", "--memory", "16", "--latency", "2", "--cost", "0"], capsys)
    assert code == 0 and data["ok"] and data["target"]["tier"] == "local"
    code, data = run(["--store", store, "workload", "submit", "--id", "w1", "--cpu", "1", "--memory", "1", "--capabilities", "compute"], capsys)
    assert code == 0 and data["ok"]
    code, data = run(["--store", store, "dispatch", "--id", "w1"], capsys)
    assert code == 0 and data["dispatched"] == 1
    code, data = run(["--store", store, "workload", "complete", "w1", "--reason", "done"], capsys)
    assert code == 0 and data["workload"]["state"] == "completed"
    code, data = run(["--store", store, "metrics"], capsys)
    assert code == 0 and data["metrics"]["targets"] >= 1
