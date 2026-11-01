"""Tests for the cross-subsystem wiring.

These are not import smoke tests. Each one asserts a specific value, bound or
refusal produced by a neighbouring mem20 subsystem, because "the function ran"
proves nothing about whether the wiring is real.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from mem20shopz import wiring  # noqa: E402


# --- mem20famz -------------------------------------------------------------


def test_every_catalog_group_maps_to_a_real_family():
    """All five commercial groups resolve to a family the registry defines."""
    from mem20shopz import catalog

    for group in catalog.GROUPS:
        result = wiring.family_for_group(group["id"])
        assert result["known"] is True, f"{group['id']} has no family"
        assert result["family"], f"{group['id']} mapped to an empty family"
        assert result["purpose"], f"family {result['family']} has no stated purpose"


def test_family_purpose_comes_from_the_registry_not_this_module():
    """The purpose string is mem20famz's, not a copy pasted here."""
    from mem20famz import purpose

    result = wiring.family_for_group("intelligence")
    assert result["family"] == "memory-cognition"
    assert result["purpose"] == purpose("memory-cognition")
    assert result["registry_live"] is True


def test_unknown_group_is_reported_unknown_not_guessed():
    result = wiring.family_for_group("no-such-group")
    assert result["known"] is False
    assert result["family"] is None
    assert result["purpose"] == ""


# --- memory_engine ---------------------------------------------------------


def test_github_pat_in_a_webhook_body_is_detected():
    """A credential-shaped string in attacker-controlled input is caught."""
    body = '{"note": "token ghp_' + "a" * 36 + '"}'
    result = wiring.scan_for_secrets(body)
    assert result["clean"] is False
    assert result["count"] >= 1
    assert "GitHub Personal Access Token" in result["labels"]


def test_openai_style_key_is_detected():
    body = "sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
    result = wiring.scan_for_secrets(body)
    assert result["clean"] is False
    assert "OpenAI-style API key" in result["labels"]


def test_clean_body_reports_clean_and_returns_it_unchanged():
    body = '{"id": "evt_1", "type": "checkout.session.completed"}'
    result = wiring.scan_for_secrets(body)
    assert result["clean"] is True
    assert result["count"] == 0
    assert result["redacted"] == body


def test_redacted_copy_does_not_contain_the_secret():
    secret = "ghp_" + "b" * 36
    result = wiring.scan_for_secrets(f"token {secret}")
    assert secret not in result["redacted"]


# --- mem20sitemapz ---------------------------------------------------------


def test_catalog_json_is_a_shippable_source_asset():
    result = wiring.validate_catalog_asset("catalog.json")
    assert result["source_file"] is True
    assert result["skipped"] is False
    assert result["shippable"] is True


def test_node_modules_asset_is_refused():
    """The sitemap's skip rule applies to shop assets too."""
    result = wiring.validate_catalog_asset("node_modules/thing.js")
    assert result["skipped"] is True
    assert result["shippable"] is False


def test_binary_asset_is_not_shippable():
    result = wiring.validate_catalog_asset("hero.png")
    assert result["source_file"] is False
    assert result["shippable"] is False


# --- mem20kanbanz ----------------------------------------------------------


def test_missing_kanban_door_is_reported_unavailable_never_success():
    """An unreachable door must not look like a created card."""
    outcome = wiring.open_fulfilment_card(
        "ord-1", "Fulfil x", door_url="http://127.0.0.1:1", timeout=0.5
    )
    assert outcome.status in {"door-unavailable", "refused"}
    assert outcome.status != "created"
    assert outcome.card_id == ""


# --- mem20teamz ------------------------------------------------------------


def test_room_announcement_is_routed_and_recorded(tmp_path):
    result = wiring.announce_in_room(
        "fulfilment",
        "mem20shopz",
        "Paid order ord-9 for foundation-single.",
        home=str(tmp_path),
    )
    assert result["ok"] is True
    assert result["room"] == "fulfilment"
    assert result["kind"] in {"direct", "broadcast"}


def test_room_announcement_with_a_mention_wakes_that_profile(tmp_path):
    from mem20teamz.store import Store

    home = tmp_path
    store = Store(home / "teamz.sqlite")
    store.create_room("fulfilment", "paid orders")
    store.join("fulfilment", "ops-bot", "agent")

    result = wiring.announce_in_room(
        "fulfilment", "mem20shopz", "@ops-bot please fulfil ord-10.", home=str(home)
    )
    assert result["ok"] is True
    assert result["kind"] == "direct"
    assert "ops-bot" in result["woken"]


# --- the whole hand-off ----------------------------------------------------


def test_hand_off_records_every_step_even_when_a_neighbour_is_down(tmp_path):
    report = wiring.hand_off_order(
        order_ref="ord-42",
        sku_id="foundation-single",
        group="foundations",
        customer="buyer@example.com",
        raw_payload='{"id": "evt_42"}',
        door_url="http://127.0.0.1:1",
        home=str(tmp_path),
    )
    data = report.as_dict()
    assert data["order_ref"] == "ord-42"
    assert data["family"]["family"] == "platform"
    assert data["secret_scan"]["clean"] is True
    assert data["kanban"]["status"] != "created"
    assert data["room"]["ok"] is True
    # One line per subsystem, so the audit record names what was reached.
    assert len(data["steps"]) == 4
    assert any(s.startswith("famz:") for s in data["steps"])
    assert any(s.startswith("kanbanz:") for s in data["steps"])
    assert any(s.startswith("teamz:") for s in data["steps"])


def test_hand_off_flags_a_secret_in_the_payload(tmp_path):
    report = wiring.hand_off_order(
        order_ref="ord-43",
        sku_id="foundation-single",
        group="foundations",
        raw_payload="ghp_" + "c" * 36,
        door_url="http://127.0.0.1:1",
        home=str(tmp_path),
    )
    assert report.secret_scan["clean"] is False
    assert report.secret_scan["count"] >= 1
