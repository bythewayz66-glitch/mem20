"""Webhook delivery that is signed, retried, and replay-resistant."""
import importlib
import pytest
MOD = "mem20webhooksupernetworkz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_empty_secret_refused():
    import pytest
    with pytest.raises(ValueError):
        _m().WebhookSuperNetwork("")


def test_non_positive_tolerance_refused():
    import pytest
    with pytest.raises(ValueError):
        _m().WebhookSuperNetwork("s", tolerance_seconds=0)


def test_valid_signature_verifies():
    w = _m().WebhookSuperNetwork("s3cret")
    sig = w.sign("hello", 1000)
    assert w.verify("hello", 1000, sig, now=1000) is True


def test_tampered_body_fails():
    w = _m().WebhookSuperNetwork("s3cret")
    sig = w.sign("hello", 1000)
    import pytest
    with pytest.raises(Exception) as e:
        w.verify("HELLO", 1000, sig, now=1000)
    assert "mismatch" in str(e.value)


def test_wrong_secret_fails():
    a = _m().WebhookSuperNetwork("secret-a"); b = _m().WebhookSuperNetwork("secret-b")
    import pytest
    with pytest.raises(Exception):
        b.verify("hello", 1000, a.sign("hello", 1000), now=1000)


def test_replay_outside_tolerance_is_refused():
    w = _m().WebhookSuperNetwork("s3cret", tolerance_seconds=60)
    sig = w.sign("hello", 1000)
    import pytest
    with pytest.raises(Exception) as e:
        w.verify("hello", 1000, sig, now=2000)
    assert "stale" in str(e.value)


def test_missing_signature_fails_closed():
    w = _m().WebhookSuperNetwork("s3cret")
    import pytest
    with pytest.raises(Exception):
        w.verify("hello", 1000, None, now=1000)


def test_duplicate_delivery_is_skipped():
    w = _m().WebhookSuperNetwork("s")
    sig = w.sign("hello", 1000)
    first = w.deliver("hello", 1000, sig, now=1000, idempotency_key="k1")
    second = w.deliver("hello", 1000, sig, now=1000, idempotency_key="k1")
    assert first["delivered"] is True
    assert second["delivered"] is False
    assert w.duplicates_skipped == 1


def test_distinct_keys_both_deliver():
    w = _m().WebhookSuperNetwork("s")
    sig = w.sign("hello", 1000)
    assert w.deliver("hello", 1000, sig, now=1000, idempotency_key="a")["delivered"]
    assert w.deliver("hello", 1000, sig, now=1000, idempotency_key="b")["delivered"]
