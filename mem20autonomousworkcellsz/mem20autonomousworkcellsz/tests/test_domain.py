import importlib
import tempfile

MOD = "mem20autonomousworkcellsz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_create():
    m = _m()
    c = m.create_cell("c", 2)
    assert c["capacity"] == 2


def test_enqueue():
    m = _m()
    c = m.create_cell("c", 2)
    m.enqueue(c, {"id": 1})
    assert len(c["queue"]) == 1


def test_assign():
    m = _m()
    c = m.create_cell("c", 2)
    m.assign_workers(c, ["w1", "w2", "w3"])
    assert len(c["workers"]) == 2


def test_process():
    m = _m()
    c = m.create_cell("c", 2)
    m.enqueue(c, {"id": 1})
    m.assign_workers(c, ["w1"])
    r = m.process_next(c)
    assert r is not None


def test_health():
    m = _m()
    c = m.create_cell("c", 2)
    r = m.cell_health(c)
    assert "queue_depth" in r


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
