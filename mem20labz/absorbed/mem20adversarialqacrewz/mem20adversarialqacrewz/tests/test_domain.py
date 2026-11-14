import importlib
import tempfile

MOD = "mem20adversarialqacrewz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_gen():
    m = _m()
    c = m.generate_adversarial_cases({"base_input": {"value": 5}}, 5)
    assert len(c) == 5


def test_mutation():
    m = _m()
    assert 0 <= m.mutation_score("abc", "abd") <= 1


def test_fuzz():
    m = _m()
    r = m.fuzz_input({"x": 5, "s": "a"}, 1)
    assert "x" in r


def test_verdict():
    m = _m()
    v = m.verdict([{"pass": True}, {"pass": False}])
    assert v["release_blocked"] is True


def test_hash():
    m = _m()
    assert len(m.hash_case({"a": 1})) == 12


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
