"""Skill memory transfer: transfer skills between agents."""
import copy


def extract(agent, skill):
    skills = agent.get("skills", {})
    if skill in skills:
        return copy.deepcopy(skills[skill])
    return None


def transfer(src, dst, skill):
    mem = extract(src, skill)
    if mem is None:
        return {"ok": False, "reason": "skill not found"}
    dst.setdefault("skills", {})[skill] = mem
    return {"ok": True}


def merge_skills(agent, incoming):
    agent.setdefault("skills", {}).update(incoming)
    return agent


def transfer_health(transfers):
    ok = sum(1 for t in transfers if t.get("ok"))
    return {"total": len(transfers), "ok": ok}
