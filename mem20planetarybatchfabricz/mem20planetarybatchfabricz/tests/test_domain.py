import importlib
MOD="mem20planetarybatchfabricz"
def _m(): return importlib.import_module(MOD+".domain")
def test_submit(): m=_m(); r=m.submit_job("us","p",1); assert r["status"]=="queued"
def test_sched(): m=_m(); j=m.submit_job("us","p",1); r=m.schedule([j],{"us":1}); assert len(r)==1
def test_status(): m=_m(); j=m.submit_job("us","p",1); assert m.job_status(j)=="queued"
def test_health(): m=_m(); r=m.fabric_health({"us":5,"eu":3}); assert r["regions"]==2
def test_retry(): m=_m(); j=m.submit_job("us","p",1); r=m.retry(j); assert r["ok"] is True
