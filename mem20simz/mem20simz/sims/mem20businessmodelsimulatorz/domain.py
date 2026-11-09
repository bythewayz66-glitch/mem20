"""Business model simulator: revenue, costs, margins, scenarios, and estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["revenue","cost","profit","margin","break_even","scenario_sim","sensitivity","model_report","probe","estate_context"]

def revenue(units, price):
    return round(units * price, 2)

def cost(fixed, variable_per_unit, units):
    return round(fixed + variable_per_unit * units, 2)

def profit(rev, cst):
    return round(rev - cst, 2)

def margin(rev, cst):
    if rev == 0:
        return 0.0
    return round((rev - cst) / rev, 4)

def break_even(fixed, price, variable_per_unit):
    contrib = price - variable_per_unit
    if contrib <= 0:
        return None
    return math.ceil(fixed / contrib)

def scenario_sim(base_units, price, fixed, var, growth=0.1, periods=4):
    out = []
    units = base_units
    for i in range(periods):
        r = revenue(units, price); c = cost(fixed, var, units)
        out.append({"period": i + 1, "units": units, "revenue": r, "cost": c, "profit": profit(r, c), "margin": margin(r, c)})
        units = int(units * (1 + growth))
    return out

def sensitivity(price, units, fixed, var, delta=0.1):
    base = profit(revenue(units, price), cost(fixed, var, units))
    up = profit(revenue(units, price * (1 + delta)), cost(fixed, var, units))
    down = profit(revenue(units, price * (1 - delta)), cost(fixed, var, units))
    return {"base": base, "up": up, "down": down}

def model_report(base_units=100, price=10.0, fixed=200.0, var=4.0, growth=0.1, periods=4):
    scen = scenario_sim(base_units, price, fixed, var, growth=growth, periods=periods)
    sens = sensitivity(price, base_units, fixed, var)
    be = break_even(fixed, price, var)
    last = scen[-1] if scen else {}
    peers = {
        "demand_signal": ecosystem.demand_signal([base_units * (1+growth)**i for i in range(5)], capacity=int(base_units*2)),
        "counterfactual_scenarios": ecosystem.counterfactual_scenarios({"price": price, "units": base_units}, {"effect": 0.1, "change": {"price": price * 1.1}}),
        "partnership_synergy": ecosystem.partnership_synergy({"revenue": last.get("revenue", 0), "markets": ["saas"], "tech": ["py"]}, {"revenue": last.get("revenue", 0)*2, "markets": ["saas"], "tech": ["py"]}),
        "lifecycle_value": ecosystem.lifecycle_value({"tenure_months": 12, "spend": price * 3, "events": 5}),
        "loyalty_graph": ecosystem.loyalty_graph(["core", "addon"]),
        "pipeline_signal": ecosystem.pipeline_signal([{"deal_value": last.get("revenue", price*base_units), "budget": price*base_units, "authority": True, "need": True, "timeline_days": 20, "touches": 1}]),
    }
    return {"ok": all(v.get("ok") for v in peers.values()), "break_even_units": be, "scenario_periods": len(scen), "final_profit": last.get("profit"), "sensitivity": sens, "peers": peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=model_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
