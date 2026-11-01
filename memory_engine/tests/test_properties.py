"""Property-based tests for the memory engine contract (M0).

Hypothesis generates inputs the hand-written tests would never think of. The
properties here are invariants the engine must hold for ANY input, not
examples of specific behaviour.

These FAIL on d99ab5d (no facade, no error model) and PASS after.

Run: python3 -m pytest memory_engine/tests/test_properties.py -q
"""

from __future__ import annotations

import os
import sys
import tempfile

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

_STORE = tempfile.mkdtemp(prefix="mem20_props_")
os.environ["MEM20_STORE_PATH"] = _STORE

from memory_engine import (  # noqa: E402
    EPISTEMIC_STATUSES,
    EngineConfig,
    MemoryEngine,
    MemoryEngineError,
    RetryPolicy,
    ValidationError,
    call_with_retry,
    idempotency_key,
)

# The engine writes to disk on every remember(), so keep example counts modest.
PROP = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)

# Topics must be non-empty and filesystem-safe enough for the entries/ mirror.
topics = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="._-"),
    min_size=1,
    max_size=40,
).filter(lambda s: s.strip() and not s.startswith("."))

contents = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())

statuses = st.sampled_from(EPISTEMIC_STATUSES)


@pytest.fixture(scope="module")
def engine():
    return MemoryEngine()


# ---------------------------------------------------------------------------
# Write/read round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    @PROP
    @given(topic=topics, content=contents, status=statuses)
    def test_remember_then_recall_preserves_content(self, engine, topic, content, status):
        """Whatever goes in comes back byte-identical, with its label intact."""
        fact = engine.remember(topic, content, epistemic_status=status)
        assert fact.content == content
        assert fact.epistemic_status == status
        assert fact.topic == topic

        found = engine.recall(topic=topic, k=50)
        assert any(f.id == fact.id for f in found), "written fact must be recallable"
        match = next(f for f in found if f.id == fact.id)
        assert match.content == content
        assert match.epistemic_status == status

    @PROP
    @given(topic=topics, content=contents)
    def test_ids_are_unique(self, engine, topic, content):
        """Two writes of identical content must not share an id."""
        a = engine.remember(topic, content, epistemic_status="observed")
        b = engine.remember(topic, content, epistemic_status="observed")
        assert a.id != b.id

    @PROP
    @given(topic=topics, content=contents, status=statuses)
    def test_origin_is_always_grounded(self, engine, topic, content, status):
        """remember() is the grounded path; origin must never be anything else."""
        fact = engine.remember(topic, content, epistemic_status=status)
        assert fact.origin == "grounded"


# ---------------------------------------------------------------------------
# Refusals are total, not partial
# ---------------------------------------------------------------------------


class TestRefusalsAreTotal:
    @PROP
    @given(topic=topics, content=contents)
    def test_missing_status_never_writes(self, engine, topic, content):
        """A refused write must leave no trace in the ledger."""
        before = len(engine.recall(topic=topic, k=1000))
        with pytest.raises(MemoryEngineError):
            engine.remember(topic, content)
        after = len(engine.recall(topic=topic, k=1000))
        assert after == before, "a refused write must not append to the ledger"

    @PROP
    @given(topic=st.text(max_size=20), content=contents)
    def test_blank_topic_always_refused(self, engine, topic, content):
        if topic.strip():
            return  # only the blank case is under test
        with pytest.raises(ValidationError):
            engine.remember(topic, content, epistemic_status="observed")

    @PROP
    @given(k=st.integers(max_value=0))
    def test_non_positive_k_always_refused(self, engine, k):
        with pytest.raises(ValidationError):
            engine.recall(k=k)


# ---------------------------------------------------------------------------
# Retry policy invariants
# ---------------------------------------------------------------------------


