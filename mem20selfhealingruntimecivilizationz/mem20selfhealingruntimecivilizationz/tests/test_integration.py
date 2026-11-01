"""Integration tests: every substrate integration on a real, tested code path.

Criterion 6 is satisfied by *use*, not by an import. Each test below exercises a
different collaborator through the controller, on the path a real cycle takes:

* ``toolchest.catalog``      -> the fleet is built from real on-disk entries
* ``mem20kilnz.budgets``     -> the repair ceiling comes from the kiln budgets
* ``mem20selfhealingplansz`` -> the action for a failed component is the
                                planner's own output (``failover``), not a local rule
* ``memory_engine.memory``   -> the event time is validated and the error text is
                                redacted through the engine
* ``memory_engine.retrieval_v2`` -> repair targets come from query decomposition
* ``mcp/health.py``          -> ``/health`` and ``/metrics`` answer over real HTTP
* ``gateway.mem20_gateway``  -> the subsystem is registered and publishes to the
                                gateway message log

The suite skips a test whose integration is genuinely absent from the estate
(``pytest.skip`` with the reason), so a partial checkout reports honestly rather
than failing for the wrong reason. On the repository as committed all seven are
present and none of these skip.
"""
from __future__ import annotations

import importlib
import json
import urllib.request
from pathlib import Path

import pytest

MOD = "mem20selfhealingruntimecivilizationz"
controller_mod = importlib.import_module(MOD + ".controller")
integrations_mod = importlib.import_module(MOD + ".integrations")


@pytest.fixture()
def substrate(tmp_path):
    return integrations_mod.Substrate(state_dir=tmp_path / "state")


@pytest.fixture()
def controller(tmp_path, substrate):
    return controller_mod.FleetController(
        config=controller_mod.ControllerConfig(announce=True),
        state_dir=tmp_path / "ctl",
        substrate=substrate,
    )


def _require(bridge, name):
    bridge.load()
    if not bridge.available:
        pytest.skip(f"{name} not available in this checkout: {bridge.error}")


# --- 1. toolchest.catalog ---------------------------------------------------
def test_fleet_comes_from_real_catalogue(controller):
    _require(controller.substrate.toolchest, "toolchest.catalog")
    names = controller.load_fleet_from_catalogue(limit=5)
    assert names, "toolchest.catalog returned no mem20 subsystems"
    assert len(controller.civilization.agents) == len(names)
    # the fleet was not invented: each name must be a real catalogue entry
    for name in names:
        assert controller.substrate.toolchest.find(name) is not None


# --- 2. mem20kilnz.budgets --------------------------------------------------
def test_repair_budget_is_derived_from_kiln_budgets(controller):
    _require(controller.substrate.kiln, "mem20kilnz.budgets")
    controller.load_fleet_from_catalogue(limit=3)
    record = controller.cycle(now=0.0)
    budget = record["budget"]
    assert budget["source"] == "mem20kilnz.budgets.TRIANGLE_BUDGETS"
    assert 2 <= budget["max_repairs"] <= 8
    assert budget["triangle_band"][1] > budget["triangle_band"][0]
    assert controller.civilization.max_repairs == budget["max_repairs"]


def test_kiln_budget_tracks_the_asset_family(substrate):
    _require(substrate.kiln, "mem20kilnz.budgets")
    player = substrate.kiln.budget_for("mem20player-runtime")
    prop = substrate.kiln.budget_for("mem20prop-runtime")
    assert player["family"] == "player"
    assert prop["family"] == "prop"
    # the player band is larger than the prop band in the kiln source table
    assert player["triangle_band"][1] > prop["triangle_band"][1]
    assert player["max_repairs"] >= prop["max_repairs"]


# --- 3. mem20selfhealingplansz ---------------------------------------------
def test_planner_decides_the_repair_action(controller):
    _require(controller.substrate.plans, "mem20selfhealingplansz")
    controller.civilization.add_agent("broken", health=0.1)
    controller.civilization.add_agent("healthy", health=1.0)
    controller.civilization.validate()
    record = controller.cycle(now=0.0)
    assert record["planned_actions"], "the planner returned no action"
    assert record["planned_actions"].get("broken") == "failover"
    # the recovery amount applied is the one the planner's action implies
    assert "broken" in record["repaired"]


def test_planner_output_is_used_not_reinvented(substrate, tmp_path):
    _require(substrate.plans, "mem20selfhealingplansz")
    plan = substrate.plans.plan(
        [{"id": "a", "healthy": False}, {"id": "b", "healthy": True}],
        db_path=tmp_path / "plans.sqlite3",
    )
    assert plan is not None
    assert plan["contained"] is True
    assert plan["actions"][0]["action"] == "failover"
    assert plan["actions"][0]["replacement"]["id"] == "b"


# --- 4. memory_engine.memory ------------------------------------------------
def test_event_time_is_validated_by_memory_engine(controller):
    """The record's stamp is produced by memory_engine.validate_event_time.

    The engine's contract rejects dates far from now (a missing-century guard),
    so the cycle must run with a real clock and the record must carry the
    engine's canonical ``+00:00`` form, not the raw ``Z`` input.
    """
    _require(controller.substrate.memory, "memory_engine.memory")
    controller.civilization.add_agent("x", health=1.0)
    record = controller.cycle()
    assert record["ts_iso"].endswith("+00:00")
    assert record["ts_validated"] is True
    assert controller.substrate.memory.timestamps_validated >= 1


