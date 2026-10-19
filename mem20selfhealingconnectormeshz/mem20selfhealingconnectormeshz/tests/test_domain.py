"""Retry with exponential backoff and jitter, then give up loudly."""
import importlib
import pytest
MOD = "mem20selfhealingconnectormeshz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_invalid_backoff_refused():
    import pytest
    with pytest.raises(ValueError):
        _m().SelfHealingConnectorMesh(base_delay=-1)
    with pytest.raises(ValueError):
        _m().SelfHealingConnectorMesh(factor=0.5)


def test_success_on_first_try_does_not_sleep():
    m = _m().SelfHealingConnectorMesh()
    slept = []
    assert m.call(lambda: "ok", sleep=slept.append) == "ok"
    assert slept == []


def test_retries_then_succeeds():
    m = _m().SelfHealingConnectorMesh()
    calls = []
    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("blip")
        return "recovered"
    slept = []
    assert m.call(flaky, retries=5, sleep=slept.append) == "recovered"
    assert len(slept) == 2


def test_permanent_failure_raises_after_budget():
    m = _m().SelfHealingConnectorMesh()
    slept = []
    with pytest.raises(Exception) as e:
        m.call(lambda: 1 / 0, retries=2, sleep=slept.append)
    assert "failed after 3 attempts" in str(e.value)
    assert len(slept) == 2


def test_delay_grows_exponentially_and_is_capped():
    m = _m().SelfHealingConnectorMesh(base_delay=1, factor=2, max_delay=8,
                                      jitter=False)
    ds = [m.delay_for(i) for i in range(1, 8)]
    assert ds[0] < ds[1] < ds[2]
    assert max(ds) == 8


def test_jitter_spreads_retries_so_they_do_not_synchronise():
    m = _m().SelfHealingConnectorMesh(base_delay=1, factor=2, jitter=True,
                                      rng=__import__("random").Random(7))
    ds = [m.delay_for(3) for _ in range(12)]
    assert len(set(ds)) > 1


def test_non_transient_failure_is_not_retried():
    m = _m().SelfHealingConnectorMesh()
    calls = []
    def bad():
        calls.append(1)
        raise ValueError("400 invalid")
    with pytest.raises(ValueError):
        m.call_if_transient(bad, is_transient=lambda e: "timeout" in str(e),
                            retries=5, sleep=lambda s: None)
    assert len(calls) == 1


import pytest
