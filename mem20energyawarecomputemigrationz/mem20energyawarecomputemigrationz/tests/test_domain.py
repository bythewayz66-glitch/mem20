import importlib
MOD="mem20energyawarecomputemigrationz"
def _m(): return importlib.import_module(MOD+".domain")
def test_cost(): m=_m(); assert m.energy_cost({"power_watts":100,"speed":1.0,"energy_rate":0.12},10)>0
def test_migrate(): m=_m(); src={"power_watts":200,"speed":1,"energy_rate":0.2}; dst={"power_watts":50,"speed":2,"energy_rate":0.1}; r=m.migrate_decision(src,dst,{"size":10}); assert "migrate" in r
def test_carbon(): m=_m(); assert m.carbon_footprint({"power_watts":100,"speed":1,"carbon_g_per_kwh":400},10)>0
def test_greenest(): m=_m(); n1={"id":"a","power_watts":100,"speed":1,"energy_rate":0.1,"carbon_g_per_kwh":400}; n2={"id":"b","power_watts":50,"speed":2,"energy_rate":0.1,"carbon_g_per_kwh":200}; r=m.greenest_node([n1,n2],{"size":10}); assert r["id"]=="b"
def test_plan(): m=_m(); r=m.migration_plan([{"id":"w1","size":5}],[{"id":"n1","power_watts":50,"speed":2,"energy_rate":0.1,"carbon_g_per_kwh":200}]); assert len(r)==1
