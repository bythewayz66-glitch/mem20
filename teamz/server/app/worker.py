"""Autonomous goal worker.

A room (channel) can have a goal and a team. While the goal is active, the
worker wakes on a fixed cadence and has one agent take the next concrete step:
it reads the room history, decides what to do, actually runs terminal / file /
gh tools, writes the files, and reports back into the room. Progress, next step
and step count are persisted, so the room resumes where it left off after a
server restart without anyone re-prompting it.

The worker is deliberately conservative: one step per room per tick, a hard cap
on steps per goal, and every exception is contained so a bad model reply can
never kill the loop.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
from typing import Any, Dict, List, Optional

from .config import settings
from .execution import execute_actions, tools_manifest
from .models import (
    AgentSkill,
    AgentSkillCertificate,
    AgentSkillProgress,
    MentorSession,
    SkillDecayConfig,
    SkillMarketplaceListing,
    SkillTreeNode,
)
from .state import StateStore

STEP_MARKERS = (
    "goal",
    "build",
    "create",
    "implement",
    "write",
    "fix",
    "add",
    "test",
    "deploy",
    "design",
    "research",
    "refactor",
    "ship",
)


# --- Skill System Constants ---
XP_PER_SUCCESSFUL_TOOL = 10
XP_PER_SUCCESSFUL_STEP = 25
XP_PER_GOAL_COMPLETION = 100
XP_BASE_PER_LEVEL = 100  # XP needed for level 1, doubles each level


def _tokens(text: str) -> set[str]:
    out = set()
    cur = []
    for ch in (text or "").lower():
        if ch.isalnum():
            cur.append(ch)
        else:
            if cur:
                out.add("".join(cur))
                cur = []
    if cur:
        out.add("".join(cur))
    return out


def _xp_for_level(level: int) -> int:
    """Calculate total XP needed to reach a given level."""
    return XP_BASE_PER_LEVEL * (2 ** (level - 1))


def _level_from_xp(xp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    while xp >= _xp_for_level(level + 1):
        level += 1
    return level


def _xp_to_next_level(xp: int) -> int:
    """XP needed to reach next level."""
    level = _level_from_xp(xp)
    next_level_xp = _xp_for_level(level + 1)
    return max(0, next_level_xp - xp)


def _agent_skill_level(agent: Dict[str, Any], skill_key: str) -> int:
    """Get an agent's current level for a skill."""
    for skill in agent.get("skills") or []:
        if isinstance(skill, dict) and skill.get("key") == skill_key:
            return int(skill.get("level") or 1)
    return 0


def _agent_skill_xp(agent: Dict[str, Any], skill_key: str) -> int:
    """Get an agent's current XP for a skill."""
    for skill in agent.get("skills") or []:
        if isinstance(skill, dict) and skill.get("key") == skill_key:
            return int(skill.get("xp") or 0)
    return 0


def _add_skill_xp(agent: Dict[str, Any], skill_key: str, xp_gained: int) -> Dict[str, Any]:
    """Add XP to an agent's skill and return updated agent."""
    skills = list(agent.get("skills") or [])
    for skill in skills:
        if skill.get("key") == skill_key:
            skill["xp"] = int(skill.get("xp") or 0) + xp_gained
            skill["level"] = _level_from_xp(skill["xp"])
            return agent
    # Skill doesn't exist yet, add it
    skills.append({
        "key": skill_key,
        "label": skill_key.replace("-", " ").title(),
        "level": 1,
        "xp": xp_gained,
    })
    return agent


