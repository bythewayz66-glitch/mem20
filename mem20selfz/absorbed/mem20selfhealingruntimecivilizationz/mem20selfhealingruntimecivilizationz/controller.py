"""Fleet controller: the self-healing runtime civilization as a running system.

This is the layer that turns the pure domain model in :mod:`domain` into an
operational subsystem, and it is where the substrate integrations earn their
place. A cycle does the following, in order, with the mem20 module that does the
real work named in brackets:

1. **Catalogue** — ask ``toolchest.catalog`` which mem20 subsystems exist on
   disk and whether each is importable. Importable subsystems start near-full
   health; ones that are not importable start degraded, so a fresh run has real
   failures to repair rather than a synthetic scenario. [``toolchest.catalog``]
2. **Budget** — derive the repair ceiling from the kiln triangle budgets, so the
   repair budget is a published number from another subsystem, not a constant
   invented here. [``mem20kilnz.budgets``]
3. **Plan** — ask the plans subsystem which action to take for the unhealthy
   components (failover / restart) instead of hard-coding a rule.
   [``mem20selfhealingplansz``]
4. **Decompose** — split the failure description into repair target fragments.
   [``memory_engine.retrieval_v2``]
5. **Cycle** — run the bounded detect/quarantine/cascade/repair pass. [``domain``]
6. **Redact + timestamp** — scrub credentials out of repair error text and
   validate the record's event time against the memory engine's event-time
   contract, *before* anything is persisted or published.
   [``memory_engine.memory``]
7. **Persist** — write the cycle record and an event to SQLite WAL via the
   subsystem's own store. [``runtime.Store``]
8. **Announce / publish** — register on the fleet gateway and broadcast the
   summary. [``gateway.mem20_gateway``]
9. **Serve** — expose ``/health /ready /metrics`` through the MCP health
   surface, fed by this controller. [``mcp/health.py``]

Every step degrades: if an integration is missing, that step is skipped and the
record says so in ``integrations`` — the controller never fabricates the work.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import domain
from .integrations import Substrate
from .runtime import Store

__all__ = ["FleetController", "ControllerConfig", "main"]

DEFAULT_STATE_DIR = Path(os.environ.get("MEM20_SELFHEALING_STATE", "state/selfhealing"))

#: how much health a planner action restores, keyed by the planner's own action
#: vocabulary. A full failover replaces the failing component; a restart is a
#: partial recovery, which is exactly the distinction the plan makes.
ACTION_RECOVERY = {
    "failover": 0.9,
    "restart": 0.6,
    "restart-or-failover": 0.6,
    "restart_or_failover": 0.6,
}
DEFAULT_RECOVERY = 0.5


@dataclass
class ControllerConfig:
    """Runtime knobs. Defaults are the values the tests and the demo assert."""

    threshold: float = 0.30
    repair_amount: float = 0.50
    max_repairs: int = 3
    history_limit: int = 200
    health_port: int = 0
    announce: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ControllerConfig":
        fields = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in fields})


class FleetController:
    """Owns the civilization, the substrate, the store and the health surface."""

    def __init__(
        self,
        config: Optional[ControllerConfig] = None,
        state_dir: Optional[Path] = None,
        substrate: Optional[Substrate] = None,
        repo_root: Optional[Path] = None,
    ) -> None:
        self.config = config or ControllerConfig()
        self.state_dir = Path(state_dir or DEFAULT_STATE_DIR)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.substrate = substrate or Substrate(root=repo_root, state_dir=self.state_dir)
        self.store = Store(self.state_dir / "civilization.sqlite3")
        self.civilization = domain.Civilization(
            threshold=self.config.threshold,
            repair_amount=self.config.repair_amount,
            max_repairs=self.config.max_repairs,
            history_limit=self.config.history_limit,
        )
        self.cycles = 0
        self.repairs_applied = 0
        self.redactions = 0
        self.planned_actions: Dict[str, str] = {}
        self.health_server: Optional[Dict[str, Any]] = None
        self.created_at = time.time()
        self._announced = False
        self._budget: Dict[str, Any] = {}

    # -- construction --------------------------------------------------------
    @classmethod
    def from_catalogue(
        cls,
        limit: Optional[int] = 12,
        root: Optional[Path] = None,
        **kwargs: Any,
    ) -> "FleetController":
        """Build a controller whose fleet is the real on-disk mem20 estate.

        Subsystem health comes from what the catalogue actually measured:
        importable subsystems start at 1.0, non-importable ones at 0.15 (below
        the default threshold, so the first cycle has genuine work to do).
        """
        controller = cls(root=root, **kwargs)
        controller.load_fleet_from_catalogue(limit=limit, root=root)
        return controller

    def load_fleet_from_catalogue(
        self,
        limit: Optional[int] = 12,
        root: Optional[Path] = None,
    ) -> List[str]:
        entries = self.substrate.toolchest.catalogue(root=root or self.substrate.paths.root)
        names: List[str] = []
        for entry in entries:
            name = str(entry.get("name") or "")
            if not name.startswith("mem20"):
                continue
            importable = self.substrate.toolchest.importable(name, root=root)
            health = 1.0 if importable else (0.85 if importable is None else 0.15)
            if name in self.civilization.agents:
                continue
            try:
                self.civilization.add_agent(name, health=health)
            except domain.CivilizationError:
                continue
            names.append(name)
            if limit is not None and len(names) >= limit:
                break
        if names:
            # A dependency-free fleet would never exercise the cascade path, so
            # wire each later subsystem behind the first: the gateway is the
            # estate's entry point, and everything else depends on it.
            head = names[0]
            for name in names[1:]:
                if head in self.civilization.agents and name != head:
                    self.civilization.agents[name].depends_on = [head]
        self.civilization.validate()
        return names

    # -- introspection -------------------------------------------------------
    def health(self) -> Dict[str, Any]:
        return self.civilization.health()

    def metrics_snapshot(self) -> Dict[str, Any]:
        base = self.civilization.health()
        return {
            "roadmap": "RM-217",
            "cycles": self.cycles,
            "repairs_applied": self.repairs_applied,
            "redactions": self.redactions,
            "agents": base["agents"],
            "alive": base["alive"],
            "quarantined": base["quarantined"],
            "dead": base["dead"],
            "avg_health": base["avg_health"],
            "integrations_available": self.substrate.probe()["available"],
            "uptime_seconds": round(time.time() - self.created_at, 3),
        }

    def integrations(self) -> Dict[str, Any]:
        return self.substrate.probe()

    # -- the cycle -----------------------------------------------------------
    def _plan_actions(self, unhealthy: Sequence[str]) -> Dict[str, str]:
        """Ask the plans subsystem what to do; fall back to a documented rule."""
        if not unhealthy:
            return {}
        components = [
            {"id": name, "healthy": False}
            for name in unhealthy
        ]
        components.append({"id": "_spare", "healthy": True})
        plan = self.substrate.plans.plan(
            components, db_path=self.state_dir / "plans.sqlite3"
        )
        actions: Dict[str, str] = {}
        if isinstance(plan, dict):
            for action in plan.get("actions", []) or []:
                if not isinstance(action, dict):
                    continue
                failed = action.get("failed") or {}
                ident = failed.get("id") if isinstance(failed, dict) else None
                if ident:
                    actions[str(ident)] = str(action.get("action", ""))
        return actions

    def cycle(self, now: Optional[float] = None) -> Dict[str, Any]:
        """Run one full self-healing cycle and return its persisted record."""
        civ = self.civilization
        civ.validate()

        # 2. budget from the kiln asset budgets (published numbers, not invented)
        if not self._budget:
            self._budget = self.substrate.kiln.budget_for("mem20gateway")
            civ.max_repairs = int(self._budget.get("max_repairs", civ.max_repairs))

        # 3. plan for the components that are currently below threshold
        unhealthy = sorted(
            a.name
            for a in civ.agents.values()
            if a.status != domain.DEAD and a.health <= civ.threshold
        )
        self.planned_actions = self._plan_actions(unhealthy)

        # 4. decompose the failure description into repair targets
        targets = self.substrate.retrieval.targets(
            "unhealthy subsystems " + " ".join(unhealthy) if unhealthy else ""
        )

        # 5. the bounded cycle itself
        def repair(name: str) -> float:
            action = self.planned_actions.get(name, "")
            return ACTION_RECOVERY.get(action, DEFAULT_RECOVERY)

        record = civ.run_cycle(repair_fn=repair if self.planned_actions else None, now=now)
        self.cycles += 1
        self.repairs_applied += len(record["repaired"])

        # 6. redact error text and validate the event time
        record["failed"] = [
            {
                "agent": item["agent"],
                "error": self.substrate.memory.redact(item["error"]),
            }
            for item in record.get("failed", []) or []
        ]
        # The event time is validated by memory_engine, whose contract rejects
        # dates absurdly far from now (a missing-century typo guard). A record is
        # never published with an unvalidated timestamp: when the engine rejects
        # the value we fall back to the current time and say so in the record.
        candidate = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime(record["ts"] if now is not None else time.time()),
        )
        validated = self.substrate.memory.validate_ts(candidate)
        record["ts_validated"] = validated != candidate
        record["ts_iso"] = validated if record["ts_validated"] else candidate
        record["planned_actions"] = dict(self.planned_actions)
        record["repair_targets"] = list(targets)
        record["budget"] = dict(self._budget)
        record["cycle"] = self.cycles
        record["integrations"] = {
            r["integration"]: r["available"] for r in self.substrate.probe()["integrations"]
        }
        self.redactions = self.substrate.memory.redactions

        # 7. persist
        cycle_id = f"c{self.cycles:05d}-{uuid.uuid4().hex[:8]}"
        self.store.put(
            "cycle",
            cycle_id,
            {k: v for k, v in record.items() if k != "ts"},
            node="local",
        )

        # 8. announce once, then publish the summary
        if self.config.announce:
            if not self._announced:
                self.substrate.gateway.announce(
                    name="mem20selfhealingruntimecivilizationz",
                    location="local",
                )
                self._announced = True
            self.substrate.gateway.publish(
                "mem20selfhealingruntimecivilizationz",
                json.dumps(
                    {
                        "cycle": self.cycles,
                        "status": record["status"],
                        "repaired": record["repaired"],
                        "remaining": record["remaining"],
                    },
                    sort_keys=True,
                ),
            )

        record["cycle_id"] = cycle_id
        # NOTE: no ``report`` key here — the civilization report embeds
        # ``last_cycle``, which is this very record, so attaching it would make
        # the payload circular and un-serialisable. Callers that want the report
        # use ``controller.report()``.
        return record

    def run(self, cycles: int = 1, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Run ``cycles`` bounded cycles (never unbounded)."""
        out = []
        for _ in range(max(1, int(cycles))):
            out.append(self.cycle(now=now))
        return out

    # -- surfaces ------------------------------------------------------------
    def start_health_surface(self, port: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Expose /health /ready /metrics through the MCP health module."""
        self.health_server = self.substrate.health.start(
            self, port=self.config.health_port if port is None else port
        )
        return self.health_server

    def stop_health_surface(self) -> None:
        self.substrate.health.stop()
        self.health_server = None

    def report(self) -> Dict[str, Any]:
        return {
            "roadmap": "RM-217",
            "status": self.civilization.status(),
            "cycles": self.cycles,
            "budget": self._budget,
            "planned_actions": self.planned_actions,
            "civilization": self.civilization.report(),
            "integrations": self.substrate.probe(),
            "metrics": self.metrics_snapshot(),
        }


# --- CLI --------------------------------------------------------------------

def _write_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI: ``demo`` | ``catalogue`` | ``run`` | ``report`` | ``probe`` | ``serve``."""
    import argparse

    ap = argparse.ArgumentParser(
        prog="mem20selfhealingruntimecivilizationz",
        description="Self-healing runtime civilization — fleet controller",
    )
    ap.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="run the deterministic demo cycle (JSON)")
    p_cat = sub.add_parser("catalogue", help="show the catalogue this controller discovers")
    p_cat.add_argument("--limit", type=int, default=12)
    p_run = sub.add_parser("run", help="run N cycles against the real catalogue")
    p_run.add_argument("--cycles", type=int, default=1)
    p_run.add_argument("--limit", type=int, default=12)
    p_run.add_argument("--damage", action="append", default=[], metavar="AGENT=AMOUNT")
    p_run.add_argument("--no-gateway", action="store_true")
    p_rep = sub.add_parser("report", help="report the current fleet state")
    p_rep.add_argument("--limit", type=int, default=12)
    sub.add_parser("probe", help="report which mem20 integrations resolve")
    p_serve = sub.add_parser("serve", help="run cycles and serve /health /ready /metrics")
    p_serve.add_argument("--port", type=int, default=0)
    p_serve.add_argument("--cycles", type=int, default=1)

    args = ap.parse_args(argv)

    if args.cmd == "demo":
        _write_json(domain._demo())
        return 0

    cfg = ControllerConfig(announce=not getattr(args, "no_gateway", False))
    controller = FleetController(
        config=cfg,
        state_dir=Path(args.state_dir),
    )

    if args.cmd == "probe":
        _write_json(controller.integrations())
        return 0

    controller.load_fleet_from_catalogue(limit=args.limit)

    if args.cmd == "catalogue":
        _write_json(
            {
                "agents": len(controller.civilization.agents),
                "names": sorted(controller.civilization.agents),
            }
        )
        return 0

    if args.cmd == "report":
        _write_json(controller.report())
        return 0

    for pair in getattr(args, "damage", []) or []:
        name, _, amount = pair.partition("=")
        controller.civilization.damage(name.strip(), float(amount))

    if args.cmd == "serve":
        controller.start_health_surface(port=args.port)
        controller.run(cycles=args.cycles)
        info = controller.health_server or {}
        print(
            json.dumps(
                {"serving": True, "port": info.get("port"), "metrics": controller.metrics_snapshot()},
                indent=2,
                sort_keys=True,
            ),
            flush=True,
        )
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:  # pragma: no cover - interactive only
            controller.stop_health_surface()
        return 0

    _write_json(controller.run(cycles=args.cycles))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
