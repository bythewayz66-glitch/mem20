import importlib
MOD="mem20visualdataflowcomposerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_pipeline("p1"); assert r["name"]=="p1"
def test_node(): m=_m(); r=m.create_pipeline("p1"); n=m.add_node(r,"source"); assert n["type"]=="source"
def test_conn(): m=_m(); r=m.create_pipeline("p1"); a=m.add_node(r,"a"); b=m.add_node(r,"b"); m.connect(r,a["id"],b["id"]); assert len(r["edges"])==1
def test_exec(): m=_m(); r=m.create_pipeline("p1"); m.add_node(r,"a"); res=m.execute(r,{},lambda n,d: 42); assert len(res)==1
def test_health(): m=_m(); r=m.create_pipeline("p1"); m.add_node(r,"a"); assert m.pipeline_health(r)["nodes"]==1
