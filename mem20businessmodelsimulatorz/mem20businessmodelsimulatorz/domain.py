"""Business model simulator: revenue, costs, margins, scenarios."""
import math


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
        r = revenue(units, price)
        c = cost(fixed, var, units)
        out.append({"period": i + 1, "units": units, "revenue": r, "cost": c, "profit": profit(r, c), "margin": margin(r, c)})
        units = int(units * (1 + growth))
    return out


def sensitivity(price, units, fixed, var, delta=0.1):
    base = profit(revenue(units, price), cost(fixed, var, units))
    up = profit(revenue(units, price * (1 + delta)), cost(fixed, var, units))
    down = profit(revenue(units, price * (1 - delta)), cost(fixed, var, units))
    return {"base": base, "up": up, "down": down}
