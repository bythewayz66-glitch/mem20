import importlib
MOD="mem20eventstreamsuperhighwayz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); s=m.create_stream("s"); assert s["name"]=="s"
def test_publish(): m=_m(); s=m.create_stream("s"); e=m.publish(s,"click",{"x":1}); assert e["type"]=="click"
def test_subscribe(): m=_m(); s=m.create_stream("s"); m.subscribe(s,"u1"); assert "u1" in s["subscribers"]
def test_consume(): m=_m(); s=m.create_stream("s"); m.publish(s,"a",{}); m.subscribe(s,"u1"); r=m.consume(s,"u1"); assert len(r)==1
def test_throughput(): m=_m(); s=m.create_stream("s"); m.publish(s,"a",{}); assert m.throughput(s)>=0
