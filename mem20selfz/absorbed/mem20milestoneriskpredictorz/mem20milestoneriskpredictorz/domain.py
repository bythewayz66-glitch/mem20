"""Milestone risk that says a milestone is late while there is still time.

Domain research: burn-up / remaining-work estimation. Risk comes from the gap
between actual throughput and what the remaining scope requires, not from a
subjective confidence number. The useful output is a forecast date and the
slack against it, plus an explicit 'already late' rather than a probability
that quietly rounds to zero.
"""
from datetime import datetime, timedelta


class MilestoneRiskPredictor:
    def __init__(self, ideal_velocity=1.0):
        if ideal_velocity <= 0:
            raise ValueError("velocity must be positive")
        self.ideal = float(ideal_velocity)
        self.points = []   # (date_iso, completed_units)

    def add_point(self, date_iso, completed_units):
        d = datetime.fromisoformat(str(date_iso).replace("Z", "+00:00"))
        c = float(completed_units)
        if self.points and c < self.points[-1][1] - 1e-9:
            raise ValueError("completed units cannot go backwards")
        self.points.append((d, c))
        return len(self.points)

    def velocity(self):
        if len(self.points) < 2:
            return None
        (d0, c0), (d1, c1) = self.points[0], self.points[-1]
        days = (d1 - d0).total_seconds() / 86400.0
        if days <= 0:
            return None
        return (c1 - c0) / days

    def forecast(self, remaining_units, from_date_iso=None, confidence_slack=0.2):
        v = self.velocity()
        if v is None:
            return {"forecast_date": None,
                    "note": "need at least two points at different dates"}
        start = datetime.fromisoformat(str(from_date_iso).replace("Z", "+00:00")) \
            if from_date_iso else self.points[-1][0]
        ideal_days = remaining_units / self.ideal
        actual_days = remaining_units / v if v > 0 else float("inf")
        slack_days = actual_days * confidence_slack
        eta = start + timedelta(days=actual_days + slack_days)
        return {
            "velocity": round(v, 6),
            "ideal_days": round(ideal_days, 4),
            "actual_days": None if actual_days == float("inf") else round(actual_days, 4),
            "forecast_date": None if actual_days == float("inf") else eta.date().isoformat(),
            "slack_days": round(slack_days, 4),
            "behind": bool(v < self.ideal),
            "at_risk": bool(actual_days > ideal_days * 1.5),
        }

    def missed_deadline(self, deadline_iso):
        f = self.forecast(remaining_units=0.0001)
        if f.get("forecast_date") is None:
            return None
        dl = datetime.fromisoformat(str(deadline_iso).replace("Z", "+00:00"))
        return datetime.fromisoformat(f["forecast_date"]) > dl
