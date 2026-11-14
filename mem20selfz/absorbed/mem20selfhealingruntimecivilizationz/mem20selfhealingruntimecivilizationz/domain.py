"""Self-healing runtime civilization: a fleet of agents that repairs itself.

The domain idea
---------------
A "civilization" is a set of agents plus the dependency edges between them. An
agent is healthy while its own damage budget is unspent *and* the agents it
depends on are healthy — a failure propagates along the dependency graph, which
is what makes this a civilization rather than a pile of unrelated workers.

The controller runs a fixed loop:

    1. sample        read every agent's health (site-local probe result)
    2. quarantine    mark agents unusable if health is at/below the threshold
    3. cascade       a quarantined agent quarantines its dependents
    4. repair        each quarantined agent gets a bounded repair attempt
    5. heal          a successful repair restores health and un-quarantines
    6. recover       once every quarantined agent is healthy again, the whole
                     civilization returns to service in one step

Two invariants are worth stating because they are what the tests pin down:

* **Bounded work.** A single ``run_cycle`` performs at most one repair attempt
  per unhealthy agent. There is no unbounded retry loop, so a permanently dead
  dependency cannot make the controller spin.
* **No silent recovery.** ``status`` only reports ``recovered`` when every agent
  that was quarantined in that cycle is healthy again. A partially healed fleet
  reports ``degraded`` — it never rounds up.

Domain states are deliberately small: ``alive``, ``quarantined`` and ``dead``.
Health is a float in ``[0.0, 1.0]``; ``0.0`` is death and is terminal for that
agent (repair cannot resurrect it, matching the roadmap's honesty rule that lost
agents are replaced, not revived).

This module is pure standard library and has no persistence of its own: the
``runtime`` module owns storage, jobs and the HTTP surface.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence

# --- states -----------------------------------------------------------------
ALIVE = "alive"
QUARANTINED = "quarantined"
DEAD = "dead"

#: status values returned by :meth:`Civilization.status`
HEALTHY = "healthy"
DEGRADED = "degraded"
DOWN = "down"

#: A repair callable takes the agent name and returns the health it restored.
RepairFn = Callable[[str], float]


class CivilizationError(ValueError):
    """Raised for structurally invalid civilizations."""


@dataclass
class Agent:
    """One agent in the fleet."""

    name: str
    health: float = 1.0
    depends_on: List[str] = field(default_factory=list)
    status: str = ALIVE
    repairs: int = 0
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise CivilizationError("agent name must be a non-empty string")
        self.health = _clamp(self.health)
        self.depends_on = list(dict.fromkeys(self.depends_on))
        if self.health <= 0.0:
            self.status = DEAD

    @property
    def usable(self) -> bool:
        return self.status == ALIVE

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "health": round(self.health, 6),
            "depends_on": list(self.depends_on),
            "status": self.status,
            "repairs": self.repairs,
            "reason": self.reason,
        }


def _clamp(value: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError) as exc:
        raise CivilizationError(f"health must be numeric, got {value!r}") from exc
    if v != v:  # NaN
        raise CivilizationError("health must not be NaN")
    return max(0.0, min(1.0, v))


class Civilization:
    """The self-healing fleet.

    Parameters
    ----------
    threshold:
        An agent at or below this health is quarantined at the start of a cycle.
    repair_amount:
        Health restored per successful repair when no ``repair_fn`` is given.
    max_repairs:
        Hard cap on repair attempts per agent across the life of the object.
        This is what stops a flapping agent from consuming the whole budget.
    history_limit:
        How many cycle records to retain (oldest are dropped).
    """

    def __init__(
        self,
        threshold: float = 0.3,
        repair_amount: float = 0.5,
        max_repairs: int = 3,
        history_limit: int = 200,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.threshold = _clamp(threshold)
        self.repair_amount = _clamp(repair_amount)
        self.max_repairs = max(1, int(max_repairs))
        self.history_limit = max(1, int(history_limit))
        self._clock = clock or time.time
        self.agents: Dict[str, Agent] = {}
        self.history: List[Dict[str, object]] = []
        self.last_cycle: Optional[Dict[str, object]] = None

    # -- construction --------------------------------------------------------
    @classmethod
    def from_spec(cls, spec: object, **kwargs: object) -> "Civilization":
        """Build a civilization from a spec.

        Accepts either ``{"agents": {name: {...}}}`` (mapping form) or a list of
        ``{"name": ..., "depends_on": [...]}`` records — the shapes the SDK layer
        and ``CAPABILITY.json`` naturally produce.
        """
        civ = cls(**kwargs)  # type: ignore[arg-type]
        if isinstance(spec, Mapping):
            agents = spec.get("agents", spec) if "agents" in spec else spec
        elif isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
            agents = spec
        else:
            raise CivilizationError("spec must be a mapping or a sequence")
        if isinstance(agents, Mapping):
            for name, cfg in agents.items():
                cfg = cfg or {}
                if not isinstance(cfg, Mapping):
                    raise CivilizationError(f"agent {name!r} config must be a mapping")
                civ.add_agent(
                    str(name),
                    health=cfg.get("health", 1.0),
                    depends_on=cfg.get("depends_on", ()),
                )
        else:
            for cfg in agents:
                if not isinstance(cfg, Mapping) or "name" not in cfg:
                    raise CivilizationError("each agent needs a name")
                civ.add_agent(
                    str(cfg["name"]),
                    health=cfg.get("health", 1.0),
                    depends_on=cfg.get("depends_on", ()),
                )
        civ.validate()
        return civ

    def add_agent(
        self,
        name: str,
        health: float = 1.0,
        depends_on: Sequence[str] = (),
    ) -> Agent:
        if name in self.agents:
            raise CivilizationError(f"duplicate agent {name!r}")
        agent = Agent(name=name, health=health, depends_on=list(depends_on))
        self.agents[name] = agent
        return agent

    def remove_agent(self, name: str) -> Agent:
        if name not in self.agents:
            raise CivilizationError(f"unknown agent {name!r}")
        for other in self.agents.values():
            if name in other.depends_on:
                other.depends_on.remove(name)
        return self.agents.pop(name)

    def validate(self) -> None:
        """Reject unknown dependency targets, self-edges and dependency cycles."""
        for agent in self.agents.values():
            for dep in agent.depends_on:
                if dep not in self.agents:
                    raise CivilizationError(
                        f"agent {agent.name!r} depends on unknown agent {dep!r}"
                    )
                if dep == agent.name:
                    raise CivilizationError(f"agent {agent.name!r} depends on itself")
        # iterative DFS with colouring: 0 unvisited, 1 in-stack, 2 done
        colour: Dict[str, int] = {n: 0 for n in self.agents}
        for root in self.agents:
            if colour[root]:
                continue
            colour[root] = 1
            stack = [(root, iter(self.agents[root].depends_on))]
            while stack:
                node, children = stack[-1]
                descended = False
                for child in children:
                    if colour[child] == 1:
                        raise CivilizationError(f"dependency cycle through {child!r}")
                    if colour[child] == 0:
                        colour[child] = 1
                        stack.append((child, iter(self.agents[child].depends_on)))
                        descended = True
                        break
                if not descended:
                    colour[node] = 2
                    stack.pop()

    # -- observation ---------------------------------------------------------
    def dependents_of(self, name: str) -> List[str]:
        """Every agent that (transitively) depends on ``name``."""
        self._agent(name)
        out: List[str] = []
        frontier = [name]
        seen = {name}
        while frontier:
            cur = frontier.pop()
            for other in self.agents.values():
                if cur in other.depends_on and other.name not in seen:
                    seen.add(other.name)
                    out.append(other.name)
                    frontier.append(other.name)
        return sorted(out)

    def health(self) -> Dict[str, object]:
        """Aggregate health snapshot (stable ordering, rounded floats)."""
        counts = {ALIVE: 0, QUARANTINED: 0, DEAD: 0}
        for agent in self.agents.values():
            counts[agent.status] = counts.get(agent.status, 0) + 1
        total = max(1, len(self.agents))
        avg = sum(a.health for a in self.agents.values()) / total
        return {
            "agents": len(self.agents),
            "alive": counts[ALIVE],
            "quarantined": counts[QUARANTINED],
            "dead": counts[DEAD],
            "avg_health": round(avg, 6),
            "usable_ratio": round(counts[ALIVE] / total, 6),
        }

    def status(self) -> str:
        """``healthy`` / ``degraded`` / ``down`` — never rounded up."""
        if not self.agents:
            return DOWN
        counts = self.health()
        if counts[ALIVE] == len(self.agents):
            return HEALTHY
        return DOWN if counts[ALIVE] == 0 else DEGRADED

    # -- mutation ------------------------------------------------------------
    def damage(self, name: str, amount: float) -> Agent:
        """Apply damage. Reaching 0.0 is terminal (the agent is dead)."""
        agent = self._agent(name)
        if agent.status == DEAD:
            return agent
        agent.health = _clamp(agent.health - abs(float(amount)))
        if agent.health <= 0.0:
            agent.health = 0.0
            agent.status = DEAD
            agent.reason = "health exhausted"
        return agent

    def heal(self, name: str, amount: float) -> Agent:
        """Restore health. A dead agent is never resurrected."""
        agent = self._agent(name)
        if agent.status == DEAD:
            return agent
        agent.health = _clamp(agent.health + abs(float(amount)))
        if agent.health > self.threshold:
            agent.status = ALIVE
            agent.reason = ""
        return agent

    def quarantine(self, name: str, reason: str = "health below threshold") -> Agent:
        agent = self._agent(name)
        if agent.status != DEAD:
            agent.status = QUARANTINED
            agent.reason = reason
        return agent

    def _agent(self, name: str) -> Agent:
        try:
            return self.agents[name]
        except KeyError as exc:
            raise CivilizationError(f"unknown agent {name!r}") from exc

    # -- the control loop ----------------------------------------------------
    def run_cycle(
        self,
        repair_fn: Optional[RepairFn] = None,
        now: Optional[float] = None,
    ) -> Dict[str, object]:
        """One bounded detect -> quarantine -> cascade -> repair -> recover cycle.

        Returns a record of what happened; the same record is appended to
        :attr:`history` (bounded by ``history_limit``).
        """
        ts = self._clock() if now is None else float(now)
        quarantined: List[str] = []
        cascaded: List[str] = []
        repaired: List[str] = []
        exhausted: List[str] = []
        failed: List[Dict[str, str]] = []

        # 1-2. sample and quarantine
        for agent in self.agents.values():
            if agent.status == DEAD:
                continue
            if agent.health <= self.threshold:
                agent.status = QUARANTINED
                agent.reason = "health below threshold"
                quarantined.append(agent.name)

        # 3. cascade along dependency edges, to a fixed point
        changed = True
        while changed:
            changed = False
            for agent in self.agents.values():
                if agent.status == DEAD or agent.name in quarantined:
                    continue
                if any(
                    self.agents[dep].status in (QUARANTINED, DEAD)
                    for dep in agent.depends_on
                ):
                    agent.status = QUARANTINED
                    agent.reason = "dependency quarantined"
                    quarantined.append(agent.name)
                    cascaded.append(agent.name)
                    changed = True

        # 4-5. bounded repair of everything now quarantined
        for name in quarantined:
            agent = self.agents[name]
            if agent.repairs >= self.max_repairs:
                exhausted.append(name)
                continue
            agent.repairs += 1
            try:
                if repair_fn is not None:
                    agent.health = _clamp(agent.health + _clamp(repair_fn(name)))
                else:
                    agent.health = _clamp(agent.health + self.repair_amount)
            except Exception as exc:  # a failing repair must not abort the cycle
                failed.append({"agent": name, "error": f"{type(exc).__name__}: {exc}"})
                continue
            if agent.health > self.threshold:
                agent.status = ALIVE
                agent.reason = ""
                repaired.append(name)

        # 6. recovery is all-or-nothing within the cycle
        still_bad = sorted(
            a.name for a in self.agents.values() if a.status in (QUARANTINED, DEAD)
        )
        recovered = not still_bad

        record: Dict[str, object] = {
            "ts": round(ts, 6),
            "status": HEALTHY if recovered else self.status(),
            "quarantined": sorted(quarantined),
            "cascaded": sorted(cascaded),
            "repaired": sorted(repaired),
            "exhausted": sorted(exhausted),
            "failed": failed,
            "recovered": recovered,
            "remaining": still_bad,
            "health": self.health(),
        }
        self.last_cycle = record
        self.history.append(record)
        if len(self.history) > self.history_limit:
            del self.history[: len(self.history) - self.history_limit]
        return record

    def auto_heal(
        self,
        repair_fn: Optional[RepairFn] = None,
        now: Optional[float] = None,
    ) -> Dict[str, object]:
        """Pre-4.0 name for one bounded healing cycle (kept for compatibility)."""
        return self.run_cycle(repair_fn=repair_fn, now=now)

    # -- reporting -----------------------------------------------------------
    def report(self) -> Dict[str, object]:
        """Full fleet report: status, per-agent state, last cycle, repair budget."""
        return {
            "status": self.status(),
            "health": self.health(),
            "agents": {n: a.as_dict() for n, a in sorted(self.agents.items())},
            "last_cycle": self.last_cycle,
            "repair_budget": {
                n: {"used": a.repairs, "limit": self.max_repairs}
                for n, a in sorted(self.agents.items())
            },
            "threshold": self.threshold,
        }


# --- module-level helpers (compatible with the 3.x dict-based API) ----------

def create_civilization(agents: object, **kwargs: object) -> Civilization:
    """Create a civilization from a list of names or a full spec mapping."""
    if isinstance(agents, Mapping):
        return Civilization.from_spec(agents, **kwargs)
    civ = Civilization(**kwargs)  # type: ignore[arg-type]
    for name in agents:  # type: ignore[union-attr]
        civ.add_agent(str(name))
    return civ


def damage(civ: Civilization, agent: str, amount: float) -> Civilization:
    civ.damage(agent, amount)
    return civ


def heal(civ: Civilization, agent: str, amount: float) -> Civilization:
    civ.heal(agent, amount)
    return civ


def auto_heal(civ: Civilization, **kwargs: object) -> Civilization:
    civ.auto_heal(**kwargs)  # type: ignore[arg-type]
    return civ


def civ_health(civ: Civilization) -> Dict[str, object]:
    return {**civ.health(), "status": civ.status()}


# --- CLI --------------------------------------------------------------------

def _demo() -> Dict[str, object]:
    """Deterministic demo used by ``demo`` and by the README example."""
    civ = create_civilization(
        {
            "agents": {
                "gateway": {"health": 1.0},
                "memory_engine": {"health": 0.9, "depends_on": ["gateway"]},
                "mcp": {"health": 0.85, "depends_on": ["memory_engine"]},
                "sdk": {"health": 1.0, "depends_on": ["mcp"]},
            }
        },
        threshold=0.30,
        repair_amount=0.5,
    )
    civ.damage("gateway", 0.80)      # gateway falls to 0.20 -> below threshold
    cycle = civ.run_cycle(now=0.0)   # detect, cascade to all dependents, repair
    return {"cycle": cycle, "report": civ.report()}


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: ``demo`` | ``run`` | ``report``; JSON on stdout."""
    import argparse
    import json
    import sys
    from pathlib import Path

    ap = argparse.ArgumentParser(
        prog="mem20selfhealingruntimecivilizationz",
        description="Self-healing runtime civilization controller",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="run the deterministic demo cycle")
    p_run = sub.add_parser("run", help="run one healing cycle against a JSON spec")
    p_run.add_argument("--spec", help="path to a JSON civilization spec (default: stdin)")
    p_run.add_argument("--damage", action="append", default=[], metavar="AGENT=AMOUNT",
                       help="damage an agent before the cycle (repeatable)")
    p_report = sub.add_parser("report", help="report a JSON spec without running a cycle")
    p_report.add_argument("--spec", help="path to a JSON civilization spec (default: stdin)")

    args = ap.parse_args(argv)
    if args.cmd == "demo":
        print(json.dumps(_demo(), indent=2, sort_keys=True, default=str))
        return 0

    raw = Path(args.spec).read_text(encoding="utf-8") if args.spec else sys.stdin.read()
    civ = Civilization.from_spec(json.loads(raw or "{}"))
    if args.cmd == "report":
        print(json.dumps(civ.report(), indent=2, sort_keys=True, default=str))
        return 0
    for pair in args.damage:
        name, _, amount = pair.partition("=")
        civ.damage(name.strip(), float(amount))
    print(json.dumps(civ.run_cycle(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
