"""Cross-subsystem wiring for the mem20 storefront.

The storefront is not an island. A completed purchase has to reach the rest of
the estate, and the estate's shared contracts have to be honoured on the way
out. This module is the single place where mem20shopz touches its neighbours,
so the dependency surface is one file instead of being scattered through the
request path.

Six mem20 subsystems are used here, each for a job it already owns:

``mem20famz``
    The family registry. Every SKU is attributed to the subsystem family that
    actually delivers it, so a receipt can say *which* part of mem20 the
    customer bought rather than only a price.

``mem20kanbanz``
    The one true kanban door. A paid order becomes a fulfilment card on the
    ``fulfilment`` board. The door is the only writer; this module never opens
    a database.

``mem20teamz``
    The room router. The provisioning notice is parsed into a plan and posted
    into the ``fulfilment`` room, so humans and agents see the same record.

``memory_engine``
    Secret detection. A webhook body is attacker-controlled input; before any
    of it is logged or persisted it is scanned for credential-shaped strings.

``mem20sitemapz``
    The scan policy. Catalog assets are validated with the same "is this a
    source file" rule the sitemap uses, so the shop cannot ship a binary or a
    secret path as a product asset.

``mem20cliz``
    The shared machine contract. ``--json`` on the shop CLI produces the same
    envelope as every other fleet CLI.

Every integration is *optional at runtime and loud when it fails*: a missing
kanban door must not lose a paid order, but it must also never look like it
succeeded. Each helper returns an explicit status string, and the caller
records it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("mem20shopz.wiring")

# ---------------------------------------------------------------------------
# mem20famz — which family of mem20 does this SKU actually buy?
# ---------------------------------------------------------------------------

#: SKU group -> the mem20famz family that delivers it. The shop's five catalog
#: groups are commercial packaging; the family is the engineering truth.
GROUP_FAMILY = {
    "foundations": "platform",
    "operations": "resilience",
    "intelligence": "memory-cognition",
    "creative": "production",
    "support": "human-team",
}


def family_for_group(group: str) -> dict[str, Any]:
    """Attribute a catalog group to a mem20 family, with its stated purpose.

    Uses ``mem20famz.family_of`` for a package-level answer when one is asked
    for, and ``mem20famz.purpose`` for the family's own definition. Returns an
    explicit ``known: False`` rather than inventing a family for a group the
    registry does not cover.
    """
    from mem20famz import family_of, purpose

    family = GROUP_FAMILY.get(group)
    if family is None:
        return {"group": group, "family": None, "purpose": "", "known": False}
    return {
        "group": group,
        "family": family,
        "purpose": purpose(family),
        "known": True,
        # A package-level lookup proves the registry is live, not just a dict
        # in this file: if mem20famz is missing or broken this raises. The
        # probe package is one the registry actually carries, so a False here
        # means the registry is broken rather than merely incomplete.
        "registry_live": family_of("mem20revenueleakhunterz") is not None,
    }


# ---------------------------------------------------------------------------
# memory_engine — scan attacker-controlled input before it is persisted
# ---------------------------------------------------------------------------


def scan_for_secrets(payload: str) -> dict[str, Any]:
    """Scan a webhook body for credential-shaped strings.

    The body of a Stripe webhook is attacker-controlled until the signature is
    verified, and even then it can carry a customer-supplied field. Nothing is
    logged or stored before this runs.

    Returns the finding labels and a redacted copy. The redacted copy is what
    the caller should persist; the original is never returned.
    """
    from memory_engine.memory import detect_secrets, redact_secrets

    findings = detect_secrets(payload)
    redacted, _ = redact_secrets(payload)
    return {
        "clean": not findings,
        "count": len(findings),
        "labels": sorted({f.label for f in findings}),
        "redacted": redacted,
    }


# ---------------------------------------------------------------------------
# mem20sitemapz — the estate's own rule for "is this a shippable source file"
# ---------------------------------------------------------------------------


def validate_catalog_asset(path: str) -> dict[str, Any]:
    """Check a catalog asset against the sitemap's source-file policy.

    The shop must not serve a binary, a database or a secret path as a product
    asset. Rather than inventing a second rule, this defers to the policy the
    sitemap already enforces across the estate.
    """
    from pathlib import Path

    from mem20sitemapz.policy import is_skipped_dir, is_skipped_file, is_source_file

    p = Path(path)
    skipped = is_skipped_dir(p.parent.name) or is_skipped_file(p)
    return {
        "path": str(p),
        "shippable": is_source_file(p) and not skipped,
        "source_file": is_source_file(p),
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# mem20kanbanz — a paid order becomes a fulfilment card
# ---------------------------------------------------------------------------


@dataclass
class FulfilmentOutcome:
    """What happened when the order was handed to the kanban door."""

    status: str  # "created" | "door-unavailable" | "refused"
    detail: str = ""
    card_id: str = ""
    board: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "detail": self.detail,
            "card_id": self.card_id,
            "board": self.board,
        }


def open_fulfilment_card(
    order_ref: str,
    title: str,
    detail: str = "",
    board: str = "fulfilment",
    door_url: str | None = None,
    timeout: float = 5.0,
) -> FulfilmentOutcome:
    """Create a fulfilment card for a paid order.

    A missing door is reported as ``door-unavailable`` and never as success: an
    order that silently produced no card is exactly the drift this wiring
    exists to prevent. The caller decides whether to retry or to page a human.
    """
    from mem20kanbanz.door import DEFAULT_DOOR, Door, DoorError

    door = Door(door_url or DEFAULT_DOOR, timeout=timeout)
    try:
        if not door.healthy():
            return FulfilmentOutcome(
                status="door-unavailable",
                detail=f"kanban door at {door.base} did not answer",
                board=board,
            )
        card = door.add_card(board, title, content=detail, metadata={"order_ref": order_ref})
        return FulfilmentOutcome(
            status="created",
            detail=f"card {card.id} on {board}",
            card_id=str(card.id),
            board=board,
        )
    except DoorError as exc:
        return FulfilmentOutcome(status="refused", detail=str(exc), board=board)


# ---------------------------------------------------------------------------
# mem20teamz — post the provisioning notice into the fulfilment room
# ---------------------------------------------------------------------------


def announce_in_room(
    room: str,
    sender: str,
    text: str,
    home: str | None = None,
) -> dict[str, Any]:
    """Post a provisioning notice and let mem20teamz route it.

    ``mem20teamz.router.route`` decides whether the message wakes a named
    profile or becomes a broadcast plan. The shop does not re-implement that
    decision; it hands the text over and records what the router did.
    """
    from pathlib import Path

    from mem20teamz.router import route
    from mem20teamz.store import Store, StoreError

    root = Path(home) if home else Path.home() / ".mem20teamz"
    root.mkdir(parents=True, exist_ok=True)
    store = Store(root / "teamz.sqlite")
    try:
        if room not in {r["name"] for r in store.rooms()}:
            store.create_room(room, "paid orders awaiting fulfilment")
        record = route(store, room, sender, text)
    except StoreError as exc:
        return {"ok": False, "error": str(exc), "room": room}
    return {
        "ok": True,
        "room": room,
        "kind": record["kind"],
        "woken": [w["profile"] for w in record["woken"]],
        "plan": record["plan"],
    }


# ---------------------------------------------------------------------------
# The whole hand-off, in one call
# ---------------------------------------------------------------------------


@dataclass
class HandoffReport:
    """Everything the storefront did with a paid order, in one record."""

    order_ref: str
    family: dict[str, Any] = field(default_factory=dict)
    secret_scan: dict[str, Any] = field(default_factory=dict)
    kanban: dict[str, Any] = field(default_factory=dict)
    room: dict[str, Any] = field(default_factory=dict)
    steps: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "order_ref": self.order_ref,
            "family": self.family,
            "secret_scan": self.secret_scan,
            "kanban": self.kanban,
            "room": self.room,
            "steps": self.steps,
        }


def hand_off_order(
    order_ref: str,
    sku_id: str,
    group: str,
    customer: str = "",
    raw_payload: str = "",
    door_url: str | None = None,
    room: str = "fulfilment",
    home: str | None = None,
) -> HandoffReport:
    """Run the full post-payment hand-off across the estate.

    Each step is attempted independently and its outcome recorded, so one
    unavailable neighbour cannot hide the others. The report is the audit
    record: it says exactly which subsystems were reached and what each said.
    """
    report = HandoffReport(order_ref=order_ref)

    report.family = family_for_group(group)
    report.steps.append(
        f"famz: {report.family.get('family') or 'unmapped'} "
        f"({report.family.get('purpose') or 'no purpose recorded'})"
    )

    if raw_payload:
        report.secret_scan = scan_for_secrets(raw_payload)
        report.steps.append(
            f"memory_engine: {'clean' if report.secret_scan['clean'] else str(report.secret_scan['count']) + ' finding(s)'}"
        )

    outcome = open_fulfilment_card(
        order_ref=order_ref,
        title=f"Fulfil {sku_id} for {customer or 'unknown customer'}",
        detail=f"order {order_ref} · sku {sku_id} · group {group}",
        door_url=door_url,
    )
    report.kanban = outcome.as_dict()
    report.steps.append(f"kanbanz: {outcome.status} — {outcome.detail}")

    notice = (
        f"Paid order {order_ref} for {sku_id} ({group}). "
        f"Fulfilment card: {outcome.card_id or 'not created'}."
    )
    report.room = announce_in_room(room, "mem20shopz", notice, home=home)
    report.steps.append(
        f"teamz: {'posted as ' + str(report.room.get('kind')) if report.room.get('ok') else 'failed — ' + str(report.room.get('error'))}"
    )

    return report
