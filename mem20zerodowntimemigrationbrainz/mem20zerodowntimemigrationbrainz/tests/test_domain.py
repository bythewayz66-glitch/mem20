"""Dual-read / dual-write cutover that can be abandoned safely."""
import importlib
import pytest
MOD = "mem20zerodowntimemigrationbrainz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_writes_before_migration_go_to_old_only():
    m = _m().ZeroDowntimeMigrationBrain()
    m.write({"id": 1})
    assert m.writes == {"old": 1, "new": 0}


def test_migrating_writes_to_both_stores():
    m = _m().ZeroDowntimeMigrationBrain(); m.begin()
    m.write({"id": 1})
    assert m.writes["old"] == 1 and m.writes["new"] == 1


def test_unverified_cutover_is_refused():
    import pytest
    m = _m().ZeroDowntimeMigrationBrain()      # no verifier
    m.begin()
    with pytest.raises(Exception) as e:
        m.verify_and_cutover()
    assert "refusing unverified" in str(e.value)


def test_disagreeing_stores_block_cutover():
    import pytest
    m = _m().ZeroDowntimeMigrationBrain(
        verify=lambda: {"match": False, "old_only": 2, "new_only": 1})
    m.begin()
    with pytest.raises(Exception) as e:
        m.verify_and_cutover()
    assert "disagree" in str(e.value)


def test_agreeing_stores_cut_over_and_stop_writing_old():
    m = _m().ZeroDowntimeMigrationBrain(verify=lambda: {"match": True})
    m.begin()
    m.write({"id": 1})
    r = m.verify_and_cutover()
    assert r["verified"] is True
    old_before = m.writes["old"]
    m.write({"id": 2})
    assert m.writes["old"] == old_before, "old store written after cutover"
    assert m.writes["new"] == 2


def test_cannot_cut_over_from_idle():
    import pytest
    m = _m().ZeroDowntimeMigrationBrain(verify=lambda: {"match": True})
    with pytest.raises(Exception):
        m.verify_and_cutover()


def test_rollback_returns_to_dual_write():
    m = _m().ZeroDowntimeMigrationBrain(verify=lambda: {"match": True})
    m.begin(); m.rollback()
    m.write({"id": 1})
    assert m.writes["old"] >= 1 and m.writes["new"] >= 1
