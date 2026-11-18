from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .config import settings
from .connectors import connectors_status, gh_exec, gh_status, github_request, github_status, google_api_request, google_status
from .execution import (
    execute_actions,
    files_status,
    file_edit,
    file_list,
    file_read,
    file_write,
    gh_status as gh_tool_status,
    github_status as github_tool_status,
    terminal_exec,
    terminal_status,
    tools_manifest,
)
from .mem20 import Mem20Error, get_mem20_client
from .fleet import FleetClient, get_fleet_client, init_fleet_integration, shutdown_fleet_integration
from .models import (
    ChatRequest,
    ChatResponse,
    ChatChoice,
    FileEditRequest,
    FileListRequest,
    FileReadRequest,
    FileWriteRequest,
    MemoryRecallRequest,
    MemoryStoreRequest,
    OptimizePromptRequest,
    OptimizePromptResponse,
    RoutingMeta,
    AttemptInfo,
    RuntimeExecRequest,
    SetGoalRequest,
    TerminalExecRequest,
    ToolCallRequest,
    Usage,
    WorkerControlRequest,
    WorkspaceSnapshot,
    # Phase 7
    DeadLetterActionRequest,
    WorkerLogQuery,
    # Phase 8
    AlertEvent,
    AlertRule,
    CreateAlertRuleRequest,
    CreateCostBudgetRequest,
    ExportTracesRequest,
    ObservabilityConfig,
    WorkerLogQuery,
    WorkerControlRequest,
)
from .providers.base import RouteContext, StreamEvent
from .router import Router
from .skills import load_skill_catalogue, skill_status
import json
from pathlib import Path
from .state import StateStore
from .worker import GoalWorker


