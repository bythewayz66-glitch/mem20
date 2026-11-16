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
import json
import time
from typing import Any, Dict, List, Optional

from .config import settings
from .execution import execute_actions, tools_manifest
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
    candidates = [a for a in agents if isinstance(a, dict) and a.get("name")]
    if not candidates:
        return None
    # Prefer an enabled worker, then a lead, then highest keyword score.
    enabled = [a for a in candidates if a.get("workerEnabled") is not False]
    pool = enabled or candidates
    return max(pool, key=lambda a: (score_agent_for_goal(a, goal_text), bool(a.get("isLead"))))


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
