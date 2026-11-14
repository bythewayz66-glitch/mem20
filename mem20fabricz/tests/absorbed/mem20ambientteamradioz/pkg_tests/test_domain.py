import importlib
MOD="mem20ambientteamradioz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create():
    m=_m(); c=m.create_channel("general"); assert c["name"]=="general"
def test_join_leave():
    m=_m(); c=m.create_channel("g"); m.join_channel(c,"u1"); assert "u1" in c["members"]; m.leave_channel(c,"u1"); assert "u1" not in c["members"]
def test_send():
    m=_m(); c=m.create_channel("g"); m.join_channel(c,"u1"); r=m.send_message(c,"u1","hi"); assert r["ok"] is True
def test_activity():
    m=_m(); c=m.create_channel("g"); m.join_channel(c,"u1"); m.send_message(c,"u1","hi"); r=m.channel_activity(c); assert r["recent_count"]==1
def test_route():
    m=_m(); c=m.create_channel("g"); m.join_channel(c,"u1"); r=m.route_message([c],"u1","hi"); assert "g" in r