app = FastAPI(title="teamz orchestrator", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = Router(cfg=settings)
state_store = StateStore(settings.state_file)
worker = GoalWorker(state_store, router, load_skill_catalogue())


@app.on_event("startup")
async def _startup() -> None:
    if settings.goal_enabled and settings.goal_worker_enabled:
        await worker.start()
    # Initialize fleet integration (Steps 6-9)
    if settings.fleet_enabled:
        await init_fleet_integration()


@app.on_event("shutdown")
async def _shutdown() -> None:
    try:
        await worker.stop()
    except Exception:
        pass
    try:
        await get_mem20_client().close()
    except Exception:
        pass
    # Shutdown fleet integration
    await shutdown_fleet_integration()


@app.get("/health")
async def health() -> Dict[str, Any]:
    mem20_ok = False
    if settings.mem20_enabled:
        try:
            await asyncio.wait_for(get_mem20_client().ensure(), timeout=5.0)
            mem20_ok = True
        except Exception:
            mem20_ok = False
    return {
        "ok": True,
        "service": "teamz-orchestrator",
        "mem20": {"enabled": settings.mem20_enabled, "connected": mem20_ok},
        "providers": [getattr(p, "name", "unknown") for p in router.providers],
        "keyless_first": settings.keyless_first,
        "ts": int(time.time()),
    }


@app.get("/v1/status")
async def status() -> Dict[str, Any]:
    mem20 = {"enabled": settings.mem20_enabled, "connected": False, "tools": 0}
    if settings.mem20_enabled:
        try:
            client = get_mem20_client()
            await asyncio.wait_for(client.ensure(), timeout=5.0)
            tools = await asyncio.wait_for(client.tools(), timeout=5.0)
            mem20.update({"connected": True, "tools": len(tools)})
        except Exception as e:
            mem20.update({"error": str(e)})
    providers = []
    for p in router.providers:
        providers.append(
            {
                "name": getattr(p, "name", "unknown"),
                "keyless": bool(getattr(p, "keyless", False) and not getattr(p, "api_key", "")),
                "has_api_key": bool(getattr(p, "api_key", "")),
                "base_url": getattr(p, "base_url", None),
                "default_model": getattr(p, "default_model", None),
                "local_runtime": bool(getattr(p, "local_runtime", False)),
            }
        )
    return {
        "ok": True,
        "providers": providers,
        "mem20": mem20,
        "persistence": state_store.summary(),
        "worker": worker.status(),
        "skills": skill_status(),
        "tools": {
            "terminal": terminal_status(),
            "files": files_status(),
            "gh": gh_tool_status(),
            "github": github_tool_status(),
            "manifest": tools_manifest(),
        },
        "config": {
            "max_attempts": settings.max_attempts,
            "keyless_first": settings.keyless_first,
            "request_timeout_s": settings.request_timeout_s,
        },
    }


def _routing_meta(attempts: List[Dict[str, Any]], requested_model: Optional[str]) -> RoutingMeta:
    success = next((a for a in attempts if a.get("status") == "success"), None)
    failed = [a for a in attempts if a.get("status") == "failed"]
    return RoutingMeta(
        selected_provider=success.get("provider") if success else None,
        selected_model=success.get("model") if success else None,
        attempts=[AttemptInfo(**a) for a in attempts],
        fallback_used=bool(failed and success),
        requested_model=requested_model,
    )


def _usage_obj(u: Optional[Dict[str, Any]]) -> Optional[Usage]:
    if not u:
        return None
    try:
        return Usage(**{k: v for k, v in u.items() if k in {"prompt_tokens", "completion_tokens", "total_tokens"}})
    except Exception:
        return None


def _messages_to_dicts(messages: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in messages or []:
        if hasattr(m, "model_dump"):
            out.append(m.model_dump())
        elif isinstance(m, dict):
            out.append(m)
        else:
            out.append({"role": "user", "content": str(m)})
    return out


async def _maybe_store_memory(kind: str, conversation: Optional[Dict[str, Any]], text: str) -> None:
    if not settings.mem20_enabled or not text.strip():
        return
    conv = conversation or {}
    conv_id = conv.get("id") or conv.get("conversationId") or "unknown"
    tags = ["teamz", f"conversation:{conv_id}", kind]
    name = conv.get("name")
    if name:
        tags.append(f"channel:{str(name)[:64]}")
    if conv.get("kind"):
        tags.append(f"kind:{conv.get('kind')}")
    try:
        client = get_mem20_client()
        await client.memory_store(text[:4000], category="teamz", tags=tags)
    except Exception:
        return


async def _recall_memories_for_context(query: str, conversation: Optional[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    if not settings.mem20_enabled:
        return []
    client = get_mem20_client()
    queries = []
    conv = conversation or {}
    conv_id = conv.get("id") or conv.get("conversationId")
    name = conv.get("name")
    if conv_id:
        queries.append(f"conversation:{conv_id} {query}")
    if name:
        queries.append(f"{name} {query}")
    queries.append(query)
    seen = set()
    out: List[Dict[str, Any]] = []
    for q in queries:
        try:
            items = await client.recall_texts(q, limit=limit)
        except Exception:
            items = []
        for it in items:
            key = str(it.get("id") or it.get("text", ""))[:200]
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        if len(out) >= limit:
            break
    return out[:limit]


async def _augment_messages_with_channel_memory(messages: List[Dict[str, Any]], conversation: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not settings.mem20_enabled or not conversation:
        return messages
    # Derive query from latest user message
    query = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            c = m.get("content")
            query = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
            break
    if not query:
        query = str(conversation.get("name") or conversation.get("topic") or "conversation context")
    memories = await _recall_memories_for_context(query[:500], conversation, limit=6)
    if not memories:
        return messages
    lines = []
    for mem in memories:
        txt = str(mem.get("text") or "").strip()
        if txt:
            lines.append(f"- {txt[:400]}")
    if not lines:
        return messages
    memory_block = (
        "Persistent channel memory/context (mem20, relevant recalled items):\n" + "\n".join(lines)
    )
    # Inject as a system message after the first system message if present, else prepend.
    out = list(messages)
    insert_at = 0
    if out and out[0].get("role") == "system":
        insert_at = 1
    out.insert(insert_at, {"role": "system", "content": memory_block})
    return out


def _execution_tools_instruction() -> str:
    tools = tools_manifest()
    lines = []
    for t in tools:
        name = t.get("name")
        desc = t.get("description", "")
        params = t.get("params")
        if name:
            lines.append(f"- {name}: {desc}" + (f" params={json.dumps(params, ensure_ascii=False)}" if params else ""))
    return (
        "You have REAL execution tools on the server and can create/modify files, run commands, and inspect the workspace. "
        "When the user asks you to build, create, edit, fix, run, test, or produce anything outside chat, you MUST use these tools to actually do it. "
        "Do not only describe or pretend; produce real artifacts/files/command results.\n\n"
        "To use tools, reply with STRICT JSON only (no markdown fences) in this shape:\n"
        "{\n"
        '  "thought": "brief plan",\n'
        '  "tool_actions": [\n'
        '    {"tool": "terminal|write_file|edit_file|read_file|list_files|gh|github|run_tests|...", "args": {...}}\n'
        "  ]\n"
        "}\n"
        "The server will execute tool_actions and return results to you. After receiving results, either emit more tool_actions JSON or reply with a normal final answer summarizing what was actually created/changed (include file paths/commands). "
        "Use write_file/edit_file/terminal to build apps and write real code. Prefer small, verifiable steps.\n\n"
        "Available execution tools:\n" + "\n".join(lines)
    )


def _lead_runtime_instruction(agent: Optional[Dict[str, Any]], conversation: Optional[Dict[str, Any]]) -> Optional[str]:
    if not agent or not (agent.get("isLead") or agent.get("lead")):
        return None
    return (
        "You are the LEAD AGENT for this workspace. You can add, remove, and program agents and the runtime itself. "
        "When asked, you can make new channels, make agents, and program/configure current ones. "
        "You must orchestrate and delegate work to groups of agents that match the task.\n\n"
        "For workspace/runtime management changes, include a fenced code block with language `teamz-actions` containing STRICT JSON: "
        "{\"actions\":[ ... ]}.\n"
        "Supported actions: "
        "create_channel {name, agentIds?:[], agentNames?:[], topic?}; "
        "rename_channel {conversationId|channelId|nameMatch, name}; "
        "update_channel_members {conversationId|channelId|nameMatch, agentIds?:[], agentNames?:[], addAgentIds?:[], addAgentNames?:[], removeAgentIds?:[], removeAgentNames?:[]}; "
        "delete_channel {conversationId|channelId|nameMatch}; "
        "create_agent {name, role?, systemPrompt?, model?, skills?:[{key,label,level}], isLead?:bool, emoji?, accent?}; "
        "update_agent {agentId|agentName, name?, systemPrompt?, model?, skills?:[], addSkills?:[], isLead?:bool, role?, status?}; "
        "delete_agent {agentId|agentName}; "
        "invite_agent_to_channel {conversationId|channelId|nameMatch, agentId|agentName}; "
        "send_message {conversationId|channelId|nameMatch|agentName, text, directedAgentNames?:[]}; "
        "open_direct_chat {agentId|agentName}.\n"
        "Use names/ids from workspace context when possible. Prefer agentNames/nameMatch when ids unknown. "
        "If asked to create a channel or agent, actually emit the corresponding teamz-actions block. "
        "For HTML presentation deliverables when a job is completed, include a fenced block with language `presentation` containing complete HTML."
    )


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    # Try fenced json blocks
    fence_patterns = [
        r"```(?:json)?\s*(\{[\s\S]*?\})\s*```",
        r"```\s*(\{[\s\S]*?\})\s*```",
    ]
    for pat in fence_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            try:
                obj = json.loads(m.group(1))
                if isinstance(obj, dict):
                    return obj
            except Exception:
                pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except Exception:
            # Try to find balanced-ish object by trimming trailing text after last valid-ish brace region
            return None
    return None


def _normalize_chat_tool_actions(parsed: Any) -> List[Dict[str, Any]]:
    if not isinstance(parsed, dict):
        return []
    raw = parsed.get("tool_actions") or parsed.get("actions") or parsed.get("tool_calls")
    if not isinstance(raw, list):
        return []
    actions: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        # Support worker style: {"tool":"write_file","args":{...}}
        # and generic: {"name":"write_file","arguments":{...}}
        tool = item.get("tool") or item.get("name") or item.get("type")
        args = item.get("args") if isinstance(item.get("args"), dict) else (
            item.get("arguments") if isinstance(item.get("arguments"), dict) else None
        )
        if not tool:
            continue
        action: Dict[str, Any] = {"tool": str(tool)}
        if isinstance(args, dict):
            action["args"] = args
        else:
            # Inline params form
            inline = {k: v for k, v in item.items() if k not in {"tool", "name", "type", "args", "arguments"}}
            if inline:
                action["args"] = inline
        actions.append(action)
    # Avoid executing frontend runtime-control actions via execution tool runner.
    runtime_control = {
        "create_channel", "rename_channel", "update_channel_members", "delete_channel",
        "create_agent", "update_agent", "delete_agent", "invite_agent_to_channel",
        "send_message", "open_direct_chat", "delegate", "post_message",
    }
    filtered = [a for a in actions if str(a.get("tool") or "").lower() not in runtime_control]
    return filtered


async def _run_agentic_tool_loop(
    base_messages: List[Dict[str, Any]],
    req: ChatRequest,
    *,
    max_iterations: int = 6,
) -> Dict[str, Any]:
    messages = list(base_messages)
    all_attempts: List[Dict[str, Any]] = []
    all_tool_results: List[Dict[str, Any]] = []
    final_text = ""
    final_model = req.model or (req.agent or {}).get("model") or "unknown"
    final_usage = None

    for _ in range(max_iterations):
        ctx = RouteContext(
            messages=messages,
            requested_model=req.model or (req.agent or {}).get("model"),
            strict_model=bool(req.strict_model),
            stream=False,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            metadata=req.metadata or {},
        )
        result = await router.complete(ctx)
        attempts = [a.to_dict() if hasattr(a, "to_dict") else a for a in result.attempts]
        all_attempts.extend(attempts)
        text = (result.text or "").strip()
        final_text = text
        final_model = result.model or final_model
        final_usage = result.usage or final_usage

        parsed = _extract_json_object(text)
        tool_actions = _normalize_chat_tool_actions(parsed)
        if not tool_actions:
            break

        # Execute real tools server-side
        tool_results = await execute_actions(tool_actions, agent_id=(req.agent or {}).get("id") if isinstance(req.agent, dict) else None)
        all_tool_results.extend(tool_results)

        # Feed tool call + results back to model for next step/final answer
        messages.append({"role": "assistant", "content": text})
        result_lines = []
        for tr in tool_results:
            tool = tr.get("tool")
            ok = tr.get("ok")
            err = tr.get("error")
            data = tr.get("data")
            try:
                data_s = json.dumps(data, ensure_ascii=False)
            except Exception:
                data_s = str(data)
            if len(data_s) > 6000:
                data_s = data_s[:6000] + "…"
            if ok:
                result_lines.append(f"- {tool}: OK {data_s}")
            else:
                result_lines.append(f"- {tool}: ERROR {err} {data_s}")
        messages.append({
            "role": "user",
            "content": (
                "Tool execution results (real server-side actions):\n"
                + ("\n".join(result_lines) if result_lines else "- (no results)")
                + "\n\nContinue: if more actions are needed, reply with STRICT JSON tool_actions. "
                  "If finished, reply with a clear final answer describing what you actually created/changed, including file paths and command outcomes."
            ),
        })

    # If the model ended on a tool-actions JSON message, produce a user-facing summary
    if final_text:
        parsed_final = _extract_json_object(final_text)
        if parsed_final and _normalize_chat_tool_actions(parsed_final):
            ok_count = sum(1 for r in all_tool_results if r.get("ok"))
            fail_count = len(all_tool_results) - ok_count
            final_text = (
                "Executed requested tool actions.\n\n"
                f"Results: {ok_count} succeeded, {fail_count} failed.\n"
                + "\n".join(
                    f"- {'✓' if r.get('ok') else '✗'} {r.get('tool')}: {r.get('error') or (r.get('data') or {}).get('path') or (r.get('data') or {}).get('command') or 'done'}"
                    for r in all_tool_results[-20:]
                )
            )

    return {
        "text": final_text,
        "model": final_model,
        "usage": final_usage,
        "attempts": all_attempts,
        "tool_results": all_tool_results,
    }


async def _augment_messages_for_agent_runtime(messages: List[Dict[str, Any]], req: ChatRequest) -> List[Dict[str, Any]]:
    out = await _augment_messages_with_channel_memory(messages, req.conversation)
    exec_instr = _execution_tools_instruction()
    insert_at = 1 if out and out[0].get("role") == "system" else 0
    out.insert(insert_at, {"role": "system", "content": exec_instr})
    lead_instr = _lead_runtime_instruction(req.agent, req.conversation)
    if lead_instr:
        # Keep lead runtime-control instruction prominent (after execution tools instruction)
        insert_at = 1 if out and out[0].get("role") == "system" else 0
        out.insert(insert_at, {"role": "system", "content": lead_instr})
    # Provide compact roster/channel context if available in metadata for orchestration/delegation
    meta = req.metadata or {}
    workspace = meta.get("workspace") if isinstance(meta.get("workspace"), dict) else None
    if workspace:
        try:
            agents = workspace.get("agents") or []
            convs = workspace.get("conversations") or []
            roster = []
            for a in agents[:40]:
                if not isinstance(a, dict):
                    continue
                skills = a.get("skills") or []
                sk = ", ".join([f"{(s.get('label') or s.get('key'))}(L{s.get('level',1)})" for s in skills if isinstance(s, dict)][:6])
                roster.append(f"- {a.get('name')} (id:{a.get('id')}, lead:{bool(a.get('isLead'))}, role:{(a.get('origin') or {}).get('role') if isinstance(a.get('origin'), dict) else a.get('role','')}) skills:{sk}")
            chans = []
            for c in convs[:30]:
                if not isinstance(c, dict):
                    continue
                chans.append(f"- {c.get('name')} (id:{c.get('id')}, kind:{c.get('kind')}, members:{len(c.get('agentIds') or [])}, topic:{c.get('topic','')})")
            if roster or chans:
                ctx = "Workspace runtime context (for orchestration/delegation):\nAgents:\n" + ("\n".join(roster) if roster else "- none") + "\nConversations:\n" + ("\n".join(chans) if chans else "- none")
                insert_at = 1 if out and out[0].get("role") == "system" else 0
                out.insert(insert_at, {"role": "system", "content": ctx})
        except Exception:
            pass
    return out


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    base_messages = _messages_to_dicts(req.messages)
    ctx_messages = await _augment_messages_for_agent_runtime(base_messages, req)

    # Persist latest user message context to channel memory (best-effort)
    if settings.mem20_enabled:
        last_user = None
        for m in reversed(base_messages):
            if m.get("role") == "user":
                c = m.get("content")
                last_user = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                break
        if last_user:
            await _maybe_store_memory("user", req.conversation, f"User: {last_user}")

    # Run agentic tool loop (server-side execution). Uses non-stream completions internally
    # so tool calls can be detected/executed; streaming requests receive a final streamed payload.
    try:
        loop_result = await _run_agentic_tool_loop(ctx_messages, req, max_iterations=6)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"agent execution failed: {e}")

    final_text = loop_result.get("text") or ""
    final_model = loop_result.get("model") or (req.model or (req.agent or {}).get("model") or "unknown")
    final_usage = loop_result.get("usage")
    attempts = loop_result.get("attempts") or []
    meta = _routing_meta(attempts, req.model or (req.agent or {}).get("model"))

    if final_text:
        await _maybe_store_memory("assistant", req.conversation, f"Assistant: {final_text}")

    if not req.stream:
        resp = ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
            created=int(time.time()),
            model=final_model,
            choices=[ChatChoice(index=0, message={"role": "assistant", "content": final_text}, finish_reason="stop")],
            usage=_usage_obj(final_usage),
            routing=meta,
        )
        return JSONResponse(resp.model_dump())

    async def event_stream() -> AsyncIterator[str]:
        if attempts:
            yield f"event: meta\ndata: {json.dumps({'type':'meta','attempts':attempts}, ensure_ascii=False)}\n\n"
        if final_text:
            # Emit in chunks so clients that expect incremental deltas still work.
            chunk_size = 400
            for i in range(0, len(final_text), chunk_size):
                delta = final_text[i:i + chunk_size]
                payload = {
                    "id": "chatcmpl-stream",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {"content": delta}, "finish_reason": None}],
                    "model": final_model,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        done_payload = {
            "type": "done",
            "text": final_text,
            "model": final_model,
            "usage": final_usage,
            "routing": meta.model_dump() if meta else None,
            "fallback_used": False,
            "tool_results": loop_result.get("tool_results") or [],
        }
        yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/v1/optimize-prompt", response_model=OptimizePromptResponse)
async def optimize_prompt(req: OptimizePromptRequest):
    draft = (req.draft or "").strip()
    if not draft:
        raise HTTPException(status_code=400, detail="draft is required")

    memories: List[Dict[str, Any]] = []
    conv = req.conversation or req.channel or {}
    if req.use_memory and settings.mem20_enabled:
        q = req.memory_query or draft
        memories = await _recall_memories_for_context(q, conv, limit=6)

    history_lines = []
    for h in (req.history or [])[-20:]:
        role = h.get("role") or h.get("authorType") or "user"
        name = h.get("authorName") or h.get("name") or role
        text = h.get("text") or h.get("content") or ""
        if isinstance(text, list):
            text = json.dumps(text, ensure_ascii=False)
        text = str(text).strip()
        if text:
            history_lines.append(f"- {name}: {text[:500]}")

    agent_lines = []
    for a in (req.agents or [])[:30]:
        nm = a.get("name") or a.get("id") or "agent"
        role = a.get("origin", {}).get("role") if isinstance(a.get("origin"), dict) else a.get("role")
        lead = a.get("isLead") or a.get("lead")
        skills = a.get("skills") or []
        skill_names = []
        for s in skills[:8]:
            if isinstance(s, dict):
                lvl = s.get("level")
                label = str(s.get("label") or s.get("name") or s.get("key") or "")
                if label:
                    skill_names.append(f"{label}" + (f"(L{lvl})" if lvl else ""))
            else:
                skill_names.append(str(s))
        desc = f"{nm}" + (" [lead]" if lead else "") + (f" ({role})" if role else "")
        if skill_names:
            desc += ": " + ", ".join([s for s in skill_names if s])
        agent_lines.append(f"- {desc}")

    memory_lines = [f"- {m.get('text','')[:400]}" for m in memories if m.get("text")]

    system = (
        "You improve user prompts for an AI team workspace. "
        "Rewrite the draft into a clearer, more specific, context-aware prompt while preserving intent. "
        "Use the provided conversation history, channel context, agent roster (roles/skills/lead), and recalled persistent memories when relevant. "
        "Do not invent facts. Keep it concise and actionable. Return ONLY the improved prompt text."
    )
    user_parts = [
        f"Channel/Conversation: {json.dumps({k: conv.get(k) for k in ('id','name','kind','topic') if conv.get(k) is not None}, ensure_ascii=False)}",
        "Agents/participants:\n" + ("\n".join(agent_lines) if agent_lines else "- (none provided)"),
        "Recent conversation:\n" + ("\n".join(history_lines) if history_lines else "- (none provided)"),
        "Relevant persistent memories:\n" + ("\n".join(memory_lines) if memory_lines else "- (none recalled)"),
        f"Goal/context hint: {req.goal or '(none)'}",
        "Draft prompt to improve:\n" + draft,
    ]
    ctx = RouteContext(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(user_parts)}],
        requested_model=None,
        strict_model=False,
        stream=False,
        temperature=0.3,
    )
    result = await router.complete(ctx)
    improved = (result.text or draft).strip()
    attempts = [a.to_dict() if hasattr(a, "to_dict") else a for a in result.attempts]
    meta = _routing_meta(attempts, None)

    if settings.mem20_enabled:
        try:
            cid = (conv.get("id") or conv.get("conversationId") or "unknown")
            await get_mem20_client().memory_store(
                f"Prompt optimized in conversation {cid}. Draft: {draft[:500]} | Improved: {improved[:800]}",
                category="teamz",
                tags=["teamz", f"conversation:{cid}", "prompt_optimization"],
            )
        except Exception:
            pass

    return OptimizePromptResponse(prompt=improved, original=draft, memories_used=memories, routing=meta)


