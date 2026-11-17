"""Agent execution tools: real shell, real file editing, GitHub/gh.

These are the "hands" the agents use to do work themselves instead of telling
the user what to type. Everything runs server-side inside the configured
workspace root, and every call returns a structured, JSON-safe result.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import settings
from .state import StateStore
from .models import RouteContext


class ToolError(RuntimeError):
    """A tool call was rejected or could not be completed."""


@dataclass
class ToolResult:
    ok: bool
    tool: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    truncated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "tool": self.tool,
            "data": self.data,
            "error": self.error,
            "truncated": self.truncated,
        }


MAX_OUTPUT_CHARS = 200_000


def _clip(text: str, limit: int = MAX_OUTPUT_CHARS) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit] + f"\n…[truncated {len(text) - limit} chars]", True


# --------------------------------------------------------------------------
# Terminal
# --------------------------------------------------------------------------

def terminal_status() -> Dict[str, Any]:
    shell = shutil.which("bash") or shutil.which("sh") or shutil.which("zsh")
    return {
        "enabled": settings.terminal_enabled,
        "shell": shell,
        "workdir": settings.terminal_workdir,
        "timeout_s": settings.terminal_timeout_s,
        "allow_all": settings.terminal_allow_all,
        "allow_prefixes": settings.terminal_allow_prefixes,
    }


def _terminal_policy_ok(command: str) -> tuple[bool, str]:
    if settings.terminal_allow_all:
        return True, ""
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return False, f"could not parse command: {e}"
    if not parts:
        return False, "empty command"
    exe = os.path.basename(parts[0])
    if exe in {"sudo", "su", "doas"}:
        return False, f"'{exe}' is not permitted"
    if exe not in settings.terminal_allow_prefixes:
        return False, f"'{exe}' is not in TEAMZ_TERMINAL_ALLOW_PREFIXES"
    return True, ""


def terminal_exec(
    command: str,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    agent_id: Optional[str] = None,
) -> ToolResult:
    if not settings.terminal_enabled:
        return ToolResult(False, "terminal", error="terminal access is disabled")
    command = (command or "").strip()
    if not command:
        return ToolResult(False, "terminal", error="command is required")
    ok, reason = _terminal_policy_ok(command)
    if not ok:
        return ToolResult(False, "terminal", error=reason)

    workdir = Path(cwd or settings.terminal_workdir).expanduser()
    if not workdir.is_dir():
        return ToolResult(False, "terminal", error=f"working directory does not exist: {workdir}")
    shell = shutil.which("bash") or shutil.which("sh")
    if not shell:
        return ToolResult(False, "terminal", error="no shell available")

    timeout_f = min(max(timeout if timeout is not None else settings.terminal_timeout_s, 1.0), 600.0)
    started = time.time()
    try:
        proc = subprocess.run(
            [shell, "-lc", command],
            cwd=str(workdir),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_f,
            check=False,
        )
        elapsed_ms = int((time.time() - started) * 1000)
        out = proc.stdout or ""
        err = proc.stderr or ""
        combined = out
        if err:
            combined += (("\n" if combined else "") + err)
        combined, truncated = _clip(combined)
        return ToolResult(
            proc.returncode == 0,
            "terminal",
            data={
                "command": command,
                "cwd": str(workdir),
                "exit_code": proc.returncode,
                "stdout": out,
                "stderr": err,
                "output": combined,
                "elapsed_ms": elapsed_ms,
                "agent_id": agent_id,
                "timed_out": False,
            },
            truncated=truncated,
        )
    except subprocess.TimeoutExpired as e:
        elapsed_ms = int((time.time() - started) * 1000)
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        err = (e.stderr or "") if isinstance(e.stderr, str) else ""
        combined, truncated = _clip((out + "\n" + err).strip())
        return ToolResult(
            False,
            "terminal",
            data={
                "command": command,
                "cwd": str(workdir),
                "exit_code": None,
                "stdout": out,
                "stderr": err,
                "output": combined + f"\n[timeout after {int(timeout_f)}s]",
                "elapsed_ms": elapsed_ms,
                "agent_id": agent_id,
                "timed_out": True,
            },
            error=f"command timed out after {int(timeout_f)}s",
            truncated=truncated,
        )
    except Exception as e:
        return ToolResult(False, "terminal", error=str(e))


# --------------------------------------------------------------------------
# File tools
# --------------------------------------------------------------------------

def files_status() -> Dict[str, Any]:
    return {
        "enabled": settings.files_enabled,
        "root": settings.files_root,
        "max_bytes": settings.files_max_bytes,
    }


def _safe_path(path: str, *, must_exist: bool = False) -> Path:
    import os
    root = Path(os.path.expanduser(settings.files_root)).resolve()
    raw = Path(os.path.expanduser(str(path or "")))
    candidate = raw if raw.is_absolute() else (root / raw)
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as e:
        raise ToolError(f"invalid path: {e}")
    root_s = str(root)
    res_s = str(resolved)
    if res_s != root_s and not res_s.startswith(root_s + os.sep):
        raise ToolError(f"path escapes the workspace root ({root_s})")
    if must_exist and not resolved.exists():
        raise ToolError(f"no such file or directory: {path}")
    return resolved


def _read_text(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    if b"\x00" in data[:4096]:
        return "", True
    return data.decode("utf-8", errors="replace"), False


def file_read(path: str, *, offset: int = 0, limit: int = 2000) -> ToolResult:
    if not settings.files_enabled:
        return ToolResult(False, "read_file", error="file tools are disabled")
    try:
        p = _safe_path(path, must_exist=True)
        if p.is_dir():
            return ToolResult(False, "read_file", error=f"{path} is a directory")
        text, binary = _read_text(p)
        if binary:
            return ToolResult(False, "read_file", error=f"{path} looks binary; refusing to dump it")
        lines = text.splitlines()
        total = len(lines)
        start = max(0, offset)
        end = min(total, start + max(1, limit))
        body = "\n".join(lines[start:end])
        body, truncated = _clip(body)
        return ToolResult(
            True,
            "read_file",
            data={"path": str(p), "total_lines": total, "offset": start, "limit": end - start, "content": body},
            truncated=truncated,
        )
    except ToolError as e:
        return ToolResult(False, "read_file", error=str(e))
    except Exception as e:
        return ToolResult(False, "read_file", error=str(e))


def file_write(path: str, content: str, *, append: bool = False) -> ToolResult:
    if not settings.files_enabled:
        return ToolResult(False, "write_file", error="file tools are disabled")
    try:
        p = _safe_path(path)
        if p.is_dir():
            return ToolResult(False, "write_file", error=f"{path} is a directory")
        if p.exists() and p.stat().st_size > settings.files_max_bytes:
            return ToolResult(False, "write_file", error=f"{path} exceeds the max file size")
        if content and len(content.encode("utf-8")) > settings.files_max_bytes:
            return ToolResult(False, "write_file", error="content exceeds TEAMZ_FILES_MAX_BYTES")
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with p.open(mode, encoding="utf-8") as f:
            f.write(content)
        size = p.stat().st_size
        return ToolResult(True, "write_file", data={"path": str(p), "bytes": size, "append": bool(append)})
    except ToolError as e:
        return ToolResult(False, "write_file", error=str(e))
    except Exception as e:
        return ToolResult(False, "write_file", error=str(e))


def file_edit(
    path: str,
    old_string: str,
    new_string: str,
    *,
    replace_all: bool = False,
) -> ToolResult:
    if not settings.files_enabled:
        return ToolResult(False, "edit_file", error="file tools are disabled")
    if old_string == new_string:
        return ToolResult(False, "edit_file", error="old_string and new_string are identical")
    try:
        p = _safe_path(path, must_exist=True)
        if p.is_dir():
            return ToolResult(False, "edit_file", error=f"{path} is a directory")
        text, binary = _read_text(p)
        if binary:
            return ToolResult(False, "edit_file", error=f"{path} looks binary; edit text files only")
        count = text.count(old_string)
        if count == 0:
            return ToolResult(False, "edit_file", error="old_string not found in file")
        if count > 1 and not replace_all:
            return ToolResult(
                False,
                "edit_file",
                error=f"old_string is not unique ({count} matches); pass replace_all=true or more context",
            )
        new_text = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
        if len(new_text.encode("utf-8")) > settings.files_max_bytes:
            return ToolResult(False, "edit_file", error="result exceeds TEAMZ_FILES_MAX_BYTES")
        p.write_text(new_text, encoding="utf-8")
        return ToolResult(
            True,
            "edit_file",
            data={"path": str(p), "replacements": count if replace_all else 1, "bytes": len(new_text.encode("utf-8"))},
        )
    except ToolError as e:
        return ToolResult(False, "edit_file", error=str(e))
    except Exception as e:
        return ToolResult(False, "edit_file", error=str(e))


def file_list(path: str = ".", *, max_entries: int = 500) -> ToolResult:
    if not settings.files_enabled:
        return ToolResult(False, "list_files", error="file tools are disabled")
    try:
        p = _safe_path(path, must_exist=True)
        if not p.is_dir():
            return ToolResult(False, "list_files", error=f"{path} is not a directory")
        entries: List[Dict[str, Any]] = []
        for child in sorted(p.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
            try:
                st = child.stat()
            except OSError:
                continue
            entries.append(
                {
                    "name": child.name,
                    "path": str(child),
                    "type": "dir" if child.is_dir() else "file",
                    "size": st.st_size,
                    "mtime": int(st.st_mtime * 1000),
                }
            )
            if len(entries) >= max_entries:
                break
        return ToolResult(
            True,
            "list_files",
            data={"path": str(p), "entries": entries, "count": len(entries), "truncated": len(entries) >= max_entries},
        )
    except ToolError as e:
        return ToolResult(False, "list_files", error=str(e))
    except Exception as e:
        return ToolResult(False, "list_files", error=str(e))


# --------------------------------------------------------------------------
# GitHub / gh
# --------------------------------------------------------------------------

def _gh_available() -> bool:
    return shutil.which("gh") is not None


def gh_status() -> Dict[str, Any]:
    from .connectors import gh_path

    path = gh_path()
    return {
        "enabled": settings.gh_enabled,
        "available": bool(path),
        "path": path,
        "configured": bool(path),
    }


def github_status() -> Dict[str, Any]:
    from .connectors import github_token

    token = github_token()
    return {
        "enabled": settings.github_enabled,
        "configured": bool(token),
        "auth": "token" if token else "none",
    }


def gh_run(args: List[str], *, cwd: Optional[str] = None, timeout: float = 60.0) -> ToolResult:
    from .connectors import gh_exec

    if not settings.gh_enabled:
        return ToolResult(False, "gh", error="gh access is disabled")
    if not isinstance(args, list) or not args or any(not isinstance(a, str) for a in args):
        return ToolResult(False, "gh", error="args must be a non-empty list of strings")
    res = gh_exec(args, cwd=cwd, timeout=timeout)
    out = (res.get("stdout") or "") + (res.get("stderr") or "")
    out, truncated = _clip(out)
    return ToolResult(
        bool(res.get("ok")),
        "gh",
        data={
            "args": args,
            "exit_code": res.get("exit_code"),
            "output": out,
            "json": res.get("json"),
        },
        error=None if res.get("ok") else (res.get("stderr") or "gh command failed"),
        truncated=truncated,
    )


def github_run(method: str, path: str, *, params: Optional[Dict[str, Any]] = None, body: Any = None) -> ToolResult:
    from .connectors import github_request

    if not settings.github_enabled:
        return ToolResult(False, "github", error="github access is disabled")
    if not path:
        return ToolResult(False, "github", error="path is required")
    res = github_request(method, path, params=params, json_body=body)
    data = res.get("data")
    if isinstance(data, (dict, list)):
        blob = json.dumps(data, ensure_ascii=False)
    else:
        blob = str(data)
    blob, truncated = _clip(blob)
    return ToolResult(
        bool(res.get("ok")),
        "github",
        data={"method": method.upper(), "path": path, "status": res.get("status"), "output": blob},
        error=None if res.get("ok") else f"github {res.get('status')}",
        truncated=truncated,
    )


# --------------------------------------------------------------------------
# Dispatcher
# --------------------------------------------------------------------------

TOOL_NAMES = {
    "terminal",
    "run_terminal",
    "shell",
    "write_file",
    "edit_file",
    "read_file",
    "list_files",
    "gh",
    "gh_exec",
    "github",
}


async def execute_tool(name: str, args: Optional[Dict[str, Any]] = None) -> ToolResult:
    """Execute one agent tool call by name. Never raises."""
    args = args if isinstance(args, dict) else {}
    tool = str(name or "").strip().lower()
    try:
        if tool in {"terminal", "run_terminal", "shell"}:
            return terminal_exec(
                str(args.get("command") or args.get("cmd") or ""),
                cwd=args.get("cwd") if isinstance(args.get("cwd"), str) else None,
                timeout=float(args["timeout"]) if isinstance(args.get("timeout"), (int, float)) else None,
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else None,
            )
        if tool == "write_file":
            return file_write(
                str(args.get("path") or args.get("file") or ""),
                str(args.get("content") if args.get("content") is not None else args.get("text") or ""),
                append=bool(args.get("append")),
            )
        if tool == "edit_file":
            return file_edit(
                str(args.get("path") or args.get("file") or ""),
                str(args.get("old_string") if args.get("old_string") is not None else args.get("old") or ""),
                str(args.get("new_string") if args.get("new_string") is not None else args.get("new") or ""),
                replace_all=bool(args.get("replace_all")),
            )
        if tool == "read_file":
            return file_read(
                str(args.get("path") or args.get("file") or ""),
                offset=int(args.get("offset") or 0),
                limit=int(args.get("limit") or 2000),
            )
        if tool == "list_files":
            return file_list(
                str(args.get("path") or args.get("dir") or "."),
                max_entries=int(args.get("max_entries") or 500),
            )
        if tool in {"gh", "gh_exec"}:
            return gh_run(
                list(args.get("args") or []) if isinstance(args.get("args"), list) else [],
                cwd=args.get("cwd") if isinstance(args.get("cwd"), str) else None,
                timeout=float(args.get("timeout") or 60.0),
            )
        if tool == "github":
            return github_run(
                str(args.get("method") or "GET"),
                str(args.get("path") or args.get("url") or ""),
                params=args.get("params") if isinstance(args.get("params"), dict) else None,
                body=args.get("body") if "body" in args else args.get("json"),
            )
        if tool == "run_tests":
            return await run_tests(
                path=args.get("path") if isinstance(args.get("path"), str) else None,
                framework=args.get("framework") if isinstance(args.get("framework"), str) else None,
                args=args.get("args") if isinstance(args.get("args"), list) else None,
                coverage=bool(args.get("coverage", True)),
            )
        if tool == "run_mutation_tests":
            return await run_mutation_tests(
                path=args.get("path") if isinstance(args.get("path"), str) else None,
                framework=args.get("framework") if isinstance(args.get("framework"), str) else None,
                timeout=float(args.get("timeout")) if isinstance(args.get("timeout"), (int, float)) else None,
            )
        if tool == "run_contract_tests":
            return await run_contract_tests(
                schema_path=args.get("schema_path") if isinstance(args.get("schema_path"), str) else None,
                base_url=args.get("base_url") if isinstance(args.get("base_url"), str) else None,
                endpoints=args.get("endpoints") if isinstance(args.get("endpoints"), list) else None,
            )
        if tool == "run_visual_regression":
            return await run_visual_regression(
                test_name=args.get("test_name") if isinstance(args.get("test_name"), str) else None,
                url=args.get("url") if isinstance(args.get("url"), str) else None,
                baseline_path=args.get("baseline_path") if isinstance(args.get("baseline_path"), str) else None,
                threshold_pct=float(args.get("threshold_pct")) if isinstance(args.get("threshold_pct"), (int, float)) else None,
            )
        if tool == "run_performance_benchmark":
            return await run_performance_benchmark(
                script_path=args.get("script_path") if isinstance(args.get("script_path"), str) else None,
                target_url=args.get("target_url") if isinstance(args.get("target_url"), str) else None,
                duration=args.get("duration") if isinstance(args.get("duration"), str) else None,
                vus=int(args.get("vus")) if isinstance(args.get("vus"), (int, float)) else None,
            )
        if tool == "run_security_scan":
            return await run_security_scan(
                tool=args.get("tool") if isinstance(args.get("tool"), str) else None,
                path=args.get("path") if isinstance(args.get("path"), str) else None,
                config=args.get("config") if isinstance(args.get("config"), str) else None,
            )
        if tool == "run_dependency_audit":
            return await run_dependency_audit(
                path=args.get("path") if isinstance(args.get("path"), str) else None,
                manager=args.get("manager") if isinstance(args.get("manager"), str) else None,
                auto_pr=bool(args.get("auto_pr")),
            )
        if tool == "detect_flaky_tests":
            return await detect_flaky_tests(
                path=args.get("path") if isinstance(args.get("path"), str) else None,
                framework=args.get("framework") if isinstance(args.get("framework"), str) else None,
                runs=int(args.get("runs")) if isinstance(args.get("runs"), (int, float)) else None,
            )
        if tool == "get_coverage_report":
            return await get_coverage_report(
                room_id=args.get("room_id") if isinstance(args.get("room_id"), str) else None,
                project_id=args.get("project_id") if isinstance(args.get("project_id"), str) else None,
                threshold_pct=float(args.get("threshold_pct")) if isinstance(args.get("threshold_pct"), (int, float)) else None,
            )
        if tool == "get_quality_dashboard":
            return await get_quality_dashboard(
                room_id=args.get("room_id") if isinstance(args.get("room_id"), str) else None,
            )
        if tool == "list_providers":
            return await list_providers()
        if tool == "add_provider":
            return await add_provider(config=args.get("config") if isinstance(args.get("config"), dict) else {})
        if tool == "update_provider":
            return await update_provider(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
                config=args.get("config") if isinstance(args.get("config"), dict) else {},
            )
        if tool == "remove_provider":
            return await remove_provider(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
            )
        if tool == "get_provider_health":
            return await get_provider_health()
        if tool == "set_provider_priority":
            return await set_provider_priority(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
                priority=int(args.get("priority") or 100),
            )
        if tool == "get_provider_models":
            return await get_provider_models(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
            )
        if tool == "set_provider_model":
            return await set_provider_model(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
                model=args.get("model") if isinstance(args.get("model"), str) else "",
            )
        if tool == "configure_byok":
            return await configure_byok(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                provider=args.get("provider") if isinstance(args.get("provider"), str) else "",
                api_key=args.get("api_key") if isinstance(args.get("api_key"), str) else "",
                api_key_env=args.get("api_key_env") if isinstance(args.get("api_key_env"), str) else None,
            )
        if tool == "get_byok_status":
            return await get_byok_status(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
            )
        if tool == "set_provider_cost_budget":
            return await set_provider_cost_budget(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
                budget_usd=float(args.get("budget_usd") or 0),
                period_days=int(args.get("period_days") or 30),
                per_model_limits=args.get("per_model_limits") if isinstance(args.get("per_model_limits"), dict) else None,
            )
        if tool == "get_provider_cost_budget":
            return await get_provider_cost_budget(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
            )
        if tool == "get_provider_marketplace":
            return await get_provider_marketplace()
        if tool == "install_provider":
            return await install_provider(
                provider_id=args.get("provider_id") if isinstance(args.get("provider_id"), str) else "",
            )
        if tool == "configure_routing":
            return await configure_routing(
                strategy=args.get("strategy") if isinstance(args.get("strategy"), str) else "priority",
                cost_weight=float(args.get("cost_weight") or 0.3),
                latency_weight=float(args.get("latency_weight") or 0.4),
                quality_weight=float(args.get("quality_weight") or 0.3),
            )
        if tool == "get_routing_config":
            return await get_routing_config()
        if tool == "memory_search":
            return await memory_search(
                query=args.get("query") if isinstance(args.get("query"), str) else "",
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else None,
                top_k=int(args.get("top_k") or 10),
                include_episodic=bool(args.get("include_episodic", True)),
                include_semantic=bool(args.get("include_semantic", True)),
                include_pins=bool(args.get("include_pins", True)),
                include_knowledge_graph=bool(args.get("include_knowledge_graph", True)),
                include_git_history=bool(args.get("include_git_history", False)),
            )
        if tool == "pin_memory":
            return await pin_memory(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                content=args.get("content") if isinstance(args.get("content"), str) else "",
                context=args.get("context") if isinstance(args.get("context"), dict) else {},
                source=args.get("source") if isinstance(args.get("source"), str) else "",
                tags=args.get("tags") if isinstance(args.get("tags"), list) else None,
                importance=float(args.get("importance") or 1.0),
                created_by=args.get("created_by") if isinstance(args.get("created_by"), str) else None,
            )
        if tool == "get_pins":
            return await get_pins(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                limit=int(args.get("limit") or 50),
            )
        if tool == "unpin_memory":
            return await unpin_memory(
                pin_id=args.get("pin_id") if isinstance(args.get("pin_id"), str) else "",
            )
        if tool == "record_episode":
            return await record_episode(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                task_description=args.get("task_description") if isinstance(args.get("task_description"), str) else "",
                context=args.get("context") if isinstance(args.get("context"), dict) else {},
                actions=args.get("actions") if isinstance(args.get("actions"), list) else [],
                outcome=args.get("outcome") if isinstance(args.get("outcome"), str) else "",
                success=bool(args.get("success", True)),
                lessons_learned=args.get("lessons_learned") if isinstance(args.get("lessons_learned"), list) else [],
                tags=args.get("tags") if isinstance(args.get("tags"), list) else None,
                importance=float(args.get("importance") or 1.0),
            )
        if tool == "recall_episodes":
            return await recall_episodes(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                query=args.get("query") if isinstance(args.get("query"), str) else "",
                top_k=int(args.get("top_k") or 5),
            )
        if tool == "add_concept":
            return await add_concept(
                name=args.get("name") if isinstance(args.get("name"), str) else "",
                type=args.get("type") if isinstance(args.get("type"), str) else "",
                definition=args.get("definition") if isinstance(args.get("definition"), str) else "",
                context=args.get("context") if isinstance(args.get("context"), str) else "",
                examples=args.get("examples") if isinstance(args.get("examples"), list) else None,
                related_concepts=args.get("related_concepts") if isinstance(args.get("related_concepts"), list) else None,
                tags=args.get("tags") if isinstance(args.get("tags"), list) else None,
                source=args.get("source") if isinstance(args.get("source"), str) else None,
                confidence=float(args.get("confidence") or 1.0),
                created_by=args.get("created_by") if isinstance(args.get("created_by"), str) else None,
            )
        if tool == "add_adr":
            return await add_adr(
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                status=args.get("status") if isinstance(args.get("status"), str) else "",
                context=args.get("context") if isinstance(args.get("context"), str) else "",
                decision=args.get("decision") if isinstance(args.get("decision"), str) else "",
                consequences=args.get("consequences") if isinstance(args.get("consequences"), list) else [],
                alternatives=args.get("alternatives") if isinstance(args.get("alternatives"), list) else None,
                tags=args.get("tags") if isinstance(args.get("tags"), list) else None,
                created_by=args.get("created_by") if isinstance(args.get("created_by"), str) else None,
            )
        if tool == "search_concepts":
            return await search_concepts(
                query=args.get("query") if isinstance(args.get("query"), str) else "",
                top_k=int(args.get("top_k") or 10),
                concept_type=args.get("concept_type") if isinstance(args.get("concept_type"), str) else None,
                tags=args.get("tags") if isinstance(args.get("tags"), list) else None,
            )
        if tool == "add_code_entity":
            return await add_code_entity(
                type=args.get("type") if isinstance(args.get("type"), str) else "",
                name=args.get("name") if isinstance(args.get("name"), str) else "",
                qualified_name=args.get("qualified_name") if isinstance(args.get("qualified_name"), str) else "",
                properties=args.get("properties") if isinstance(args.get("properties"), dict) else None,
                source=args.get("source") if isinstance(args.get("source"), str) else None,
                confidence=float(args.get("confidence") or 1.0),
            )
        if tool == "add_code_relation":
            return await add_code_relation(
                source_id=args.get("source_id") if isinstance(args.get("source_id"), str) else "",
                target_id=args.get("target_id") if isinstance(args.get("target_id"), str) else "",
                type=args.get("type") if isinstance(args.get("type"), str) else "",
                properties=args.get("properties") if isinstance(args.get("properties"), dict) else None,
                confidence=float(args.get("confidence") or 1.0),
            )
        if tool == "find_code_path":
            return await find_code_path(
                source_name=args.get("source_name") if isinstance(args.get("source_name"), str) else "",
                target_name=args.get("target_name") if isinstance(args.get("target_name"), str) else "",
            )
        if tool == "explain_code_change":
            return await explain_code_change(
                file_path=args.get("file_path") if isinstance(args.get("file_path"), str) else "",
                start_line=int(args.get("start_line") or 0),
                end_line=int(args.get("end_line") or 0),
            )
        if tool == "query_git_history":
            return await query_git_history(
                question=args.get("question") if isinstance(args.get("question"), str) else "",
                top_k=int(args.get("top_k") or 10),
                include_commits=bool(args.get("include_commits", True)),
                include_diffs=bool(args.get("include_diffs", True)),
                include_blame=bool(args.get("include_blame", False)),
                file_path=args.get("file_path") if isinstance(args.get("file_path"), str) else None,
            )
        if tool == "run_memory_consolidation":
            return await run_memory_consolidation()
        if tool == "export_memory_pack":
            return await export_memory_pack(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else None,
                include_episodic=bool(args.get("include_episodic", True)),
                include_semantic=bool(args.get("include_semantic", True)),
                include_pins=bool(args.get("include_pins", True)),
                include_knowledge_graph=bool(args.get("include_knowledge_graph", False)),
            )
        if tool == "import_memory_pack":
            return await import_memory_pack(
                pack=args.get("pack") if isinstance(args.get("pack"), dict) else {},
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else None,
            )
        if tool == "get_memory_stats":
            return await get_memory_stats()
        return ToolResult(False, tool or "unknown", error=f"unknown tool: {name}")
    except ToolError as e:
        return ToolResult(False, tool or "unknown", error=str(e))
    except Exception as e:
        return ToolResult(False, tool or "unknown", error=f"{type(e).__name__}: {e}")


# --- Phase 7: Test Implementation Functions ----------------------------------

async def run_tests(
    path: Optional[str] = None,
    framework: Optional[str] = None,
    args: Optional[List[str]] = None,
    coverage: bool = True,
) -> ToolResult:
    """Run tests in the workspace with coverage reporting."""
    try:
        workdir = Path(path) if path else Path(settings.files_root).expanduser().resolve()
        if not workdir.is_dir():
            return ToolResult(False, "run_tests", error=f"path not found: {workdir}")
        
        # Auto-detect framework if not specified
        if not framework:
            if (workdir / "pytest.ini").exists() or (workdir / "pyproject.toml").exists():
                framework = "pytest"
            elif (workdir / "package.json").exists():
                framework = "vitest"
            elif (workdir / "go.mod").exists():
                framework = "go"
            elif (workdir / "Cargo.toml").exists():
                framework = "cargo"
            else:
                framework = "pytest"
        
        # Build command
        test_args = args or []
        if coverage:
            if framework == "pytest":
                test_args.extend(["--cov", "--cov-report=json", "--cov-report=term-missing"])
            elif framework == "vitest":
                test_args.extend(["--coverage"])
            elif framework == "go":
                test_args.extend(["-coverprofile=coverage.out"])
            elif framework == "cargo":
                test_args.extend(["--", "--coverage"])
        
        # Build command
        if framework == "pytest":
            cmd = ["python", "-m", "pytest"] + test_args
        elif framework == "vitest":
            cmd = ["npx", "vitest", "run"] + test_args
        elif framework == "jest":
            cmd = ["npx", "jest"] + test_args
        elif framework == "go":
            cmd = ["go", "test"] + test_args
        elif framework == "cargo":
            cmd = ["cargo", "test"] + test_args
        else:
            return ToolResult(False, "run_tests", error=f"unsupported framework: {framework}")
        
        # Run tests
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workdir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            elapsed_ms = int((time.time() - start_time) * 1000)
        except asyncio.TimeoutError:
            return ToolResult(False, "run_tests", error="test timeout (300s)")
        
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        
        # Parse coverage if available
        coverage_pct = 0.0
        if coverage:
            if framework == "pytest":
                cov_file = workdir / "coverage.json"
                if cov_file.exists():
                    try:
                        cov_data = json.loads(cov_file.read_text())
                        coverage_pct = cov_data.get("totals", {}).get("percent_covered", 0.0)
                    except Exception:
                        pass
            elif framework == "vitest":
                cov_file = workdir / "coverage" / "coverage-summary.json"
                if cov_file.exists():
                    try:
                        cov_data = json.loads(cov_file.read_text())
                        coverage_pct = cov_data.get("total", {}).get("lines", {}).get("pct", 0.0)
                    except Exception:
                        pass
        
        return ToolResult(
            proc.returncode == 0,
            "run_tests",
            data={
                "framework": framework,
                "exit_code": proc.returncode,
                "stdout": stdout_text[:50000],
                "stderr": stderr_text[:50000],
                "coverage_pct": coverage_pct,
                "elapsed_ms": elapsed_ms,
            },
            error=None if proc.returncode == 0 else stderr_text[:1000],
        )
    except Exception as e:
        return ToolResult(False, "run_tests", error=f"{type(e).__name__}: {e}")


async def run_mutation_tests(
    path: Optional[str] = None,
    framework: Optional[str] = None,
    timeout: Optional[float] = None,
) -> ToolResult:
    """Run mutation testing (mutmut for Python, stryker for JS/TS)."""
    try:
        workdir = Path(path) if path else Path(settings.files_root).expanduser().resolve()
        if not workdir.is_dir():
            return ToolResult(False, "run_mutation_tests", error=f"path not found: {workdir}")
        
        if not framework:
            if (workdir / "pytest.ini").exists() or (workdir / "pyproject.toml").exists():
                framework = "mutmut"
            elif (workdir / "package.json").exists():
                framework = "stryker"
            else:
                framework = "mutmut"
        
        start_time = time.time()
        
        if framework == "mutmut":
            cmd = ["mutmut", "run", "--paths-to-mutate", "."]
            timeout_f = timeout or 600
        elif framework == "stryker":
            cmd = ["npx", "stryker", "run"]
            timeout_f = timeout or 600
        else:
            return ToolResult(False, "run_mutation_tests", error=f"unsupported mutation framework: {framework}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workdir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_f)
            elapsed_ms = int((time.time() - start_time) * 1000)
        except asyncio.TimeoutError:
            return ToolResult(False, "run_mutation_tests", error="mutation test timeout")
        
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        
        # Parse results
        total_mutants = 0
        killed_mutants = 0
        survived_mutants = 0
        timeout_mutants = 0
        error_mutants = 0
        
        if framework == "mutmut":
            # Parse mutmut output
            for line in stdout_text.split("\n"):
                if "killed:" in line.lower():
                    killed_mutants = int(line.split(":")[-1].strip())
                elif "survived:" in line.lower():
                    survived_mutants = int(line.split(":")[-1].strip())
                elif "timeout:" in line.lower():
                    timeout_mutants = int(line.split(":")[-1].strip())
                elif "error:" in line.lower():
                    error_mutants = int(line.split(":")[-1].strip())
            total_mutants = killed_mutants + survived_mutants + timeout_mutants + error_mutants
        elif framework == "stryker":
            # Parse stryker JSON output
            try:
                report_file = Path("reports/mutation/json/report.json")
                if report_file.exists():
                    data = json.loads(report_file.read_text())
                    total_mutants = data.get("totalMutants", 0)
                    killed_mutants = data.get("killedMutants", 0)
                    survived_mutants = data.get("survivedMutants", 0)
                    timeout_mutants = data.get("timeoutMutants", 0)
                    error_mutants = data.get("errorMutants", 0)
            except Exception:
                pass
        
        mutation_score = (killed_mutants / total_mutants * 100) if total_mutants > 0 else 0.0
        
        return ToolResult(
            True,
            "run_mutation_tests",
            data={
                "framework": framework,
                "total_mutants": total_mutants,
                "killed_mutants": killed_mutants,
                "survived_mutants": survived_mutants,
                "timeout_mutants": timeout_mutants,
                "error_mutants": error_mutants,
                "mutation_score": round(mutation_score, 2),
                "elapsed_ms": elapsed_ms,
            },
        )
    except Exception as e:
        return ToolResult(False, "run_mutation_tests", error=f"{type(e).__name__}: {e}")


async def run_contract_tests(
    schema_path: Optional[str] = None,
    base_url: Optional[str] = None,
    endpoints: Optional[List[str]] = None,
) -> ToolResult:
    """Run contract tests against OpenAPI schema."""
    try:
        import httpx
        from jsonschema import validate, ValidationError
        
        if not schema_path:
            return ToolResult(False, "run_contract_tests", error="schema_path required")
        
        schema_file = Path(schema_path)
        if not schema_file.exists():
            return ToolResult(False, "run_contract_tests", error=f"schema not found: {schema_path}")
        
        schema = json.loads(schema_file.read_text())
        paths = schema.get("paths", {})
        
        if not base_url:
            base_url = "http://localhost:8000"
        
        results = []
        endpoints_to_test = endpoints or list(paths.keys())
        
        async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
            for endpoint in endpoints_to_test:
                if endpoint not in paths:
                    continue
                path_schema = paths[endpoint]
                for method, method_schema in path_schema.items():
                    method = method.upper()
                    if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                        continue
                    
                    # Build test request from schema
                    test_data = {}
                    if "requestBody" in method_schema:
                        content = method_schema["requestBody"].get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            test_data = _generate_test_data_from_schema(schema)
                    
                    try:
                        response = await client.request(method, endpoint, json=test_data if test_data else None)
                        # Validate response against schema
                        if "responses" in method_schema:
                            for status_code, response_schema in method_schema["responses"].items():
                                if str(response.status_code) == status_code or status_code.startswith("2"):
                                    if "content" in response_schema:
                                        for media_type, media_schema in response_schema["content"].items():
                                            if media_type == "application/json":
                                                validate(instance=response.json(), schema=media_schema.get("schema", {}))
                                                break
                        results.append({
                            "endpoint": endpoint,
                            "method": method,
                            "status": response.status_code,
                            "valid": True,
                        })
                    except ValidationError as e:
                        results.append({
                            "endpoint": endpoint,
                            "method": method,
                            "valid": False,
                            "error": str(e),
                        })
                    except Exception as e:
                        results.append({
                            "endpoint": endpoint,
                            "method": method,
                            "valid": False,
                            "error": str(e),
                        })
        
        valid_count = sum(1 for r in results if r.get("valid", False))
        total = len(results)
        
        return ToolResult(
            True,
            "run_contract_tests",
            data={
                "total_tests": len(results),
                "passed": valid_count,
                "failed": total - valid_count,
                "results": results,
            },
        )
    except Exception as e:
        return ToolResult(False, "run_contract_tests", error=f"{type(e).__name__}: {e}")


async def run_visual_regression(
    test_name: Optional[str] = None,
    url: Optional[str] = None,
    baseline_path: Optional[str] = None,
    threshold_pct: Optional[float] = None,
) -> ToolResult:
    """Run visual regression tests with Playwright."""
    try:
        from playwright.async_api import async_playwright
        
        if not test_name or not url:
            return ToolResult(False, "run_visual_regression", error="test_name and url required")
        
        threshold = threshold_pct or 0.1
        baseline_file = Path(baseline_path) if baseline_path else Path(f"baselines/{test_name}.png")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            
            # Take current screenshot
            current_screenshot = await page.screenshot(full_page=True)
            await browser.close()
        
        # Compare with baseline
        if baseline_file.exists():
            from PIL import Image
            import io
            
            baseline_img = Image.open(baseline_file)
            current_img = Image.open(io.BytesIO(current_screenshot))
            
            # Resize if needed
            if baseline_img.size != current_img.size:
                current_img = current_img.resize(baseline_img.size)
            
            # Calculate diff
            diff = ImageChops.difference(baseline_img, current_img)
            diff_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0, 0))
            total_pixels = baseline_img.width * baseline_img.height
            diff_pct = (diff_pixels / total_pixels) * 100
            
            passed = diff_pct <= threshold
            
            return ToolResult(
                True,
                "run_visual_regression",
                data={
                    "test_name": test_name,
                    "diff_pct": round(diff_pct, 2),
                    "threshold_pct": threshold,
                    "passed": passed,
                    "diff_pixels": diff_pixels,
                    "total_pixels": total_pixels,
                },
            )
        else:
            # Save as new baseline
            baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(baseline_file, "wb") as f:
                f.write(current_screenshot)
            
            return ToolResult(
                True,
                "run_visual_regression",
                data={
                    "test_name": test_name,
                    "baseline_created": True,
                    "path": str(baseline_file),
                },
            )
    except Exception as e:
        return ToolResult(False, "run_visual_regression", error=f"{type(e).__name__}: {e}")


async def run_performance_benchmark(
    script_path: Optional[str] = None,
    target_url: Optional[str] = None,
    duration: Optional[str] = None,
    vus: Optional[int] = None,
) -> ToolResult:
    """Run performance benchmarks with k6."""
    try:
        if not script_path and not target_url:
            return ToolResult(False, "run_performance_benchmark", error="script_path or target_url required")
        
        script_file = Path(script_path) if script_path else None
        
        if script_file and script_file.exists():
            script_content = script_file.read_text()
        else:
            # Generate basic k6 script
            script_content = f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

export const options = {{
    stages: [
        {{ duration: '30s', target: {vus or 10} }},
        {{ duration: '1m', target: {vus or 10} }},
        {{ duration: '30s', target: 0 }},
    ],
}};

export default function() {{
    const res = http.get('{target_url or "http://localhost:8000"}');
    check(res, {{ 'status 200': (r) => r.status === 200 }});
    sleep(1);
}}
"""
            script_file = Path("/tmp/k6_script.js")
            script_file.write_text(script_content)
            script_path = str(script_file)
        
        cmd = ["k6", "run", "--out", "json=results.json", script_path]
        if duration:
            cmd.extend(["--duration", duration])
        
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            elapsed_ms = int((time.time() - start_time) * 1000)
        except asyncio.TimeoutError:
            return ToolResult(False, "run_performance_benchmark", error="benchmark timeout")
        
        # Parse k6 JSON output
        results_file = Path("results.json")
        metrics = {}
        if results_file.exists():
            try:
                data = json.loads(results_file.read_text())
                metrics = {
                    "latency_p50": data.get("http_req_duration", {}).get("p50", 0),
                    "latency_p95": data.get("http_req_duration", {}).get("p95", 0),
                    "latency_p99": data.get("http_req_duration", {}).get("p99", 0),
                    "throughput": data.get("http_reqs", {}).get("rate", 0),
                    "error_rate": data.get("http_req_failed", {}).get("rate", 0),
                }
            except Exception:
                pass
        
        return ToolResult(
            True,
            "run_performance_benchmark",
            data={
                "metrics": metrics,
                "elapsed_ms": elapsed_ms,
            },
        )
    except Exception as e:
        return ToolResult(False, "run_performance_benchmark", error=f"{type(e).__name__}: {e}")


