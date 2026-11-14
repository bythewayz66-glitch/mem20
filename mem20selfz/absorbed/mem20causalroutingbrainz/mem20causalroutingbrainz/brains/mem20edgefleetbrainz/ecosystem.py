"""Cross-subsystem wiring for mem20causalroutingbrainz (mem20 criterion 6).

A fleet brain that only knows about its own SQLite file is a simulator, not an
estate system. The peers below are the fleet-specific judgements it needs, and
none of them is a generic "memory/focus/catalog" pick: each one owns a distinct
part of the physical-device problem.

===========================  ==================================================
subsystem                    function actually called
===========================  ==================================================
``mem20zerotouchnodeswarmz`` ``register_node`` / ``discover`` / ``quorum`` /
                              ``assign_task``
``mem20energyawarecomputemigrationz`` ``energy_cost`` / ``carbon_footprint`` /
                              ``greenest_node`` / ``migrate_decision``
``mem20devicecapabilitycompilerz`` ``detect_capabilities`` / ``compatibility`` /
                              ``feature_flags``
``mem20hardwaremarketplacez`` ``price_estimate`` / ``search`` /
                              ``marketplace_health``
``mem20roamingworkloadschedulerz`` ``schedule`` / ``node_load`` /
                              ``scheduler_health``
``mem20modelsleepandwakesystemz`` ``track_activity`` / ``should_sleep`` /
                              ``sleep`` / ``wake`` / ``sleep_health``
===========================  ==================================================

Every adapter is called from :mod:`mem20causalroutingbrainz.service` on the normal
register/submit/dispatch path, so the tests exercise real return values instead
of asserting an import statement exists. The failure policy matches the rest of
the estate: a missing or raising sibling is recorded as
``{"ok": False, "error": ...}`` and never aborts a schedule; the service then
surfaces an explicit warning so an operator can see which physical judgement was
unavailable.

Import layout
-------------
These projects use the nested ``<project>/<project>/domain.py`` layout, so
``_bootstrap()`` puts each project directory ahead of the repo root. Without
that, ``import mem20zerotouchnodeswarmz`` would match the outer directory as a
namespace package with no exports.
"""
from __future__ import annotations

import pathlib
import sys
import time
from typing import Iterable, Mapping, Sequence

__all__ = [
    "swarm_admission",
    "energy_plan",
    "device_fit",
    "hardware_quote",
    "roaming_plan",
    "sleep_plan",
    "probe",
]

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

_PROJECTS = (
    "mem20zerotouchnodeswarmz",
    "mem20energyawarecomputemigrationz",
    "mem20devicecapabilitycompilerz",
    "mem20hardwaremarketplacez",
    "mem20roamingworkloadschedulerz",
    "mem20modelsleepandwakesystemz",
)


def _bootstrap() -> None:
    """Put each project directory ahead of the repo root on ``sys.path``."""
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)


_bootstrap()


def _swarm_node(node: Mapping) -> dict:
    """Translate a fleet node into the swarm's vocabulary."""
    return {
        "id": node.get("node_id") or node.get("id"),
        "capacity": float(node.get("cpu_cores", 1)),
        "availability": float(node.get("reliability", 1.0)),
        "capabilities": list(node.get("capabilities") or ()),
        "latency_ms": float(node.get("latency_ms", 0.0)),
        "energy": float(node.get("idle_watts", 0.0)),
        "status": "ready" if node.get("status", "online") in ("online", "degraded") else
                  str(node.get("status", "online")),
    }


def _energy_node(node: Mapping) -> dict:
    """Translate a fleet node into the energy migration's vocabulary."""
    return {
        "id": node.get("node_id") or node.get("id"),
        "power_watts": float(node.get("peak_watts", 100.0)),
        "speed": float(node.get("cpu_cores", 1)),
        "energy_rate": float(node.get("price_per_hour", 0.12)),
        "carbon_g_per_kwh": float(node.get("carbon_g_per_kwh", 400.0)),
    }