@app.post("/v1/memory/recall")
async def memory_recall(req: MemoryRecallRequest):
    if not settings.mem20_enabled:
        return {"items": [], "enabled": False}
    try:
        client = get_mem20_client()
        items = await client.recall_texts(req.query, limit=req.limit)
        return {"items": items, "enabled": True}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mem20 recall failed: {e}")


@app.post("/v1/memory/store")
async def memory_store(req: MemoryStoreRequest):
    if not settings.mem20_enabled:
        raise HTTPException(status_code=503, detail="mem20 is disabled")
    try:
        client = get_mem20_client()
        res = await client.memory_store(req.content, category=req.category, tags=req.tags)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mem20 store failed: {e}")


@app.get("/v1/tools")
async def list_tools():
    if not settings.mem20_enabled:
        return {"tools": [], "enabled": False}
    try:
        client = get_mem20_client()
        tools = await client.tools()
        return {"tools": tools, "enabled": True}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mem20 tools/list failed: {e}")


@app.post("/v1/tools/call")
async def call_tool(req: ToolCallRequest):
    if not settings.mem20_enabled:
        raise HTTPException(status_code=503, detail="mem20 is disabled")
    try:
        client = get_mem20_client()
        result = await client.call_tool(req.name, req.arguments)
        return {"ok": True, "result": result}
    except Mem20Error as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mem20 tool call failed: {e}")


