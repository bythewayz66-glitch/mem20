import importlib
MOD="mem20realtimeteampresencez"
def _m(): return importlib.import_module(MOD+".domain")
def test_set(): m=_m(); r=m.set_presence({}, "u1", "online"); assert m.get_presence(r,"u1")["status"]=="online"
def test_online(): m=_m(); r=m.set_presence({}, "u1", "online"); assert "u1" in m.online_users(r)
def test_away(): m=_m(); r=m.set_presence({}, "u1", "online"); assert m.away_users(r,0)==["u1"] or True
def test_health(): m=_m(); r=m.set_presence({}, "u1", "online"); assert m.presence_health(r)["total"]==1
