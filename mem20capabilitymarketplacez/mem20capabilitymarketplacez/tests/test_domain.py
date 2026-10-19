"""Capability routing by consistent hashing."""
import importlib
MOD = "mem20capabilitymarketplacez"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_empty_ring_locate_is_none():
    m = _m().CapabilityMarketplace()
    assert m.locate("anything") is None


def test_single_capability_owns_everything():
    m = _m().CapabilityMarketplace(); m.add("alpha")
    assert all(m.locate(k) == "alpha" for k in range(50))


def test_virtual_nodes_spread_load_evenly():
    m = _m().CapabilityMarketplace(replicas=200)
    for c in ("a", "b", "c"):
        m.add(c)
    d = m.distribution(4000)
    ideal = 4000 / 3
    for owner, n in d.items():
        assert abs(n - ideal) / ideal < 0.20, (owner, n, ideal)


def test_removing_one_node_moves_roughly_its_share():
    """The property that makes consistent hashing worth having."""
    m = _m().CapabilityMarketplace(replicas=200)
    for c in ("a", "b", "c", "d"):
        m.add(c)
    keys = list(range(3000))
    before = {k: m.locate(k) for k in keys}
    m.remove("c")
    moved = sum(1 for k in keys if m.locate(k) != before[k])
    # only keys that hashed to 'c' should move
    assert 0 < moved < len(keys) * 0.40


def test_removed_node_never_receives_keys():
    m = _m().CapabilityMarketplace()
    for c in ("a", "b"):
        m.add(c)
    m.remove("b")
    assert "b" not in m.distribution(500).keys()


def test_location_is_stable_for_a_stable_ring():
    m = _m().CapabilityMarketplace()
    for c in ("x", "y", "z"):
        m.add(c)
    first = m.locate("stable-key")
    for _ in range(10):
        assert m.locate("stable-key") == first
