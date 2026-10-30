"""Skill-based progression brain: XP, levels, skill trees."""
import math


def gain_xp(player, amount):
    player["xp"] = player.get("xp", 0) + amount
    player["level"] = int(player["xp"] ** 0.5) // 10 + 1  # simple
    return player


def unlock_skill(player, skill, cost):
    if player.get("xp", 0) >= cost:
        player.setdefault("skills", []).append(skill)
        player["xp"] -= cost
        return {"ok": True}
    return {"ok": False, "reason": "insufficient xp"}


def level(player):
    return player.get("level", 1)


def progression_health(player):
    return {"level": player.get("level", 1), "xp": player.get("xp", 0), "skills": len(player.get("skills", []))}
