import importlib
MOD="mem20crossruntimeeventlatticez"
def _m(): return importlib.import_module(MOD+".domain")
def test_emit(): m=_m(); e=m.emit("click",{"x":1}); assert e["type"]=="click"
def test_order(): m=_m(); e1=m.emit("a",{}); e2=m.emit("b",{}); r=m.order_events([e2,e1]); assert r[0]["id"]==e1["id"]
def test_link(): m=_m(); p=m.emit("p",{}); c=m.emit("c",{}); m.causal_link(p,c); assert c["parent"]==p["id"]
def test_merge(): m=_m(); r=m.lattice_merge([{"events":[m.emit("a",{})]},{"events":[m.emit("b",{})]}]); assert r["count"]==2
def test_filter(): m=_m(); ev=[m.emit("a",{}),m.emit("b",{})]; r=m.filter_by_type(ev,"a"); assert len(r)==1