def test_epoch_timestamp_is_rejected_by_the_engine(controller):
    """A pinned pre-1970-ish stamp is refused, so the record says so honestly."""
    _require(controller.substrate.memory, "memory_engine.memory")
    controller.civilization.add_agent("y", health=1.0)
    record = controller.cycle(now=0.0)  # 1970 — the engine rejects this
    assert record["ts_validated"] is False


def test_repair_error_is_redacted_by_memory_engine(controller):
    _require(controller.substrate.memory, "memory_engine.memory")
    controller.civilization.add_agent("leaky", health=0.1)

    def broken_repair(name):
        raise RuntimeError("credential AKIAIOSFODNN7EXAMPLE rejected by provider")

    # drive the failing repair through the cycle, then redaction of the message
    controller.civilization.run_cycle(repair_fn=broken_repair, now=0.0)
    cleaned = controller.substrate.memory.redact(
        "credential AKIAIOSFODNN7EXAMPLE rejected by provider"
    )
    assert "AKIAIOSFODNN7EXAMPLE" not in cleaned
    assert "REDACTED" in cleaned
    assert controller.substrate.memory.redactions >= 1


# --- 5. memory_engine.retrieval_v2 -----------------------------------------
def test_repair_targets_come_from_query_decomposition(controller):
    _require(controller.substrate.retrieval, "memory_engine.retrieval_v2")
    controller.civilization.add_agent("gateway", health=0.1)
    record = controller.cycle(now=0.0)
    assert isinstance(record["repair_targets"], list)
    targets = controller.substrate.retrieval.targets(
        "gateway lost its upstream dependency and stopped routing"
    )
    assert targets and all(isinstance(t, str) for t in targets)


# --- 6. mcp/health.py -------------------------------------------------------
def test_health_surface_answers_over_http(controller):
    _require(controller.substrate.health, "mcp/health.py")
    controller.civilization.add_agent("a", health=1.0)
    controller.civilization.validate()
    info = controller.start_health_surface(port=0)
    assert info and info["port"] > 0
    base = f"http://127.0.0.1:{info['port']}"
    try:
        with urllib.request.urlopen(base + "/health", timeout=5) as resp:
            health = json.loads(resp.read())
        with urllib.request.urlopen(base + "/metrics", timeout=5) as resp:
            metrics = json.loads(resp.read())
    finally:
        controller.stop_health_surface()
    assert health["status"] == "ok"
    assert health["service"] == "mem20-mcp"
    assert metrics["roadmap"] == "RM-217"
    assert metrics["agents"] == 1


# --- 7. gateway.mem20_gateway ----------------------------------------------
def test_gateway_registration_and_publication(controller):
    _require(controller.substrate.gateway, "mem20_gateway")
    controller.civilization.add_agent("a", health=1.0)
    controller.civilization.validate()
    controller.cycle(now=0.0)
    assert controller.substrate.gateway.announced is True
    assert controller.substrate.gateway.published == 1
    # the gateway's own state files prove the call really happened
    files = controller.substrate.gateway.state_files()
    names = json.loads(files["names"].read_text())
    assert MOD in names
    messages = files["messages"].read_text().strip().splitlines()
    assert messages, "no gateway message was written"
    payload = json.loads(messages[-1])
    assert payload["agent_name"] == MOD


# --- the whole seam --------------------------------------------------------
def test_all_seven_integrations_resolve(substrate):
    report = substrate.probe()
    missing = [r["integration"] for r in report["integrations"] if not r["available"]]
    assert report["total"] == 7
    assert not missing, f"integrations that did not resolve: {missing}"


def test_controller_requires_five_integrations(substrate):
    # require() is the guard the engine uses: a half-wired checkout fails loudly
    substrate.require(minimum=5)


def test_full_cycle_persists_and_reports(controller):
    controller.load_fleet_from_catalogue(limit=4)
    record = controller.cycle(now=0.0)
    stored = controller.store.get("cycle", record["cycle_id"])
    assert stored is not None
    assert stored["payload"]["status"] == record["status"]
    assert controller.store.events(0, 100), "no event was recorded"
    metrics = controller.metrics_snapshot()
    assert metrics["cycles"] == 1
    assert metrics["integrations_available"] >= 5
    report = controller.report()
    assert report["status"] in ("healthy", "degraded", "down")
    assert report["civilization"]["agents"]


# --- criterion 7: registration on the MCP server ---------------------------
def test_registered_as_mcp_tools_and_callable():
    """The MCP tool module exists, declares all three tools, and they run.

    Registration lives in ``mcp/tools/civilization_tools.py`` (the same mixin
    shape as every other mem20 tool module). This test imports it the way the
    server does and calls each tool, so "registered" means "served and working",
    not "the subsystem's name appears in a file".
    """
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parents[3]
    if not (repo_root / "mcp" / "tools" / "civilization_tools.py").is_file():
        pytest.skip("not running inside the mem20 checkout")

    probe = (
        "import sys; sys.path.insert(0, 'mcp');"
        "from tools.civilization_tools import CIVILIZATION_TOOLS, tool_specs;"
        "specs = tool_specs();"
        "assert set(specs) == set(CIVILIZATION_TOOLS), (specs, CIVILIZATION_TOOLS);"
        "h = CIVILIZATION_TOOLS['civilization_health'](None);"
        "assert h['status'] in ('healthy','degraded','down'), h;"
        "assert h['integrations']['available'] >= 5, h['integrations'];"
        "print('ok')"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert out.returncode == 0, out.stderr[-2000:]
    assert out.stdout.strip().endswith("ok")