# --------------------------------------------------------------------------
# adapters
# --------------------------------------------------------------------------
def swarm_admission(node: Mapping, peers: Sequence[Mapping] = (),
                    capability: str | None = None,
                    urgency: float = 0.5) -> dict:
    """Admit a node to the zero-touch swarm and cross-check the fleet view.

    The fleet brain owns capacity accounting, but the swarm owns membership:
    whether a node joins, whether the resulting membership has quorum, and which
    node the swarm would pick for a capability. Asking it here keeps the fleet
    from advertising a node the swarm would never accept.
    """
    try:
        from mem20zerotouchnodeswarmz.domain import (
            assign_task,
            discover,
            quorum,
            register_node,
        )

        swarm = {"nodes": [_swarm_node(peer) for peer in peers]}
        admitted = register_node(swarm, _swarm_node(node))
        ready = discover(admitted, capability=capability)
        task = {"capability": capability, "urgency": float(urgency)}
        assignment = assign_task(admitted, task)
        chosen = assignment.get("node") or {}
        return {"ok": True, "subsystem": "mem20zerotouchnodeswarmz",
                "admitted": len(admitted["nodes"]), "ready": len(ready),
                "quorum": quorum(admitted),
                "preferred_node": chosen.get("id"),
                "preferred_score": assignment.get("score"),
                "fallbacks": [item.get("id") for item in assignment.get("fallbacks", [])]}
    except Exception as exc:  # noqa: BLE001 - reported, never fatal
        return {"ok": False, "subsystem": "mem20zerotouchnodeswarmz",
                "error": f"{type(exc).__name__}: {exc}"}


def energy_plan(nodes: Sequence[Mapping], workload: Mapping,
                source: Mapping | None = None) -> dict:
    """Rank nodes by energy and carbon for this workload.

    ``energy_cost`` is a monetary figure and ``carbon_footprint`` is grams of
    CO2, so they are reported separately instead of being collapsed into one
    invented "green score". The fleet uses this as an explicit component of the
    placement explanation and as the authority for rebalance moves.
    """
    try:
        from mem20energyawarecomputemigrationz.domain import (
            carbon_footprint,
            energy_cost,
            greenest_node,
            migrate_decision,
        )

        candidates = [_energy_node(node) for node in nodes]
        if not candidates:
            return {"ok": True, "subsystem": "mem20energyawarecomputemigrationz",
                    "greenest": None, "energy_cost": 0.0, "carbon_g": 0.0}
        size = max(1.0, float(workload.get("cpu", 1.0))
                   * float(workload.get("duration_s", 60.0)) / 60.0)
        payload = {"size": size, "id": workload.get("workload_id")}
        greenest = greenest_node(candidates, payload)
        cost = energy_cost(greenest, size)
        carbon = carbon_footprint(greenest, size)
        migration = None
        if source is not None:
            migration = migrate_decision(_energy_node(source), greenest, payload)
        return {"ok": True, "subsystem": "mem20energyawarecomputemigrationz",
                "greenest": greenest.get("id") if greenest else None,
                "energy_cost": cost, "carbon_g": carbon,
                "migration": migration, "workload_size": size}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20energyawarecomputemigrationz",
                "error": f"{type(exc).__name__}: {exc}"}


def device_fit(device: Mapping, requirements: Iterable[str] = ()) -> dict:
    """Ask the capability compiler what the device can actually run.

    This is separate from the fleet's own capability gate: the compiler derives
    tiers and feature flags from hardware (ML capable, 3D capable, low-memory
    mode) that a workload author should not have to restate in every submission.
    """
    try:
        from mem20devicecapabilitycompilerz.domain import (
            compatibility,
            detect_capabilities,
            feature_flags,
        )

        hardware = {
            "cpu_cores": int(device.get("cpu_cores", 1)),
            "gpu": bool(device.get("gpu_count", 0)),
            "memory_gb": float(device.get("memory_gb", 1)),
            "storage_gb": float(device.get("storage_gb", 100)),
            "network": str(device.get("network", "wifi")),
        }
        caps = detect_capabilities(hardware)
        verdict = compatibility(hardware, list(requirements))
        return {"ok": True, "subsystem": "mem20devicecapabilitycompilerz",
                "tier": caps.get("tier"),
                "can_run_ml": caps.get("can_run_ml"),
                "can_render_3d": caps.get("can_render_3d"),
                "compatible": verdict.get("compatible"),
                "missing": verdict.get("missing", []),
                "features": feature_flags(caps)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20devicecapabilitycompilerz",
                "error": f"{type(exc).__name__}: {exc}"}