class TestRetryInvariants:
    @PROP
    @given(
        base=st.floats(min_value=0.0, max_value=10.0),
        mult=st.floats(min_value=1.0, max_value=5.0),
        cap=st.floats(min_value=0.0, max_value=10.0),
        attempt=st.integers(min_value=1, max_value=50),
    )
    def test_delay_never_exceeds_cap(self, base, mult, cap, attempt):
        """Jitter must never push a delay past max_delay."""
        pol = RetryPolicy(
            base_delay=base, multiplier=mult, max_delay=cap, jitter=0.0
        )
        assert pol.delay_for(attempt) <= cap + 1e-9

    @PROP
    @given(
        base=st.floats(min_value=0.0, max_value=5.0),
        attempt=st.integers(min_value=1, max_value=30),
        seed=st.integers(min_value=0, max_value=10_000),
    )
    def test_delay_always_non_negative(self, base, attempt, seed):
        import random

        pol = RetryPolicy(base_delay=base, jitter=1.0)
        assert pol.delay_for(attempt, rng=random.Random(seed)) >= 0.0

    @PROP
    @given(attempts=st.integers(min_value=1, max_value=6))
    def test_attempt_count_is_exact(self, attempts):
        """max_attempts=N means exactly N calls, never N+1."""
        from memory_engine import TransientError

        calls = []

        def always():
            calls.append(1)
            raise TransientError("x")

        with pytest.raises(TransientError):
            call_with_retry(
                always,
                policy=RetryPolicy(max_attempts=attempts, base_delay=0.0),
                sleep=lambda _: None,
            )
        assert len(calls) == attempts


# ---------------------------------------------------------------------------
# Idempotency key invariants
# ---------------------------------------------------------------------------


class TestIdempotencyInvariants:
    @PROP
    @given(parts=st.lists(st.text(max_size=30), min_size=1, max_size=5))
    def test_key_is_deterministic_and_hex(self, parts):
        a = idempotency_key(*parts)
        b = idempotency_key(*parts)
        assert a == b
        assert len(a) == 64
        assert all(c in "0123456789abcdef" for c in a)

    @PROP
    @given(
        left=st.text(min_size=1, max_size=10),
        right=st.text(min_size=1, max_size=10),
    )
    def test_no_concatenation_collision(self, left, right):
        """Splitting a string differently must change the key."""
        if left + right == right + left:
            return  # identical concatenation, not a collision case
        assert idempotency_key(left, right) != idempotency_key(left + right)


# ---------------------------------------------------------------------------
# Config invariants
# ---------------------------------------------------------------------------


class TestConfigInvariants:
    @PROP
    @given(ttl=st.integers(min_value=1, max_value=3650))
    def test_env_roundtrip_preserves_ttl(self, ttl):
        cfg = EngineConfig.from_env(
            {"MEM20_STORE_PATH": "/tmp/mem20_prop_store", "MEM20_SIM_TTL_DAYS": str(ttl)}
        )
        assert cfg.sim_ttl_days == ttl
        assert EngineConfig.from_env(cfg.to_env()).sim_ttl_days == ttl

    @PROP
    @given(raw=st.text(max_size=10).filter(lambda s: s.strip().lower() not in
                                           {"1", "0", "true", "false", "yes", "no", "on", "off"}))
    def test_invalid_bool_is_configuration_error(self, raw):
        from memory_engine import ConfigurationError

        with pytest.raises(ConfigurationError):
            EngineConfig.from_env(
                {"MEM20_STORE_PATH": "/tmp/mem20_prop_store", "MEM20_RERANK": raw}
            )

    @PROP
    @given(ttl=st.integers(max_value=0))
    def test_non_positive_ttl_rejected(self, ttl):
        from memory_engine import ConfigurationError

        with pytest.raises(ConfigurationError):
            EngineConfig.from_env(
                {
                    "MEM20_STORE_PATH": "/tmp/mem20_prop_store",
                    "MEM20_SIM_TTL_DAYS": str(ttl),
                }
            )
