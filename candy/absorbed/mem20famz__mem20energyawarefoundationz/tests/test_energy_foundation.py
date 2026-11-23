import importlib, json, threading, time, urllib.request
MOD="mem20energyawarefoundationz"
def m(): return importlib.import_module(MOD+".domain")
def test_legacy_api():
    d=m(); r=d.power_reading({"id":"a","power_watts":50,"ts":1}); assert r["device"]=="a" and r["watts"]==50
    c=d.threshold_check({"device":"a","watts":120},100); assert c["exceeded"] and c["overage"]==20
    b=d.energy_budget([{"id":"a","power_watts":60},{"id":"b","power_watts":40}],90); assert b["within_budget"]==False and b["headroom"]==-10
    a=d.optimize_power([{"id":"a","power_watts":100}],0.1); assert a[0]["target"]==90.0
    assert d.daily_energy([{"power_watts":500}],24)==12.0
def test_advanced_evaluate():
    d=m(); res=d.evaluate([{"id":"a","power_watts":120},{"id":"b","power_watts":40}], {"budget_watts":150,"default_threshold_watts":100})
    assert res["ok"] is False and res["budget"]["within_budget"] is False and any(c["exceeded"] for c in res["threshold_checks"])
def test_ecosystem_six_peers():
    from mem20energyawarefoundationz import ecosystem
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.resource_governance({"power_watts":100},{"power_watts":90})["ok"]
    assert ecosystem.business_twin_alerts({"w":120},{"w":100})["ok"]
    assert ecosystem.ambient_fabric([{"cpu":1,"memory":1,"storage":1,"status":"online"}])["ok"]
    assert ecosystem.telemetry_aggregate([{"player":"m","action":"read"}])["ok"]
    assert ecosystem.orchestrate_actions([{"device":"d","action":"reduce"}])["ok"]
    assert ecosystem.action_workcell([{"device":"d","action":"reduce"}])["ok"]
def test_service_runtime_http(tmp_path):
    from mem20energyawarefoundationz.service import FoundationService
    from mem20energyawarefoundationz.runtime import serve
    svc=FoundationService(tmp_path/"f.db")
    svc.put_device({"device_id":"m1","power_watts":120}); svc.put_policy({"policy_id":"default","budget_watts":150,"default_threshold_watts":100})
    ev=svc.evaluate(); assert ev["ok"] is False and ev["signals"]["resource_governor"]["ok"] and ev["signals"]["business_twin"]["ok"] and ev["signals"]["ambient_fabric"]["ok"] and ev["signals"]["orchestration"]["ok"] and ev["signals"]["workcell"]["ok"]
    st=svc.status(); assert st["ok"] and st["telemetry_signal"]["ok"]
    doc=svc.doctor(); assert doc["ok"] and doc["probe"]["count"]==6
    sim=svc.simulate(); assert sim["ok"]
    httpd=serve(svc,"127.0.0.1",0); port=httpd.server_address[1]; t=threading.Thread(target=httpd.serve_forever,daemon=True); t.start(); time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r: assert json.loads(r.read())["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r: assert json.loads(r.read())["probe"]["count"]==6
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r: assert "Energy-Aware" in r.read().decode("utf-8","ignore")
    finally:
        httpd.shutdown(); httpd.server_close(); t.join(timeout=2)
