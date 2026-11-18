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
import uuid
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
    AlertEvent,
    AlertRule,
    AuditLogEntry,
    CostBudget,
    ObservabilityConfig,
    ReplaySnapshot,
    TelemetrySpan,
    TelemetryTrace,
    TimelineEvent,
    TokenUsageRecord,
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
                "You may delegate and orchestrate: create agents/channels, invite members, post messages to other rooms/agents, and set goals for rooms so work continues autonomously until stopped. "
                "When delegating, give clear instructions and assign work to the right agents/channels."
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
                "Take the NEXT concrete step now. Use tools/runtime actions as needed, then reply with STRICT JSON only:\n"
                '{"summary": string, "progress": 0-100, "next_step": string, "done": boolean, '
                '"tool_actions": [{"tool": "terminal|write_file|edit_file|read_file|list_files|gh|github|run_tests|...", "args": {...}}], '
                '"runtime_actions": [{"type": "create_channel|create_agent|update_agent|invite_agent_to_channel|update_channel_members|rename_channel|send_message|set_goal|delete_channel|delete_agent", "...": "..."}], '
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
            try:
                tool_results = execute_actions(parsed.get("tool_actions"), agent_id=agent.get("id"))
            except Exception as e:
                tool_results = [{"ok": False, "tool": "execute_actions", "error": str(e)}]

        runtime_actions_raw = []
        if isinstance(parsed, dict):
            for k in ("runtime_actions", "teamz_actions", "actions"):
                v = parsed.get(k)
                if isinstance(v, list):
                    runtime_actions_raw = v
                    break
        runtime_actions = _normalize_runtime_actions(runtime_actions_raw)

        summary = str(
            (parsed or {}).get("summary")
            or (raw.strip().splitlines()[0] if raw.strip() else f"{agent.get('name')} ran a work step.")
        )
        progress = _clamp_progress((parsed or {}).get("progress"), goal.get("progress", 0))
        done = bool((parsed or {}).get("done")) or progress >= 100
        next_step = str((parsed or {}).get("next_step") or ("" if done else "Continue the next concrete step."))
        learned = (parsed or {}).get("learned_skills") if isinstance((parsed or {}).get("learned_skills"), list) else []

        state = self.store.load()

        # Apply runtime/delegation actions (workspace orchestration) on current state
        runtime_results: List[Dict[str, Any]] = []
        if runtime_actions:
            try:
                runtime_results = _apply_worker_runtime_actions(
                    state,
                    runtime_actions,
                    current_conversation_id=conversation_id,
                    actor=agent,
                )
            except Exception as e:
                runtime_results = [{"ok": False, "type": "runtime_actions", "error": str(e)}]

        # --- Award XP for successful tool executions and step ---
        for tr in tool_results:
            if tr.get("ok"):
                skill_key = self._tool_to_skill_key(tr.get("tool"))
                if skill_key:
                    for ag in state.get("agents") or []:
                        if isinstance(ag, dict) and ag.get("id") == agent.get("id"):
                            _add_skill_xp(ag, skill_key, XP_PER_SUCCESSFUL_TOOL)
                            break
        # Bonus XP for completing a step
        for ag in state.get("agents") or []:
            if isinstance(ag, dict) and ag.get("id") == agent.get("id"):
                skills = [s for s in (ag.get("skills") or []) if isinstance(s, dict)]
                if skills:
                    top = max(skills, key=lambda s: int(s.get("level", 1) or 1))
                    _add_skill_xp(ag, str(top.get("key") or "general"), XP_PER_SUCCESSFUL_STEP)
                break

        goal_state = (state.setdefault("goals", {}).get(conversation_id) or {})
        goal_state.update(
            {
                "text": goal_state.get("text") or goal.get("text") or "",
                "progress": progress,
                "status": "done" if done else "active",
                "done": done,
                "active": not done,
                "steps": int(goal_state.get("steps", goal.get("steps", 0)) or 0) + 1,
                "lastStep": summary,
                "nextStep": next_step,
                "updatedAt": int(time.time() * 1000),
                "lastAgentId": agent.get("id"),
                "lastError": None,
                "cooldownUntil": None,
            }
        )
        state.setdefault("goals", {})[conversation_id] = goal_state

        msg_text = _compose_step_message(summary, next_step, done, tool_results, agent.get("name"))
        if runtime_results:
            ok_rt = sum(1 for r in runtime_results if r.get("ok"))
            fail_rt = len(runtime_results) - ok_rt
            rt_lines = [f"Runtime actions: {ok_rt} ok, {fail_rt} failed"]
            for r in runtime_results[:10]:
                mark = "✓" if r.get("ok") else "✗"
                detail = r.get("name") or r.get("id") or r.get("error") or r.get("type") or ""
                rt_lines.append(f"- {mark} {r.get('type')}: {detail}")
            msg_text = msg_text.rstrip() + "\n\n" + "\n".join(rt_lines)

        bucket = state.setdefault("messages", {}).setdefault(conversation_id, [])
        bucket.append(
            {
                "id": f"m-{int(time.time()*1000)}-{len(bucket)}",
                "conversationId": conversation_id,
                "authorType": "agent",
                "authorId": agent.get("id"),
                "authorName": agent.get("name"),
                "text": msg_text,
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
                "runtime_actions": [r.get("type") for r in runtime_results if r.get("ok")],
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
            "runtimeResults": runtime_results,
            "elapsedMs": int((time.time() - started) * 1000),
        }

    def _tool_to_skill_key(self, tool: Any) -> Optional[str]:
        t = str(tool or "").strip().lower()
        if not t:
            return None
        mapping = {
            "terminal": "terminal",
            "run_tests": "testing",
            "write_file": "coding",
            "edit_file": "coding",
            "read_file": "code-reading",
            "list_files": "filesystem",
            "gh": "github",
            "github": "github",
        }
        return mapping.get(t)

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


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _resolve_agent_ref(state: Dict[str, Any], ref: Any) -> Optional[Dict[str, Any]]:
    if not ref:
        return None
    if isinstance(ref, dict):
        ref = ref.get("agentId") or ref.get("agent_id") or ref.get("id") or ref.get("name") or ref.get("agentName")
    ref_s = str(ref).strip()
    if not ref_s:
        return None
    for a in state.get("agents") or []:
        if not isinstance(a, dict):
            continue
        if str(a.get("id") or "") == ref_s:
            return a
    ref_l = ref_s.lower()
    for a in state.get("agents") or []:
        if not isinstance(a, dict):
            continue
        if str(a.get("name") or "").strip().lower() == ref_l:
            return a
    return None


def _resolve_conversation_ref(state: Dict[str, Any], action: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for key in ("conversationId", "conversation_id", "channelId", "channel_id", "id"):
        v = action.get(key)
        if v:
            for c in state.get("conversations") or []:
                if isinstance(c, dict) and str(c.get("id") or "") == str(v):
                    return c
    for key in ("nameMatch", "channelName", "name"):
        v = action.get(key)
        if v:
            vl = str(v).strip().lower()
            for c in state.get("conversations") or []:
                if isinstance(c, dict) and str(c.get("name") or "").strip().lower() == vl:
                    return c
    # direct chat target by agent name/id
    for key in ("agentName", "agentId", "agent"):
        a = _resolve_agent_ref(state, action.get(key))
        if a:
            for c in state.get("conversations") or []:
                if isinstance(c, dict) and c.get("kind") == "direct" and (c.get("agentIds") or [None])[0] == a.get("id"):
                    return c
    return None


def _ensure_messages_bucket(state: Dict[str, Any], conversation_id: str) -> List[Dict[str, Any]]:
    msgs = state.setdefault("messages", {})
    if not isinstance(msgs.get(conversation_id), list):
        msgs[conversation_id] = []
    return msgs[conversation_id]


def _normalize_runtime_actions(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        action = dict(item)
        if "type" not in action and "tool" in action:
            action["type"] = action.get("tool")
        if "type" not in action and "name" in action:
            action["type"] = action.get("name")
        if action.get("type"):
            action["type"] = str(action["type"]).strip().lower()
            out.append(action)
    return out


def _apply_worker_runtime_actions(
    state: Dict[str, Any],
    actions: List[Dict[str, Any]],
    *,
    current_conversation_id: Optional[str] = None,
    actor: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    now_ms = int(time.time() * 1000)
    for action in actions:
        if not isinstance(action, dict):
            continue
        t = str(action.get("type") or action.get("tool") or action.get("name") or "").strip().lower()
        try:
            if t == "create_agent":
                name = str(action.get("name") or "").strip()
                if not name:
                    results.append({"ok": False, "type": t, "error": "missing name"})
                    continue
                agent = {
                    "id": _uid("agent"),
                    "name": name,
                    "status": "online",
                    "createdAt": now_ms,
                    "emoji": action.get("emoji") or "🤖",
                    "accent": action.get("accent") or "#6b7280",
                    "systemPrompt": str(action.get("systemPrompt") or action.get("system_prompt") or f"You are {name}, a helpful AI agent.").strip(),
                    "model": action.get("model"),
                    "skills": _normalize_skills(action.get("skills") or []),
                    "isLead": bool(action.get("isLead") or action.get("lead")),
                    "origin": {"role": str(action.get("role") or "").strip()} if action.get("role") else {},
                }
                state.setdefault("agents", []).append(agent)
                # optional direct chat
                direct = {
                    "id": _uid("conv"),
                    "kind": "direct",
                    "name": agent["name"],
                    "agentIds": [agent["id"]],
                    "createdAt": now_ms,
                }
                state.setdefault("conversations", []).insert(0, direct)
                _ensure_messages_bucket(state, direct["id"])
                # optional add to channel
                target_conv = _resolve_conversation_ref(state, action)
                if target_conv and target_conv.get("kind") == "channel":
                    ids = list(target_conv.get("agentIds") or [])
                    if agent["id"] not in ids:
                        ids.append(agent["id"])
                        target_conv["agentIds"] = ids
                results.append({"ok": True, "type": t, "id": agent["id"], "name": agent["name"]})
            elif t == "create_channel":
                name = str(action.get("name") or "").strip() or "New Channel"
                agent_ids: List[str] = []
                for x in (action.get("agentIds") or []):
                    a = _resolve_agent_ref(state, x)
                    if a and a.get("id") and a["id"] not in agent_ids:
                        agent_ids.append(a["id"])
                for x in (action.get("agentNames") or []):
                    a = _resolve_agent_ref(state, x)
                    if a and a.get("id") and a["id"] not in agent_ids:
                        agent_ids.append(a["id"])
                if not agent_ids and actor and actor.get("id"):
                    agent_ids.append(actor["id"])
                conv = {
                    "id": _uid("conv"),
                    "kind": "channel",
                    "name": name,
                    "agentIds": agent_ids,
                    "topic": str(action.get("topic") or "").strip() or None,
                    "createdAt": now_ms,
                }
                state.setdefault("conversations", []).insert(0, conv)
                _ensure_messages_bucket(state, conv["id"])
                results.append({"ok": True, "type": t, "id": conv["id"], "name": conv["name"]})
            elif t in {"update_agent", "program_agent"}:
                a = _resolve_agent_ref(state, action.get("agentId") or action.get("agentName") or action.get("agent"))
                if not a:
                    results.append({"ok": False, "type": t, "error": "agent not found"})
                    continue
                if action.get("name"):
                    a["name"] = str(action["name"]).strip() or a.get("name")
                if action.get("systemPrompt") or action.get("system_prompt"):
                    a["systemPrompt"] = str(action.get("systemPrompt") or action.get("system_prompt"))
                if action.get("model") is not None:
                    a["model"] = action.get("model")
                if isinstance(action.get("skills"), list):
                    a["skills"] = _normalize_skills(action.get("skills"))
                if isinstance(action.get("addSkills"), list):
                    existing = list(a.get("skills") or [])
                    for sk in _normalize_skills(action.get("addSkills")):
                        found = next((x for x in existing if x.get("key") == sk.get("key")), None)
                        if found:
                            found["level"] = max(int(found.get("level") or 1), int(sk.get("level") or 1))
                        else:
                            existing.append(sk)
                    a["skills"] = existing
                if "isLead" in action or "lead" in action:
                    a["isLead"] = bool(action.get("isLead") or action.get("lead"))
                if action.get("status"):
                    a["status"] = str(action.get("status"))
                results.append({"ok": True, "type": t, "id": a.get("id")})
            elif t in {"invite_agent_to_channel", "invite_agent", "add_agent_to_channel", "update_channel_members", "set_channel_members"}:
                conv = _resolve_conversation_ref(state, action)
                if not conv or conv.get("kind") != "channel":
                    results.append({"ok": False, "type": t, "error": "channel not found"})
                    continue
                ids = set(str(x) for x in (conv.get("agentIds") or []) if x)
                # full set if provided
                if isinstance(action.get("agentIds"), list) or isinstance(action.get("agentNames"), list):
                    ids = set()
                    for x in (action.get("agentIds") or []):
                        a = _resolve_agent_ref(state, x)
                        if a and a.get("id"):
                            ids.add(str(a["id"]))
                    for x in (action.get("agentNames") or []):
                        a = _resolve_agent_ref(state, x)
                        if a and a.get("id"):
                            ids.add(str(a["id"]))
                for key in ("addAgentIds", "addAgentNames", "agentId", "agentName", "agent"):
                    vals = action.get(key)
                    if vals is None:
                        continue
                    if not isinstance(vals, list):
                        vals = [vals]
                    for x in vals:
                        a = _resolve_agent_ref(state, x)
                        if a and a.get("id"):
                            ids.add(str(a["id"]))
                for key in ("removeAgentIds", "removeAgentNames"):
                    for x in (action.get(key) or []):
                        a = _resolve_agent_ref(state, x)
                        if a and a.get("id"):
                            ids.discard(str(a["id"]))
                conv["agentIds"] = list(ids)
                results.append({"ok": True, "type": t, "id": conv.get("id"), "agentIds": conv["agentIds"]})
            elif t in {"rename_channel", "update_channel"}:
                conv = _resolve_conversation_ref(state, action)
                if not conv:
                    results.append({"ok": False, "type": t, "error": "channel not found"})
                    continue
                if action.get("name") or action.get("newName"):
                    conv["name"] = str(action.get("name") or action.get("newName")).strip() or conv.get("name")
                if "topic" in action:
                    conv["topic"] = str(action.get("topic") or "").strip() or None
                results.append({"ok": True, "type": t, "id": conv.get("id")})
            elif t in {"delete_channel", "delete_conversation"}:
                conv = _resolve_conversation_ref(state, action)
                if not conv:
                    results.append({"ok": False, "type": t, "error": "channel not found"})
                    continue
                if conv.get("kind") == "direct":
                    results.append({"ok": False, "type": t, "error": "cannot delete direct chat"})
                    continue
                cid = conv.get("id")
                state["conversations"] = [c for c in (state.get("conversations") or []) if not (isinstance(c, dict) and c.get("id") == cid)]
                (state.get("messages") or {}).pop(cid, None)
                (state.get("goals") or {}).pop(cid, None)
                if state.get("activeConversationId") == cid:
                    convs = state.get("conversations") or []
                    state["activeConversationId"] = convs[0]["id"] if convs else None
                results.append({"ok": True, "type": t, "id": cid})
            elif t == "delete_agent":
                a = _resolve_agent_ref(state, action.get("agentId") or action.get("agentName") or action.get("agent"))
                if not a:
                    results.append({"ok": False, "type": t, "error": "agent not found"})
                    continue
                aid = a.get("id")
                state["agents"] = [x for x in (state.get("agents") or []) if not (isinstance(x, dict) and x.get("id") == aid)]
                new_convs = []
                for c in (state.get("conversations") or []):
                    if not isinstance(c, dict):
                        continue
                    if c.get("kind") == "direct" and (c.get("agentIds") or [None])[0] == aid:
                        (state.get("messages") or {}).pop(c.get("id"), None)
                        continue
                    if c.get("kind") == "channel":
                        c["agentIds"] = [x for x in (c.get("agentIds") or []) if x != aid]
                    new_convs.append(c)
                state["conversations"] = new_convs
                results.append({"ok": True, "type": t, "id": aid})
            elif t in {"send_message", "delegate", "post_message"}:
                conv = _resolve_conversation_ref(state, action)
                # fallback: create/find direct chat by target agent
                if not conv:
                    target_a = _resolve_agent_ref(state, action.get("agentName") or action.get("agent") or action.get("to") or action.get("toAgent"))
                    if target_a:
                        for c in state.get("conversations") or []:
                            if isinstance(c, dict) and c.get("kind") == "direct" and (c.get("agentIds") or [None])[0] == target_a.get("id"):
                                conv = c
                                break
                        if not conv:
                            conv = {
                                "id": _uid("conv"),
                                "kind": "direct",
                                "name": target_a.get("name") or "Chat",
                                "agentIds": [target_a.get("id")],
                                "createdAt": now_ms,
                            }
                            state.setdefault("conversations", []).insert(0, conv)
                            _ensure_messages_bucket(state, conv["id"])
                if not conv:
                    # default to current room if available
                    if current_conversation_id:
                        conv = next((c for c in (state.get("conversations") or []) if isinstance(c, dict) and c.get("id") == current_conversation_id), None)
                if not conv:
                    results.append({"ok": False, "type": t, "error": "conversation not found"})
                    continue
                text = str(action.get("text") or action.get("message") or action.get("content") or "").strip()
                if not text:
                    results.append({"ok": False, "type": t, "error": "missing text"})
                    continue
                directed = []
                for key in ("directedAgentIds", "directedAgentNames", "mentions"):
                    for x in (action.get(key) or []):
                        a = _resolve_agent_ref(state, x)
                        if a and a.get("id"):
                            directed.append(a["id"])
                author_id = actor.get("id") if actor else None
                msg = {
                    "id": _uid("m"),
                    "conversationId": conv.get("id"),
                    "authorType": "agent" if author_id else "user",
                    "authorId": author_id,
                    "authorName": actor.get("name") if actor else None,
                    "text": text,
                    "createdAt": now_ms,
                    "status": "sent",
                }
                if directed:
                    msg["mentions"] = directed
                    msg["directed"] = True
                _ensure_messages_bucket(state, conv["id"]).append(msg)
                results.append({"ok": True, "type": t, "id": conv.get("id")})
            elif t in {"set_goal", "create_goal", "update_goal"}:
                conv = _resolve_conversation_ref(state, action) or (next((c for c in (state.get("conversations") or []) if isinstance(c, dict) and c.get("id") == current_conversation_id), None) if current_conversation_id else None)
                if not conv:
                    results.append({"ok": False, "type": t, "error": "conversation not found"})
                    continue
                cid = conv.get("id")
                goals = state.setdefault("goals", {})
                text = str(action.get("text") or action.get("goal") or action.get("objective") or "").strip()
                active = action.get("active")
                if active is None:
                    active = True
                if not text and t == "set_goal":
                    goals.pop(cid, None)
                    results.append({"ok": True, "type": t, "id": cid, "cleared": True})
                    continue
                existing = goals.get(cid) or {}
                goals[cid] = {
                    "text": text or existing.get("text", ""),
                    "active": bool(active),
                    "done": bool(existing.get("done")) if existing else False,
                    "status": "active" if bool(active) else existing.get("status", "paused"),
                    "progress": int(existing.get("progress", 0) or 0),
                    "steps": int(existing.get("steps", 0) or 0),
                    "lastStep": existing.get("lastStep"),
                    "nextStep": existing.get("nextStep"),
                    "lastError": None,
                    "lastAgentId": existing.get("lastAgentId"),
                    "createdAt": int(existing.get("createdAt") or now_ms),
                    "updatedAt": now_ms,
                    "cooldownUntil": None,
                }
                results.append({"ok": True, "type": t, "id": cid})
            elif t == "open_direct_chat":
                a = _resolve_agent_ref(state, action.get("agentId") or action.get("agentName") or action.get("agent"))
                if not a:
                    results.append({"ok": False, "type": t, "error": "agent not found"})
                    continue
                conv = None
                for c in state.get("conversations") or []:
                    if isinstance(c, dict) and c.get("kind") == "direct" and (c.get("agentIds") or [None])[0] == a.get("id"):
                        conv = c
                        break
                if not conv:
                    conv = {
                        "id": _uid("conv"),
                        "kind": "direct",
                        "name": a.get("name") or "Chat",
                        "agentIds": [a.get("id")],
                        "createdAt": now_ms,
                    }
                    state.setdefault("conversations", []).insert(0, conv)
                    _ensure_messages_bucket(state, conv["id"])
                state["activeConversationId"] = conv.get("id")
                results.append({"ok": True, "type": t, "id": conv.get("id")})
            else:
                # ignore unknown runtime action types here (some are frontend-only concepts)
                results.append({"ok": False, "type": t or "unknown", "error": "unsupported runtime action"})
        except Exception as e:
            results.append({"ok": False, "type": t, "error": str(e)})
    return results


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


# --- Phase 8: Observability & Debugging ------------------------------------

    def _sign_audit_entry(self, entry: AuditLogEntry) -> str:
        """Sign an audit log entry for immutability."""
        if not settings.observability.audit_log_signing_key:
            return "unsigned"
        import hmac
        data = f"{entry.id}:{entry.timestamp}:{entry.actor_id}:{entry.action}:{entry.resource_type}:{entry.resource_id}"
        return hmac.new(
            settings.observability.audit_log_signing_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    def _create_audit_log(
        self,
        actor_id: str,
        actor_type: str,
        action: str,
        resource_type: str,
        resource_id: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """Create and persist an audit log entry."""
        entry = AuditLogEntry(
            id=f"audit-{uuid.uuid4().hex[:12]}",
            timestamp=int(time.time() * 1000),
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before=before,
            after=after,
            signature="",
            metadata=metadata or {},
        )
        entry.signature = self._sign_audit_entry(entry)
        
        state = self.store.load()
        state.setdefault("audit_log", []).append(entry.model_dump())
        self.store.save(state)
        return entry

    def _start_span(
        self,
        trace_id: str,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        room_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TelemetrySpan:
        """Start a new telemetry span."""
        span_id = f"span-{uuid.uuid4().hex[:12]}"
        span = TelemetrySpan(
            id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=int(time.time() * 1_000_000),
            tags=tags or {},
            attributes=attributes or {},
        )
        
        state = self.store.load()
        state.setdefault("telemetry_spans", []).append(span.model_dump())
        self.store.save(state)
        return span

    def _end_span(
        self,
        span_id: str,
        status: Literal["ok", "error", "cancelled"] = "ok",
        error_message: Optional[str] = None,
    ) -> Optional[TelemetrySpan]:
        """End a telemetry span."""
        state = self.store.load()
        spans = state.get("telemetry_spans", [])
        
        for i, span in enumerate(spans):
            if span.get("id") == span_id:
                end_time = int(time.time() * 1_000_000)
                span["end_time"] = end_time
                span["duration_ms"] = span["end_time"] - span["start_time"]
                span["status"] = status
                if error_message:
                    span["error_message"] = error_message
                spans[i] = span
                self.store.save(state)
                return TelemetrySpan(**span)
        return None

    def _record_token_usage(
        self,
        room_id: str,
        agent_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        span_id: Optional[str] = None,
    ) -> TokenUsageRecord:
        """Record token usage for cost tracking."""
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = (prompt_tokens * 0.000015) + (completion_tokens * 0.00006)  # rough estimate
        
        record = TokenUsageRecord(
            id=f"token-{uuid.uuid4().hex[:12]}",
            room_id=room_id,
            agent_id=agent_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost_usd,
            timestamp=int(time.time() * 1000),
            span_id=span_id,
        )
        
        state = self.store.load()
        state.setdefault("token_usage", []).append(record.model_dump())
        
        # Update cost budget
        budgets = state.get("cost_budgets", [])
        for budget in budgets:
            if budget.get("scope") == "room" and budget.get("scope_id") == room_id:
                budget["spent_usd"] = budget.get("spent_usd", 0) + cost_usd
        
        self.store.save(state)
        return TokenUsageRecord(**record.model_dump())

    # --- Public Observability API Methods ---

    async def start_trace(
        self,
        operation_name: str,
        room_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> TelemetryTrace:
        """Start a new distributed trace."""
        trace_id = f"trace-{uuid.uuid4().hex[:16]}"
        root_span = self._start_span(
            trace_id=trace_id,
            operation_name=operation_name,
            room_id=room_id,
            goal_id=goal_id,
            agent_id=agent_id,
            tags={"type": "root"},
        )
        
        trace = TelemetryTrace(
            trace_id=trace_id,
            root_span_id=root_span.id,
            spans=[root_span],
            start_time=root_span.start_time,
            room_id=room_id,
            goal_id=goal_id,
            agent_id=agent_id,
        )
        
        state = self.store.load()
        state.setdefault("telemetry_traces", []).append(trace.model_dump())
        self.store.save(state)
        
        return trace

    async def end_trace(
        self,
        trace_id: str,
        status: Literal["ok", "error", "cancelled"] = "ok",
    ) -> Optional[TelemetryTrace]:
        """End a distributed trace."""
        state = self.store.load()
        traces = state.get("telemetry_traces", [])
        
        for i, trace in enumerate(traces):
            if trace.get("trace_id") == trace_id:
                end_time = int(time.time() * 1_000_000)
                trace["end_time"] = end_time
                trace["status"] = status
                traces[i] = trace
                self.store.save(state)
                return TelemetryTrace(**trace)
        return None

    async def get_trace(self, trace_id: str) -> Optional[TelemetryTrace]:
        """Get a trace by ID."""
        state = self.store.load()
        traces = state.get("telemetry_traces", [])
        for trace in traces:
            if trace.get("trace_id") == trace_id:
                return TelemetryTrace(**trace)
        return None

    async def query_traces(
        self,
        room_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TelemetryTrace]:
        """Query traces with filters."""
        state = self.store.load()
        traces = state.get("telemetry_traces", [])
        
        filtered = []
        for trace in traces:
            if room_id and trace.get("room_id") != room_id:
                continue
            if goal_id and trace.get("goal_id") != goal_id:
                continue
            if agent_id and trace.get("agent_id") != agent_id:
                continue
            if start_time and trace.get("start_time", 0) < start_time:
                continue
            if end_time and trace.get("end_time", 0) > end_time:
                continue
            filtered.append(TelemetryTrace(**trace))
        
        filtered.sort(key=lambda t: t.start_time, reverse=True)
        return filtered[offset:offset + limit]

    async def get_token_usage(
        self,
        room_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TokenUsageRecord]:
        """Get token usage records with filters."""
        state = self.store.load()
        records = state.get("token_usage", [])
        
        filtered = []
        for record in records:
            if room_id and record.get("room_id") != room_id:
                continue
            if agent_id and record.get("agent_id") != agent_id:
                continue
            if start_time and record.get("timestamp", 0) < start_time:
                continue
            if end_time and record.get("timestamp", 0) > end_time:
                continue
            filtered.append(TokenUsageRecord(**record))
        
        filtered.sort(key=lambda r: r.timestamp, reverse=True)
        return filtered[offset:offset + limit]

    async def get_cost_budget(self, scope: str, scope_id: str) -> Optional[CostBudget]:
        """Get cost budget for a scope."""
        state = self.store.load()
        budgets = state.get("cost_budgets", [])
        
        for budget in budgets:
            if budget.get("scope") == scope and budget.get("scope_id") == scope_id:
                return CostBudget(**budget)
        return None

    async def create_cost_budget(
        self,
        scope: str,
        scope_id: str,
        budget_usd: float,
        period_start: int,
        period_end: int,
        alert_threshold_pct: float = 80.0,
        hard_stop: bool = False,
    ) -> CostBudget:
        """Create a cost budget."""
        budget = CostBudget(
            id=f"budget-{uuid.uuid4().hex[:12]}",
            scope=scope,
            scope_id=scope_id,
            budget_usd=budget_usd,
            period_start=period_start,
            period_end=period_end,
            alert_threshold_pct=alert_threshold_pct,
            hard_stop=hard_stop,
        )
        
        state = self.store.load()
        state.setdefault("cost_budgets", []).append(budget.model_dump())
        self.store.save(state)
        return budget

    async def check_cost_budgets(self) -> List[Dict[str, Any]]:
        """Check all cost budgets and trigger alerts if needed."""
        state = self.store.load()
        budgets = state.get("cost_budgets", [])
        alerts = []
        
        for budget in budgets:
            pct = (budget.get("spent_usd", 0) / budget["budget_usd"] * 100) if budget["budget_usd"] > 0 else 0
            if pct >= budget.get("alert_threshold_pct", 80):
                self._create_audit_log(
                    actor_id="system",
                    actor_type="system",
                    action="cost_budget_alert",
                    resource_type="cost_budget",
                    resource_id=budget["id"],
                    metadata={"budget_id": budget["id"], "spent_pct": pct},
                )
                alerts.append({
                    "budget_id": budget["id"],
                    "scope": budget["scope"],
                    "scope_id": budget["scope_id"],
                    "spent_pct": pct,
                    "budget_usd": budget["budget_usd"],
                    "spent_usd": budget.get("spent_usd", 0),
                })
        
        return alerts

    async def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Create an alert rule."""
        if not rule.id:
            rule.id = f"alert-{uuid.uuid4().hex[:12]}"
        
        state = self.store.load()
        state.setdefault("alert_rules", []).append(rule.model_dump())
        self.store.save(state)
        return rule

    async def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        state = self.store.load()
        return [AlertRule(**r) for r in state.get("alert_rules", [])]

    async def check_alerts(self) -> List[AlertEvent]:
        """Check all alert rules and trigger alerts."""
        state = self.store.load()
        rules = state.get("alert_rules", [])
        triggered = []
        
        for rule in rules:
            if not rule.get("enabled", True):
                continue
            
            # Check cooldown
            last_alert = next(
                (a for a in state.get("alerts", []) if a.get("rule_id") == rule.get("id")),
                None
            )
            if last_alert:
                cooldown = rule.get("cooldown_seconds", 300)
                if time.time() * 1000 - last_alert.get("triggered_at", 0) < cooldown * 1000:
                    continue
            
            # Evaluate condition (simplified - in production use a proper expression evaluator)
            triggered = False
            message = ""
            if "goal_stalled" in rule.get("condition", ""):
                state = self.store.load()
                goals = state.get("goals", {})
                for goal in goals.values():
                    if goal.get("active") and not goal.get("done"):
                        if goal.get("lastStep") and time.time() * 1000 - goal.get("updatedAt", 0) > 300000:
                            triggered = True
                            message = f"Goal {goal.get('id')} stalled for >5 minutes"
                            break
            elif "error_rate" in rule.get("condition", ""):
                # Simplified check
                pass
            elif "cost" in rule.get("condition", ""):
                alerts = await self.check_cost_budgets()
                if alerts:
                    triggered = True
                    message = f"Cost budget exceeded: {len(alerts)} budgets over threshold"
            
            if triggered:
                alert = AlertEvent(
                    id=f"alert-{uuid.uuid4().hex[:12]}",
                    rule_id=rule["id"],
                    message=message,
                    severity=rule.get("severity", "warning"),
                    triggered_at=int(time.time() * 1000),
                )
                state.setdefault("alerts", []).append(alert.model_dump())
                self.store.save(state)
                triggered.append(alert)
        
        return triggered

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        """Acknowledge an alert."""
        state = self.store.load()
        alerts = state.get("alerts", [])
        
        for alert in alerts:
            if alert.get("id") == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = acknowledged_by
                alert["acknowledged_at"] = int(time.time() * 1000)
                self.store.save(state)
                return {"ok": True, "alert": alert}
        
        return {"ok": False, "error": "alert not found"}

    async def get_alerts(
        self,
        room_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50,
    ) -> List[AlertEvent]:
        """Get alerts with filters."""
        state = self.store.load()
        alerts = state.get("alerts", [])
        
        filtered = []
        for alert in alerts:
            if room_id and alert.get("room_id") != room_id:
                continue
            if severity and alert.get("severity") != severity:
                continue
            if acknowledged is not None and alert.get("acknowledged") != acknowledged:
                continue
            filtered.append(AlertEvent(**alert))
        
        filtered.sort(key=lambda a: a.triggered_at, reverse=True)
        return filtered[:limit]

    async def get_audit_log(
        self,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """Query audit log with filters."""
        state = self.store.load()
        logs = state.get("audit_log", [])
        
        filtered = []
        for log in logs:
            if actor_id and log.get("actor_id") != actor_id:
                continue
            if actor_type and log.get("actor_type") != actor_type:
                continue
            if action and log.get("action") != action:
                continue
            if resource_type and log.get("resource_type") != resource_type:
                continue
            if resource_id and log.get("resource_id") != resource_id:
                continue
            if start_time and log.get("timestamp", 0) < start_time:
                continue
            if end_time and log.get("timestamp", 0) > end_time:
                continue
            filtered.append(AuditLogEntry(**log))
        
        filtered.sort(key=lambda l: l.timestamp, reverse=True)
        return filtered[offset:offset + limit]

    async def create_replay_snapshot(
        self,
        trace_id: str,
        seed: str,
        step: int,
        state_hash: str,
        prompt: str,
        context: Dict[str, Any],
    ) -> ReplaySnapshot:
        """Create a replay snapshot for deterministic replay."""
        snapshot = ReplaySnapshot(
            id=f"replay-{uuid.uuid4().hex[:12]}",
            trace_id=trace_id,
            seed=seed,
            step=step,
            state_hash=state_hash,
            prompt=prompt,
            context=context,
            created_at=int(time.time() * 1000),
        )
        
        state = self.store.load()
        state.setdefault("replay_snapshots", []).append(snapshot.model_dump())
        self.store.save(state)
        
        return snapshot

    async def get_replay_snapshots(self, trace_id: str) -> List[ReplaySnapshot]:
        """Get all snapshots for a trace."""
        state = self.store.load()
        snapshots = state.get("replay_snapshots", [])
        
        return [
            ReplaySnapshot(**s) for s in snapshots
            if s.get("trace_id") == trace_id
        ]

    async def get_room_timeline(
        self,
        room_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        agent_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[TimelineEvent]:
        """Get timeline events for Gantt chart view."""
        state = self.store.load()
        messages = state.get("messages", {}).get(room_id, [])
        
        events = []
        for msg in messages:
            if msg.get("deleted") or msg.get("unsent"):
                continue
            if start_time and msg.get("createdAt", 0) < start_time:
                continue
            if end_time and msg.get("createdAt", 0) > end_time:
                continue
            if agent_id and msg.get("authorId") != agent_id:
                continue
            
            event = TimelineEvent(
                id=f"evt-{uuid.uuid4().hex[:8]}",
                room_id=room_id,
                agent_id=msg.get("authorId", "unknown"),
                agent_name=msg.get("authorName", "Unknown"),
                event_type="step_end" if msg.get("authorType") == "agent" else "step_start",
                start_time=msg.get("createdAt", 0),
                end_time=None,
                duration_ms=None,
                label=msg.get("text", "")[:100],
                details={"message_id": msg.get("id")},
                color="#3b82f6" if msg.get("authorType") == "agent" else "#ef4444",
            )
            events.append(event)
        
        events.sort(key=lambda e: e.start_time)
        return events[:limit]

    async def get_observability_config(self) -> ObservabilityConfig:
        """Get current observability configuration."""
        return settings.observability

    async def update_observability_config(self, config: ObservabilityConfig) -> ObservabilityConfig:
        """Update observability configuration."""
        # In a real implementation, this would update settings
        # For now, return current config
        return settings.observability

    async def export_traces(self, request: TraceExportRequest) -> Dict[str, Any]:
        """Export traces in specified format."""
        state = self.store.load()
        traces = state.get("telemetry_traces", [])
        
        # Filter traces
        filtered = []
        for trace in traces:
            if request.trace_ids and trace.get("trace_id") not in request.trace_ids:
                continue
            if request.start_time and trace.get("start_time", 0) < request.start_time:
                continue
            if request.end_time and trace.get("end_time", 0) > request.end_time:
                continue
            filtered.append(trace)
        
        if request.format == "jaeger":
            # Convert to Jaeger format
            jaeger_spans = []
            for trace in filtered:
                for span_data in trace.get("spans", []):
                    jaeger_spans.append({
                        "traceID": trace.get("trace_id"),
                        "spanID": span_data.get("id"),
                        "parentSpanID": span_data.get("parent_span_id") or "",
                        "operationName": span_data.get("operation_name"),
                        "startTime": span_data.get("start_time"),
                        "duration": span_data.get("duration_ms") * 1000,
                        "tags": [{"key": k, "vStr": v, "type": "string"} for k, v in span_data.get("tags", {}).items()],
                    })
            return {"format": "jaeger", "data": {"spans": jaeger_spans}}
        
        elif request.format == "zipkin":
            # Convert to Zipkin format
            zipkin_spans = []
            for trace in filtered:
                for span_data in trace.get("spans", []):
                    zipkin_spans.append({
                        "traceId": trace.get("trace_id"),
                        "id": span_data.get("id"),
                        "parentId": span_data.get("parent_span_id"),
                        "name": span_data.get("operation_name"),
                        "timestamp": span_data.get("start_time"),
                        "duration": span_data.get("duration_ms") * 1000,
                        "tags": span_data.get("tags", {}),
                    })
            return {"format": "zipkin", "data": zipkin_spans}
        
        elif request.format == "tempo":
            # Tempo format (similar to Jaeger)
            return {"format": "tempo", "data": filtered}
        
        return {"format": "json", "data": filtered}


# Add method to record tool execution in trace
    def _record_tool_in_trace(
        self,
        trace_id: str,
        tool_name: str,
        args: Dict[str, Any],
        result: ToolResult,
        agent_id: Optional[str] = None,
    ) -> None:
        """Record a tool execution as a span in a trace."""
        if not settings.observability.tracing_enabled:
            return
        
        state = self.store.load()
        traces = state.get("telemetry_traces", [])
        
        for trace in traces:
            if trace.get("trace_id") == trace_id:
                span = self._start_span(
                    trace_id=trace_id,
                    operation_name=f"tool.{tool_name}",
                    parent_span_id=None,  # Would need to track current span
                    agent_id=agent_id,
                    tags={"tool": tool_name},
                    attributes={"args": args, "result_ok": result.ok},
                )
                if not result.ok:
                    span["status"] = "error"
                    span["error_message"] = result.error
                trace["spans"].append(span)
                self.store.save(state)
                break

    def _record_llm_call_in_trace(
        self,
        trace_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record an LLM call in a trace."""
        if not settings.observability.tracing_enabled:
            return
        
        state = self.store.load()
        traces = state.get("telemetry_traces", [])
        
        for trace in traces:
            if trace.get("trace_id") == trace_id:
                span = TelemetrySpan(
                    id=f"span-{uuid.uuid4().hex[:12]}",
                    trace_id=trace_id,
                    operation_name="llm.call",
                    start_time=int(time.time() * 1_000_000),
                    end_time=int(time.time() * 1_000_000),
                    duration_ms=0,  # Would need actual timing
                    tags={"model": model},
                    attributes={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "cost_usd": cost_usd,
                    },
                    status="ok",
                )
                trace["spans"].append(span.model_dump())
                
                # Record token usage
                self._record_token_usage(
                    room_id=trace.get("room_id", "unknown"),
                    agent_id="system",
                    provider="openai",  # Would need actual provider
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
                self.store.save(state)
                break
