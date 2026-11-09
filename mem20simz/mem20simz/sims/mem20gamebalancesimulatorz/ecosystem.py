"""Six unique peers for Game Balance Simulator (#315), different from #300-#314."""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Dict

_PEER_TIMEOUT_S = 1.5
_EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="gbs-peer")


def _safe(name: str, fn: Callable[[], Dict[str, Any]]):
    try:
        fut = _EXEC.submit(fn)
        return {"ok": True, "subsystem": name, **(fut.result(timeout=_PEER_TIMEOUT_S) or {})}
    except concurrent.futures.TimeoutError:
        fut.cancel()
        return {"ok": False, "subsystem": name, "error": f"TimeoutError: peer call timed out after {_PEER_TIMEOUT_S}s"}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


def skill_progression(payload=None) -> Dict[str, Any]:
    def run():
        from mem20skillbasedprogressionbrainz.domain import gain_xp, level, progression_health
        p = {"xp": int((payload or {}).get("xp", 120)), "skills": []}
        gain_xp(p, int((payload or {}).get("xp_gain", 50)))
        return {"level": level(p), "health": progression_health(p)}
    return _safe("mem20skillbasedprogressionbrainz", run)


def player_motivation(payload=None) -> Dict[str, Any]:
    def run():
        from mem20twinz.domain import create_twin, update, predict_churn, motivation_segments
        t = create_twin(str((payload or {}).get("player", "p1")))
        update(t, {"type": str((payload or {}).get("event", "win"))})
        return {"churn_risk": predict_churn(t), "segments": motivation_segments(t)}
    return _safe("mem20twinz", run)


def level_architecture(payload=None) -> Dict[str, Any]:
    def run():
        from mem20ailevelarchitectz.domain import difficulty_curve, pacing_profile, generate_layout
        levels = int((payload or {}).get("levels", 5))
        curve = difficulty_curve(levels)
        pacing = pacing_profile(int((payload or {}).get("duration", 60)), 4)
        layout = generate_layout(10, 10, rooms=min(3, levels), seed=1)
        return {"difficulty_curve": curve, "pacing": pacing, "layout_type": type(layout).__name__}
    return _safe("mem20ailevelarchitectz", run)


def community_challenge(payload=None) -> Dict[str, Any]:
    def run():
        from mem20communitychallengeenginez.domain import create_challenge, join, record_progress, leaderboard
        c = create_challenge("balance-challenge", int((payload or {}).get("goal", 100)))
        join(c, "u1")
        record_progress(c, "u1", int((payload or {}).get("progress", 10)))
        return {"leaderboard": leaderboard(c)}
    return _safe("mem20communitychallengeenginez", run)


def skill_transfer(payload=None) -> Dict[str, Any]:
    def run():
        from mem20skillmemorytransferz.domain import transfer, merge_skills, transfer_health
        src = {"id": "s", "skills": {"aim": 3, "economy": 2}}
        dst = {"id": "d", "skills": {}}
        tr = transfer(src, dst, "aim")
        merged = merge_skills(dst, {"economy": 1})
        health = transfer_health([tr] if isinstance(tr, dict) else [{"ok": bool(tr)}])
        return {"transfer": tr, "merged": merged, "health": health}
    return _safe("mem20skillmemorytransferz", run)


def impact_rewards(payload=None) -> Dict[str, Any]:
    def run():
        from mem20realworldimpactrewardsz.domain import record_impact, compute_reward, impact_health
        imp = {}
        record_impact(imp, "u1", "quest", 5)
        reward = compute_reward(imp, "u1")
        health = impact_health(imp)
        return {"reward": reward, "health": health}
    return _safe("mem20realworldimpactrewardsz", run)


def probe() -> Dict[str, Any]:
    checks = {
        "skill_progression": skill_progression(),
        "player_motivation": player_motivation(),
        "level_architecture": level_architecture(),
        "community_challenge": community_challenge(),
        "skill_transfer": skill_transfer(),
        "impact_rewards": impact_rewards(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