def hardware_quote(node: Mapping, listings: Sequence[Mapping] = ()) -> dict:
    """Price a node's hardware through the estate's hardware marketplace.

    The fleet's hourly price is an operator choice, not a valuation. The
    marketplace gives an independent replacement-cost estimate and a comparable
    listing, which is what makes a submitted ``max_price_per_hour`` meaningful
    instead of self-referential.
    """
    try:
        from mem20hardwaremarketplacez.domain import (
            marketplace_health,
            price_estimate,
            search,
        )

        hardware = {
            "cores": int(node.get("cpu_cores", 1)),
            "memory_gb": float(node.get("memory_gb", 1)),
            "storage_gb": float(node.get("storage_gb", 100)),
            "gpu": bool(node.get("gpu_count", 0)),
        }
        estimate = price_estimate(hardware)
        inventory = [
            {
                "seller": str(item.get("region", "local")),
                "hardware": f"{item.get('kind', 'server')} "
                            f"{item.get('cpu_cores', 1)}c/"
                            f"{item.get('memory_gb', 1)}gb",
                "price": float(item.get("price_per_hour", 0.0)),
                "available": str(item.get("status", "online")) in ("online", "degraded"),
            }
            for item in listings
        ]
        query = str(node.get("kind", "server"))
        matches = search(inventory, query)
        health = marketplace_health(inventory)
        return {"ok": True, "subsystem": "mem20hardwaremarketplacez",
                "estimate": estimate, "matches": len(matches),
                "market": health}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20hardwaremarketplacez",
                "error": f"{type(exc).__name__}: {exc}"}


def roaming_plan(workloads: Sequence[Mapping], nodes: Sequence[Mapping]) -> dict:
    """Ask the roaming scheduler for an independent assignment.

    The fleet's scorer is energy- and reliability-aware; the roaming scheduler
    is load-only and roaming-oriented. Running both and recording the divergence
    is deliberate: when the two disagree the operator sees that the decision is
    contested instead of receiving a single confident answer.
    """
    try:
        from mem20roamingworkloadschedulerz.domain import (
            node_load,
            schedule,
            scheduler_health,
        )

        work = [{"id": item.get("workload_id") or item.get("id"),
                 "cost": float(item.get("cpu", 1.0))}
                for item in workloads]
        fleet = [{"id": item.get("node_id") or item.get("id"),
                  "load": float(item.get("current_cpu", 0.0))}
                 for item in nodes]
        # Schedule mutates the node loads as it assigns; pass the translated
        # fleet directly so ``loads`` below reports the post-assignment state
        # instead of the state before the scheduler ran.
        assignments = schedule(work, fleet)
        return {"ok": True, "subsystem": "mem20roamingworkloadschedulerz",
                "assignments": assignments,
                "loads": node_load(fleet),
                "health": scheduler_health(fleet)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20roamingworkloadschedulerz",
                "error": f"{type(exc).__name__}: {exc}"}


def sleep_plan(nodes: Sequence[Mapping], idle_threshold: float = 300.0,
               now: float | None = None) -> dict:
    """Decide which idle nodes should sleep and which must stay awake.

    Edge hardware is often a phone or a laptop; keeping every node awake burns
    the energy budget the fleet is supposed to optimise. The sleep system owns
    the idle policy, so the fleet asks it rather than inventing a second one.
    """
    try:
        from mem20modelsleepandwakesystemz.domain import (
            should_sleep,
            sleep,
            sleep_health,
            track_activity,
            wake,
        )

        now = time.time() if now is None else float(now)
        models: list[dict] = []
        for node in nodes:
            last_seen = float(node.get("last_seen", 0.0) or now)
            model = {"id": node.get("node_id") or node.get("id")}
            track_activity(model, activity_ts=last_seen)
            if should_sleep(model, idle_threshold=idle_threshold):
                models.append(sleep(model))
            else:
                models.append(wake(model, trigger="recent-activity"))
        sleeping = [m["id"] for m in models if m.get("state") == "sleeping"]
        awake = [m["id"] for m in models if m.get("state") == "awake"]
        return {"ok": True, "subsystem": "mem20modelsleepandwakesystemz",
                "sleeping": sleeping, "awake": awake,
                "health": sleep_health(models)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20modelsleepandwakesystemz",
                "error": f"{type(exc).__name__}: {exc}"}


def probe() -> dict:
    """Run every adapter once and report which physical judgements are live."""
    node = {"node_id": "probe-a", "cpu_cores": 8, "memory_gb": 16,
            "gpu_count": 1, "reliability": 0.98, "capabilities": ["cpu", "gpu"],
            "last_seen": time.time()}
    workload = {"workload_id": "probe-w", "cpu": 2, "duration_s": 60,
                "required_capabilities": ["cpu"]}
    checks = [
        swarm_admission(node, peers=[node], capability="cpu"),
        energy_plan([node], workload),
        device_fit(node, requirements=["gpu", "memory_4gb"]),
        hardware_quote(node, listings=[node]),
        roaming_plan([workload], [node]),
        sleep_plan([node]),
    ]
    return {
        "ok": all(check.get("ok") for check in checks),
        "checks": {check.get("subsystem", "unknown"): check for check in checks},
        "reachable": sorted({check.get("subsystem") for check in checks
                             if check.get("ok")}),
    }
