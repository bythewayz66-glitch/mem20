"""Game production control center: milestones, sprints, burndown."""
import math


def sprint_plan(tasks, capacity):
    plan = []
    current = []
    used = 0
    for t in tasks:
        effort = t.get("effort", 1)
        if used + effort > capacity and current:
            plan.append({"sprint": len(plan) + 1, "tasks": current, "effort": used})
            current = []
            used = 0
        current.append(t.get("id"))
        used += effort
    if current:
        plan.append({"sprint": len(plan) + 1, "tasks": current, "effort": used})
    return plan


def burndown(tasks, completed_ids):
    total = sum(t.get("effort", 1) for t in tasks)
    done = sum(t.get("effort", 1) for t in tasks if t.get("id") in completed_ids)
    return {"total": total, "done": done, "remaining": total - done, "percent": round(done / max(1, total), 4)}


def milestone_status(milestones, today):
    out = []
    for m in milestones:
        due = m.get("due_day", 0)
        status = "on_track" if today <= due else "overdue"
        out.append({"id": m.get("id"), "status": status, "days_left": due - today})
    return out


def risk_score(project):
    score = 0.0
    if project.get("scope_creep"):
        score += 0.3
    if project.get("team_size", 5) < 3:
        score += 0.3
    if project.get("budget_ratio", 1.0) > 1.0:
        score += 0.4
    return round(min(1.0, score), 4)


def production_health(sprints):
    if not sprints:
        return 0.0
    completed = sum(1 for s in sprints if s.get("done"))
    return round(completed / len(sprints), 4)