# --- Connectors ---

@app.get("/v1/connectors/status")
async def connectors_status_endpoint():
    return connectors_status()


@app.get("/v1/connectors/github/status")
async def connectors_github_status():
    return github_status().to_dict()


@app.post("/v1/connectors/github/request")
async def connectors_github_request(payload: Dict[str, Any]):
    method = str(payload.get("method") or "GET").upper()
    path = str(payload.get("path") or "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    params = payload.get("params") if isinstance(payload.get("params"), dict) else None
    body = payload.get("body") if ("body" in payload) else payload.get("json")
    return github_request(method, path, params=params, json_body=body)


@app.get("/v1/connectors/gh/status")
async def connectors_gh_status():
    return gh_status().to_dict()


@app.post("/v1/connectors/gh/exec")
async def connectors_gh_exec(payload: Dict[str, Any]):
    args = payload.get("args")
    if not isinstance(args, list):
        raise HTTPException(status_code=400, detail="args (list) is required")
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    timeout = payload.get("timeout")
    try:
        timeout_f = float(timeout) if timeout is not None else 60.0
    except Exception:
        timeout_f = 60.0
    timeout_f = max(1.0, min(timeout_f, 300.0))
    return gh_exec([str(a) for a in args], cwd=cwd, timeout=timeout_f)


@app.get("/v1/connectors/google/status")
async def connectors_google_status():
    return google_status().to_dict()


@app.post("/v1/connectors/google/request")
async def connectors_google_request(payload: Dict[str, Any]):
    method = str(payload.get("method") or "GET").upper()
    url = str(payload.get("url") or payload.get("path") or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url or path is required")
    scopes = payload.get("scopes") if isinstance(payload.get("scopes"), list) else None
    params = payload.get("params") if isinstance(payload.get("params"), dict) else None
    body = payload.get("body") if ("body" in payload) else payload.get("json")
    headers = payload.get("headers") if isinstance(payload.get("headers"), dict) else None
    return google_api_request(method, url, scopes=[str(s) for s in scopes] if scopes else None, params=params, json_body=body, headers=headers)


# --- Runtime planning for lead agent / orchestration ---


@app.post("/v1/runtime/plan")
async def runtime_plan(payload: Dict[str, Any]):
    """Plan runtime/workspace actions for a lead agent request.
    Returns structured actions the frontend can apply (create/remove/program agents/channels, delegate).
    """
    request_text = str(payload.get("request") or payload.get("prompt") or payload.get("message") or "").strip()
    if not request_text:
        raise HTTPException(status_code=400, detail="request is required")
    workspace = payload.get("workspace") or {}
    agents = workspace.get("agents") or payload.get("agents") or []
    conversations = workspace.get("conversations") or payload.get("conversations") or []
    active_conversation = workspace.get("activeConversation") or payload.get("activeConversation") or payload.get("conversation")
    history = payload.get("history") or []

    # Recall relevant persistent memories
    memories: List[Dict[str, Any]] = []
    if settings.mem20_enabled:
        q = request_text
        if active_conversation and isinstance(active_conversation, dict):
            q = f"{active_conversation.get('name','')} {request_text}"
        memories = await _recall_memories_for_context(q, active_conversation if isinstance(active_conversation, dict) else None, limit=8)

    system = (
        "You are the runtime planner for a lead AI agent in the teamz workspace. "
        "Given the user's request and current workspace state, produce a concrete plan and structured actions. "
        "The lead agent can add, remove, and program agents and the runtime itself; make new channels; make agents; "
        "program/configure current ones; and orchestrate/delegate work to groups of agents that match the task. "
        "Return STRICT JSON only with this shape: {\n"
        "  \"summary\": string,\n"
        "  \"actions\": [ {\"type\": string, ...params} ],\n"
        "  \"delegations\": [ {\"agent_id\": string|null, \"agent_name\": string|null, \"task\": string, \"reason\": string} ],\n"
        "  \"response\": string\n"
        "}\n"
        "Supported action types and params: "
        "create_channel {name, agentIds?:[], agentNames?:[], topic?}; "
        "rename_channel {conversationId|channelId|nameMatch, name}; "
        "update_channel_members {conversationId|channelId|nameMatch, agentIds?:[], agentNames?:[], addAgentIds?:[], addAgentNames?:[], removeAgentIds?:[], removeAgentNames?:[]}; "
        "delete_channel {conversationId|channelId|nameMatch}; "
        "create_agent {name, role?, systemPrompt?, model?, skills?:[{key,label,level}], isLead?:bool, emoji?, accent?, templateId?, seniority?}; "
        "update_agent {agentId|agentName, name?, systemPrompt?, model?, skills?:[{key,label,level}], addSkills?:[{key,label,level}], isLead?:bool, emoji?, accent?, status?, endpointUrl?}; "
        "delete_agent {agentId|agentName}; "
        "invite_agent_to_channel {conversationId|channelId|nameMatch, agentId|agentName}; "
        "send_message {conversationId|channelId|nameMatch|agentName(for direct), text, directedAgentNames?:[], directedAgentIds?:[]}. "
        "Use existing ids/names from workspace when possible. Prefer agentNames/nameMatch when ids unknown. "
        "Keep actions minimal, valid, and executable. Do not invent non-existent agents in delegations unless also creating them."
    )
    # Compact context
    agent_ctx = []
    for a in agents[:60]:
        if not isinstance(a, dict):
            continue
        skills = a.get("skills") or []
        sk = ", ".join([f"{(s.get('label') or s.get('key'))}(L{s.get('level',1)})" for s in skills if isinstance(s, dict)][:8])
        agent_ctx.append({
            "id": a.get("id"), "name": a.get("name"), "isLead": bool(a.get("isLead")),
            "role": (a.get("origin") or {}).get("role") if isinstance(a.get("origin"), dict) else a.get("role"),
            "model": a.get("model"), "skills": sk,
        })
    conv_ctx = []
    for c in conversations[:60]:
        if not isinstance(c, dict):
            continue
        conv_ctx.append({"id": c.get("id"), "kind": c.get("kind"), "name": c.get("name"), "agentIds": c.get("agentIds"), "topic": c.get("topic")})
    hist_ctx = []
    for h in history[-20:]:
        if not isinstance(h, dict):
            continue
        hist_ctx.append({"authorType": h.get("authorType"), "authorName": h.get("authorName"), "text": str(h.get("text") or "")[:400]})

    user = (
        f"User request: {request_text}\n\n"
        f"Active conversation: {json.dumps(active_conversation, ensure_ascii=False)[:2000] if active_conversation else 'null'}\n\n"
        f"Agents: {json.dumps(agent_ctx, ensure_ascii=False)[:6000]}\n\n"
        f"Conversations/channels: {json.dumps(conv_ctx, ensure_ascii=False)[:6000]}\n\n"
        f"Recent history: {json.dumps(hist_ctx, ensure_ascii=False)[:4000]}\n\n"
        f"Relevant memories: {json.dumps([m.get('text') for m in memories[:6]], ensure_ascii=False)[:3000]}"
    )
    ctx = RouteContext(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], stream=False, temperature=0.2)
    result = await router.complete(ctx)
    parsed = _extract_json_object(result.text) or {}
    actions = parsed.get("actions") if isinstance(parsed.get("actions"), list) else []
    delegations = parsed.get("delegations") if isinstance(parsed.get("delegations"), list) else []
    out = {
        "ok": True,
        "summary": parsed.get("summary") or "",
        "actions": actions,
        "delegations": delegations,
        "response": parsed.get("response") or parsed.get("summary") or "",
        "memories_used": memories,
        "routing": _routing_meta([a.to_dict() if hasattr(a, "to_dict") else a for a in result.attempts], None).model_dump(),
        "raw": None if parsed else result.text,
    }
    if settings.mem20_enabled:
        try:
            await get_mem20_client().memory_store(
                f"Runtime plan for request: {request_text[:300]} => actions={len(actions)} delegations={len(delegations)} summary={str(out.get('summary',''))[:300]}",
                category="teamz",
                tags=["teamz", "runtime", "lead_agent", "plan"],
            )
        except Exception:
            pass
    return out


# --- Opportunity / portfolio scanning ---

@app.post("/v1/opportunities/scan")
async def scan_opportunities(payload: Dict[str, Any]):
    """Scan chats/messages for opportunities to create tools, skills, capabilities, and reusable assets."""
    conversations = payload.get("conversations") or payload.get("chats") or []
    messages = payload.get("messages") or []
    agents = payload.get("agents") or []
    if messages and not conversations:
        conversations = [{"id": payload.get("conversationId", "unknown"), "messages": messages}]

    corpus_parts = []
    for conv in conversations[:10]:
        cid = conv.get("id") or conv.get("conversationId") or "conversation"
        cname = conv.get("name") or cid
        corpus_parts.append(f"## Conversation: {cname} ({cid})")
        for m in (conv.get("messages") or [])[-60:]:
            who = m.get("authorName") or m.get("role") or m.get("authorType") or "unknown"
            txt = m.get("text") or m.get("content") or ""
            if isinstance(txt, list):
                txt = json.dumps(txt, ensure_ascii=False)
            txt = str(txt).strip()
            if txt:
                corpus_parts.append(f"- {who}: {txt[:600]}")
        corpus_parts.append("")
    corpus = "\n".join(corpus_parts)[:12000]
    if not corpus.strip():
        if settings.mem20_enabled:
            mem_items = await _recall_memories_for_context("opportunities tools skills capabilities reusable assets", None, limit=12)
            corpus = "\n".join(f"- {i.get('text','')}" for i in mem_items)

    agent_summary = []
    for a in agents[:40]:
        skills = a.get("skills") or []
        sk = ", ".join((f"{s.get('label') or s.get('key')}(L{s.get('level',1)})") for s in skills if isinstance(s, dict)) if skills else ""
        agent_summary.append(f"- {a.get('id','')} {a.get('name','agent')} lead={bool(a.get('isLead'))}: {sk}")

    system = (
        "You analyze team chat transcripts to find opportunities to create reusable assets. "
        "Identify: (1) skills/capabilities agents demonstrated or should learn, (2) tools/automations worth building, "
        "(3) reusable prompts/workflows/templates. Return STRICT JSON only with keys: "
        "{\"opportunities\":[{\"type\":\"skill|tool|capability|asset\",\"title\":str,\"description\":str,\"evidence\":str,\"suggested_agent\":str|null,\"suggested_agent_id\":str|null,\"suggested_skill_level\":1-5|null,\"reusable\":true}],"
        "\"portfolio_updates\":[{\"agent_name\":str,\"agent_id\":str|null,\"skill\":str,\"skill_key\":str,\"level\":1-5,\"evidence\":str}]}"
    )
    user = (
        "Known agents/skills:\n" + ("\n".join(agent_summary) if agent_summary else "- none") +
        "\n\nChat corpus:\n" + (corpus or "- empty")
    )
    ctx = RouteContext(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], stream=False, temperature=0.2)
    result = await router.complete(ctx)
    parsed = _extract_json_object(result.text) or {"opportunities": [], "portfolio_updates": [], "raw": result.text}
    if not isinstance(parsed.get("opportunities"), list):
        parsed["opportunities"] = []
    if not isinstance(parsed.get("portfolio_updates"), list):
        parsed["portfolio_updates"] = []
    attempts = [a.to_dict() if hasattr(a, "to_dict") else a for a in result.attempts]
    parsed["routing"] = _routing_meta(attempts, None).model_dump()

    if settings.mem20_enabled:
        try:
            await get_mem20_client().memory_store(
                "Opportunity scan results: " + json.dumps(parsed, ensure_ascii=False)[:3500],
                category="teamz",
                tags=["teamz", "opportunities", "scan"],
            )
        except Exception:
            pass
    return parsed


