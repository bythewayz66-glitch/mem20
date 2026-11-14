"""Energy-aware scheduling under a hard power budget.

Domain research: deferring work to when and where power is cheap and clean.
The real constraint is feasibility, not preference: a schedule that exceeds
the power budget is invalid, and the scheduler must say so rather than
silently oversubscribe. Cost is modelled as a time-varying rate, so the same
job at a different hour costs something different. Selection is by cheapest
feasible slot, and ties break earliest-first so behaviour is deterministic.
"""
import itertools


class BatteryAwareAgentScheduler:
    def __init__(self, power_budget_watts, rates):
        """rates: {hour: watts_per_unit} - the power price at that hour."""
        if power_budget_watts <= 0:
            raise ValueError("power budget must be positive")
        if not rates:
            raise ValueError("need at least one rate")
        self.budget = float(power_budget_watts)
        self.rates = {int(h): float(w) for h, w in rates.items()}
        self._seq = itertools.count()
        self.deferred = 0

    def cost(self, work_units, hour):
        if hour not in self.rates:
            raise KeyError(f"no rate known for hour {hour}")
        return float(work_units) * self.rates[hour]

    def cheapest_slot(self, work_units, hours):
        """Cheapest hour, earliest first on a tie. None if infeasible."""
        feasible = [(self.cost(work_units, h), h) for h in hours
                    if self.cost(work_units, h) <= self.budget]
        if not feasible:
            self.deferred += 1
            return None
        return min(feasible, key=lambda t: (t[0], t[1]))[1]

    def schedule(self, work_units, hours):
        if self.cheapest_slot(work_units, hours) is None:
            return {"scheduled": False, "reason": "no hour fits the power budget",
                    "work_units": work_units, "deferred_total": self.deferred}
        hour = self.cheapest_slot(work_units, hours)
        return {"scheduled": True, "hour": hour,
                "cost_watts": round(self.cost(work_units, hour), 6),
                "headroom_watts": round(self.budget - self.cost(work_units, hour), 6)}