async def run_security_scan(
    tool: Optional[str] = None,
    path: Optional[str] = None,
    config: Optional[str] = None,
) -> ToolResult:
    """Run security scans (semgrep, trivy, bandit)."""
    try:
        workdir = Path(path) if path else Path(settings.files_root).expanduser().resolve()
        if not workdir.is_dir():
            return ToolResult(False, "run_security_scan", error=f"path not found: {workdir}")
        
        scan_tool = tool or "semgrep"
        findings = []
        
        if scan_tool == "semgrep":
            cmd = ["semgrep", "scan", "--json", "--config=auto", str(workdir)]
        elif scan_tool == "trivy":
            cmd = ["trivy", "fs", "--format", "json", str(workdir)]
        elif scan_tool == "bandit":
            cmd = ["bandit", "-r", str(workdir), "-f", "json"]
        else:
            return ToolResult(False, "run_security_scan", error=f"unsupported tool: {scan_tool}")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            return ToolResult(False, "run_security_scan", error="scan timeout")
        
        stdout_text = stdout.decode("utf-8", errors="replace")
        
        try:
            data = json.loads(stdout_text)
            if scan_tool == "semgrep":
                for result in data.get("results", []):
                    findings.append({
                        "tool": "semgrep",
                        "severity": result.get("extra", {}).get("severity", "info"),
                        "finding": result.get("extra", {}).get("message", ""),
                        "file_path": result.get("path"),
                        "line_number": result.get("start", {}).get("line"),
                        "description": result.get("extra", {}).get("message", ""),
                    })
            elif scan_tool == "trivy":
                for result in data.get("Results", []):
                    for vuln in result.get("Vulnerabilities", []):
                        findings.append({
                            "tool": "trivy",
                            "severity": vuln.get("Severity", "UNKNOWN").lower(),
                            "finding": vuln.get("Title", ""),
                            "file_path": result.get("Target"),
                            "description": vuln.get("Description", ""),
                        })
            elif scan_tool == "bandit":
                for result in data.get("results", []):
                    findings.append({
                        "tool": "bandit",
                        "severity": result.get("issue_severity", "").lower(),
                        "finding": result.get("issue_text", ""),
                        "file_path": result.get("filename"),
                        "line_number": result.get("line_number"),
                        "description": result.get("issue_text", ""),
                    })
        except Exception:
            pass
        
        return ToolResult(
            True,
            "run_security_scan",
            data={"tool": scan_tool, "findings": findings, "count": len(findings)},
        )
    except Exception as e:
        return ToolResult(False, "run_security_scan", error=f"{type(e).__name__}: {e}")


