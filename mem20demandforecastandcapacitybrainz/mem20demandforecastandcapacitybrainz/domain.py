"""Demand forecast with an honest prediction interval.

Domain research: an EWMA plus a running estimate of residual spread. The
interval widens when the series is volatile and narrows when it is steady,
and it is derived from observed error rather than assumed. What must never
happen is a point forecast presented without its uncertainty, because
capacity decisions made on a bare point estimate are how over-provisioning
happens.
"""
import math


class DemandForecastAndCapacityBrain:
    def __init__(self, alpha=0.3, window=50):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        if window < 2:
            raise ValueError("window must be >= 2")
        self.alpha = float(alpha)
        self.window = int(window)
        self.observations = []
        self.level = None

    def observe(self, value):
        v = float(value)
        self.observations.append(v)
        self.observations = self.observations[-self.window:]
        self.level = v if self.level is None else \
            self.alpha * v + (1 - self.alpha) * self.level
        return self.level

    def residual_sigma(self):
        """Spread of observed error, not an assumed constant."""
        if len(self.observations) < 3:
            return None
        diffs = [self.observations[i] - self.observations[i - 1]
                 for i in range(1, len(self.observations))]
        if not diffs:
            return None
        mean = sum(diffs) / len(diffs)
        var = sum((d - mean) ** 2 for d in diffs) / max(1, len(diffs) - 1)
        return math.sqrt(var)

    def forecast(self, steps=1, z=1.96):
        """Point forecast plus a prediction interval. Never a bare number."""
        if self.level is None:
            return {"point": None, "low": None, "high": None,
                    "note": "no observations yet"}
        sigma = self.residual_sigma()
        if sigma is None:
            return {"point": self.level, "low": self.level, "high": self.level,
                    "note": "too few observations for an interval"}
        width = z * sigma * math.sqrt(max(1, int(steps)))
        return {"point": round(self.level, 6),
                "low": round(self.level - width, 6),
                "high": round(self.level + width, 6),
                "sigma": round(sigma, 6),
                "n": len(self.observations),
                "note": "interval widens with horizon via sqrt(steps)"}

    def capacity_for(self, service_level=0.99):
        """Capacity headroom that holds the interval above a threshold."""
        f = self.forecast()
        if f["point"] is None or f.get("sigma") is None:
            return None
        return round(f["high"] / max(1e-9, (1 - service_level)), 6)
