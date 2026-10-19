"""Every stored fact must be labeled as such: fact, fiction, or honestly unknown.

The grounded/simulated firewall (test_grounded_firewall.py) protects the PARTITION
boundary: imagined content cannot reach the grounded ledger. These tests protect the
LABEL boundary inside the grounded partition, which the partition firewall says
nothing about.

The gap this file exists to close, measured on the live store before the change:
393 of 447 grounded facts carried epistemic_status=None (87.9%), and the recall
surfaces stripped the label from the few facts that had one. A fact with no label
was the easiest state to be in and the most trusted: epistemic_veto() only fired on
imagined/hypothesis/agent_generated, so an unlabeled fact passed the validation gate
silently.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VALID_STATUSES = ["observed", "inferred", "imagined", "user_stated", "hypothesis",
                  "agent_generated"]


@pytest.fixture()
def mem(tmp_path, monkeypatch):
    """A memory module bound to an isolated store, reloaded per test."""
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "store"))
    for mod in [m for m in list(sys.modules) if m == "memory"]:
        del sys.modules[mod]
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    module = importlib.import_module("memory")
    yield module
    for name in [m for m in list(sys.modules) if m == "memory"]:
        del sys.modules[name]


def _labeled(mem, topic, content, status="observed", **kw):
    return mem.remember(topic=topic, content=content, epistemic_status=status, **kw)


class TestGroundedWriteRequiresALabel:
    """The write path must not accept a fact whose epistemic kind is unstated."""

    def test_unlabeled_grounded_write_is_refused(self, mem):
        with pytest.raises(ValueError):
            mem.remember(topic="t", content="a claim with no declared basis")

    def test_refusal_names_the_valid_statuses(self, mem):
        with pytest.raises(ValueError) as exc:
            mem.remember(topic="t", content="a claim")
        for status in VALID_STATUSES:
            assert status in str(exc.value)

    def test_explicit_none_is_refused_too(self, mem):
        # A caller explicitly passing None is the same claim as omitting it.
        with pytest.raises(ValueError):
            mem.remember(topic="t", content="a claim", epistemic_status=None)

    def test_invalid_status_is_refused(self, mem):
        with pytest.raises(ValueError):
            mem.remember(topic="t", content="a claim", epistemic_status="probably")

    def test_refused_write_leaves_no_record(self, mem):
        with pytest.raises(ValueError):
            mem.remember(topic="t", content="a claim")
        assert [r for r in mem._load_ledger() if r.get("action") == "remember"] == []

    def test_each_valid_status_is_accepted_and_persisted(self, mem):
        for status in VALID_STATUSES:
            rec = _labeled(mem, "t", f"claim typed {status}", status=status)
            assert rec["epistemic_status"] == status
        stored = [r["epistemic_status"]
                  for r in mem._load_ledger() if r.get("action") == "remember"]
        assert stored == VALID_STATUSES

    def test_simulated_write_still_immutable_and_imagined(self, mem):
        # Tightening the grounded path must not loosen the simulated one.
        sim = mem.remember_simulated(topic="t", content="a dragon guards the vault")
        assert sim["epistemic_status"] == "imagined"
        assert sim["origin"] == "simulated"


class TestLabelSurvivesEveryRetrievalSurface:
    """A label that is dropped on read is a label the agent never sees."""

    def test_recall_returns_the_label(self, mem):
        _labeled(mem, "labelled-topic", "the sky is blue", status="observed")
        rows = mem.recall(topic="labelled-topic", k=5)
        assert any(r.get("epistemic_status") == "observed" for r in rows)

    def test_recall_semantic_returns_the_label(self, mem):
        _labeled(mem, "semantic-topic", "the sky is blue", status="observed")
        rows = mem.recall_semantic("the sky is blue", k=3)
        assert rows, "semantic recall returned nothing to check"
        assert all("epistemic_status" in r for r in rows)
        assert rows[0]["epistemic_status"] == "observed"

    def test_recall_hybrid_returns_the_label(self, mem):
        _labeled(mem, "hybrid-topic", "the sky is blue", status="observed")
        rows = mem.recall_hybrid("the sky is blue", k=3)
        assert rows, "hybrid recall returned nothing to check"
        assert all("epistemic_status" in r for r in rows)
        assert rows[0]["epistemic_status"] == "observed"

    def test_label_survives_a_status_change_on_read(self, mem):
        rec = _labeled(mem, "t", "a claim", status="inferred")
        mem.set_epistemic_status(rec["id"], "hypothesis")
        rows = mem.recall(topic="t", k=5)
        row = next(r for r in rows if r["id"] == rec["id"])
        assert row["epistemic_status"] == "hypothesis"


class TestVetoRefusesUnvalidatedBeliefs:
    """The gate that asks 'may I rely on this fact?' must not wave through silence."""

    def test_observed_fact_passes(self, mem):
        rec = _labeled(mem, "t", "a verified claim", status="observed")
        assert mem.epistemic_veto([rec["id"]])["veto"] is False

    def test_hypothesis_is_vetoed(self, mem):
        rec = _labeled(mem, "t", "a guess", status="hypothesis")
        assert mem.epistemic_veto([rec["id"]])["veto"] is True

    def test_agent_generated_is_vetoed(self, mem):
        rec = _labeled(mem, "t", "my own prior claim", status="agent_generated")
        assert mem.epistemic_veto([rec["id"]])["veto"] is True

    def test_user_stated_passes(self, mem):
        rec = _labeled(mem, "t", "you told me this", status="user_stated")
        assert mem.epistemic_veto([rec["id"]])["veto"] is False

    def test_unlabeled_legacy_fact_is_vetoed(self, mem):
        # Backfilled legacy facts are 'unlabeled': honest, but unbacked.
        rec = _labeled(mem, "t", "an old claim", status="unlabeled")
        assert mem.epistemic_veto([rec["id"]])["veto"] is True

    def test_unknown_fact_id_is_an_offender_not_a_pass(self, mem):
        # A hallucinated or typo'd id used to fall through the loop silently and
        # produce 'OK', which is the most dangerous possible answer to this gate.
        result = mem.epistemic_veto(["does-not-exist"])
        assert result["veto"] is True
        assert any("not found" in o["reason"] for o in result["offenders"])

    def test_veto_names_every_offending_fact(self, mem):
        good = _labeled(mem, "t", "verified", status="observed")
        bad = _labeled(mem, "t", "a guess", status="hypothesis")
        result = mem.epistemic_veto([good["id"], bad["id"], "missing-id"])
        assert result["veto"] is True
        assert {o["fact_id"] for o in result["offenders"]} == {bad["id"], "missing-id"}


class TestPromotionCannotLaunderFictionIntoFact:
    """Promotion is the one door from the simulated partition to the grounded one."""

    def _grounded_facts(self, mem, needle):
        return [r for r in mem.recall(topic=None, k=100)
                if needle in r.get("content", "") and r.get("origin") == "grounded"]

    def test_free_text_confirmation_does_not_stamp_observed(self, mem):
        sim = mem.remember_simulated(topic="t", content="the vault is under the north gate")
        mem.promote_simulated_to_grounded(sim["id"], confirmation="I think this is right")
        grounded = self._grounded_facts(mem, "vault is under")
        assert grounded, "promotion wrote no grounded record"
        assert grounded[0]["epistemic_status"] != "observed"

    def test_free_text_promotion_records_its_weak_evidence(self, mem):
        sim = mem.remember_simulated(topic="t", content="the vault is under the north gate")
        result = mem.promote_simulated_to_grounded(sim["id"], confirmation="probably true")
        assert result["epistemic_status"] in ("hypothesis", "inferred", "unlabeled")

    def test_promoted_record_keeps_the_promotion_provenance(self, mem):
        sim = mem.remember_simulated(topic="t", content="the vault is under the north gate")
        mem.promote_simulated_to_grounded(sim["id"], confirmation="probably true")
        grounded = self._grounded_facts(mem, "vault is under")
        assert grounded[0]["source"] == f"promoted:{sim['id']}"

    def test_free_text_promotion_is_still_refused_by_the_veto(self, mem):
        # The point of the weaker label: grounding a guess does not make it a fact.
        sim = mem.remember_simulated(topic="t", content="the vault is under the north gate")
        result = mem.promote_simulated_to_grounded(sim["id"], confirmation="probably true")
        assert mem.epistemic_veto([result["grounded_id"]])["veto"] is True


class TestLegacyBackfillIsHonest:
    """Old unlabeled facts cannot be vouched for after the fact."""

    def test_backfill_marks_them_unlabeled_not_observed(self, mem):
        # Simulate a pre-fix ledger row written before labels were mandatory.
        legacy = {
            "id": "legacy1", "ts": mem._now(), "actor": "agent",
            "action": "remember", "topic": "legacy", "tags": [],
            "priority": "normal", "content": "an old unlabeled claim",
            "valid_from": mem._now(), "epistemic_status": None,
            "origin": "grounded", "store": "grounded",
        }
        mem._append_ledger(legacy)
        report = mem.backfill_epistemic_labels()
        assert report["backfilled"] == 1
        row = next(r for r in mem._load_ledger() if r["id"] == "legacy1")
        assert row["epistemic_status"] == "unlabeled"

    def test_backfill_does_not_invent_observed(self, mem):
        legacy = {
            "id": "legacy2", "ts": mem._now(), "actor": "agent",
            "action": "remember", "topic": "legacy", "tags": [],
            "priority": "normal", "content": "an old unlabeled claim",
            "valid_from": mem._now(), "epistemic_status": None,
            "origin": "grounded", "store": "grounded",
        }
        mem._append_ledger(legacy)
        mem.backfill_epistemic_labels()
        statuses = {r["epistemic_status"] for r in mem._load_ledger()
                    if r.get("action") == "remember"}
        assert "observed" not in statuses

    def test_backfill_leaves_already_labeled_facts_alone(self, mem):
        rec = _labeled(mem, "t", "already labeled", status="inferred")
        report = mem.backfill_epistemic_labels()
        assert report["backfilled"] == 0
        row = next(r for r in mem._load_ledger() if r["id"] == rec["id"])
        assert row["epistemic_status"] == "inferred"

    def test_backfill_does_not_touch_simulated_content(self, mem):
        sim = mem.remember_simulated(topic="t", content="a dragon guards the vault")
        mem.backfill_epistemic_labels()
        rows = [r for r in mem._load_simulated_ledger() if r.get("action") == "simulate"]
        assert all(r["epistemic_status"] == "imagined" for r in rows)

    def test_backfill_does_not_rewrite_content(self, mem):
        original = "an old unlabeled claim"
        legacy = {
            "id": "legacy3", "ts": mem._now(), "actor": "agent",
            "action": "remember", "topic": "legacy", "tags": [],
            "priority": "normal", "content": original,
            "valid_from": mem._now(), "epistemic_status": None,
            "origin": "grounded", "store": "grounded",
        }
        mem._append_ledger(legacy)
        mem.backfill_epistemic_labels()
        row = next(r for r in mem._load_ledger() if r["id"] == "legacy3")
        assert row["content"] == original


class TestAuditReportsLabelCoverage:
    """Coverage has to be a number someone can check, not an assumption."""

    def test_coverage_counts_labeled_and_unlabeled(self, mem):
        _labeled(mem, "t", "a verified claim", status="observed")
        legacy = {
            "id": "legacy4", "ts": mem._now(), "actor": "agent",
            "action": "remember", "topic": "legacy", "tags": [],
            "priority": "normal", "content": "an old unlabeled claim",
            "valid_from": mem._now(), "epistemic_status": None,
            "origin": "grounded", "store": "grounded",
        }
        mem._append_ledger(legacy)
        cov = mem.label_coverage()
        assert cov["total"] == 2
        assert cov["labeled"] == 1
        assert cov["unlabeled"] == 1

    def test_explicit_unlabeled_counts_as_unlabeled(self, mem):
        # 'unlabeled' is an absence of a finding, not a finding. It must not be
        # counted as coverage, or backfilling would look like fixing the problem.
        _labeled(mem, "t", "a claim of unknown basis", status="unlabeled")
        cov = mem.label_coverage()
        assert cov["unlabeled"] == 1
        assert cov["coverage"] == 0.0

    def test_backfilled_rows_are_not_double_counted(self, mem):
        legacy = {
            "id": "legacy6", "ts": mem._now(), "actor": "agent",
            "action": "remember", "topic": "legacy", "tags": [],
            "priority": "normal", "content": "an old unlabeled claim",
            "valid_from": mem._now(), "epistemic_status": None,
            "origin": "grounded", "store": "grounded",
        }
        mem._append_ledger(legacy)
        mem.backfill_epistemic_labels()
        cov = mem.label_coverage()
        assert cov["unlabeled"] == 1, "backfilled fact counted twice"
        assert cov["by_status"]["unlabeled"] == 1

    def test_coverage_is_complete_when_everything_is_labeled(self, mem):
        _labeled(mem, "t", "claim a", status="observed")
        _labeled(mem, "t", "claim b", status="inferred")
        cov = mem.label_coverage()
        assert cov["unlabeled"] == 0
        assert cov["coverage"] == 1.0

    def test_audit_flags_an_unlabeled_store(self, mem):
        legacy = {
            "id": "legacy5", "ts": mem._now(), "actor": "agent",
            "action": "remember", "topic": "legacy", "tags": [],
            "priority": "normal", "content": "an old unlabeled claim",
            "valid_from": mem._now(), "epistemic_status": None,
            "origin": "grounded", "store": "grounded",
        }
        mem._append_ledger(legacy)
        audit = mem.audit_contamination()
        assert audit["label_coverage"]["unlabeled"] == 1
        assert audit["status"] != "CLEAN"

    def test_audit_is_clean_when_everything_is_labeled(self, mem):
        _labeled(mem, "t", "a verified claim", status="observed")
        audit = mem.audit_contamination()
        assert audit["label_coverage"]["unlabeled"] == 0
        assert audit["status"] == "CLEAN"


class TestEventSourcedWritesCarryLabels:
    """Not every ledger row goes through remember(). Those must carry a label too."""

    def test_supersede_row_is_labeled(self, mem):
        rec = _labeled(mem, "t", "first claim", status="inferred")
        mem.supersede(rec["id"], "a corrected claim", epistemic_status="observed")
        rows = [r for r in mem._load_ledger() if r.get("action") == "supersede"]
        assert rows, "supersede wrote no ledger row"
        assert all(r.get("epistemic_status") for r in rows)

    def test_supersede_marker_carries_the_old_facts_label(self, mem):
        # The marker is a statement about the OLD claim, so it inherits the old
        # claim's status rather than the correction's.
        rec = _labeled(mem, "t", "first claim", status="hypothesis")
        mem.supersede(rec["id"], "a corrected claim", epistemic_status="observed")
        marker = next(r for r in mem._load_ledger() if r.get("action") == "supersede")
        assert marker["epistemic_status"] == "hypothesis"

    def test_supersede_requires_a_label_for_the_correction(self, mem):
        rec = _labeled(mem, "t", "first claim", status="observed")
        with pytest.raises(ValueError):
            mem.supersede(rec["id"], "a corrected claim")

    def test_update_validity_row_is_labeled(self, mem):
        rec = _labeled(mem, "t", "a claim", status="observed")
        mem.update_validity(rec["id"], valid_to="2030-01-01T00:00:00+00:00")
        rows = [r for r in mem._load_ledger() if r.get("action") == "update_validity"]
        assert rows, "update_validity wrote no ledger row"
        assert all(r.get("epistemic_status") for r in rows)

    def test_assess_confidence_row_is_labeled(self, mem):
        rec = _labeled(mem, "t", "a claim", status="inferred")
        mem.assess_confidence(rec["id"], 0.8)
        rows = [r for r in mem._load_ledger() if r.get("action") == "assess_confidence"]
        assert rows, "assess_confidence wrote no ledger row"
        assert all(r.get("epistemic_status") for r in rows)


class TestNoSilentLabelLosingAnywhere:
    """A belt-and-braces sweep: no grounded row may ever carry a missing label."""

    def test_every_grounded_row_in_the_ledger_has_a_label(self, mem):
        _labeled(mem, "t", "claim a", status="observed")
        _labeled(mem, "t", "claim b", status="hypothesis")
        mem.supersede(mem._load_ledger()[0]["id"], "a corrected claim",
                      epistemic_status="observed")
        for row in mem._load_ledger():
            assert row.get("epistemic_status"), (
                f"ledger row {row.get('action')} / {row.get('id')} has no label")

    def test_saved_ledger_on_disk_has_no_null_labels(self, mem):
        _labeled(mem, "t", "claim a", status="observed")
        with open(mem.LEDGER, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    assert row.get("epistemic_status")


class TestSimulatedLabelIsImmutable:
    """The simulated partition's 'imagined' is the firewall's anchor."""

    def test_relabelling_a_simulated_record_is_refused(self, mem):
        sim = mem.remember_simulated(topic="t", content="a dragon guards the vault")
        with pytest.raises(PermissionError):
            mem.set_epistemic_status(sim["id"], "observed")

    def test_simulated_record_keeps_its_status_after_the_attempt(self, mem):
        sim = mem.remember_simulated(topic="t", content="a dragon guards the vault")
        with pytest.raises(PermissionError):
            mem.set_epistemic_status(sim["id"], "observed")
        row = next(r for r in mem._load_simulated_ledger() if r.get("id") == sim["id"])
        assert row["epistemic_status"] == "imagined"