async def run_dependency_audit(
    path: Optional[str] = None,
    manager: str = "npm",
    auto_pr: bool = False,
) -> ToolResult:
    """Audit dependencies for updates and vulnerabilities."""
    try:
        workdir = Path(path) if path else Path(settings.files_root).expanduser().resolve()
        if not workdir.is_dir():
            return ToolResult(False, "run_dependency_audit", error=f"path not found: {workdir}")
        
        results = []
        
        if manager == "npm":
            cmd = ["npm", "audit", "--json"]
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=str(workdir), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            try:
                data = json.loads(stdout.decode())
                for vuln in data.get("vulnerabilities", {}).values():
                    if isinstance(vuln, dict):
                        results.append({
                            "manager": "npm",
                            "package": vuln.get("name"),
                            "severity": vuln.get("severity", "").lower(),
                            "current_version": vuln.get("version"),
                            "latest_version": vuln.get("fixedVersion", "unknown"),
                            "cve_ids": vuln.get("cves", []),
                        })
            except Exception:
                pass
        elif manager == "pip":
            cmd = ["pip", "list", "--outdated", "--format=json"]
            proc = await asyncio.create_subprocess_exec(*cmd, cwd=str(workdir), stdout=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            try:
                for line in stdout.decode().strip().split("\n"):
                    if line:
                        pkg = json.loads(line)
                        results.append({
                            "manager": "pip",
                            "package": pkg.get("name"),
                            "current_version": pkg.get("version"),
                            "latest_version": pkg.get("latest_version"),
                            "update_type": "patch",
                        })
            except Exception:
                pass
        
        return ToolResult(True, "run_dependency_audit", data={"results": results, "count": len(results)})
    except Exception as e:
        return ToolResult(False, "run_dependency_audit", error=f"{type(e).__name__}: {e}")


async def detect_flaky_tests(
    path: Optional[str] = None,
    framework: Optional[str] = None,
    runs: Optional[int] = None,
) -> ToolResult:
    """Detect flaky tests by re-running multiple times."""
    try:
        workdir = Path(path) if path else Path(settings.files_root).expanduser().resolve()
        if not workdir.is_dir():
            return ToolResult(False, "detect_flaky_tests", error=f"path not found: {workdir}")
        
        num_runs = runs or 5
        test_results = {}
        
        if not framework:
            if (workdir / "pytest.ini").exists() or (workdir / "pyproject.toml").exists():
                framework = "pytest"
            elif (workdir / "package.json").exists():
                framework = "vitest"
            else:
                framework = "pytest"
        
        for run in range(num_runs):
            if framework == "pytest":
                cmd = ["python", "-m", "pytest", "--json-report", f"--json-report-file=results_{run}.json"]
            elif framework == "vitest":
                cmd = ["npx", "vitest", "run", "--reporter=json", f"--outputFile=results_{run}.json"]
            else:
                return ToolResult(False, "detect_flaky_tests", error=f"unsupported framework: {framework}")
            
            proc = await asyncio.create_subprocess_exec(
                *cmd, cwd=str(workdir), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            results_file = Path(f"results_{run}.json")
            if results_file.exists():
                try:
                    data = json.loads(results_file.read_text())
                    for test in data.get("tests", []):
                        name = test.get("name", "")
                        if name not in test_results:
                            test_results[name] = {"passes": 0, "failures": 0}
                        if test.get("outcome") == "passed":
                            test_results[name]["passes"] += 1
                        else:
                            test_results[name]["failures"] += 1
                except Exception:
                    pass
        
        flaky_tests = []
        for name, results in test_results.items():
            total = results["passes"] + results["failures"]
            if total > 0:
                pass_rate = results["passes"] / total
                if 0 < pass_rate < 1:
                    flaky_tests.append({
                        "test_name": name,
                        "flaky_score": 1 - abs(pass_rate - 0.5) * 2,  # Higher = more flaky
                        "pass_rate": pass_rate,
                        "runs": total,
                    })
        
        flaky_tests.sort(key=lambda x: x["flaky_score"], reverse=True)
        
        return ToolResult(
            True,
            "detect_flaky_tests",
            data={"flaky_tests": flaky_tests, "total_analyzed": len(test_results)},
        )
    except Exception as e:
        return ToolResult(False, "detect_flaky_tests", error=f"{type(e).__name__}: {e}")


async def get_coverage_report(
    room_id: Optional[str] = None,
    project_id: Optional[str] = None,
    threshold_pct: Optional[float] = None,
) -> ToolResult:
    """Get coverage report for a room or project."""
    try:
        # Look for coverage files
        coverage_files = list(Path(settings.files_root).expanduser().resolve().rglob("coverage.json"))
        coverage_files.extend(Path(settings.files_root).expanduser().resolve().rglob("coverage-summary.json"))
        
        if not coverage_files:
            return ToolResult(False, "get_coverage_report", error="no coverage files found")
        
        total_lines = 0
        covered_lines = 0
        
        for cov_file in coverage_files:
            try:
                data = json.loads(cov_file.read_text())
                if "totals" in data:
                    total_lines += data["totals"].get("num_statements", 0)
                    covered_lines += data["totals"].get("covered_lines", 0)
                elif "total" in data:
                    total_lines += data["total"].get("lines", {}).get("total", 0)
                    covered_lines += data["total"].get("lines", {}).get("covered", 0)
            except Exception:
                continue
        
        coverage_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
        threshold = threshold_pct or 80.0
        gate_passed = coverage_pct >= threshold
        
        return ToolResult(
            True,
            "get_coverage_report",
            data={
                "total_lines": total_lines,
                "covered_lines": covered_lines,
                "coverage_pct": round(coverage_pct, 2),
                "threshold_pct": threshold,
                "gate_passed": gate_passed,
            },
        )
    except Exception as e:
        return ToolResult(False, "get_coverage_report", error=f"{type(e).__name__}: {e}")


async def get_quality_dashboard(
    room_id: Optional[str] = None,
) -> ToolResult:
    """Get quality dashboard data for a room."""
    try:
        state = StateStore(settings.state_file).load()
        
        # Get room info
        room = None
        if room_id:
            room = next((c for c in (state.get("conversations") or []) if c.get("id") == room_id), None)
        
        # Collect metrics
        dashboard = {
            "room_id": room_id,
            "room_name": room.get("name") if room else None,
            "metrics": {
                "test_health": {"value": 0, "threshold": 0.8, "status": "unknown"},
                "coverage": {"value": 0, "threshold": 80, "status": "unknown"},
                "mutation_score": {"value": 0, "threshold": 80, "status": "unknown"},
                "flaky_tests": {"value": 0, "threshold": 0.1, "status": "unknown"},
                "security": {"value": 0, "threshold": 0, "status": "unknown"},
                "performance": {"value": 0, "threshold": 10, "status": "unknown"},
            },
        }
        
        # Calculate test health from recent activity
        if room_id:
            messages = state.get("messages", {}).get(room_id, [])
            test_steps = [m for m in messages if m.get("kind") == "goal-step"]
            if test_steps:
                passed = sum(1 for m in test_steps if "✓" in m.get("text", "") or "✓" in m.get("summary", ""))
                total = len(test_steps)
                test_health = passed / total if total > 0 else 0
                dashboard["metrics"]["test_health"]["value"] = round(test_health, 2)
                dashboard["metrics"]["test_health"]["status"] = "healthy" if test_health >= 0.8 else "warning" if test_health >= 0.5 else "critical"
        
        return ToolResult(True, "get_quality_dashboard", data=dashboard)
    except Exception as e:
        return ToolResult(False, "get_quality_dashboard", error=f"{type(e).__name__}: {e}")


async def execute_actions(actions: Any, *, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Execute a list of agent tool actions, returning one result per action."""
    results: List[Dict[str, Any]] = []
    if not isinstance(actions, list):
        return results
    for raw in actions:
        if not isinstance(raw, dict):
            results.append(ToolResult(False, "unknown", error="action must be an object").to_dict())
            continue
        name = raw.get("tool") or raw.get("name") or raw.get("type") or ""
        args = raw.get("args") if isinstance(raw.get("args"), dict) else {
            k: v for k, v in raw.items() if k not in {"tool", "name", "type"}
        }
        if agent_id and "agent_id" not in args:
            args = {**args, "agent_id": agent_id}
        result = await execute_tool(str(name), args)
        results.append(result.to_dict())
    return results


def tools_manifest() -> List[Dict[str, Any]]:
    """The tool surface advertised to agents in their runtime instructions."""
    return [
        {
            "name": "terminal",
            "description": "Run a real shell command in the workspace (bash). Use for git, builds, tests, installs.",
            "params": {"command": "string", "cwd?": "string", "timeout?": "number"},
        },
        {
            "name": "write_file",
            "description": "Create or overwrite a file with exact content. Use this to write code yourself.",
            "params": {"path": "string", "content": "string", "append?": "boolean"},
        },
        {
            "name": "edit_file",
            "description": "Replace an exact string in an existing file (one match, or all with replace_all).",
            "params": {"path": "string", "old_string": "string", "new_string": "string", "replace_all?": "boolean"},
        },
        {
            "name": "read_file",
            "description": "Read a file with offset/limit paging.",
            "params": {"path": "string", "offset?": "number", "limit?": "number"},
        },
        {
            "name": "list_files",
            "description": "List a directory in the workspace.",
            "params": {"path?": "string"},
        },
        {
            "name": "gh",
            "description": "Run a GitHub CLI command (issues, PRs, repos, actions).",
            "params": {"args": ["string"], "cwd?": "string"},
        },
        {
            "name": "github",
            "description": "Call the GitHub REST API.",
            "params": {"method": "string", "path": "string", "params?": "object", "body?": "object"},
        },
        {
            "name": "run_tests",
            "description": "Run tests in the workspace (pytest, vitest, jest, go test, cargo test). Returns test results and coverage.",
            "params": {"path?": "string", "framework?": "string", "args?": ["string"], "coverage?": "boolean"},
        },
        {
            "name": "run_mutation_tests",
            "description": "Run mutation testing (mutmut, stryker, go-mutesting). Returns mutation score and killed/survived mutants.",
            "params": {"path?": "string", "framework?": "string", "timeout?": "number"},
        },
        {
            "name": "run_contract_tests",
            "description": "Run contract tests against OpenAPI schema. Validates request/response against schema.",
            "params": {"schema_path": "string", "base_url?": "string", "endpoints?": ["string"]},
        },
        {
            "name": "run_visual_regression",
            "description": "Run visual regression tests with Playwright. Compares screenshots against baseline.",
            "params": {"test_name": "string", "url": "string", "baseline_path?": "string", "threshold_pct?": "number"},
        },
        {
            "name": "run_performance_benchmark",
            "description": "Run performance benchmarks (k6, artillery, wrk). Measures latency, throughput, memory.",
            "params": {"script_path": "string", "target_url": "string", "duration?": "string", "vus?": "number"},
        },
        {
            "name": "run_security_scan",
            "description": "Run security scans (semgrep, trivy, bandit, zap). Returns findings with severity.",
            "params": {"tool": "string", "path?": "string", "config?": "string"},
        },
        {
            "name": "run_dependency_audit",
            "description": "Audit dependencies for updates and vulnerabilities. Can auto-create PRs.",
            "params": {"path?": "string", "manager": "string", "auto_pr?": "boolean"},
        },
        {
            "name": "detect_flaky_tests",
            "description": "Detect flaky tests by re-running multiple times. Returns flaky score per test.",
            "params": {"path": "string", "framework?": "string", "runs?": "number"},
        },
        {
            "name": "get_coverage_report",
            "description": "Get coverage report for a room or project. Checks coverage gate.",
            "params": {"room_id?": "string", "project_id?": "string", "threshold_pct?": "number"},
        },
        {
            "name": "get_quality_dashboard",
            "description": "Get quality dashboard data for a room. Test health, coverage, mutation score, flaky tests, security, performance.",
            "params": {"room_id": "string"},
        },
        # Phase 9: Provider Management
        {
            "name": "list_providers",
            "description": "List all available LLM providers with their health status.",
            "params": {},
        },
        {
            "name": "add_provider",
            "description": "Add a new LLM provider configuration.",
            "params": {"config": "object"},
        },
        {
            "name": "update_provider",
            "description": "Update an existing LLM provider configuration.",
            "params": {"provider_id": "string", "config": "object"},
        },
        {
            "name": "remove_provider",
            "description": "Remove an LLM provider.",
            "params": {"provider_id": "string"},
        },
        {
            "name": "get_provider_health",
            "description": "Get health status for all providers.",
            "params": {},
        },
        {
            "name": "set_provider_priority",
            "description": "Set provider priority for routing.",
            "params": {"provider_id": "string", "priority": "number"},
        },
        {
            "name": "get_provider_models",
            "description": "Get available models for a provider.",
            "params": {"provider_id": "string"},
        },
        {
            "name": "set_provider_model",
            "description": "Set default model for a provider.",
            "params": {"provider_id": "string", "model": "string"},
        },
        {
            "name": "configure_byok",
            "description": "Configure Bring Your Own Key for an agent.",
            "params": {"agent_id": "string", "provider": "string", "api_key": "string", "api_key_env": "string"},
        },
        {
            "name": "get_byok_status",
            "description": "Get BYOK configuration status for an agent.",
            "params": {"agent_id": "string"},
        },
        {
            "name": "set_provider_cost_budget",
            "description": "Set cost budget for a provider.",
            "params": {"provider_id": "string", "budget_usd": "number", "period_days": "number", "per_model_limits": "object"},
        },
        {
            "name": "get_provider_cost_budget",
            "description": "Get cost budget for a provider.",
            "params": {"provider_id": "string"},
        },
        {
            "name": "get_provider_marketplace",
            "description": "Get available providers from the marketplace.",
            "params": {},
        },
        {
            "name": "install_provider",
            "description": "Install a provider from the marketplace.",
            "params": {"provider_id": "string"},
        },
        {
            "name": "configure_routing",
            "description": "Configure LLM routing strategy.",
            "params": {"strategy": "string", "cost_weight": "number", "latency_weight": "number", "quality_weight": "number"},
        },
        {
            "name": "get_routing_config",
            "description": "Get current LLM routing configuration.",
            "params": {},
        },
        # Phase 10: Memory & Knowledge
        {
            "name": "memory_search",
            "description": "Search across all memory systems (episodic, semantic, pins, knowledge graph, git history).",
            "params": {"query": "string", "agent_id?": "string", "top_k?": "number", "include_episodic?": "boolean", "include_semantic?": "boolean", "include_pins?": "boolean", "include_knowledge_graph?": "boolean", "include_git_history?": "boolean"},
        },
        {
            "name": "pin_memory",
            "description": "Pin a memory item for long-term retention ('Remember this').",
            "params": {"agent_id": "string", "content": "string", "context": "object", "source": "string", "tags?": ["string"], "importance?": "number", "created_by?": "string"},
        },
        {
            "name": "get_pins",
            "description": "Get pinned memories for an agent.",
            "params": {"agent_id": "string", "limit?": "number"},
        },
        {
            "name": "unpin_memory",
            "description": "Unpin a memory item.",
            "params": {"pin_id": "string"},
        },
        {
            "name": "record_episode",
            "description": "Record an episodic memory (how I solved X).",
            "params": {"agent_id": "string", "task_description": "string", "context": "object", "actions": ["object"], "outcome": "string", "success": "boolean", "lessons_learned": ["string"], "tags?": ["string"], "importance?": "number"},
        },
        {
            "name": "recall_episodes",
            "description": "Recall episodic memories for an agent.",
            "params": {"agent_id": "string", "query": "string", "top_k?": "number"},
        },
        {
            "name": "add_concept",
            "description": "Add a semantic concept (glossary term, ADR, pattern, etc.).",
            "params": {"name": "string", "type": "string", "definition": "string", "context": "string", "examples?": ["string"], "related_concepts?": ["string"], "tags?": ["string"], "source?": "string", "confidence?": "number", "created_by?": "string"},
        },
        {
            "name": "add_adr",
            "description": "Add an Architecture Decision Record.",
            "params": {"title": "string", "status": "string", "context": "string", "decision": "string", "consequences": ["string"], "alternatives?": ["string"], "tags?": ["string"], "created_by?": "string"},
        },
        {
            "name": "search_concepts",
            "description": "Search semantic concepts.",
            "params": {"query": "string", "top_k?": "number", "concept_type?": "string", "tags?": ["string"]},
        },
        {
            "name": "add_code_entity",
            "description": "Add a code entity to the knowledge graph.",
            "params": {"type": "string", "name": "string", "qualified_name": "string", "properties?": "object", "source?": "string", "confidence?": "number"},
        },
        {
            "name": "add_code_relation",
            "description": "Add a relation between code entities.",
            "params": {"source_id": "string", "target_id": "string", "type": "string", "properties?": "object", "confidence?": "number"},
        },
        {
            "name": "find_code_path",
            "description": "Find path between two code entities in the knowledge graph.",
            "params": {"source_name": "string", "target_name": "string"},
        },
        {
            "name": "explain_code_change",
            "description": "Explain why code was changed using git history.",
            "params": {"file_path": "string", "start_line": "number", "end_line": "number"},
        },
        {
            "name": "query_git_history",
            "description": "Query git history with natural language.",
            "params": {"question": "string", "top_k?": "number", "include_commits?": "boolean", "include_diffs?": "boolean", "include_blame?": "boolean", "file_path?": "string"},
        },
        {
            "name": "run_memory_consolidation",
            "description": "Run memory consolidation (summarize, decay, link, prune).",
            "params": {},
        },
        {
            "name": "export_memory_pack",
            "description": "Export memory as a portable pack for onboarding.",
            "params": {"agent_id?": "string", "include_episodic?": "boolean", "include_semantic?": "boolean", "include_pins?": "boolean", "include_knowledge_graph?": "boolean"},
        },
        {
            "name": "import_memory_pack",
            "description": "Import a memory pack.",
            "params": {"pack": "object", "agent_id?": "string"},
        },
        {
            "name": "get_memory_stats",
            "description": "Get memory system statistics.",
            "params": {},
        },
    ]


# --- Phase 9: Provider Management Implementation ------------------------------

async def list_providers() -> ToolResult:
    """List all configured providers with health status."""
    try:
        from .config import settings
        from .providers import build_providers
        
        providers = build_providers()
        results = []
        for p in providers:
            results.append({
                "id": getattr(p, "name", "unknown"),
                "name": getattr(p, "name", "unknown"),
                "base_url": getattr(p, "base_url", ""),
                "default_model": getattr(p, "default_model", ""),
                "keyless": getattr(p, "keyless", False),
                "has_api_key": bool(getattr(p, "api_key", "")),
                "supports_streaming": getattr(p, "supports_streaming", True),
                "supports_function_calling": getattr(p, "supports_function_calling", False),
            })
        return ToolResult(True, "list_providers", data={"providers": results})
    except Exception as e:
        return ToolResult(False, "list_providers", error=f"{type(e).__name__}: {e}")


async def add_provider(config: Dict[str, Any]) -> ToolResult:
    """Add a new provider configuration (stored in settings/state)."""
    try:
        from .config import settings
        from .state import StateStore
        
        required = ["id", "name", "provider_type", "base_url"]
        for req in required:
            if req not in config:
                return ToolResult(False, "add_provider", error=f"missing required field: {req}")
        
        state = StateStore(settings.state_file).load()
        providers = state.get("providers", [])
        
        if any(p.get("id") == config["id"] for p in providers):
            return ToolResult(False, "add_provider", error=f"provider {config['id']} already exists")
        
        new_provider = {
            "id": config["id"],
            "name": config["name"],
            "provider_type": config["provider_type"],
            "base_url": config["base_url"],
            "api_key": config.get("api_key", ""),
            "api_key_env": config.get("api_key_env"),
            "models": config.get("models", []),
            "enabled": config.get("enabled", True),
            "priority": config.get("priority", 100),
            "timeout_s": config.get("timeout_s", 60.0),
            "max_retries": config.get("max_retries", 3),
            "keyless": config.get("keyless", False),
            "supports_streaming": config.get("supports_streaming", True),
            "supports_function_calling": config.get("supports_function_calling", False),
            "supports_vision": config.get("supports_vision", False),
            "max_context_tokens": config.get("max_context_tokens", 4096),
            "default_model": config.get("default_model"),
            "prompt_template": config.get("prompt_template"),
            "cost_per_1k_prompt_tokens": config.get("cost_per_1k_prompt_tokens", 0.0),
            "cost_per_1k_completion_tokens": config.get("cost_per_1k_completion_tokens", 0.0),
            "headers": config.get("headers", {}),
            "extra_params": config.get("extra_params", {}),
        }
        
        state.setdefault("providers", []).append(new_provider)
        StateStore(settings.state_file).save(state)
        
        return ToolResult(True, "add_provider", data={"provider": new_provider})
    except Exception as e:
        return ToolResult(False, "add_provider", error=f"{type(e).__name__}: {e}")


async def update_provider(provider_id: str, config: Dict[str, Any]) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        providers = state.get("providers", [])
        
        idx = next((i for i, p in enumerate(providers) if p.get("id") == provider_id), None)
        if idx is None:
            return ToolResult(False, "update_provider", error=f"provider {provider_id} not found")
        
        # Update only provided fields
        for key, value in config.items():
            if key != "id":
                providers[idx][key] = value
        
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "update_provider", data={"provider": providers[idx]})
    except Exception as e:
        return ToolResult(False, "update_provider", error=f"{type(e).__name__}: {e}")


async def remove_provider(provider_id: str) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        providers = state.get("providers", [])
        
        idx = next((i for i, p in enumerate(providers) if p.get("id") == provider_id), None)
        if idx is None:
            return ToolResult(False, "remove_provider", error=f"provider {provider_id} not found")
        
        removed = providers.pop(idx)
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "remove_provider", data={"removed": removed})
    except Exception as e:
        return ToolResult(False, "remove_provider", error=f"{type(e).__name__}: {e}")


async def get_provider_health() -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        import httpx
        
        state = StateStore(settings.state_file).load()
        providers = state.get("providers", [])
        client = httpx.AsyncClient(timeout=10.0)
        
        health_results = []
        for p in providers:
            provider_health = await _check_provider_health(p, client)
            health_results.append(provider_health)
        
        await client.aclose()
        return ToolResult(True, "get_provider_health", data={"health": health_results})
    except Exception as e:
        return ToolResult(False, "get_provider_health", error=f"{type(e).__name__}: {e}")


async def _check_provider_health(provider: Dict, client) -> Dict:
    """Check health of a single provider."""
    try:
        start = time.perf_counter()
        response = await client.get(f"{provider['base_url']}/health", timeout=5.0)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code == 200:
            return {
                "provider_id": provider.get("id"),
                "provider_name": provider.get("name"),
                "status": "healthy",
                "latency_ms": latency_ms,
                "last_check": int(time.time() * 1000),
            }
    except Exception as e:
        return {
            "provider_id": provider.get("id"),
            "provider_name": provider.get("name"),
            "status": "unhealthy",
            "last_error": str(e),
            "last_check": int(time.time() * 1000),
        }
    return {"provider_id": provider.get("id"), "status": "unknown"}


async def set_provider_priority(provider_id: str, priority: int) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        providers = state.get("providers", [])
        
        idx = next((i for i, p in enumerate(providers) if p.get("id") == provider_id), None)
        if idx is None:
            return ToolResult(False, "set_provider_priority", error=f"provider {provider_id} not found")
        
        providers[idx]["priority"] = priority
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "set_provider_priority", data={"provider_id": provider_id, "priority": priority})
    except Exception as e:
        return ToolResult(False, "set_provider_priority", error=f"{type(e).__name__}: {e}")


async def get_provider_models(provider_id: str) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        from .providers import build_providers
        from .models import RouteContext
        import httpx
        
        providers = build_providers()
        provider = next((p for p in providers if getattr(p, "name", "") == provider_id), None)
        if not provider:
            return ToolResult(False, "get_provider_models", error=f"provider {provider_id} not found")
        
        candidates = await provider.candidates(RouteContext(messages=[]), httpx.AsyncClient())
        models = [{"name": c.get("model"), "id": c.get("model")} for c in candidates]
        return ToolResult(True, "get_provider_models", data={"provider_id": provider_id, "models": models})
    except Exception as e:
        return ToolResult(False, "get_provider_models", error=f"{type(e).__name__}: {e}")


async def set_provider_model(provider_id: str, model: str) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        providers = state.get("providers", [])
        
        idx = next((i for i, p in enumerate(providers) if p.get("id") == provider_id), None)
        if idx is None:
            return ToolResult(False, "set_provider_model", error=f"provider {provider_id} not found")
        
        providers[idx]["default_model"] = model
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "set_provider_model", data={"provider_id": provider_id, "model": model})
    except Exception as e:
        return ToolResult(False, "set_provider_model", error=f"{type(e).__name__}: {e}")


async def configure_byok(agent_id: str, provider: str, api_key: str, api_key_env: Optional[str] = None) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        agents = state.get("agents", [])
        
        agent = next((a for a in agents if a.get("id") == agent_id), None)
        if not agent:
            return ToolResult(False, "configure_byok", error=f"agent {agent_id} not found")
        
        byok = agent.setdefault("byok", {})
        byok[provider] = {
            "api_key": api_key,
            "api_key_env": api_key_env,
            "valid": True,
            "last_validated": int(time.time() * 1000),
        }
        
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "configure_byok", data={"agent_id": agent_id, "provider": provider, "byok": byok[provider]})
    except Exception as e:
        return ToolResult(False, "configure_byok", error=f"{type(e).__name__}: {e}")


async def get_byok_status(agent_id: str) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        agents = state.get("agents", [])
        
        agent = next((a for a in agents if a.get("id") == agent_id), None)
        if not agent:
            return ToolResult(False, "get_byok_status", error=f"agent {agent_id} not found")
        
        byok = agent.get("byok", {})
        return ToolResult(True, "get_byok_status", data={"agent_id": agent_id, "byok": byok})
    except Exception as e:
        return ToolResult(False, "get_byok_status", error=f"{type(e).__name__}: {e}")


async def set_provider_cost_budget(
    provider_id: str,
    budget_usd: float,
    period_days: int = 30,
    per_model_limits: Optional[Dict[str, float]] = None,
) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        import uuid
        
        state = StateStore(settings.state_file).load()
        budgets = state.setdefault("provider_budgets", [])
        
        # Remove existing budget for this provider
        budgets[:] = [b for b in budgets if b.get("provider_id") != provider_id]
        
        budget = {
            "id": f"budget-{uuid.uuid4().hex[:12]}",
            "provider_id": provider_id,
            "budget_usd": budget_usd,
            "spent_usd": 0.0,
            "period_start": int(time.time() * 1000),
            "period_end": int((time.time() + period_days * 86400) * 1000),
            "alert_threshold_pct": 80.0,
            "hard_stop": False,
            "per_model_limits": per_model_limits or {},
        }
        
        state.setdefault("provider_budgets", []).append(budget)
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "set_provider_cost_budget", data={"budget": budget})
    except Exception as e:
        return ToolResult(False, "set_provider_cost_budget", error=f"{type(e).__name__}: {e}")


async def get_provider_cost_budget(provider_id: str) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        budgets = state.get("provider_budgets", [])
        
        budget = next((b for b in budgets if b.get("provider_id") == provider_id), None)
        if not budget:
            return ToolResult(False, "get_provider_cost_budget", error="budget not found")
        
        return ToolResult(True, "get_provider_cost_budget", data={"budget": budget})
    except Exception as e:
        return ToolResult(False, "get_provider_cost_budget", error=f"{type(e).__name__}: {e}")


async def get_provider_marketplace() -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        listings = state.get("provider_marketplace", [])
        
        return ToolResult(True, "get_provider_marketplace", data={"listings": listings})
    except Exception as e:
        return ToolResult(False, "get_provider_marketplace", error=f"{type(e).__name__}: {e}")


async def install_provider(provider_id: str) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        import httpx
        
        state = StateStore(settings.state_file).load()
        listings = state.get("provider_marketplace", [])
        
        listing = next((l for l in listings if l.get("id") == provider_id), None)
        if not listing:
            return ToolResult(False, "install_provider", error="provider not found in marketplace")
        
        # In a real implementation, this would download and install the provider
        # For now, we'll add it to the providers list
        state.setdefault("providers", []).append({
            "id": listing["id"],
            "name": listing["name"],
            "provider_type": listing["provider_type"],
            "base_url": listing.get("base_url", ""),
            "models": listing.get("models", []),
            "enabled": True,
            "priority": 100,
        })
        
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "install_provider", data={"provider": listing})
    except Exception as e:
        return ToolResult(False, "install_provider", error=f"{type(e).__name__}: {e}")


async def configure_routing(
    strategy: str = "priority",
    cost_weight: float = 0.3,
    latency_weight: float = 0.4,
    quality_weight: float = 0.3,
) -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        routing = state.setdefault("routing_config", {})
        
        routing.update({
            "strategy": strategy,
            "cost_weight": cost_weight,
            "latency_weight": latency_weight,
            "quality_weight": quality_weight,
            "prefer_keyless": True,
            "prefer_local": True,
            "max_fallback_attempts": 3,
            "fallback_timeout_s": 30.0,
        })
        
        StateStore(settings.state_file).save(state)
        return ToolResult(True, "configure_routing", data={"routing": routing})
    except Exception as e:
        return ToolResult(False, "configure_routing", error=f"{type(e).__name__}: {e}")


async def get_routing_config() -> ToolResult:
    try:
        from .config import settings
        from .state import StateStore
        
        state = StateStore(settings.state_file).load()
        routing = state.get("routing_config", {})
        return ToolResult(True, "get_routing_config", data={"routing": routing})
    except Exception as e:
        return ToolResult(False, "get_routing_config", error=f"{type(e).__name__}: {e}")


# --- Phase 10: Memory & Knowledge ----------------------------------------------

async def memory_search(
    query: str,
    agent_id: Optional[str] = None,
    top_k: int = 10,
    include_episodic: bool = True,
    include_semantic: bool = True,
    include_pins: bool = True,
    include_knowledge_graph: bool = True,
    include_git_history: bool = False,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        results = await manager.search(
            query=query,
            agent_id=agent_id,
            top_k=top_k,
            include_episodic=include_episodic,
            include_semantic=include_semantic,
            include_pins=include_pins,
            include_knowledge_graph=include_knowledge_graph,
            include_git_history=include_git_history,
        )
        
        # Convert to serializable format
        serializable = {}
        for key, value in results.items():
            serializable[key] = []
            for item in value:
                if isinstance(item, dict):
                    serializable[key].append(item)
                elif hasattr(item, '__dict__'):
                    serializable[key].append(item.__dict__)
                else:
                    serializable[key].append(str(item))
        
        return ToolResult(True, "memory_search", data={"results": serializable})
    except Exception as e:
        return ToolResult(False, "memory_search", error=f"{type(e).__name__}: {e}")


async def pin_memory(
    agent_id: str,
    content: str,
    context: Dict[str, Any],
    source: str,
    tags: Optional[List[str]] = None,
    importance: float = 1.0,
    created_by: Optional[str] = None,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        pin_id = await manager.pin_memory(
            agent_id=agent_id,
            content=content,
            context=context,
            source=source,
            tags=tags,
            importance=importance,
            created_by=created_by,
        )
        
        return ToolResult(True, "pin_memory", data={"pin_id": pin_id})
    except Exception as e:
        return ToolResult(False, "pin_memory", error=f"{type(e).__name__}: {e}")


async def get_pins(agent_id: str, limit: int = 50) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        pins = await manager.get_pins(agent_id, limit)
        return ToolResult(True, "get_pins", data={"pins": [p.__dict__ for p in pins]})
    except Exception as e:
        return ToolResult(False, "get_pins", error=f"{type(e).__name__}: {e}")


async def unpin_memory(pin_id: str) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        success = await manager.unpin_memory(pin_id)
        return ToolResult(True, "unpin_memory", data={"success": success})
    except Exception as e:
        return ToolResult(False, "unpin_memory", error=f"{type(e).__name__}: {e}")


async def record_episode(
    agent_id: str,
    task_description: str,
    context: Dict[str, Any],
    actions: List[Dict[str, Any]],
    outcome: str,
    success: bool,
    lessons_learned: List[str],
    tags: Optional[List[str]] = None,
    importance: float = 1.0,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        episode_id = await manager.record_episode(
            agent_id=agent_id,
            task_description=task_description,
            context=context,
            actions=actions,
            outcome=outcome,
            success=success,
            lessons_learned=lessons_learned,
            tags=tags,
            importance=importance,
        )
        
        return ToolResult(True, "record_episode", data={"episode_id": episode_id})
    except Exception as e:
        return ToolResult(False, "record_episode", error=f"{type(e).__name__}: {e}")


async def recall_episodes(agent_id: str, query: str, top_k: int = 5) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        episodes = await manager.recall_episodes(agent_id, query, top_k)
        return ToolResult(True, "recall_episodes", data={"episodes": [ep.__dict__ for ep in episodes]})
    except Exception as e:
        return ToolResult(False, "recall_episodes", error=f"{type(e).__name__}: {e}")


async def add_concept(
    name: str,
    type: str,
    definition: str,
    context: str,
    examples: Optional[List[str]] = None,
    related_concepts: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    source: Optional[str] = None,
    confidence: float = 1.0,
    created_by: Optional[str] = None,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        concept_id = await manager.add_concept(
            name=name,
            type=type,
            definition=definition,
            context=context,
            examples=examples,
            related_concepts=related_concepts,
            tags=tags,
            source=source,
            confidence=confidence,
            created_by=created_by,
        )
        
        return ToolResult(True, "add_concept", data={"concept_id": concept_id})
    except Exception as e:
        return ToolResult(False, "add_concept", error=f"{type(e).__name__}: {e}")


async def add_adr(
    title: str,
    status: str,
    context: str,
    decision: str,
    consequences: List[str],
    alternatives: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    created_by: Optional[str] = None,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        adr_id = await manager.add_adr(
            title=title,
            status=status,
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives=alternatives,
            tags=tags,
            created_by=created_by,
        )
        
        return ToolResult(True, "add_adr", data={"adr_id": adr_id})
    except Exception as e:
        return ToolResult(False, "add_adr", error=f"{type(e).__name__}: {e}")


async def search_concepts(query: str, top_k: int = 10, concept_type: Optional[str] = None, tags: Optional[List[str]] = None) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        concepts = await manager.search_concepts(query, top_k=top_k)
        return ToolResult(True, "search_concepts", data={"concepts": [c.__dict__ for c in concepts]})
    except Exception as e:
        return ToolResult(False, "search_concepts", error=f"{type(e).__name__}: {e}")


async def add_code_entity(
    type: str,
    name: str,
    qualified_name: str,
    properties: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    confidence: float = 1.0,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        entity_id = await manager.add_code_entity(
            type=type,
            name=name,
            qualified_name=qualified_name,
            properties=properties,
            source=source,
        )
        
        return ToolResult(True, "add_code_entity", data={"entity_id": entity_id})
    except Exception as e:
        return ToolResult(False, "add_code_entity", error=f"{type(e).__name__}: {e}")


async def add_code_relation(
    source_id: str,
    target_id: str,
    type: str,
    properties: Optional[Dict[str, Any]] = None,
    confidence: float = 1.0,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        relation_id = await manager.add_code_relation(
            source_id=source_id,
            target_id=target_id,
            type=type,
            properties=properties,
        )
        
        return ToolResult(True, "add_code_relation", data={"relation_id": relation_id})
    except Exception as e:
        return ToolResult(False, "add_code_relation", error=f"{type(e).__name__}: {e}")


async def find_code_path(source_name: str, target_name: str) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        path = await manager.find_code_path(source_name, target_name)
        if path:
            path_data = [{"entity": e.__dict__, "relation": r.__dict__} for e, r in path]
        else:
            path_data = None
        
        return ToolResult(True, "find_code_path", data={"path": path_data})
    except Exception as e:
        return ToolResult(False, "find_code_path", error=f"{type(e).__name__}: {e}")


async def explain_code_change(file_path: str, start_line: int, end_line: int) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        result = await manager.explain_code_change(file_path, start_line, end_line)
        return ToolResult(True, "explain_code_change", data=result)
    except Exception as e:
        return ToolResult(False, "explain_code_change", error=f"{type(e).__name__}: {e}")


async def query_git_history(
    question: str,
    top_k: int = 10,
    include_commits: bool = True,
    include_diffs: bool = True,
    include_blame: bool = False,
    file_path: Optional[str] = None,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        results = await manager.query_git_history(
            question=question,
            top_k=top_k,
            include_commits=include_commits,
            include_diffs=include_diffs,
            include_blame=include_blame,
            file_path=file_path,
        )
        
        return ToolResult(True, "query_git_history", data=results)
    except Exception as e:
        return ToolResult(False, "query_git_history", error=f"{type(e).__name__}: {e}")


async def run_memory_consolidation() -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        result = await manager.run_consolidation()
        return ToolResult(True, "run_memory_consolidation", data=result)
    except Exception as e:
        return ToolResult(False, "run_memory_consolidation", error=f"{type(e).__name__}: {e}")


async def export_memory_pack(
    agent_id: Optional[str] = None,
    include_episodic: bool = True,
    include_semantic: bool = True,
    include_pins: bool = True,
    include_knowledge_graph: bool = False,
) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        pack = await manager.export_memory_pack(
            agent_id=agent_id,
            include_episodic=include_episodic,
            include_semantic=include_semantic,
            include_pins=include_pins,
            include_knowledge_graph=include_knowledge_graph,
        )
        
        return ToolResult(True, "export_memory_pack", data=pack)
    except Exception as e:
        return ToolResult(False, "export_memory_pack", error=f"{type(e).__name__}: {e}")


async def import_memory_pack(pack: Dict[str, Any], agent_id: Optional[str] = None) -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        counts = await manager.import_memory_pack(pack, agent_id)
        return ToolResult(True, "import_memory_pack", data={"counts": counts})
    except Exception as e:
        return ToolResult(False, "import_memory_pack", error=f"{type(e).__name__}: {e}")


async def get_memory_stats() -> ToolResult:
    try:
        from .memory import get_memory_manager
        
        manager = get_memory_manager()
        await manager.initialize()
        
        stats = manager.get_stats()
        return ToolResult(True, "get_memory_stats", data=stats)
    except Exception as e:
        return ToolResult(False, "get_memory_stats", error=f"{type(e).__name__}: {e}")
