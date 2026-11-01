"""Error-model tests: typed errors, retry policy, idempotency (M0).

These FAIL on d99ab5d (no error model existed) and PASS after.

Run: python3 -m pytest memory_engine/tests/test_error_model.py -q
"""

from __future__ import annotations

import os
import random
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

_STORE = tempfile.mkdtemp(prefix="mem20_errors_")
os.environ["MEM20_STORE_PATH"] = _STORE

from memory_engine import (  # noqa: E402
    ConfigurationError,
    EpistemicStatusError,
    MemoryEngine,
    MemoryEngineError,
    RetryPolicy,
    TransientError,
    ValidationError,
    call_with_retry,
    idempotency_key,
)


# ---------------------------------------------------------------------------
# Typed errors at the boundary
# ---------------------------------------------------------------------------


class TestTypedErrors:
    def test_missing_epistemic_status_is_typed(self):
        """The engine raises bare ValueError; the facade must type it."""
        eng = MemoryEngine()
        with pytest.raises(EpistemicStatusError) as ei:
            eng.remember("errors.epistemic", "no basis declared")
        assert ei.value.code == "epistemic_status_error"
        assert "epistemic_status" in ei.value.message

    def test_invalid_epistemic_status_is_typed(self):
        eng = MemoryEngine()
        with pytest.raises(EpistemicStatusError):
            eng.remember("errors.epistemic", "bad basis", epistemic_status="vibes")

    def test_typed_error_is_still_a_value_error(self):
        """Backward compatibility: old handlers must keep working."""
        eng = MemoryEngine()
        with pytest.raises(ValueError):
            eng.remember("errors.epistemic", "no basis")

    def test_empty_topic_is_validation_error(self):
        eng = MemoryEngine()
        with pytest.raises(ValidationError) as ei:
            eng.remember("", "content", epistemic_status="observed")
        assert ei.value.details["argument"] == "topic"

    def test_whitespace_topic_is_validation_error(self):
        eng = MemoryEngine()
        with pytest.raises(ValidationError):
            eng.remember("   ", "content", epistemic_status="observed")

    def test_bad_k_is_validation_error(self):
        eng = MemoryEngine()
        with pytest.raises(ValidationError):
            eng.recall(k=0)

    def test_bool_k_is_rejected(self):
        """True is an int in Python; it is not a valid k."""
        eng = MemoryEngine()
        with pytest.raises(ValidationError):
            eng.recall(k=True)

    def test_confidence_out_of_range_is_validation_error(self):
        eng = MemoryEngine()
        with pytest.raises(ValidationError):
            eng.remember(
                "errors.conf", "x", epistemic_status="observed", confidence=1.5
            )

    def test_alpha_out_of_range_is_validation_error(self):
        eng = MemoryEngine()
        with pytest.raises(ValidationError):
            eng.recall_hybrid("query", alpha=2.0)

    def test_supersede_unknown_id_is_not_found(self):
        from memory_engine import NotFoundError

        eng = MemoryEngine()
        with pytest.raises(NotFoundError):
            eng.supersede("does-not-exist", "new", epistemic_status="observed")

    def test_error_serialises_without_traceback(self):
        eng = MemoryEngine()
        try:
            eng.remember("errors.serialise", "x")
        except MemoryEngineError as exc:
            payload = exc.to_dict()
        else:  # pragma: no cover
            pytest.fail("expected a typed error")
        assert set(payload) == {"error", "code", "message", "details"}
        assert "Traceback" not in str(payload)


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------


class TestRetryPolicy:
    def test_rejects_zero_attempts(self):
        with pytest.raises(ConfigurationError):
            RetryPolicy(max_attempts=0)

    def test_rejects_multiplier_below_one(self):
        with pytest.raises(ConfigurationError):
            RetryPolicy(multiplier=0.5)

    def test_rejects_jitter_out_of_range(self):
        with pytest.raises(ConfigurationError):
            RetryPolicy(jitter=1.5)

    def test_delay_is_capped_before_jitter(self):
        """The cap must be a real upper bound, not one jitter can exceed."""
        pol = RetryPolicy(base_delay=1.0, multiplier=10.0, max_delay=2.0, jitter=0.0)
        assert pol.delay_for(1) == 1.0
        assert pol.delay_for(2) == 2.0
        assert pol.delay_for(10) == 2.0

    def test_delay_grows_exponentially(self):
        pol = RetryPolicy(base_delay=0.1, multiplier=2.0, max_delay=100.0, jitter=0.0)
        assert [pol.delay_for(n) for n in (1, 2, 3)] == [0.1, 0.2, 0.4]

    def test_delay_is_deterministic_given_rng(self):
        pol = RetryPolicy(base_delay=1.0, jitter=0.5)
        a = pol.delay_for(1, rng=random.Random(42))
        b = pol.delay_for(1, rng=random.Random(42))
        assert a == b

    def test_delay_never_negative(self):
        pol = RetryPolicy(base_delay=0.0, jitter=1.0)
        for n in range(1, 6):
            assert pol.delay_for(n, rng=random.Random(n)) >= 0.0

    def test_retries_transient_then_succeeds(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise TransientError("lock contention")
            return "ok"

        result = call_with_retry(
            flaky, policy=RetryPolicy(max_attempts=3), sleep=lambda _: None
        )
        assert result == "ok"
        assert len(calls) == 3

    def test_exhausts_and_reraises_last(self):
        def always():
            raise TransientError("still locked")

        with pytest.raises(TransientError, match="still locked"):
            call_with_retry(
                always, policy=RetryPolicy(max_attempts=2), sleep=lambda _: None
            )

    def test_does_not_retry_non_transient(self):
        calls = []

        def bad():
            calls.append(1)
            raise ValidationError("bad input")

        with pytest.raises(ValidationError):
            call_with_retry(
                bad, policy=RetryPolicy(max_attempts=5), sleep=lambda _: None
            )
        assert len(calls) == 1, "a validation error must not be retried"

    def test_sleeps_between_attempts_only(self):
        slept = []

        def always():
            raise TransientError("x")

        with pytest.raises(TransientError):
            call_with_retry(
                always,
                policy=RetryPolicy(max_attempts=3, base_delay=0.01, jitter=0.0),
                sleep=slept.append,
            )
        assert len(slept) == 2, "3 attempts means 2 sleeps"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_same_inputs_same_key(self):
        a = idempotency_key("topic", "content", "agent")
        b = idempotency_key("topic", "content", "agent")
        assert a == b
        assert len(a) == 64

    def test_different_inputs_different_key(self):
        assert idempotency_key("a", "b") != idempotency_key("a", "c")

    def test_separator_prevents_concatenation_collision(self):
        """("ab","c") and ("a","bc") must not collide."""
        assert idempotency_key("ab", "c") != idempotency_key("a", "bc")

    def test_namespace_changes_key(self):
        assert idempotency_key("x", namespace="a") != idempotency_key(
            "x", namespace="b"
        )

    def test_key_is_hex(self):
        key = idempotency_key("x")
        assert all(c in "0123456789abcdef" for c in key)