# --- Persistent workspace / session state ---------------------------------

@app.get("/v1/state")
async def get_state() -> Dict[str, Any]:
    return state_store.load()


@app.get("/v1/state/status")
async def get_state_status() -> Dict[str, Any]:
    return state_store.summary()


@app.put("/v1/state")
async def put_state(snapshot: WorkspaceSnapshot) -> Dict[str, Any]:
    current = state_store.load()
    data = snapshot.model_dump()
    # Preserve server-managed/runtime fields and unknown extras when the frontend
    # syncs workspace UI state, to avoid clobbering data managed by other endpoints/workers.
    for key in ("goals", "tasks", "activity"):
        if not data.get(key) and current.get(key):
            data[key] = current.get(key)
    core_keys = {"version", "updatedAt", "agents", "conversations", "messages", "filters", "activeConversationId", "goals", "tasks", "activity"}
    for key, value in current.items():
        if key in core_keys:
            continue
        if key not in data or data.get(key) in (None, {}, [], ""):
            data[key] = value
    state_store.save(data)
    return {"ok": True, "state": state_store.summary()}


@app.post("/v1/state/reset")
async def reset_state() -> Dict[str, Any]:
    from .state import empty_state

    state_store.save(empty_state())
    return {"ok": True, "state": state_store.summary()}


# --- Skill catalogue ------------------------------------------------------

@app.get("/v1/skills")
async def get_skills() -> Dict[str, Any]:
    skills = load_skill_catalogue()
    return {"skills": skills, "count": len(skills), "status": skill_status()}


# --- Agent Skill Catalog (Step 16) ------------------------------------------

TEAMZ_SKILL_CATALOG_PATH = Path(__file__).resolve().parent / "skills_catalog_agent.json"
TEAMZ_SKILL_INDEX_PATH = Path(__file__).resolve().parent / "skills_index_agent.json"
TEAMZ_SKILL_CATALOG_JSONL_PATH = Path(__file__).resolve().parent / "skills_catalog_agent.jsonl"


def _load_agent_skill_catalog() -> Dict[str, Any]:
    """Load the full agent skill catalog."""
    if TEAMZ_SKILL_CATALOG_PATH.exists():
        with open(TEAMZ_SKILL_CATALOG_PATH) as f:
            return json.load(f)
    return {"meta": {}, "skills": [], "index": {}}


def _load_agent_skill_index() -> Dict[str, Any]:
    """Load the agent skill index."""
    if TEAMZ_SKILL_INDEX_PATH.exists():
        with open(TEAMZ_SKILL_INDEX_PATH) as f:
            return json.load(f)
    return {}


