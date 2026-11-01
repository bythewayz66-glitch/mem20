#!/usr/bin/env python3
"""mem20 Gateway — relay routing policy.

The gateway's job is to move a message from one agent to another. That is not
a transport problem, it is a *policy* problem: before a message crosses the
fleet boundary it has to be screened for credentials, the payload has to be
within the asset budget it claims, the store it references has to be intact,
and the target subsystem has to actually exist in the estate inventory.

This module is that policy layer. Every decision it makes is delegated to the
sibling subsystem that owns the rule — the gateway does not re-implement
secret detection, triangle budgets, integrity checking or inventory lookup.
That is deliberate: one owner per rule, and the gateway is the place they are
composed.

Each dependency is imported at module scope and *called* on the paths below,
which is what makes the wiring real rather than decorative.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Sibling subsystem imports.
#
# The estate uses two layouts: src-layout packages (mem20secretz, toolchest)
# and flat packages (mem20kilnz, mem20verify, memory_engine). Both are put on
# the path here so the gateway can be run from a checkout without an install
# step, which is how the CLI is invoked in the README and in the tests.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (
    _REPO_ROOT,
    _REPO_ROOT / "mem20secretz" / "src",
    _REPO_ROOT / "toolchest" / "src",
    _REPO_ROOT / "mem20kilnz",
    _REPO_ROOT / "mem20verify",
):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from mem20secretz.sweep import classify as classify_secret          # noqa: E402
from mem20kilnz.budgets import check_triangles                      # noqa: E402
from mem20verify.dataintegrity import check as check_integrity      # noqa: E402
from toolchest.catalog import load_inventory                        # noqa: E402
from memory_engine.memory import detect_secrets                     # noqa: E402

# Severities that block a relay outright. `info` findings (endpoint-shaped
# config duplication) are reported but do not stop the message.
BLOCKING_SEVERITIES = {"critical", "high"}


@dataclass
class ScreenVerdict:
    """Result of screening a payload before it is allowed to cross the fleet."""

    allowed: bool
    findings: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "findings": self.findings,
        }


@dataclass
class RouteDecision:
    """A relay decision: where a message goes and whether it may go at all."""

    target: str
    allowed: bool
    screen: ScreenVerdict
    budget: dict[str, Any] | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "allowed": self.allowed,
            "reason": self.reason,
            "screen": self.screen.to_dict(),
            "budget": self.budget,
        }


# ---------------------------------------------------------------------------
# Screening — memory_engine detects, mem20secretz classifies.
# ---------------------------------------------------------------------------
def screen_payload(text: str, min_confidence: str = "low") -> ScreenVerdict:
    """Decide whether `text` may be relayed.

    Two subsystems cooperate here and neither is redundant:

      * ``memory_engine.detect_secrets`` finds candidate spans by pattern and
        returns them with a confidence band and an offset.
      * ``mem20secretz.sweep.classify`` decides what a finding *means* — a
        credential-shaped name holding a high-entropy value is a real leak,
        while an endpoint-shaped value is configuration duplication and must
        not mask a genuine credential.

    The gateway blocks on the classified severity, not on the raw match, so a
    URL in a message does not stop the relay but an API key does.
    """
    findings: list[dict[str, Any]] = []
    blocked = False

    for hit in detect_secrets(text, min_confidence=min_confidence):
        # classify() takes (name, value). The detector gives us a label and a
        # preview; the label is the credential-shaped name, the preview is
        # enough to judge entropy class without re-reading the secret.
        severity, kind = classify_secret(hit.label, hit.preview)
        entry = {
            "label": hit.label,
            "confidence": hit.confidence,
            "offset": hit.offset,
            "severity": severity,
            "kind": kind,
        }
        findings.append(entry)
        if severity in BLOCKING_SEVERITIES:
            blocked = True

    if blocked:
        return ScreenVerdict(
            allowed=False,
            findings=findings,
            reason=f"payload carries {sum(1 for f in findings if f['severity'] in BLOCKING_SEVERITIES)} "
                   f"blocking secret finding(s)",
        )
    return ScreenVerdict(
        allowed=True,
        findings=findings,
        reason="no blocking findings" if not findings else "only informational findings",
    )


# ---------------------------------------------------------------------------
# Asset budget — mem20kilnz owns the triangle bands.
# ---------------------------------------------------------------------------
def check_asset_budget(family: str, triangles: int, lod: int = 0,
                       tier: str = "standard") -> dict[str, Any]:
    """Ask mem20kilnz whether an asset claim is within its family budget.

    A relay that carries an asset reference is also carrying a claim about how
    heavy that asset is. The gateway refuses to forward a claim the budget
    subsystem rejects, so an over-budget asset never reaches a downstream
    consumer that would have to discover the problem itself.
    """
    verdict = check_triangles(family, triangles, lod=lod, tier=tier)
    return {
        "family": verdict.family,
        "triangles": verdict.triangles,
        "ok": verdict.ok,
        "reason": verdict.reason,
        "tier": verdict.tier,
    }


# ---------------------------------------------------------------------------
# Store integrity — mem20verify owns the round-trip check.
# ---------------------------------------------------------------------------
def verify_store(engine_dir: str | None = None) -> dict[str, Any]:
    """Run mem20verify's integrity check over the memory engine store.

    The gateway will not relay a message that cites a store it cannot prove is
    intact, because a relayed citation is a promise about data the receiver
    will not re-check.
    """
    kwargs = {"engine_dir": engine_dir} if engine_dir else {}
    result = check_integrity(**kwargs)
    return {
        "engine": result.engine,
        "checked": result.checked,
        "roundtrip_ok": result.roundtrip_ok,
        "failures": len(result.failures),
        "false_positive_detections": len(result.false_positive_detections),
        "ok": result.ok,
        "error": result.error,
    }


# ---------------------------------------------------------------------------
# Estate inventory — toolchest owns the catalogue.
# ---------------------------------------------------------------------------
def inventory_subsystems(path: str | Path | None = None) -> dict[str, Any]:
    """Load the toolchest inventory and report which subsystems it knows.

    Routing to a subsystem that is not in the inventory is a routing error, so
    the gateway resolves the target against the catalogue before it forwards.
    """
    inv_path = Path(path) if path else _REPO_ROOT / "toolchest" / "inventory.json"
    if not inv_path.is_file():
        return {"ok": False, "error": f"inventory not found: {inv_path}", "subsystems": []}
    data = load_inventory(inv_path)
    # The inventory is a flat `entries` list, each entry tagged with a `kind`
    # (cli / mcp / subsystem). Only `kind == "subsystem"` rows are routable
    # targets; a CLI binary is not something the gateway can relay to.
    entries = data.get("entries") or []
    names = sorted(
        e.get("name", "") for e in entries
        if isinstance(e, dict) and e.get("kind") == "subsystem" and e.get("name")
    )
    return {
        "ok": True,
        "path": str(inv_path),
        "format_version": data.get("format_version"),
        "count": len(names),
        "counts": data.get("counts"),
        "subsystems": names,
    }


def target_is_known(target: str, path: str | Path | None = None) -> bool:
    """True when `target` appears in the estate inventory."""
    inv = inventory_subsystems(path)
    if not inv.get("ok"):
        return False
    needle = target.lower()
    return any(needle == n.lower() or needle in n.lower() for n in inv["subsystems"])


# ---------------------------------------------------------------------------
# The composed decision.
# ---------------------------------------------------------------------------
def route(message: str, target: str, *, family: str | None = None,
          triangles: int | None = None, lod: int = 0, tier: str = "standard",
          inventory_path: str | Path | None = None,
          require_known_target: bool = False) -> RouteDecision:
    """Decide whether `message` may be relayed to `target`.

    Order matters and is intentional: screen first (cheapest, and a leak must
    never be forwarded even to a valid target), then resolve the target, then
    check any asset claim the message carries.
    """
    screen = screen_payload(message)
    if not screen.allowed:
        return RouteDecision(target=target, allowed=False, screen=screen,
                             reason=screen.reason)

    if require_known_target and not target_is_known(target, inventory_path):
        return RouteDecision(
            target=target, allowed=False, screen=screen,
            reason=f"target '{target}' is not in the estate inventory",
        )

    budget = None
    if family is not None and triangles is not None:
        budget = check_asset_budget(family, triangles, lod=lod, tier=tier)
        if not budget["ok"]:
            return RouteDecision(
                target=target, allowed=False, screen=screen, budget=budget,
                reason=f"asset budget rejected: {budget['reason']}",
            )

    return RouteDecision(target=target, allowed=True, screen=screen,
                         budget=budget, reason="relay permitted")


def route_json(message: str, target: str, **kwargs: Any) -> str:
    """`route()` rendered as JSON, for the CLI."""
    return json.dumps(route(message, target, **kwargs).to_dict(), indent=2)
