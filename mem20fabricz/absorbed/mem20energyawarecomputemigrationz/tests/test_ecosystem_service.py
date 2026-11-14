import json, threading, time, urllib.request
from mem20energyawarecomputemigrationz import ecosystem
from mem20energyawarecomputemigrationz.runtime import serve
from mem20energyawarecomputemigrationz.service import MigrationService

def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.battery_schedule(5,[0,1],500,{0:50,1:40})["ok"]
    assert ecosystem.energy_foundation([{"id":"n","power_watts":100}])["ok"]
    assert ecosystem.data_locality({"id":"d","size_gb":1},[{"id":"n","capacity_gb":10,"used_gb":0,"latency_ms":5,"cost_per_gb":0.01}])["ok"]
    assert ecosystem.capacity_forecast([1,2,1.5])["ok"]
    assert ecosystem.goal_priority([{"id":"m","value":2,"cost":1}],2)["ok"]
    assert ecosystem.batch_fabric()["ok"]

def test_service_plan_migrate_and_http(tmp_path):
    svc=MigrationService(tmp_path/"m.db")
    svc.put_node({"node_id":"dirty","power_watts":200,"speed":1,"energy_rate":0.2,"carbon_g_per_kwh":600,"renewable_pct":0})
    svc.put_node({"node_id":"green","power_watts":50,"speed":2,"energy_rate":0.1,"carbon_g_per_kwh":100,"renewable_pct":80})
    svc.put_workload({"workload_id":"w1","size":10,"current_node":"dirty"})
    plan=svc.plan({})
    assert plan["ok"] and plan["signals"]["capacity_forecast"]["ok"] and plan["signals"]["goal_scheduler"]["ok"] and plan["signals"]["data_locality"]["ok"] and plan["signals"]["batch_fabric"]["ok"]
    mig=svc.migrate("w1", "green")
    assert mig["ok"] and mig["to"]=="green" and mig["energy_signal"]["ok"] and mig["data_locality_signal"]["ok"]
    st=svc.status(); assert st["ok"] and st["energy_signal"]["ok"] and st["capacity_signal"]["ok"]
    doc=svc.doctor(); assert doc["ok"] and doc["probe"]["count"]==6
    sim=svc.simulate(); assert sim["ok"] and sim["passed"]==sim["total"]
    httpd=serve(svc,"127.0.0.1",0); port=httpd.server_address[1]
    t=threading.Thread(target=httpd.serve_forever,daemon=True); t.start(); time.sleep(0.05)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status") as r: assert json.loads(r.read())["ok"]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/doctor") as r: assert json.loads(r.read())["probe"]["count"]==6
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as r: assert "Energy-Aware" in r.read().decode("utf-8","ignore")
    finally:
        httpd.shutdown(); httpd.server_close(); t.join(timeout=2)