def _level_from_xp(xp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    while xp >= XP_BASE_PER_LEVEL * (2 ** level):
        level += 1
    return level


def _xp_for_next_level(xp: int) -> int:
    """XP needed to reach next level."""
    level = 1
    while xp >= XP_BASE_PER_LEVEL * (2 ** level):
        level += 1
    return XP_BASE_PER_LEVEL * (2 ** level) - xp


def score_agent_for_goal(agent: Dict[str, Any], goal_text: str) -> int:
    """Cheap keyword relevance so the worker picks a plausible owner per step."""
    goal_tokens = _tokens(goal_text)
    score = 0
    name = str(agent.get("name") or "")
    if name and name.lower() in (goal_text or "").lower():
        score += 8
    role = str((agent.get("origin") or {}).get("role") or agent.get("role") or "")
    score += 4 * len(_tokens(role) & goal_tokens)
    for skill in agent.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        label = str(skill.get("label") or skill.get("key") or "")
        score += 3 * len(_tokens(label) & goal_tokens)
        if label and label.lower() in (goal_text or "").lower():
            score += 3
    if agent.get("isLead"):
        score += 2
    if agent.get("workerEnabled"):
        score += 3
    if agent.get("status") == "offline":
        score -= 20
    return score


def pick_worker_agent(agents: List[Dict[str, Any]], goal_text: str) -> Optional[Dict[str, Any]]:
    """Select the best agent for a goal using skill-aware scoring."""
    candidates = [a for a in agents if isinstance(a, dict) and a.get("name")]
    if not candidates:
        return None
    
    # Prefer enabled workers, then leads, then skill relevance + keyword score
    enabled = [a for a in candidates if a.get("workerEnabled") is not False]
    pool = enabled or candidates
    
    def agent_score(a: Dict[str, Any]) -> float:
        # Keyword relevance (0-1)
        keyword_score = score_agent_for_goal(a, goal_text) / 50.0
        
        # Skill relevance (0-1) - how many goal-relevant skills the agent has
        goal_tokens = _tokens(goal_text)
        skill_relevance = 0.0
        for skill in a.get("skills") or []:
            if isinstance(skill, dict):
                skill_tokens = _tokens(skill.get("label") or skill.get("key") or "")
                overlap = len(skill_tokens & goal_tokens)
                if overlap > 0:
                    skill_relevance += overlap * (skill.get("level", 1) / 5.0)
        skill_relevance = min(skill_relevance / 10.0, 1.0)
        
        # Lead bonus
        lead_bonus = 0.2 if a.get("isLead") else 0.0
        
        # Worker enabled bonus
        enabled_bonus = 0.1 if a.get("workerEnabled") else 0.0
        
        # Status penalty
        status_penalty = -0.5 if a.get("status") == "offline" else 0.0
        
        # Combine scores with weights
        return (
            0.4 * keyword_score +
            0.3 * skill_relevance +
            0.1 * lead_bonus +
            0.1 * enabled_bonus +
            0.1 * status_penalty
        )
    
    return max(pool, key=agent_score)


def score_agent_for_goal(agent: Dict[str, Any], goal_text: str) -> int:
    """Legacy keyword-only scoring for backwards compatibility."""
    goal_tokens = _tokens(goal_text)
    score = 0
    name = str(agent.get("name") or "")
    if name and name.lower() in (goal_text or "").lower():
        score += 8
    role = str((agent.get("origin") or {}).get("role") or agent.get("role") or "")
    score += 4 * len(_tokens(role) & goal_tokens)
    for skill in agent.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        label = str(skill.get("label") or skill.get("key") or "")
        score += 3 * len(_tokens(label) & goal_tokens)
        if label and label.lower() in (goal_text or "").lower():
            score += 3
    if agent.get("isLead"):
        score += 2
    if agent.get("workerEnabled"):
        score += 3
    if agent.get("status") == "offline":
        score -= 20
    return score


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _clip_text(text: str, limit: int = 4000) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "…"


def build_worker_prompt(
    agent: Dict[str, Any],
    conversation: Dict[str, Any],
    goal: Dict[str, Any],
    recent_messages: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    skill_count: int,
) -> List[Dict[str, str]]:
    """System + user messages for one autonomous work turn."""
    tools = "\n".join(f"- {t['name']}: {t['description']}" for t in tools_manifest())
    system = "\n\n".join(
        [
            (agent.get("systemPrompt") or f"You are {agent.get('name')}, an autonomous worker.").strip(),
            (
                "You are an AUTONOMOUS WORKER in the teamz room "
                f"\"{conversation.get('name')}\". You keep working toward the room goal on your own — "
                "the user does not prompt you again between steps."
            ),
            (
                "You have real hands. Use them: run shell commands, read the code, write and edit files, "
                "run tests, commit, and use the GitHub CLI. Do NOT just describe what you would write — "
                "actually write the files and run the commands. If the goal is a project, build it in the "
                "workspace directory."
            ),
            (
                "Work in small, verifiable steps. After each step, report what changed and what you will do "
                "next. If the goal is complete, say done=true."
            ),
            (
                "You may learn skills: the workspace has a catalogue of "
                f"{skill_count} skills you can draw on and add to your own portfolio."
            ),
            f"Available tools:\n{tools}",
        ]
    )
    history_lines = []
    for m in recent_messages[-20:]:
        who = "User" if m.get("authorType") == "user" else (m.get("authorName") or "Agent")
        txt = _clip_text(str(m.get("text") or ""), 1200)
        if txt.strip():
            history_lines.append(f"- {who}: {txt}")
    others = [a for a in agents if a.get("id") != agent.get("id")]
    user = "\n\n".join(
        [
            f"Room goal: {goal.get('text')}",
            f"Progress so far: {goal.get('progress', 0)}%",
            f"Status: {goal.get('status', 'active')}",
            f"Steps completed: {goal.get('steps', 0)}",
            f"Last step: {goal.get('lastStep') or '(none)'}",
            f"Next step from last time: {goal.get('nextStep') or '(none)'}",
            "Team:\n" + ("\n".join(f"- {a.get('name')} ({a.get('origin', {}).get('role', a.get('role', ''))})" for a in others) if others else "- (you are the only member)"),
            "Recent room history:\n" + ("\n".join(history_lines) if history_lines else "- (empty)"),
            (
                "Take the NEXT concrete step now. Call your tools as needed, then reply with STRICT JSON only:\n"
                '{"summary": string, "progress": 0-100, "next_step": string, "done": boolean, '
                '"tool_actions": [{"tool": "terminal|write_file|edit_file|read_file|list_files|gh|github", "args": {...}}], '
                '"learned_skills": [{"key": string, "label": string, "level": 1-5}]}'
            ),
        ]
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


class GoalWorker:
    """Background loop that advances every active room goal."""

    def __init__(self, store: StateStore, router: Any, skill_catalogue: Optional[List[Dict[str, Any]]] = None) -> None:
        self.store = store
        self.router = router
        self.skill_catalogue = skill_catalogue or []
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()
        self._lock = asyncio.Lock()
        self._running = False
        self.last_run_at: Optional[int] = None
        self.last_error: Optional[str] = None
        self.log: List[Dict[str, Any]] = []

    # ---- lifecycle -------------------------------------------------------

    async def start(self) -> Dict[str, Any]:
        async with self._lock:
            if self._task is not None and not self._task.done():
                return self.status()
            self._stop.clear()
            self._task = asyncio.create_task(self._loop(), name="teamz-goal-worker")
            return self.status()

    async def stop(self) -> Dict[str, Any]:
        async with self._lock:
            self._stop.set()
            task = self._task
            self._task = None
        if task is not None:
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                task.cancel()
            except Exception:
                pass
        self._running = False
        return self.status()

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": settings.goal_enabled,
            "worker_enabled": settings.goal_worker_enabled,
            "running": self._task is not None and not self._task.done(),
            "tick_s": settings.goal_tick_s,
            "last_run_at": self.last_run_at,
            "last_error": self.last_error,
            "max_steps": settings.goal_max_steps,
            "active_goals": self._active_goal_ids(),
        }

    def _active_goal_ids(self) -> List[str]:
        try:
            state = self.store.load()
        except Exception:
            return []
        return [
            cid
            for cid, g in (state.get("goals") or {}).items()
            if isinstance(g, dict) and g.get("active", True) and not g.get("done", False)
        ]

    def _log(self, kind: str, message: str, **extra: Any) -> None:
        entry = {"kind": kind, "message": message, "at": int(time.time() * 1000)}
        entry.update(extra)
        self.log.append(entry)
        if len(self.log) > 200:
            self.log = self.log[-200:]

    # ---- loop ------------------------------------------------------------

    async def _loop(self) -> None:
        self._running = True
        self._log("info", "goal worker started")
        while not self._stop.is_set():
            try:
                await self.tick_all()
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {e}"
                self._log("error", self.last_error)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=max(1.0, settings.goal_tick_s))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
        self._running = False
        self._log("info", "goal worker stopped")

    async def tick_all(self) -> List[Dict[str, Any]]:
        state = self.store.load()
        results: List[Dict[str, Any]] = []
        for cid, goal in list((state.get("goals") or {}).items()):
            if not isinstance(goal, dict):
                continue
            if not goal.get("active", True) or goal.get("done", False):
                continue
            if goal.get("cooldownUntil") and goal["cooldownUntil"] > time.time() * 1000:
                continue
            results.append(await self.tick_conversation(cid))
        return results

    async def tick_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Run exactly one work step for a room. Safe to call by hand."""
        if not settings.goal_enabled:
            return {"ok": False, "conversationId": conversation_id, "error": "goals are disabled"}

        state = self.store.load()
        conversation = next(
            (c for c in (state.get("conversations") or []) if isinstance(c, dict) and c.get("id") == conversation_id),
            None,
        )
        if not conversation:
            return {"ok": False, "conversationId": conversation_id, "error": "room not found"}
        goal = (state.get("goals") or {}).get(conversation_id)
        if not isinstance(goal, dict) or not goal.get("text"):
            return {"ok": False, "conversationId": conversation_id, "error": "no goal set"}
        if goal.get("done"):
            return {"ok": False, "conversationId": conversation_id, "error": "goal already done"}

        members = [
            a
            for a in (state.get("agents") or [])
            if isinstance(a, dict) and a.get("id") in (conversation.get("agentIds") or [])
        ]
        agent = pick_worker_agent(members, goal.get("text") or "")
        if not agent:
            return {"ok": False, "conversationId": conversation_id, "error": "no agent in this room"}

        recent = [
            m
            for m in (state.get("messages", {}).get(conversation_id) or [])
            if isinstance(m, dict) and m.get("status") == "sent" and not m.get("deleted")
        ]
        messages = build_worker_prompt(
            agent,
            conversation,
            goal,
            recent,
            members,
            len(self.skill_catalogue),
        )
        started = time.time()
        from .providers.base import RouteContext

        ctx = RouteContext(
            messages=messages,
            requested_model=agent.get("model"),
            strict_model=False,
            stream=False,
            temperature=0.4,
            metadata={"teamz_worker": True, "conversationId": conversation_id, "agentId": agent.get("id")},
        )
        try:
            result = await asyncio.wait_for(
                self.router.complete(ctx),
                timeout=settings.goal_turn_timeout_s,
            )
        except asyncio.TimeoutError:
            self._record_failure(state, conversation_id, "timed out")
            return {"ok": False, "conversationId": conversation_id, "error": "worker turn timed out"}
        except Exception as e:
            self._record_failure(state, conversation_id, f"{type(e).__name__}: {e}")
            return {"ok": False, "conversationId": conversation_id, "error": str(e)}

        raw = result.text or ""
        parsed = _extract_json_object(raw)
        tool_results: List[Dict[str, Any]] = []
        if parsed and isinstance(parsed.get("tool_actions"), list):
            tool_results = execute_actions(parsed.get("tool_actions"), agent_id=agent.get("id"))

        # --- Award XP for successful tool executions ---
        xp_gained = 0
        for tr in tool_results:
            if tr.get("ok"):
                xp_gained += XP_PER_SUCCESSFUL_TOOL
                # Award XP to relevant skills based on tool used
                tool = tr.get("tool")
                skill_key = self._tool_to_skill_key(tr.get("tool"))
                if skill_key:
                    # Award XP to the agent's skill
                    state = self.store.load()
                    for ag in state.get("agents") or []:
                        if ag.get("id") == agent.get("id"):
                            ag = _add_skill_xp(ag, skill_key, XP_PER_SUCCESSFUL_TOOL)
                    self.store.save(state)

        # Bonus XP for completing a step successfully
        xp_gained += XP_PER_SUCCESSFUL_STEP
        state = self.store.load()
        for ag in state.get("agents") or []:
            if ag.get("id") == agent.get("id"):
                # Add to general XP (could track on a primary skill)
                for skill in ag.get("skills") or []:
                    if skill.get("level", 1) == max(s.get("level", 1) for s in ag.get("skills") or [{"level": 1}]):
                        ag = _add_skill_xp(ag, skill["key"], XP_PER_SUCCESSFUL_STEP)
                        break
        self.store.save(state)

        summary = str(
            (parsed or {}).get("summary")
            or (raw.strip().splitlines()[0] if raw.strip() else f"{agent.get('name')} ran a work step.")
        )
        progress = _clamp_progress((parsed or {}).get("progress"), goal.get("progress", 0))
        done = bool((parsed or {}).get("done")) or progress >= 100
        next_step = str((parsed or {}).get("next_step") or ("" if done else "Continue the next concrete step."))
        learned = (parsed or {}).get("learned_skills") if isinstance((parsed or {}).get("learned_skills"), list) else []

        state = self.store.load()
        goal = (state.setdefault("goals", {}).get(conversation_id) or {})
        goal.update(
            {
                "progress": progress,
                "status": "done" if done else "active",
                "done": done,
                "active": not done,
                "steps": int(goal.get("steps", 0)) + 1,
                "lastStep": summary,
                "nextStep": next_step,
                "updatedAt": int(time.time() * 1000),
                "lastAgentId": agent.get("id"),
            }
        )
        state.setdefault("messages", {}).setdefault(conversation_id, []).append(
            {
                "id": f"m-{int(time.time()*1000)}-{len(state['messages'][conversation_id])}",
                "conversationId": conversation_id,
                "authorType": "agent",
                "authorId": agent.get("id"),
                "authorName": agent.get("name"),
                "text": _compose_step_message(summary, next_step, done, tool_results, agent.get("name")),
                "createdAt": int(time.time() * 1000),
                "status": "sent",
                "kind": "goal-step",
            }
        )
        if isinstance(learned, list) and learned:
            state = _apply_learned_skills(state, agent.get("id"), learned)
        state.setdefault("activity", []).append(
            {
                "id": f"act-{int(time.time()*1000)}",
                "conversationId": conversation_id,
                "agentId": agent.get("id"),
                "agentName": agent.get("name"),
                "kind": "goal-step",
                "text": summary,
                "progress": progress,
                "tools": [t.get("tool") for t in tool_results],
                "at": int(time.time() * 1000),
            }
        )
        state["activity"] = (state.get("activity") or [])[-300:]
        self.store.save(state)

        self.last_run_at = int(time.time() * 1000)
        self._log("step", f"{conversation_id}: {summary}", agent=agent.get("name"), progress=progress, done=done)
        return {
            "ok": True,
            "conversationId": conversation_id,
            "agentId": agent.get("id"),
            "agentName": agent.get("name"),
            "summary": summary,
            "progress": progress,
            "nextStep": next_step,
            "done": done,
            "toolResults": tool_results,
            "elapsedMs": int((time.time() - started) * 1000),
        }

    def _record_failure(self, state: Dict[str, Any], conversation_id: str, error: str) -> None:
        self.last_error = error
        self._log("error", f"{conversation_id}: {error}")
        goal = (state.setdefault("goals", {}).get(conversation_id) or {})
        goal["lastError"] = error
        goal["updatedAt"] = int(time.time() * 1000)
        goal["cooldownUntil"] = int((time.time() + 120) * 1000)
        self.store.save(state)

    # ---- self improvement ------------------------------------------------

    async def self_improve(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Have an agent reflect on its work and rewrite its own prompt/skills."""
        state = self.store.load()
        agents = [a for a in (state.get("agents") or []) if isinstance(a, dict)]
        agent = next((a for a in agents if a.get("id") == agent_id), None) if agent_id else None
        if agent is None:
            agent = next((a for a in agents if a.get("isLead")), None) or (agents[0] if agents else None)
        if not agent:
            return {"ok": False, "error": "no agent to improve"}
        recent = [
            m
            for m in (state.get("messages", {}).get(state.get("activeConversationId") or "") or [])
            if isinstance(m, dict)
        ][-20:]
        system = (
            "You are a self-improvement coach for an autonomous AI worker. "
            "Given the worker's current system prompt, its skills and its recent work, propose concrete "
            "improvements that would make it a better worker: clearer operating rules, better tool habits, "
            "missing skills to learn, and a sharper role definition. Be specific and terse."
        )
        user = (
            f"Agent name: {agent.get('name')}\n"
            f"Role: {(agent.get('origin') or {}).get('role') or agent.get('role') or ''}\n"
            f"Current system prompt:\n{agent.get('systemPrompt') or '(none)'}\n\n"
            f"Current skills: {json.dumps(agent.get('skills') or [], ensure_ascii=False)}\n\n"
            f"Recent work: {json.dumps([str(m.get('text'))[:400] for m in recent], ensure_ascii=False)}\n\n"
            "Return STRICT JSON: {\"systemPrompt\": string, \"skills\": [{\"key\":string,\"label\":string,\"level\":1-5}], "
            "\"notes\": string, \"newSkills\": [{\"key\":string,\"label\":string,\"level\":1-5}]}"
        )
        from .providers.base import RouteContext

        ctx = RouteContext(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            requested_model=agent.get("model"),
            strict_model=False,
            stream=False,
            temperature=0.3,
            metadata={"teamz_self_improve": True, "agentId": agent.get("id")},
        )
        try:
            result = await asyncio.wait_for(self.router.complete(ctx), timeout=settings.goal_turn_timeout_s)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        parsed = _extract_json_object(result.text) or {}
        state = self.store.load()
        agents = state.get("agents") or []
        target = next((a for a in agents if isinstance(a, dict) and a.get("id") == agent.get("id")), None)
        if not target:
            return {"ok": False, "error": "agent disappeared"}
        if isinstance(parsed.get("systemPrompt"), str) and parsed["systemPrompt"].strip():
            target["systemPrompt"] = parsed["systemPrompt"].strip()
        if isinstance(parsed.get("skills"), list):
            target["skills"] = _normalize_skills(parsed["skills"])
        notes = str(parsed.get("notes") or "")
        state.setdefault("activity", []).append(
            {
                "id": f"act-{int(time.time()*1000)}",
                "agentId": target.get("id"),
                "agentName": target.get("name"),
                "kind": "self-improve",
                "text": notes or f"{target.get('name')} reviewed its own setup.",
                "at": int(time.time() * 1000),
            }
        )
        self.store.save(state)
        return {"ok": True, "agentId": target.get("id"), "agentName": target.get("name"), "notes": notes}

    # ---- Skill System: Decay, Certificates, Mentor Sessions ----------------

    async def process_skill_decay(self) -> Dict[str, Any]:
        """Process skill proficiency decay for all agents."""
        if not settings.goal_enabled:
            return {"ok": False, "error": "goals are disabled"}
        
        state = self.store.load()
        agents = state.get("agents") or []
        decayed_count = 0
        
        config = SkillDecayConfig()
        now = time.time() * 1000
        decay_interval_ms = config.decay_interval_hours * 3600 * 1000
        
        for agent in agents:
            if not isinstance(agent, dict):
                continue
            skills = agent.get("skills") or []
            for skill in skills:
                if not isinstance(skill, dict):
                    continue
                if skill.get("level", 1) <= 1:
                    continue  # Don't decay below level 1
                
                last_updated = skill.get("last_updated", 0)
                if now - last_updated > decay_interval_ms:
                    # Apply decay
                    xp_loss = int(skill.get("xp", 0) * 0.01)  # 1% decay
                    skill["xp"] = max(0, skill.get("xp", 0) - xp_loss)
                    skill["level"] = max(1, _level_from_xp(skill.get("xp", 0)))
                    skill["last_updated"] = int(time.time() * 1000)
                    decayed_count += 1
        
        self.store.save(state)
        return {"ok": True, "decayed_skills": decayed_count}

    async def start_mentor_session(
        self,
        mentor_agent_id: str,
        mentee_agent_id: str,
        skill_key: str,
    ) -> Dict[str, Any]:
        """Start a mentoring session between two agents."""
        state = self.store.load()
        agents = {a.get("id"): a for a in (state.get("agents") or []) if isinstance(a, dict)}
        
        mentor = agents.get(mentor_agent_id)
        mentee = agents.get(mentee_agent_id)
        
        if not mentor or not mentee:
            return {"ok": False, "error": "mentor or mentee not found"}
        
        # Check if mentor has the skill at a higher level
        mentor_level = _agent_skill_level(agents.get(mentor_agent_id) or {}, skill_key)
        mentee_level = _agent_skill_level(agents.get(mentee_agent_id) or {}, skill_key)
        
        if mentor_level <= mentee_level:
            return {"ok": False, "error": "mentor must have higher skill level than mentee"}
        
        session = MentorSession(
            id=f"mentor-{uuid.uuid4().hex[:8]}",
            mentor_agent_id=mentor_agent_id,
            mentee_agent_id=mentee_agent_id,
            skill_key=skill_key,
            status="active",
            started_at=int(time.time() * 1000),
        )
        
        state.setdefault("mentor_sessions", []).append(session.model_dump())
        self.store.save(state)
        
        return {"ok": True, "session": session.model_dump()}

    async def complete_mentor_session(
        self,
        session_id: str,
        xp_transferred: int = 50,
    ) -> Dict[str, Any]:
        """Complete a mentoring session and transfer XP to mentee."""
        state = self.store.load()
        sessions = state.get("mentor_sessions") or []
        
        for i, session in enumerate(sessions):
            if session.get("id") == session_id:
                if session.get("status") != "active":
                    return {"ok": False, "error": "session not active"}
                
                session["status"] = "completed"
                session["completed_at"] = int(time.time() * 1000)
                session["xp_transferred"] = xp_transferred
                
                # Award XP to mentee's skill
                state = self.store.load()
                for agent in state.get("agents") or []:
                    if agent.get("id") == session.get("mentee_agent_id"):
                        agent = _add_skill_xp(agent, session["skill_key"], xp_transferred)
                        break
                self.store.save(state)
                return {"ok": True, "xp_transferred": xp_transferred}
        
        return {"ok": False, "error": "session not found"}

    async def issue_skill_certificate(
        self,
        agent_id: str,
        skill_key: str,
    ) -> Dict[str, Any]:
        """Issue a skill certificate when an agent reaches level 5."""
        state = self.store.load()
        agent = next((a for a in (state.get("agents") or []) if a.get("id") == agent_id), None)
        if not agent:
            return {"ok": False, "error": "agent not found"}
        
        skill = next((s for s in (agent.get("skills") or []) if s.get("key") == skill_key), None)
        if not skill:
            return {"ok": False, "error": "agent doesn't have this skill"}
        
        if skill.get("level", 1) < 5:
            return {"ok": False, "error": "skill must be level 5 to earn certificate"}
        
        cert = AgentSkillCertificate(
            id=f"cert-{uuid.uuid4().hex[:12]}",
            agent_id=agent_id,
            skill_key=skill_key,
            skill_label=skill.get("label", skill_key),
            level_achieved=skill.get("level", 5),
            earned_at=int(time.time() * 1000),
            certificate_hash=hashlib.sha256(f"{agent_id}:{skill_key}:{time.time()}".encode()).hexdigest()[:16],
        )
        
        state.setdefault("certificates", []).append(cert.model_dump())
        self.store.save(state)
        
        return {"ok": True, "certificate": cert.model_dump()}

    def get_agent_skills(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed skill information for an agent."""
        state = self.store.load()
        agent = next((a for a in (state.get("agents") or []) if a.get("id") == agent_id), None)
        if not agent:
            return {"ok": False, "error": "agent not found"}
        
        skills = agent.get("skills") or []
        detailed = []
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            xp = skill.get("xp", 0)
            level = skill.get("level", 1)
            detailed.append({
                "key": skill.get("key"),
                "label": skill.get("label"),
                "level": level,
                "xp": xp,
                "xp_to_next": _xp_for_next_level(xp),
                "progress_pct": min(100, int((xp / _xp_for_level(level + 1)) * 100)) if level < 5 else 100,
            })
        
        return {"ok": True, "agent_id": agent_id, "skills": detailed}

    async def create_marketplace_listing(
        self,
        author_agent_id: str,
        skill_key: str,
        skill_label: str,
        description: str,
        category: str,
        price_xp: int,
        min_level: int = 1,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a skill marketplace listing."""
        state = self.store.load()
        author = next((a for a in (state.get("agents") or []) if a.get("id") == author_agent_id), None)
        if not author:
            return {"ok": False, "error": "author agent not found"}
        
        listing = SkillMarketplaceListing(
            id=f"listing-{uuid.uuid4().hex[:8]}",
            author_agent_id=author_agent_id,
            author_agent_name=author.get("name", "Unknown"),
            skill_key=skill_key,
            skill_label=skill_label,
            description=description,
            category=category,
            price_xp=price_xp,
            min_level=min_level,
            tags=tags or [],
            created_at=int(time.time() * 1000),
        )
        
        state.setdefault("marketplace_listings", []).append(listing.model_dump())
        self.store.save(state)
        
        return {"ok": True, "listing": listing.model_dump()}

    def get_marketplace_listings(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get available marketplace listings."""
        state = self.store.load()
        listings = state.get("marketplace_listings") or []
        
        if category:
            listings = [l for l in listings if l.get("category") == category]
        
        return {"ok": True, "listings": listings}


def _normalize_skills(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in raw if isinstance(raw, list) else []:
        if not isinstance(s, dict):
            continue
        key = str(s.get("key") or s.get("id") or s.get("label") or "").strip().lower().replace(" ", "-")
        if not key:
            continue
        try:
            level = int(s.get("level") or 1)
        except (TypeError, ValueError):
            level = 1
        out.append(
            {
                "key": key,
                "label": str(s.get("label") or s.get("name") or key),
                "level": max(1, min(5, level)),
            }
        )
    return out


def _apply_learned_skills(state: Dict[str, Any], agent_id: Optional[str], learned: List[Any]) -> Dict[str, Any]:
    if not agent_id:
        return state
    for agent in state.get("agents") or []:
        if not isinstance(agent, dict) or agent.get("id") != agent_id:
            continue
        skills = list(agent.get("skills") or [])
        for s in learned:
            if not isinstance(s, dict):
                continue
            key = str(s.get("key") or s.get("id") or s.get("label") or "").strip().lower().replace(" ", "-")
            if not key:
                continue
            try:
                level = max(1, min(5, int(s.get("level") or 1)))
            except (TypeError, ValueError):
                level = 1
            label = str(s.get("label") or s.get("name") or key)
            existing = next((x for x in skills if isinstance(x, dict) and x.get("key") == key), None)
            if existing:
                existing["level"] = max(int(existing.get("level") or 1), level)
            else:
                skills.append({"key": key, "label": label, "level": level})
        agent["skills"] = skills
    return state


def _clamp_progress(value: Any, fallback: int) -> int:
    try:
        num = int(round(float(value)))
    except (TypeError, ValueError):
        return fallback
    return max(0, min(100, num))


# --- Phase 6: Multi-Room Orchestration ------------------------------------

    async def create_project_room(
        self,
        name: str,
        description: str,
        template_id: Optional[str] = None,
        parent_room_id: Optional[str] = None,
        agent_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new project room (parent container for child rooms)."""
        state = self.store.load()
        root = Path(settings.files_root).expanduser().resolve()
        
        project = ProjectRoom(
            id=f"proj-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            parent_room_id=parent_room_id,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000),
        )
        
        if template_id:
            template = next((t for t in state.get("room_templates", []) if t.get("id") == template_id), None)
            if template:
                project.default_step_budget = template.get("default_step_budget", 50)
                project.default_tick_s = template.get("default_tick_s", 60.0)
        
        state.setdefault("project_rooms", []).append(project.model_dump())
        self.store.save(state)
        
        # If agent_ids provided, create a main room for the project
        if agent_ids:
            room_name = f"{name} Main"
            main_room = {
                "id": f"room-{uuid.uuid4().hex[:8]}",
                "kind": "channel",
                "name": room_name,
                "agentIds": agent_ids,
                "topic": f"Main coordination room for project: {name}",
                "createdAt": int(time.time() * 1000),
                "projectId": project.id,
            }
            state.setdefault("conversations", []).append(main_room)
            project.child_room_ids.append(main_room["id"])
            self.store.save(state)
        
        return {"ok": True, "project": project.model_dump()}

    async def add_room_to_project(
        self,
        project_id: str,
        room_name: str,
        agent_ids: List[str],
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a child room to a project."""
        state = self.store.load()
        project = next((p for p in (state.get("project_rooms") or []) if p.get("id") == project_id), None)
        if not project:
            return {"ok": False, "error": "project not found"}
        
        room = {
            "id": f"room-{uuid.uuid4().hex[:8]}",
            "kind": "channel",
            "name": room_name,
            "agentIds": agent_ids,
            "topic": topic or f"Room for {room_name}",
            "createdAt": int(time.time() * 1000),
            "projectId": project_id,
        }
        
        state.setdefault("conversations", []).append(room)
        project["child_room_ids"].append(room["id"])
        project["updated_at"] = int(time.time() * 1000)
        self.store.save(state)
        
        return {"ok": True, "room": room}

    async def set_room_dependencies(
        self,
        room_id: str,
        depends_on: List[str],
        dependency_type: str = "blocking",
    ) -> Dict[str, Any]:
        """Set dependencies for a room (rooms that must complete first)."""
        state = self.store.load()
        
        # Find the room (could be a project room or conversation)
        room = next(
            (r for r in (state.get("conversations") or []) if r.get("id") == room_id),
            None,
        )
        if not room:
            room = next(
                (p for p in (state.get("project_rooms") or []) if p.get("id") == room_id),
                None,
            )
        
        if not room:
            return {"ok": False, "error": "room/project not found"}
        
        # Validate dependencies exist
        all_rooms = {r.get("id"): r for r in (state.get("conversations") or [])}
        all_rooms.update({p.get("id"): p for p in (state.get("project_rooms") or [])})
        
        for dep_id in depends_on:
            if dep_id not in all_rooms:
                return {"ok": False, "error": f"dependency {dep_id} not found"}
        
        # Check for circular dependencies
        def has_cycle(start: str, target: str, visited: set) -> bool:
            if start == target:
                return True
            if start in visited:
                return False
            visited.add(start)
            deps = all_rooms.get(start, {}).get("dependencies", [])
            for dep in deps:
                if has_cycle(dep.depends_on[0], target, visited):
                    return True
            return False
        
        for dep_id in depends_on:
            if has_cycle(dep_id, room_id, set()):
                return {"ok": False, "error": f"circular dependency detected with {dep_id}"}
        
        # Set dependencies
        room.setdefault("dependencies", []).clear()
        for dep_id in depends_on:
            room["dependencies"].append(RoomDependency(
                room_id=room_id,
                depends_on=[dep_id],
                dependency_type="blocking",
            ).model_dump())
        
        self.store.save(state)
        return {"ok": True, "dependencies": room["dependencies"]}

    async def check_room_dependencies(
        self,
        room_id: str,
    ) -> Dict[str, Any]:
        """Check if all dependencies for a room are satisfied."""
        state = self.store.load()
        
        all_rooms = {r.get("id"): r for r in (state.get("conversations") or [])}
        all_rooms.update({p.get("id"): p for p in (state.get("project_rooms") or [])})
        
        room = all_rooms.get(room_id)
        if not room:
            return {"ok": False, "error": "room not found", "satisfied": False}
        
        deps = room.get("dependencies", [])
        if not deps:
            return {"ok": True, "satisfied": True, "pending": []}
        
        pending = []
        for dep in deps:
            dep_room = all_rooms.get(dep.depends_on[0])
            if not dep_room:
                pending.append({"room_id": dep.depends_on[0], "status": "missing"})
            elif dep_room.get("status") == "completed":
                continue
            elif dep_room.get("kind") == "channel" and dep_room.get("status") == "active":
                pending.append({"room_id": dep.depends_on[0], "status": "in_progress"})
            else:
                pending.append({"room_id": dep.depends_on[0], "status": dep_room.get("status", "unknown")})
        
        satisfied = len(pending) == 0
        return {"ok": True, "satisfied": satisfied, "pending": pending}

    async def propagate_cross_room_event(
        self,
        event: CrossRoomEvent,
    ) -> Dict[str, Any]:
        """Propagate an event to interested rooms."""
        state = self.store.load()
        
        # Store the event
        state.setdefault("cross_room_events", []).append(event.model_dump())
        
        # Find rooms that should receive this event
        # For now, broadcast to all rooms in the same project
        source_room = None
        for conv in (state.get("conversations") or []):
            if conv.get("id") == event.source_room_id:
                source_room = conv
                break
        
        project_id = source_room.get("projectId") if source_room else None
        target_rooms = []
        
        if project_id:
            project = next(
                (p for p in (state.get("project_rooms") or []) if p.get("id") == project_id),
                None,
            )
            if project:
                for child_id in project.get("child_room_ids", []):
                    child = next((c for c in (state.get("conversations") or []) if c.get("id") == child_id), None)
                    if child and child.get("id") != event.source_room_id:
                        target_rooms.append(child)
        
        # Send event to target rooms via message bus
        for room in target_rooms:
            msg = RoomMessageBusMessage(
                id=f"msg-{uuid.uuid4().hex[:8]}",
                from_room_id=event.source_room_id,
                to_room_id=room.get("id"),
                message_type="cross_room_event",
                payload=event.data,
                priority=1,
            )
            state.setdefault("message_bus", []).append(msg.model_dump())
        
        self.store.save(state)
        return {"ok": True, "propagated_to": len(target_rooms)}

    async def send_cross_room_message(
        self,
        from_room_id: str,
        to_room_id: Optional[str],
        message_type: str,
        payload: Dict[str, Any],
        priority: int = 0,
        requires_response: bool = False,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message on the cross-room message bus."""
        state = self.store.load()
        
        msg = RoomMessageBusMessage(
            id=f"msg-{uuid.uuid4().hex[:8]}",
            from_room_id=from_room_id,
            to_room_id=to_room_id,
            message_type=message_type,
            payload=payload,
            priority=priority,
            requires_response=requires_response,
            correlation_id=correlation_id,
            created_at=int(time.time() * 1000),
        )
        
        state.setdefault("message_bus", []).append(msg.model_dump())
        self.store.save(state)
        
        return {"ok": True, "message_id": msg.id}

    async def get_room_messages(
        self,
        room_id: str,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Dict[str, Any]:
        """Get messages for a room from the message bus."""
        state = self.store.load()
        messages = state.get("message_bus") or []
        
        room_messages = [
            msg for msg in messages
            if msg.get("to_room_id") == room_id or msg.get("to_room_id") is None  # broadcast
        ]
        
        messages.sort(key=lambda m: m.get("created_at", 0), reverse=True)
        messages = messages[:limit]
        
        return {"ok": True, "messages": messages}

    async def store_artifact(
        self,
        name: str,
        description: str,
        content_type: str,
        content: str,
        room_id: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store an artifact in the shared artifact store."""
        state = self.store.load()
        
        artifact = ArtifactStoreEntry(
            id=f"art-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            content_type=content_type,
            content=content,
            size_bytes=len(content.encode()),
            tags=tags or [],
            created_by="system",
            room_id=room_id,
            project_id=project_id,
            created_at=int(time.time() * 1000),
            updated_at=int(time.time() * 1000),
            metadata=metadata or {},
        )
        
        state.setdefault("artifacts", []).append(artifact.model_dump())
        self.store.save(state)
        
        # Emit event
        event = CrossRoomEvent(
            id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="artifact_created",
            source_room_id="system",
            source_agent_id=None,
            data={"artifact_id": artifact.id, "name": name, "type": content_type},
            timestamp=int(time.time() * 1000),
        )
        await self.propagate_cross_room_event(event)
        
        return {"ok": True, "artifact": artifact.model_dump()}

    async def get_artifact(
        self,
        artifact_id: str,
    ) -> Dict[str, Any]:
        """Retrieve an artifact by ID."""
        state = self.store.load()
        artifacts = state.get("artifacts") or []
        
        artifact = next((a for a in artifacts if a.get("id") == artifact_id), None)
        if not artifact:
            return {"ok": False, "error": "artifact not found"}
        
        return {"ok": True, "artifact": artifact}

    async def list_artifacts(
        self,
        room_id: Optional[str] = None,
        project_id: Optional[str] = None,
        content_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List artifacts with filtering."""
        state = self.store.load()
        artifacts = state.get("artifacts") or []
        
        filtered = artifacts
        if room_id:
            filtered = [a for a in filtered if a.get("room_id") == room_id]
        if project_id:
            filtered = [a for a in filtered if a.get("project_id") == project_id]
        if content_type:
            filtered = [a for a in filtered if a.get("content_type") == content_type]
        if tags:
            filtered = [a for a in filtered if any(t in a.get("tags", []) for t in tags)]
        
        filtered.sort(key=lambda a: a.get("created_at", 0), reverse=True)
        return {"ok": True, "artifacts": filtered[:limit], "count": len(filtered)}

    async def get_worker_pool_status(self) -> Dict[str, Any]:
        """Get status of the global worker pool."""
        state = self.store.load()
        pool = state.get("worker_pool") or []
        return {
            "ok": True,
            "pool": pool,
            "available": len([w for w in pool if w.get("status") == "available"]),
            "busy": len([w for w in pool if w.get("status") == "busy"]),
            "offline": len([w for w in pool if w.get("status") == "offline"]),
        }

    async def assign_worker_to_room(
        self,
        agent_id: str,
        room_id: str,
        task: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assign a worker from the pool to a room."""
        state = self.store.load()
        pool = state.get("worker_pool") or []
        
        worker = next((w for w in pool if w.get("agent_id") == agent_id), None)
        if not worker:
            return {"ok": False, "error": "worker not in pool"}
        
        if worker.get("status") != "available":
            return {"ok": False, "error": f"worker is {worker.get('status')}"}
        
        if worker.get("current_tasks", 0) >= worker.get("max_concurrent_tasks", 1):
            return {"ok": False, "error": "worker at max capacity"}
        
        worker["status"] = "busy"
        worker["current_room_id"] = room_id
        worker["current_task"] = task
        worker["current_tasks"] = worker.get("current_tasks", 0) + 1
        worker["assigned_at"] = int(time.time() * 1000)
        
        self.store.save(state)
        return {"ok": True, "worker": worker}

    async def release_worker_from_room(
        self,
        agent_id: str,
    ) -> Dict[str, Any]:
        """Release a worker back to the pool."""
        state = self.store.load()
        pool = state.get("worker_pool") or []
        
        worker = next((w for w in pool if w.get("agent_id") == agent_id), None)
        if not worker:
            return {"ok": False, "error": "worker not in pool"}
        
        worker["status"] = "available"
        worker["current_room_id"] = None
        worker["current_task"] = None
        worker["current_tasks"] = max(0, worker.get("current_tasks", 1) - 1)
        
        self.store.save(state)
        return {"ok": True, "worker": worker}

    async def register_worker(
        self,
        agent_id: str,
        name: str,
        role: str,
        skills: List[str],
        max_concurrent_tasks: int = 1,
    ) -> Dict[str, Any]:
        """Register a worker in the global pool."""
        state = self.store.load()
        pool = state.get("worker_pool") or []
        
        if any(w.get("agent_id") == agent_id for w in pool):
            return {"ok": False, "error": "worker already registered"}
        
        worker = WorkerPoolEntry(
            agent_id=agent_id,
            name=name,
            role=role,
            skills=skills,
            status="available",
            max_concurrent_tasks=max_concurrent_tasks,
            current_tasks=0,
            last_active=int(time.time() * 1000),
        )
        
        state.setdefault("worker_pool", []).append(worker.model_dump())
        self.store.save(state)
        
        return {"ok": True, "worker": worker.model_dump()}

    async def get_room_templates(self) -> Dict[str, Any]:
        """Get available room templates."""
        state = self.store.load()
        templates = state.get("room_templates") or []
        
        # Add default templates if none exist
        if not templates:
            templates = [
                RoomTemplate(
                    id="tmpl-dev",
                    name="Development Team",
                    description="Standard development team with frontend, backend, and DevOps",
                    category="development",
                    agent_roles=["frontend", "backend", "devops", "qa"],
                    required_skills=["typescript", "python", "docker", "testing"],
                    default_topic="Development coordination",
                    default_step_budget=50,
                    default_tick_s=60.0,
                    created_at=int(time.time() * 1000),
                ),
                RoomTemplate(
                    id="tmpl-research",
                    name="Research Team",
                    description="Research team with analysts and ML engineers",
                    category="research",
                    agent_roles=["researcher", "ml-engineer", "data-analyst"],
                    required_skills=["python", "pytorch", "data-analysis", "research"],
                    default_topic="Research coordination",
                    default_step_budget=30,
                    default_tick_s=120.0,
                    created_at=int(time.time() * 1000),
                ),
                RoomTemplate(
                    id="tmpl-ops",
                    name="Operations Team",
                    description="Operations team for deployment and monitoring",
                    category="operations",
                    agent_roles=["sre", "devops", "security"],
                    required_skills=["kubernetes", "aws", "monitoring", "security"],
                    default_topic="Operations coordination",
                    default_step_budget=20,
                    default_tick_s=60.0,
                    created_at=int(time.time() * 1000),
                ),
            ]
            state["room_templates"] = [t.model_dump() for t in templates]
            self.store.save(state)
        
        return {"ok": True, "templates": templates}

    async def create_room_from_template(
        self,
        template_id: str,
        name: str,
        agent_ids: List[str],
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a room from a template."""
        state = self.store.load()
        templates = state.get("room_templates") or []
        
        template = next((t for t in templates if t.get("id") == template_id), None)
        if not template:
            return {"ok": False, "error": "template not found"}
        
        room = {
            "id": f"room-{uuid.uuid4().hex[:8]}",
            "kind": "channel",
            "name": name,
            "agentIds": agent_ids,
            "topic": template.get("default_topic", ""),
            "createdAt": int(time.time() * 1000),
            "templateId": template_id,
            "stepBudget": template.get("default_step_budget", 50),
            "tickInterval": template.get("default_tick_s", 60.0),
        }
        
        if project_id:
            room["projectId"] = project_id
            project = next(
                (p for p in (state.get("project_rooms") or []) if p.get("id") == project_id),
                None,
            )
            if project:
                project["child_room_ids"].append(room["id"])
        
        state.setdefault("conversations", []).append(room)
        self.store.save(state)
        
        return {"ok": True, "room": room}


def _compose_step_message(
    summary: str,
    next_step: str,
    done: bool,
    tool_results: List[Dict[str, Any]],
    agent_name: str,
) -> str:
    lines = [f"**{agent_name} · work step**", "", summary]
    if tool_results:
        lines += ["", "**Actions:**"]
        for tr in tool_results:
            tool = tr.get("tool")
            if tr.get("ok"):
                lines.append(f"- `{tool}` ✓")
            else:
                lines.append(f"- `{tool}` ✗ {tr.get('error')}")
    if done:
        lines += ["", "✅ Goal complete."]
    elif next_step:
        lines += ["", f"Next: {next_step}"]
    return "\n".join(lines)