def _load_agent_skill_catalog_jsonl() -> List[Dict[str, Any]]:
    """Load the agent skill catalog as JSONL lines."""
    skills = []
    if TEAMZ_SKILL_CATALOG_JSONL_PATH.exists():
        with open(TEAMZ_SKILL_CATALOG_JSONL_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        skills.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return skills


@app.get("/v1/skills/agent-catalog")
async def get_agent_skill_catalog() -> Dict[str, Any]:
    """Get the full agent-only skill catalog (Step 16)."""
    catalog = _load_agent_skill_catalog()
    return {
        "ok": True,
        "meta": catalog.get("meta", {}),
        "count": len(catalog.get("skills", [])),
        "skills": catalog.get("skills", []),
    }


@app.get("/v1/skills/agent-catalog/index")
async def get_agent_skill_index() -> Dict[str, Any]:
    """Get the inverted index for the agent skill catalog."""
    index = _load_agent_skill_index()
    return {"ok": True, "index": index}


@app.get("/v1/skills/agent-catalog/jsonl")
async def get_agent_skill_catalog_jsonl() -> Dict[str, Any]:
    """Get the agent skill catalog as JSONL lines (streaming-friendly)."""
    skills = _load_agent_skill_catalog_jsonl()
    return {"ok": True, "count": len(skills), "skills": skills}


@app.get("/v1/skills/agent-catalog/search")
async def search_agent_skills(q: str = "", ns: str = "", cat: str = "", cap: str = "", tag: str = "", limit: int = 50) -> Dict[str, Any]:
    """Search the agent skill catalog by query, namespace, category, capability, or tag."""
    catalog = _load_agent_skill_catalog()
    skills = catalog.get("skills", [])
    
    results = []
    q_lower = q.lower()
    
    for skill in skills:
        match = True
        
        if q and q_lower not in skill.get("desc", "").lower() and q_lower not in skill.get("intent", "").lower() and q_lower not in skill.get("id", "").lower():
            match = False
        if ns and ns not in skill.get("ns", ""):
            match = False
        if cat and cat not in skill.get("cat", ""):
            match = False
        if cap and cap not in skill.get("caps", []):
            match = False
        if tag and tag not in skill.get("tags", []):
            match = False
        
        if match:
            results.append(skill)
            if len(results) >= limit:
                break
    
    return {"ok": True, "query": q, "filters": {"ns": ns, "cat": cat, "cap": cap, "tag": tag}, "count": len(results), "skills": results}


@app.post("/v1/skills/agent-catalog/refresh")
async def refresh_agent_skill_catalog() -> Dict[str, Any]:
    """Regenerate the agent skill catalog from toolchest."""
    import subprocess
    try:
        result = subprocess.run(
            ["python", "toolchest/generate_skills_catalog.py"],
            cwd="/opt/mem20",
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            # Copy generated files to teamz
            import shutil
            shutil.copy2("/opt/mem20/toolchest/skills/skills.catalog.agent.json", TEAMZ_SKILL_CATALOG_PATH)
            shutil.copy2("/opt/mem20/toolchest/skills/skills.index.agent.json", TEAMZ_SKILL_INDEX_PATH)
            shutil.copy2("/opt/mem20/toolchest/skills/skills.catalog.agent.jsonl", TEAMZ_SKILL_CATALOG_JSONL_PATH)
            return {"ok": True, "refreshed": True, "output": result.stdout}
        else:
            return {"ok": False, "error": result.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# --- Goals (room objectives) ----------------------------------------------

@app.get("/v1/goals")
async def get_goals() -> Dict[str, Any]:
    state = state_store.load()
    return {"goals": state.get("goals") or {}, "worker": worker.status()}


@app.post("/v1/goals")
async def set_goal(req: SetGoalRequest) -> Dict[str, Any]:
    text = (req.text or "").strip()
    state = state_store.load()
    goals = dict(state.get("goals") or {})
    if not text:
        goals.pop(req.conversationId, None)
        state["goals"] = goals
        state_store.save(state)
        return {"ok": True, "cleared": True, "conversationId": req.conversationId}
    existing = goals.get(req.conversationId) or {}
    goals[req.conversationId] = {
        "text": text,
        "active": bool(req.active) if not existing.get("done") else False,
        "done": bool(existing.get("done")),
        "status": existing.get("status", "active"),
        "progress": int(existing.get("progress", 0) or 0),
        "steps": int(existing.get("steps", 0) or 0),
        "lastStep": existing.get("lastStep"),
        "nextStep": existing.get("nextStep"),
        "lastError": None,
        "lastAgentId": existing.get("lastAgentId"),
        "createdAt": int(existing.get("createdAt") or time.time() * 1000),
        "updatedAt": int(time.time() * 1000),
        "cooldownUntil": None,
    }
    state["goals"] = goals
    state_store.save(state)
    if settings.goal_worker_enabled and goals[req.conversationId]["active"]:
        await worker.start()
    return {"ok": True, "goal": goals[req.conversationId]}


@app.get("/v1/goals/{conversation_id}")
async def get_goal(conversation_id: str) -> Dict[str, Any]:
    goals = state_store.load().get("goals") or {}
    goal = goals.get(conversation_id)
    if not goal:
        raise HTTPException(status_code=404, detail="no goal for this room")
    return {"ok": True, "conversationId": conversation_id, "goal": goal}


@app.delete("/v1/goals/{conversation_id}")
async def delete_goal(conversation_id: str) -> Dict[str, Any]:
    state = state_store.load()
    goals = dict(state.get("goals") or {})
    existed = goals.pop(conversation_id, None) is not None
    state["goals"] = goals
    state_store.save(state)
    return {"ok": True, "cleared": existed}


@app.post("/v1/goals/{conversation_id}/tick")
async def tick_goal(conversation_id: str) -> Dict[str, Any]:
    result = await worker.tick_conversation(conversation_id)
    return result


# --- Tasks / activity -----------------------------------------------------

@app.get("/v1/tasks")
async def get_tasks() -> Dict[str, Any]:
    state = state_store.load()
    return {"tasks": state.get("tasks") or [], "activity": (state.get("activity") or [])[-100:]}


@app.get("/v1/activity")
async def get_activity(limit: int = 100) -> Dict[str, Any]:
    state = state_store.load()
    items = state.get("activity") or []
    return {"activity": items[-max(1, min(limit, 500)):]}


# --- Terminal -------------------------------------------------------------

@app.get("/v1/terminal/status")
async def terminal_status_endpoint() -> Dict[str, Any]:
    return terminal_status()


@app.post("/v1/terminal/exec")
async def terminal_exec_endpoint(req: TerminalExecRequest) -> Dict[str, Any]:
    timeout = req.timeout
    if timeout is not None:
        timeout = max(1.0, min(float(timeout), 600.0))
    return terminal_exec(
        req.command,
        cwd=req.cwd,
        timeout=timeout,
        agent_id=req.agentId,
    ).to_dict()


# --- File tools -----------------------------------------------------------

@app.get("/v1/files/status")
async def files_status_endpoint() -> Dict[str, Any]:
    return files_status()


@app.post("/v1/files/read")
async def files_read(req: FileReadRequest) -> Dict[str, Any]:
    return file_read(req.path, offset=req.offset or 0, limit=req.limit or 2000).to_dict()


@app.post("/v1/files/write")
async def files_write(req: FileWriteRequest) -> Dict[str, Any]:
    return file_write(req.path, req.content, append=req.append).to_dict()


@app.post("/v1/files/edit")
async def files_edit(req: FileEditRequest) -> Dict[str, Any]:
    return file_edit(req.path, req.old_string, req.new_string, replace_all=req.replace_all).to_dict()


@app.post("/v1/files/list")
async def files_list(req: FileListRequest) -> Dict[str, Any]:
    return file_list(req.path or ".").to_dict()


# --- Agent runtime tool actions (terminal/files/gh/github) ----------------

@app.post("/v1/runtime/exec")
async def runtime_exec(req: RuntimeExecRequest) -> Dict[str, Any]:
    results = await execute_actions([a.model_dump() for a in req.actions], agent_id=req.agentId)
    return {"ok": True, "results": results}


# --- Autonomous worker control -------------------------------------------

@app.get("/v1/worker/status")
async def worker_status() -> Dict[str, Any]:
    return worker.status()


@app.get("/v1/worker/log")
async def worker_log(limit: int = 50) -> Dict[str, Any]:
    return {"log": worker.log[-max(1, min(limit, 200)):]}


@app.post("/v1/worker/control")
async def worker_control(req: WorkerControlRequest) -> Dict[str, Any]:
    action = (req.action or "").strip().lower()
    if action == "start":
        return await worker.start()
    if action == "stop":
        return await worker.stop()
    if action == "tick":
        if req.conversationId:
            return await worker.tick_conversation(req.conversationId)
        results = await worker.tick_all()
        return {"ok": True, "results": results}
    if action == "self-improve":
        return await worker.self_improve(req.agentId)
    raise HTTPException(status_code=400, detail="action must be start|stop|tick|self-improve")


# --- Fleet Integration (Steps 6-9) ------------------------------------------

from pydantic import BaseModel


class NamespaceCreateRequest(BaseModel):
    agent_name: str


class KanbanSyncRequest(BaseModel):
    conversation_id: str
    goal_text: str
    agent_id: Optional[str] = None


class KanbanUpdateRequest(BaseModel):
    card_id: str
    column: Optional[str] = None
    title: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None


class A2APeerRequest(BaseModel):
    name: str
    url: str
    capabilities: List[str] = []
    health_check_url: Optional[str] = None


class DecisionRecordRequest(BaseModel):
    agent_name: str
    decision: str
    rationale: str
    conversation_id: Optional[str] = None
    tags: Optional[List[str]] = None


@app.get("/v1/fleet/status")
async def fleet_status() -> Dict[str, Any]:
    """Get fleet integration status."""
    if not settings.fleet_enabled:
        return {"enabled": False}
    client = get_fleet_client()
    namespaces = await client.list_namespaces()
    a2a_peers = client.get_a2a_peers()
    health = await client.health_check_a2a_peers() if settings.a2a_enabled else {}
    return {
        "enabled": True,
        "gateway_url": settings.fleet_gateway_url,
        "agent_name": settings.fleet_agent_name,
        "namespaces": [
            {
                "agent_name": ns.agent_name,
                "store_path": ns.store_path,
                "created_at": ns.created_at,
                "status": ns.status,
            }
            for ns in namespaces
        ],
        "a2a_peers": [
            {
                "name": p.name,
                "url": p.url,
                "capabilities": p.capabilities,
                "status": p.status,
                "last_seen": p.last_seen,
            }
            for p in a2a_peers
        ],
        "a2a_health": health,
        "kanban_cards": len(client._kanban_cache),
        "decisions_recorded": len(client._decisions),
        "fleet_rules": {
            "decision_persistence": settings.fleet_decision_persistence,
            "fail_log_review": settings.fleet_fail_log_review,
        },
    }


@app.post("/v1/fleet/namespace/create")
async def fleet_namespace_create(req: NamespaceCreateRequest) -> Dict[str, Any]:
    """Create isolated mem20 namespace for an agent (Step 6)."""
    if not settings.fleet_enabled:
        raise HTTPException(status_code=503, detail="fleet integration disabled")
    client = get_fleet_client()
    namespace = await client.create_namespace(req.agent_name)
    return {
        "ok": True,
        "agent_name": namespace.agent_name,
        "store_path": namespace.store_path,
        "created_at": namespace.created_at,
        "status": namespace.status,
    }


@app.get("/v1/fleet/namespace/{agent_name}")
async def fleet_namespace_get(agent_name: str) -> Dict[str, Any]:
    """Get namespace for an agent."""
    if not settings.fleet_enabled:
        raise HTTPException(status_code=503, detail="fleet integration disabled")
    client = get_fleet_client()
    namespace = await client.get_namespace(agent_name)
    return {
        "ok": True,
        "agent_name": namespace.agent_name,
        "store_path": namespace.store_path,
        "created_at": namespace.created_at,
        "status": namespace.status,
    }


@app.get("/v1/fleet/namespaces")
async def fleet_namespaces_list() -> Dict[str, Any]:
    """List all agent namespaces."""
    if not settings.fleet_enabled:
        raise HTTPException(status_code=503, detail="fleet integration disabled")
    client = get_fleet_client()
    namespaces = await client.list_namespaces()
    return {
        "ok": True,
        "namespaces": [
            {
                "agent_name": ns.agent_name,
                "store_path": ns.store_path,
                "created_at": ns.created_at,
                "status": ns.status,
            }
            for ns in namespaces
        ],
    }


# --- Kanban Integration (Step 7) ---

@app.post("/v1/fleet/kanban/sync-goal")
async def fleet_kanban_sync_goal(req: KanbanSyncRequest) -> Dict[str, Any]:
    """Sync a teamz goal to kanban as a card (Step 7)."""
    if not settings.kanban_enabled:
        raise HTTPException(status_code=503, detail="kanban integration disabled")
    client = get_fleet_client()
    card = await client.sync_goal_to_kanban(req.conversation_id, req.goal_text, req.agent_id)
    return {"ok": True, "card": card.__dict__}


@app.post("/v1/fleet/kanban/update")
async def fleet_kanban_update(req: KanbanUpdateRequest) -> Dict[str, Any]:
    """Update kanban card (move column, etc.)."""
    if not settings.kanban_enabled:
        raise HTTPException(status_code=503, detail="kanban integration disabled")
    client = get_fleet_client()
    card = await client.update_kanban_card(req.card_id, req.column, title=req.title, priority=req.priority, tags=req.tags)
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    return {"ok": True, "card": card.__dict__}


@app.get("/v1/fleet/kanban/cards")
async def fleet_kanban_list(conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """List kanban cards, optionally filtered by conversation."""
    if not settings.kanban_enabled:
        raise HTTPException(status_code=503, detail="kanban integration disabled")
    client = get_fleet_client()
    cards = await client.get_kanban_cards(conversation_id)
    return {"ok": True, "cards": [c.__dict__ for c in cards]}


# --- A2A Setup (Step 8) ---

@app.post("/v1/fleet/a2a/peer/register")
async def fleet_a2a_register_peer(req: A2APeerRequest) -> Dict[str, Any]:
    """Register an A2A peer agent (Step 8)."""
    if not settings.a2a_enabled:
        raise HTTPException(status_code=503, detail="A2A integration disabled")
    client = get_fleet_client()
    from .fleet import A2APeer
    peer = A2APeer(name=req.name, url=req.url, capabilities=req.capabilities, health_check_url=req.health_check_url)
    client.register_a2a_peer(peer)
    return {"ok": True, "peer": peer.__dict__}


@app.get("/v1/fleet/a2a/peers")
async def fleet_a2a_list_peers() -> Dict[str, Any]:
    """List all registered A2A peers."""
    if not settings.a2a_enabled:
        raise HTTPException(status_code=503, detail="A2A integration disabled")
    client = get_fleet_client()
    peers = client.get_a2a_peers()
    return {"ok": True, "peers": [p.__dict__ for p in peers]}


@app.post("/v1/fleet/a2a/health-check")
async def fleet_a2a_health_check() -> Dict[str, Any]:
    """Health check all A2A peers."""
    if not settings.a2a_enabled:
        raise HTTPException(status_code=503, detail="A2A integration disabled")
    client = get_fleet_client()
    health = await client.health_check_a2a_peers()
    return {"ok": True, "health": health}


# --- Fleetwide Rules Enforcement (Step 9) ---

@app.post("/v1/fleet/rules/decision/record")
async def fleet_rules_record_decision(req: DecisionRecordRequest) -> Dict[str, Any]:
    """Record a decision per fleetwide decision persistence rule (Step 9)."""
    if not settings.fleet_rules_enabled:
        raise HTTPException(status_code=503, detail="fleet rules enforcement disabled")
    client = get_fleet_client()
    decision = await client.record_decision(
        req.agent_name,
        req.decision,
        req.rationale,
        req.conversation_id,
        req.tags,
    )
    return {"ok": True, "decision": decision.__dict__}


@app.get("/v1/fleet/rules/decisions")
async def fleet_rules_list_decisions(agent_name: Optional[str] = None) -> Dict[str, Any]:
    """List recorded decisions."""
    if not settings.fleet_rules_enabled:
        raise HTTPException(status_code=503, detail="fleet rules enforcement disabled")
    client = get_fleet_client()
    decisions = client.get_decisions(agent_name)
    return {"ok": True, "decisions": [d.__dict__ for d in decisions]}


@app.get("/v1/fleet/rules/fail-logs")
async def fleet_rules_review_fail_logs(agent_name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Review failure logs per fleetwide fail log review rule (Step 9)."""
    if not settings.fleet_rules_enabled:
        raise HTTPException(status_code=503, detail="fleet rules enforcement disabled")
    client = get_fleet_client()
    logs = await client.review_fail_logs(agent_name, limit)
    return {"ok": True, "logs": logs, "count": len(logs)}


# --- Phase 8: Observability & Debugging ------------------------------------

@app.post("/v1/observability/traces/start")
async def observability_start_trace(req: dict) -> Dict[str, Any]:
    """Start a new distributed trace."""
    trace = await worker.start_trace(
        operation_name=req.get("operation_name", "operation"),
        room_id=req.get("room_id"),
        goal_id=req.get("goal_id"),
        agent_id=req.get("agent_id"),
        tags=req.get("tags"),
        attributes=req.get("attributes"),
    )
    return {"ok": True, "trace": trace.model_dump()}


@app.post("/v1/observability/traces/end")
async def observability_end_trace(req: dict) -> Dict[str, Any]:
    """End a distributed trace."""
    trace = await worker.end_trace(
        trace_id=req.get("trace_id"),
        status=req.get("status", "ok"),
    )
    if not trace:
        raise HTTPException(status_code=404, detail="trace not found")
    return {"ok": True, "trace": trace.model_dump()}


@app.get("/v1/observability/traces/{trace_id}")
async def observability_get_trace(trace_id: str) -> Dict[str, Any]:
    """Get a trace by ID."""
    trace = await worker.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="trace not found")
    return {"ok": True, "trace": trace.model_dump()}


@app.get("/v1/observability/traces")
async def observability_query_traces(
    room_id: Optional[str] = None,
    goal_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Query traces with filters."""
    traces = await worker.query_traces(
        room_id=room_id,
        goal_id=goal_id,
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "traces": [t.model_dump() for t in traces], "count": len(traces)}


@app.get("/v1/observability/token-usage")
async def observability_get_token_usage(
    room_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get token usage records with filters."""
    records = await worker.get_token_usage(
        room_id=room_id,
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "records": [r.model_dump() for r in records], "count": len(records)}


@app.get("/v1/observability/cost-budgets")
async def observability_get_cost_budget(
    scope: str,
    scope_id: str,
) -> Dict[str, Any]:
    """Get cost budget for a scope."""
    budget = await worker.get_cost_budget(scope, scope_id)
    if not budget:
        raise HTTPException(status_code=404, detail="budget not found")
    return {"ok": True, "budget": budget.model_dump()}


@app.post("/v1/observability/cost-budgets")
async def observability_create_cost_budget(req: CreateCostBudgetRequest) -> Dict[str, Any]:
    """Create a cost budget."""
    budget = await worker.create_cost_budget(
        scope=req.scope,
        scope_id=req.scope_id,
        budget_usd=req.budget_usd,
        period_start=req.period_start,
        period_end=req.period_end,
        alert_threshold_pct=req.alert_threshold_pct,
        hard_stop=req.hard_stop,
    )
    return {"ok": True, "budget": budget.model_dump()}


@app.post("/v1/observability/cost-budgets/check")
async def observability_check_cost_budgets() -> Dict[str, Any]:
    """Check all cost budgets and trigger alerts if needed."""
    alerts = await worker.check_cost_budgets()
    return {"ok": True, "alerts": alerts}


@app.post("/v1/observability/alert-rules")
async def observability_create_alert_rule(req: CreateAlertRuleRequest) -> Dict[str, Any]:
    """Create an alert rule."""
    rule = await worker.create_alert_rule(req)
    return {"ok": True, "rule": rule.model_dump()}


@app.get("/v1/observability/alert-rules")
async def observability_get_alert_rules() -> Dict[str, Any]:
    """Get all alert rules."""
    rules = await worker.get_alert_rules()
    return {"ok": True, "rules": [r.model_dump() for r in rules]}


@app.post("/v1/observability/alerts/check")
async def observability_check_alerts() -> Dict[str, Any]:
    """Check all alert rules and trigger alerts."""
    alerts = await worker.check_alerts()
    return {"ok": True, "alerts": [a.model_dump() for a in alerts]}


@app.post("/v1/observability/alerts/{alert_id}/acknowledge")
async def observability_acknowledge_alert(alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
    """Acknowledge an alert."""
    result = await worker.acknowledge_alert(alert_id, acknowledged_by)
    return result


@app.get("/v1/observability/alerts")
async def observability_get_alerts(
    room_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get alerts with filters."""
    alerts = await worker.get_alerts(
        room_id=room_id,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
    )
    return {"ok": True, "alerts": [a.model_dump() for a in alerts], "count": len(alerts)}


@app.get("/v1/observability/audit-log")
async def observability_get_audit_log(
    actor_id: Optional[str] = None,
    actor_type: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Query audit log with filters."""
    logs = await worker.get_audit_log(
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "logs": [l.model_dump() for l in logs], "count": len(logs)}


@app.post("/v1/observability/replay/snapshot")
async def observability_create_replay_snapshot(req: dict) -> Dict[str, Any]:
    """Create a replay snapshot for deterministic replay."""
    snapshot = await worker.create_replay_snapshot(
        trace_id=req.get("trace_id"),
        seed=req.get("seed", ""),
        step=req.get("step", 0),
        state_hash=req.get("state_hash", ""),
        prompt=req.get("prompt", ""),
        context=req.get("context", {}),
    )
    return {"ok": True, "snapshot": snapshot.model_dump()}


@app.get("/v1/observability/replay/snapshots/{trace_id}")
async def observability_get_replay_snapshots(trace_id: str) -> Dict[str, Any]:
    """Get all snapshots for a trace."""
    snapshots = await worker.get_replay_snapshots(trace_id)
    return {"ok": True, "snapshots": [s.model_dump() for s in snapshots]}


@app.get("/v1/observability/timeline/{room_id}")
async def observability_get_room_timeline(
    room_id: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    agent_id: Optional[str] = None,
    limit: int = 200,
) -> Dict[str, Any]:
    """Get timeline events for Gantt chart view."""
    events = await worker.get_room_timeline(
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        agent_id=agent_id,
        limit=limit,
    )
    return {"ok": True, "events": [e.model_dump() for e in events], "count": len(events)}


@app.get("/v1/observability/config")
async def observability_get_config() -> Dict[str, Any]:
    """Get current observability configuration."""
    config = await worker.get_observability_config()
    return {"ok": True, "config": config.model_dump()}


@app.post("/v1/observability/config")
async def observability_update_config(config: ObservabilityConfig) -> Dict[str, Any]:
    """Update observability configuration."""
    config = await worker.update_observability_config(config)
    return {"ok": True, "config": config.model_dump()}


@app.post("/v1/observability/traces/export")
async def observability_export_traces(req: ExportTracesRequest) -> Dict[str, Any]:
    """Export traces in specified format (jaeger, zipkin, tempo, json)."""
    result = await worker.export_traces(req)
    return {"ok": True, "result": result}


@app.post("/v1/observability/alert-rules")
async def observability_create_alert_rule(req: CreateAlertRuleRequest) -> Dict[str, Any]:
    """Create an alert rule."""
    rule = await worker.create_alert_rule(req)
    return {"ok": True, "rule": rule.model_dump()}


@app.get("/v1/observability/alert-rules")
async def observability_get_alert_rules() -> Dict[str, Any]:
    """Get all alert rules."""
    rules = await worker.get_alert_rules()
    return {"ok": True, "rules": [r.model_dump() for r in rules]}


@app.post("/v1/observability/alerts/check")
async def observability_check_alerts() -> Dict[str, Any]:
    """Check all alert rules and trigger alerts."""
    alerts = await worker.check_alerts()
    return {"ok": True, "alerts": [a.model_dump() for a in alerts]}


@app.post("/v1/observability/alerts/{alert_id}/acknowledge")
async def observability_acknowledge_alert(alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
    """Acknowledge an alert."""
    result = await worker.acknowledge_alert(alert_id, acknowledged_by)
    return result


@app.get("/v1/observability/alerts")
async def observability_get_alerts(
    room_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Get alerts with filters."""
    alerts = await worker.get_alerts(
        room_id=room_id,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
    )
    return {"ok": True, "alerts": [a.model_dump() for a in alerts], "count": len(alerts)}


@app.get("/v1/observability/audit-log")
async def observability_get_audit_log(
    actor_id: Optional[str] = None,
    actor_type: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Query audit log with filters."""
    logs = await worker.get_audit_log(
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return {"ok": True, "logs": [l.model_dump() for l in logs], "count": len(logs)}


@app.post("/v1/observability/replay/snapshot")
async def observability_create_replay_snapshot(req: dict) -> Dict[str, Any]:
    """Create a replay snapshot for deterministic replay."""
    snapshot = await worker.create_replay_snapshot(
        trace_id=req.get("trace_id"),
        seed=req.get("seed", ""),
        step=req.get("step", 0),
        state_hash=req.get("state_hash", ""),
        prompt=req.get("prompt", ""),
        context=req.get("context", {}),
    )
    return {"ok": True, "snapshot": snapshot.model_dump()}


@app.get("/v1/observability/replay/snapshots/{trace_id}")
async def observability_get_replay_snapshots(trace_id: str) -> Dict[str, Any]:
    """Get all snapshots for a trace."""
    snapshots = await worker.get_replay_snapshots(trace_id)
    return {"ok": True, "snapshots": [s.model_dump() for s in snapshots]}


@app.get("/v1/observability/timeline/{room_id}")
async def observability_get_room_timeline(
    room_id: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    agent_id: Optional[str] = None,
    limit: int = 200,
) -> Dict[str, Any]:
    """Get timeline events for Gantt chart view."""
    events = await worker.get_room_timeline(
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
        agent_id=agent_id,
        limit=limit,
    )
    return {"ok": True, "events": [e.model_dump() for e in events], "count": len(events)}


@app.get("/v1/observability/config")
async def observability_get_config() -> Dict[str, Any]:
    """Get current observability configuration."""
    config = await worker.get_observability_config()
    return {"ok": True, "config": config.model_dump()}


@app.post("/v1/observability/config")
async def observability_update_config(config: ObservabilityConfig) -> Dict[str, Any]:
    """Update observability configuration."""
    config = await worker.update_observability_config(config)
    return {"ok": True, "config": config.model_dump()}


@app.post("/v1/observability/traces/export")
async def observability_export_traces(req: ExportTracesRequest) -> Dict[str, Any]:
    """Export traces in specified format (jaeger, zipkin, tempo, json)."""
    result = await worker.export_traces(req)
    return {"ok": True, "result": result}
