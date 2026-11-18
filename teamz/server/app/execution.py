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
        # Phase 12: Collaboration & Human-in-the-Loop
        if tool == "request_approval":
            return await request_approval(
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                description=args.get("description") if isinstance(args.get("description"), str) else "",
                approval_type=args.get("approval_type") if isinstance(args.get("approval_type"), str) else "",
                requester=args.get("requester") if isinstance(args.get("requester"), str) else "",
                context=args.get("context") if isinstance(args.get("context"), dict) else {},
                priority=args.get("priority") if isinstance(args.get("priority"), str) else None,
                required_approvers=args.get("required_approvers") if isinstance(args.get("required_approvers"), list) else None,
                min_approvals=args.get("min_approvals") if isinstance(args.get("min_approvals"), int) else None,
                timeout_hours=args.get("timeout_hours") if isinstance(args.get("timeout_hours"), (int, float)) else None,
                metadata=args.get("metadata") if isinstance(args.get("metadata"), dict) else None,
            )
        if tool == "decide_approval":
            return await decide_approval(
                request_id=args.get("request_id") if isinstance(args.get("request_id"), str) else "",
                user_id=args.get("user_id") if isinstance(args.get("user_id"), str) else "",
                decision=args.get("decision") if isinstance(args.get("decision"), str) else "",
                rationale=args.get("rationale") if isinstance(args.get("rationale"), str) else "",
                conditions=args.get("conditions") if isinstance(args.get("conditions"), list) else None,
            )
        if tool == "create_pair_session":
            return await create_pair_session(
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                creator_id=args.get("creator_id") if isinstance(args.get("creator_id"), str) else "",
                creator_name=args.get("creator_name") if isinstance(args.get("creator_name"), str) else "",
                is_agent=bool(args.get("is_agent", False)),
            )
        if tool == "join_pair_session":
            return await join_pair_session(
                session_id=args.get("session_id") if isinstance(args.get("session_id"), str) else "",
                user_id=args.get("user_id") if isinstance(args.get("user_id"), str) else "",
                name=args.get("name") if isinstance(args.get("name"), str) else "",
                preferred_role=args.get("preferred_role") if isinstance(args.get("preferred_role"), str) else None,
                is_agent=bool(args.get("is_agent", False)),
            )
        if tool == "create_code_review":
            return await create_code_review(
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                description=args.get("description") if isinstance(args.get("description"), str) else "",
                author=args.get("author") if isinstance(args.get("author"), str) else "",
                head_branch=args.get("head_branch") if isinstance(args.get("head_branch"), str) else "",
                base_branch=args.get("base_branch") if isinstance(args.get("base_branch"), str) else "main",
                files_changed=args.get("files_changed") if isinstance(args.get("files_changed"), list) else None,
                diff=args.get("diff") if isinstance(args.get("diff"), str) else "",
                reviewers=args.get("reviewers") if isinstance(args.get("reviewers"), list) else None,
            )
        if tool == "add_review_comment":
            return await add_review_comment(
                review_id=args.get("review_id") if isinstance(args.get("review_id"), str) else "",
                author=args.get("author") if isinstance(args.get("author"), str) else "",
                file_path=args.get("file_path") if isinstance(args.get("file_path"), str) else "",
                content=args.get("content") if isinstance(args.get("content"), str) else "",
                line_start=args.get("line_start") if isinstance(args.get("line_start"), int) else None,
                line_end=args.get("line_end") if isinstance(args.get("line_end"), int) else None,
                comment_type=args.get("comment_type") if isinstance(args.get("comment_type"), str) else "inline",
                suggestion=args.get("suggestion") if isinstance(args.get("suggestion"), str) else None,
            )
        if tool == "submit_review_decision":
            return await submit_review_decision(
                review_id=args.get("review_id") if isinstance(args.get("review_id"), str) else "",
                reviewer=args.get("reviewer") if isinstance(args.get("reviewer"), str) else "",
                decision=args.get("decision") if isinstance(args.get("decision"), str) else "",
                rationale=args.get("rationale") if isinstance(args.get("rationale"), str) else "",
            )
        if tool == "request_handoff":
            return await request_handoff(
                type=args.get("type") if isinstance(args.get("type"), str) else "",
                reason=args.get("reason") if isinstance(args.get("reason"), str) else "",
                from_party=args.get("from_party") if isinstance(args.get("from_party"), str) else "",
                to_party=args.get("to_party") if isinstance(args.get("to_party"), str) else "",
                context=args.get("context") if isinstance(args.get("context"), dict) else {},
                message=args.get("message") if isinstance(args.get("message"), str) else "",
                priority=int(args.get("priority") or 0),
            )
        if tool == "respond_handoff":
            return await respond_handoff(
                request_id=args.get("request_id") if isinstance(args.get("request_id"), str) else "",
                responder=args.get("responder") if isinstance(args.get("responder"), str) else "",
                accepted=bool(args.get("accepted", False)),
                message=args.get("message") if isinstance(args.get("message"), str) else "",
                conditions=args.get("conditions") if isinstance(args.get("conditions"), list) else None,
            )
        if tool == "create_whiteboard":
            return await create_whiteboard(
                name=args.get("name") if isinstance(args.get("name"), str) else "",
                creator=args.get("creator") if isinstance(args.get("creator"), str) else "",
                theme=args.get("theme") if isinstance(args.get("theme"), str) else None,
            )
        if tool == "add_whiteboard_element":
            return await add_whiteboard_element(
                scene_id=args.get("scene_id") if isinstance(args.get("scene_id"), str) else "",
                element=args.get("element") if isinstance(args.get("element"), dict) else {},
                user_id=args.get("user_id") if isinstance(args.get("user_id"), str) else "",
            )
        if tool == "schedule_meeting":
            return await schedule_meeting(
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                host_id=args.get("host_id") if isinstance(args.get("host_id"), str) else "",
                scheduled_at=float(args.get("scheduled_at") or 0),
                description=args.get("description") if isinstance(args.get("description"), str) else "",
                participants=args.get("participants") if isinstance(args.get("participants"), list) else None,
                tags=args.get("tags") if isinstance(args.get("tags"), list) else None,
            )
        if tool == "start_meeting":
            return await start_meeting(
                meeting_id=args.get("meeting_id") if isinstance(args.get("meeting_id"), str) else "",
            )
        if tool == "end_meeting":
            return await end_meeting(
                meeting_id=args.get("meeting_id") if isinstance(args.get("meeting_id"), str) else "",
            )
        if tool == "add_meeting_transcript":
            return await add_meeting_transcript(
                meeting_id=args.get("meeting_id") if isinstance(args.get("meeting_id"), str) else "",
                speaker_id=args.get("speaker_id") if isinstance(args.get("speaker_id"), str) else "",
                speaker_name=args.get("speaker_name") if isinstance(args.get("speaker_name"), str) else "",
                text=args.get("text") if isinstance(args.get("text"), str) else "",
                start_time=float(args.get("start_time") or 0),
                end_time=float(args.get("end_time") or 0),
                confidence=float(args.get("confidence") or 1.0),
                is_agent=bool(args.get("is_agent", False)),
            )
        if tool == "create_digest_template":
            return await create_digest_template(
                name=args.get("name") if isinstance(args.get("name"), str) else "",
                description=args.get("description") if isinstance(args.get("description"), str) else "",
                sections=args.get("sections") if isinstance(args.get("sections"), list) else [],
                recipients=args.get("recipients") if isinstance(args.get("recipients"), list) else [],
                frequency=args.get("frequency") if isinstance(args.get("frequency"), str) else "daily",
                format=args.get("format") if isinstance(args.get("format"), str) else "markdown",
            )
        if tool == "generate_digest":
            return await generate_digest(
                template_id=args.get("template_id") if isinstance(args.get("template_id"), str) else "",
                period_start=args.get("period_start") if isinstance(args.get("period_start"), (int, float)) else None,
                period_end=args.get("period_end") if isinstance(args.get("period_end"), (int, float)) else None,
            )
        if tool == "create_guest_token":
            return await create_guest_token(
                role=args.get("role") if isinstance(args.get("role"), str) else "",
                resource_type=args.get("resource_type") if isinstance(args.get("resource_type"), str) else "",
                resource_id=args.get("resource_id") if isinstance(args.get("resource_id"), str) else "",
                created_by=args.get("created_by") if isinstance(args.get("created_by"), str) else "",
                expires_in_hours=args.get("expires_in_hours") if isinstance(args.get("expires_in_hours"), (int, float)) else None,
                max_uses=args.get("max_uses") if isinstance(args.get("max_uses"), int) else None,
                resource_name=args.get("resource_name") if isinstance(args.get("resource_name"), str) else None,
                allowed_ips=args.get("allowed_ips") if isinstance(args.get("allowed_ips"), list) else None,
                allowed_domains=args.get("allowed_domains") if isinstance(args.get("allowed_domains"), list) else None,
            )
        if tool == "validate_guest_token":
            return await validate_guest_token(
                token_string=args.get("token_string") if isinstance(args.get("token_string"), str) else "",
                client_ip=args.get("client_ip") if isinstance(args.get("client_ip"), str) else None,
            )
        if tool == "open_conflict":
            return await open_conflict(
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                description=args.get("description") if isinstance(args.get("description"), str) else "",
                type=args.get("type") if isinstance(args.get("type"), str) else "",
                parties=args.get("parties") if isinstance(args.get("parties"), list) else [],
                severity=args.get("severity") if isinstance(args.get("severity"), str) else None,
                reported_by=args.get("reported_by") if isinstance(args.get("reported_by"), str) else "",
            )
        if tool == "assign_mediator":
            return await assign_mediator(
                conflict_id=args.get("conflict_id") if isinstance(args.get("conflict_id"), str) else "",
                mediator_id=args.get("mediator_id") if isinstance(args.get("mediator_id"), str) else "",
            )
        if tool == "resolve_conflict":
            return await resolve_conflict(
                conflict_id=args.get("conflict_id") if isinstance(args.get("conflict_id"), str) else "",
                resolution=args.get("resolution") if isinstance(args.get("resolution"), str) else "",
                agreed_actions=args.get("agreed_actions") if isinstance(args.get("agreed_actions"), list) else [],
            )
        if tool == "give_kudos":
            return await give_kudos(
                from_agent=args.get("from_agent") if isinstance(args.get("from_agent"), str) else "",
                to_agent=args.get("to_agent") if isinstance(args.get("to_agent"), str) else "",
                category=args.get("category") if isinstance(args.get("category"), str) else "",
                message=args.get("message") if isinstance(args.get("message"), str) else "",
                project_id=args.get("project_id") if isinstance(args.get("project_id"), str) else None,
                task_id=args.get("task_id") if isinstance(args.get("task_id"), str) else None,
                visibility=args.get("visibility") if isinstance(args.get("visibility"), str) else "team",
            )
        if tool == "update_streak":
            return await update_streak(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                streak_type=args.get("streak_type") if isinstance(args.get("streak_type"), str) else "",
                increment=bool(args.get("increment", True)),
            )
        if tool == "award_achievement":
            return await award_achievement(
                agent_id=args.get("agent_id") if isinstance(args.get("agent_id"), str) else "",
                type=args.get("type") if isinstance(args.get("type"), str) else "",
                title=args.get("title") if isinstance(args.get("title"), str) else "",
                description=args.get("description") if isinstance(args.get("description"), str) else "",
                icon=args.get("icon") if isinstance(args.get("icon"), str) else "🏆",
            )
        if tool == "record_velocity":
            return await record_velocity(
                team_id=args.get("team_id") if isinstance(args.get("team_id"), str) else "",
                completed_tasks=int(args.get("completed_tasks") or 0),
                completed_story_points=int(args.get("completed_story_points") or 0),
                cycle_times_hours=args.get("cycle_times_hours") if isinstance(args.get("cycle_times_hours"), list) else [],
                lead_times_hours=args.get("lead_times_hours") if isinstance(args.get("lead_times_hours"), list) else [],
                quality_metrics=args.get("quality_metrics") if isinstance(args.get("quality_metrics"), dict) else {},
                collaboration_data=args.get("collaboration_data") if isinstance(args.get("collaboration_data"), dict) else {},
            )
        if tool == "get_leaderboard":
            return await get_leaderboard(
                metric=args.get("metric") if isinstance(args.get("metric"), str) else "kudos_received",
                limit=int(args.get("limit") or 10),
            )
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
        # Phase 12: Collaboration & Human-in-the-Loop
        {
            "name": "request_approval",
            "description": "Request approval for a sensitive operation.",
            "params": {"title": "string", "description": "string", "approval_type": "string", "requester": "string", "context": "object", "priority?": "string", "required_approvers?": ["string"], "min_approvals?": "number", "timeout_hours?": "number", "metadata?": "object"},
        },
        {
            "name": "decide_approval",
            "description": "Decide on an approval request.",
            "params": {"request_id": "string", "user_id": "string", "decision": "string", "rationale?": "string", "conditions?": ["string"]},
        },
        {
            "name": "create_pair_session",
            "description": "Create a pair programming session.",
            "params": {"title": "string", "creator_id": "string", "creator_name": "string", "is_agent?": "boolean"},
        },
        {
            "name": "join_pair_session",
            "description": "Join a pair programming session.",
            "params": {"session_id": "string", "user_id": "string", "name": "string", "preferred_role?": "string", "is_agent?": "boolean"},
        },
        {
            "name": "create_code_review",
            "description": "Create a code review.",
            "params": {"title": "string", "description": "string", "author": "string", "head_branch": "string", "base_branch?": "string", "files_changed?": ["string"], "diff?": "string", "reviewers?": ["string"]},
        },
        {
            "name": "add_review_comment",
            "description": "Add a comment to a code review.",
            "params": {"review_id": "string", "author": "string", "file_path": "string", "content": "string", "line_start?": "number", "line_end?": "number", "comment_type?": "string", "suggestion?": "string"},
        },
        {
            "name": "submit_review_decision",
            "description": "Submit a decision on a code review.",
            "params": {"review_id": "string", "reviewer": "string", "decision": "string", "rationale?": "string"},
        },
        {
            "name": "request_handoff",
            "description": "Request a handoff between human and agent.",
            "params": {"type": "string", "reason": "string", "from_party": "string", "to_party": "string", "context": "object", "message?": "string", "priority?": "number"},
        },
        {
            "name": "respond_handoff",
            "description": "Respond to a handoff request.",
            "params": {"request_id": "string", "responder": "string", "accepted": "boolean", "message?": "string", "conditions?": ["string"]},
        },
        {
            "name": "create_whiteboard",
            "description": "Create a shared whiteboard.",
            "params": {"name": "string", "creator": "string", "theme?": "string"},
        },
        {
            "name": "add_whiteboard_element",
            "description": "Add an element to a whiteboard.",
            "params": {"scene_id": "string", "element": "object", "user_id": "string"},
        },
        {
            "name": "schedule_meeting",
            "description": "Schedule a meeting with the meeting agent.",
            "params": {"title": "string", "host_id": "string", "scheduled_at": "number", "description?": "string", "participants?": ["string"], "tags?": ["string"]},
        },
        {
            "name": "start_meeting",
            "description": "Start a scheduled meeting.",
            "params": {"meeting_id": "string"},
        },
        {
            "name": "end_meeting",
            "description": "End an active meeting.",
            "params": {"meeting_id": "string"},
        },
        {
            "name": "add_meeting_transcript",
            "description": "Add a transcript segment to a meeting.",
            "params": {"meeting_id": "string", "speaker_id": "string", "speaker_name": "string", "text": "string", "start_time": "number", "end_time": "number", "confidence?": "number", "is_agent?": "boolean"},
        },
        {
            "name": "create_digest_template",
            "description": "Create a digest template for stakeholder updates.",
            "params": {"name": "string", "description": "string", "sections": ["object"], "recipients": ["string"], "frequency?": "string", "format?": "string"},
        },
        {
            "name": "generate_digest",
            "description": "Generate a digest from a template.",
            "params": {"template_id": "string", "period_start?": "number", "period_end?": "number"},
        },
        {
            "name": "create_guest_token",
            "description": "Create a guest access token for read-only access.",
            "params": {"role": "string", "resource_type": "string", "resource_id": "string", "created_by": "string", "expires_in_hours?": "number", "max_uses?": "number", "resource_name?": "string", "allowed_ips?": ["string"], "allowed_domains?": ["string"]},
        },
        {
            "name": "validate_guest_token",
            "description": "Validate a guest access token.",
            "params": {"token_string": "string", "client_ip?": "string"},
        },
        {
            "name": "open_conflict",
            "description": "Open a conflict for mediation.",
            "params": {"title": "string", "description": "string", "type": "string", "parties": ["object"], "severity?": "string", "reported_by?": "string"},
        },
        {
            "name": "assign_mediator",
            "description": "Assign a mediator to a conflict.",
            "params": {"conflict_id": "string", "mediator_id": "string"},
        },
        {
            "name": "resolve_conflict",
            "description": "Resolve a conflict with agreed actions.",
            "params": {"conflict_id": "string", "resolution": "string", "agreed_actions": ["string"]},
        },
        {
            "name": "give_kudos",
            "description": "Give kudos to another agent.",
            "params": {"from_agent": "string", "to_agent": "string", "category": "string", "message": "string", "project_id?": "string", "task_id?": "string", "visibility?": "string"},
        },
        {
            "name": "update_streak",
            "description": "Update an agent's streak.",
            "params": {"agent_id": "string", "streak_type": "string", "increment?": "boolean"},
        },
        {
            "name": "award_achievement",
            "description": "Award an achievement to an agent.",
            "params": {"agent_id": "string", "type": "string", "title": "string", "description": "string", "icon?": "string"},
        },
        {
            "name": "record_velocity",
            "description": "Record team velocity metrics.",
            "params": {"team_id": "string", "completed_tasks": "number", "completed_story_points": "number", "cycle_times_hours": ["number"], "lead_times_hours": ["number"], "quality_metrics": "object", "collaboration_data": "object"},
        },
        {
            "name": "get_leaderboard",
            "description": "Get leaderboard for a social metric.",
            "params": {"metric?": "string", "limit?": "number"},
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


# --- Phase 12: Collaboration & Human-in-the-Loop ----------------------------------

async def request_approval(
    title: str,
    description: str,
    approval_type: str,
    requester: str,
    context: Dict[str, Any],
    priority: Optional[str] = None,
    required_approvers: Optional[List[str]] = None,
    min_approvals: Optional[int] = None,
    timeout_hours: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ToolResult:
    try:
        from .collaboration import get_approval_gate
        
        gate = get_approval_gate()
        request_id = gate.request_approval(
            title=title,
            description=description,
            approval_type=approval_type,
            requester=requester,
            context=context,
            priority=priority,
            required_approvers=required_approvers,
            min_approvals=min_approvals,
            timeout_hours=timeout_hours,
            metadata=metadata,
        )
        return ToolResult(True, "request_approval", data={"request_id": request_id})
    except Exception as e:
        return ToolResult(False, "request_approval", error=f"{type(e).__name__}: {e}")


async def decide_approval(
    request_id: str,
    user_id: str,
    decision: str,
    rationale: str = "",
    conditions: Optional[List[str]] = None,
) -> ToolResult:
    try:
        from .collaboration import get_approval_gate
        
        gate = get_approval_gate()
        success = gate.decide(request_id, user_id, decision, rationale, conditions)
        return ToolResult(True, "decide_approval", data={"success": success})
    except Exception as e:
        return ToolResult(False, "decide_approval", error=f"{type(e).__name__}: {e}")


async def create_pair_session(
    title: str,
    creator_id: str,
    creator_name: str,
    is_agent: bool = False,
) -> ToolResult:
    try:
        from .collaboration import get_pair_session
        
        pair = get_pair_session()
        session_id = pair.create_session(title, creator_id, creator_name, is_agent)
        return ToolResult(True, "create_pair_session", data={"session_id": session_id})
    except Exception as e:
        return ToolResult(False, "create_pair_session", error=f"{type(e).__name__}: {e}")


async def join_pair_session(
    session_id: str,
    user_id: str,
    name: str,
    preferred_role: Optional[str] = None,
    is_agent: bool = False,
) -> ToolResult:
    try:
        from .collaboration import get_pair_session
        
        pair = get_pair_session()
        from .pair_programming import PairRole
        role = PairRole(preferred_role) if preferred_role else None
        success = pair.join_session(session_id, user_id, name, role, is_agent)
        return ToolResult(True, "join_pair_session", data={"success": success})
    except Exception as e:
        return ToolResult(False, "join_pair_session", error=f"{type(e).__name__}: {e}")


async def create_code_review(
    title: str,
    description: str,
    author: str,
    head_branch: str,
    base_branch: str = "main",
    files_changed: Optional[List[str]] = None,
    diff: str = "",
    reviewers: Optional[List[str]] = None,
) -> ToolResult:
    try:
        from .collaboration import get_code_review
        
        reviews = get_code_review()
        review_id = reviews.create_review(
            title=title,
            description=description,
            author=author,
            head_branch=head_branch,
            base_branch=base_branch,
            files_changed=files_changed,
            diff=diff,
            reviewers=reviewers,
        )
        return ToolResult(True, "create_code_review", data={"review_id": review_id})
    except Exception as e:
        return ToolResult(False, "create_code_review", error=f"{type(e).__name__}: {e}")


async def add_review_comment(
    review_id: str,
    author: str,
    file_path: str,
    content: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    comment_type: str = "inline",
    suggestion: Optional[str] = None,
) -> ToolResult:
    try:
        from .collaboration import get_code_review
        
        reviews = get_code_review()
        comment_id = reviews.add_comment(
            review_id=review_id,
            author=author,
            file_path=file_path,
            content=content,
            line_start=line_start,
            line_end=line_end,
            comment_type=comment_type,
            suggestion=suggestion,
        )
        return ToolResult(True, "add_review_comment", data={"comment_id": comment_id})
    except Exception as e:
        return ToolResult(False, "add_review_comment", error=f"{type(e).__name__}: {e}")


async def submit_review_decision(
    review_id: str,
    reviewer: str,
    decision: str,
    rationale: str = "",
) -> ToolResult:
    try:
        from .collaboration import get_code_review
        
        reviews = get_code_review()
        success = reviews.submit_decision(review_id, reviewer, decision, rationale)
        return ToolResult(True, "submit_review_decision", data={"success": success})
    except Exception as e:
        return ToolResult(False, "submit_review_decision", error=f"{type(e).__name__}: {e}")


async def request_handoff(
    type: str,
    reason: str,
    from_party: str,
    to_party: str,
    context: Dict[str, Any],
    message: str = "",
    priority: int = 0,
) -> ToolResult:
    try:
        from .collaboration import get_handoff_manager
        from .handoff import HandoffType, HandoffReason, HandoffContext
        
        handoffs = get_handoff_manager()
        handoff_id = handoffs.request_handoff(
            type=type,
            reason=reason,
            from_party=from_party,
            to_party=to_party,
            context=HandoffContext(**context),
            message=message,
            priority=priority,
        )
        return ToolResult(True, "request_handoff", data={"handoff_id": handoff_id})
    except Exception as e:
        return ToolResult(False, "request_handoff", error=f"{type(e).__name__}: {e}")


async def respond_handoff(
    request_id: str,
    responder: str,
    accepted: bool,
    message: str = "",
    conditions: Optional[List[str]] = None,
) -> ToolResult:
    try:
        from .collaboration import get_handoff_manager
        
        handoffs = get_handoff_manager()
        success = handoffs.respond(request_id, responder, accepted, message, conditions)
        return ToolResult(True, "respond_handoff", data={"success": success})
    except Exception as e:
        return ToolResult(False, "respond_handoff", error=f"{type(e).__name__}: {e}")


async def create_whiteboard(
    name: str,
    creator: str,
    theme: Optional[str] = None,
) -> ToolResult:
    try:
        from .collaboration import get_whiteboard
        
        wb = get_whiteboard()
        scene_id = wb.create_scene(name, creator, theme)
        return ToolResult(True, "create_whiteboard", data={"scene_id": scene_id})
    except Exception as e:
        return ToolResult(False, "create_whiteboard", error=f"{type(e).__name__}: {e}")


async def add_whiteboard_element(
    scene_id: str,
    element: Dict[str, Any],
    user_id: str,
) -> ToolResult:
    try:
        from .collaboration import get_whiteboard
        from .whiteboard import WhiteboardElement, ElementType, ElementStyle
        
        wb = get_whiteboard()
        
        # Create element from dict
        style = ElementStyle()
        if element.get("style"):
            style = ElementStyle(**element["style"])
        
        elem = WhiteboardElement(
            id=str(uuid.uuid4())[:8],
            type=ElementType(element["type"]),
            x=element["x"],
            y=element["y"],
            width=element["width"],
            height=element["height"],
            angle=element.get("angle", 0.0),
            style=style,
            text=element.get("text", ""),
            points=element.get("points", []),
            created_by=user_id,
            updated_by=user_id,
        )
        
        wb.add_element(scene_id, elem, user_id)
        return ToolResult(True, "add_whiteboard_element", data={"element_id": elem.id})
    except Exception as e:
        return ToolResult(False, "add_whiteboard_element", error=f"{type(e).__name__}: {e}")


async def schedule_meeting(
    title: str,
    host_id: str,
    scheduled_at: float,
    description: str = "",
    participants: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> ToolResult:
    try:
        from .collaboration import get_meeting_agent
        
        meetings = get_meeting_agent()
        meeting_id = meetings.schedule_meeting(
            title=title,
            host_id=host_id,
            scheduled_at=scheduled_at,
            description=description,
            participants=participants,
            tags=tags,
        )
        return ToolResult(True, "schedule_meeting", data={"meeting_id": meeting_id})
    except Exception as e:
        return ToolResult(False, "schedule_meeting", error=f"{type(e).__name__}: {e}")


async def start_meeting(meeting_id: str) -> ToolResult:
    try:
        from .collaboration import get_meeting_agent
        
        meetings = get_meeting_agent()
        success = meetings.start_meeting(meeting_id)
        return ToolResult(True, "start_meeting", data={"success": success})
    except Exception as e:
        return ToolResult(False, "start_meeting", error=f"{type(e).__name__}: {e}")


async def end_meeting(meeting_id: str) -> ToolResult:
    try:
        from .collaboration import get_meeting_agent
        
        meetings = get_meeting_agent()
        success = meetings.end_meeting(meeting_id)
        return ToolResult(True, "end_meeting", data={"success": success})
    except Exception as e:
        return ToolResult(False, "end_meeting", error=f"{type(e).__name__}: {e}")


async def add_meeting_transcript(
    meeting_id: str,
    speaker_id: str,
    speaker_name: str,
    text: str,
    start_time: float,
    end_time: float,
    confidence: float = 1.0,
    is_agent: bool = False,
) -> ToolResult:
    try:
        from .collaboration import get_meeting_agent
        
        meetings = get_meeting_agent()
        segment_id = meetings.add_transcript(
            meeting_id=meeting_id,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            text=text,
            start_time=start_time,
            end_time=end_time,
            confidence=confidence,
            is_agent=is_agent,
        )
        return ToolResult(True, "add_meeting_transcript", data={"segment_id": segment_id})
    except Exception as e:
        return ToolResult(False, "add_meeting_transcript", error=f"{type(e).__name__}: {e}")


async def create_digest_template(
    name: str,
    description: str,
    sections: List[Dict[str, Any]],
    recipients: List[str],
    frequency: str = "daily",
    format: str = "markdown",
) -> ToolResult:
    try:
        from .collaboration import get_digest_generator
        from .digest import DigestTemplate, DigestSection, ContentType, DigestFormat, DigestFrequency
        
        digests = get_digest_generator()
        sections_objs = [
            DigestSection(
                type=ContentType(s["type"]),
                title=s["title"],
                content=[],
                order=s.get("order", 0),
            )
            for s in sections
        ]
        
        template = DigestTemplate(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            sections=sections_objs,
            format=format,
            frequency=frequency,
            recipients=recipients,
        )
        
        template_id = digests.create_template(template)
        return ToolResult(True, "create_digest_template", data={"template_id": template_id})
    except Exception as e:
        return ToolResult(False, "create_digest_template", error=f"{type(e).__name__}: {e}")


async def generate_digest(
    template_id: str,
    period_start: Optional[float] = None,
    period_end: Optional[float] = None,
) -> ToolResult:
    try:
        from .collaboration import get_digest_generator
        
        digests = get_digest_generator()
        digest = digests.generate_digest(template_id, period_start, period_end)
        if digest:
            return ToolResult(True, "generate_digest", data={"digest_id": digest.id})
        return ToolResult(False, "generate_digest", error="Failed to generate digest")
    except Exception as e:
        return ToolResult(False, "generate_digest", error=f"{type(e).__name__}: {e}")


async def send_digest(digest_id: str) -> ToolResult:
    try:
        from .collaboration import get_digest_generator
        
        digests = get_digest_generator()
        success = digests.send_digest(digest_id)
        return ToolResult(True, "send_digest", data={"success": success})
    except Exception as e:
        return ToolResult(False, "send_digest", error=f"{type(e).__name__}: {e}")


async def create_guest_token(
    role: str,
    resource_type: str,
    resource_id: str,
    created_by: str,
    expires_in_hours: Optional[float] = None,
    max_uses: Optional[int] = None,
    resource_name: Optional[str] = None,
    allowed_ips: Optional[List[str]] = None,
    allowed_domains: Optional[List[str]] = None,
) -> ToolResult:
    try:
        from .collaboration import get_guest_access
        from .guest_access import GuestRole, ResourceType
        
        guest = get_guest_access()
        token = guest.create_token(
            role=role,
            resource_type=resource_type,
            resource_id=resource_id,
            created_by=created_by,
            expires_in_hours=expires_in_hours,
            max_uses=max_uses,
            resource_name=resource_name,
            allowed_ips=allowed_ips,
            allowed_domains=allowed_domains,
        )
        return ToolResult(True, "create_guest_token", data={"token_id": token.id, "token": token.token})
    except Exception as e:
        return ToolResult(False, "create_guest_token", error=f"{type(e).__name__}: {e}")


async def validate_guest_token(token_string: str, client_ip: Optional[str] = None) -> ToolResult:
    try:
        from .collaboration import get_guest_access
        
        guest = get_guest_access()
        token = guest.validate_token(token_string, client_ip)
        if token:
            return ToolResult(True, "validate_guest_token", data={"token_id": token.id, "valid": True})
        return ToolResult(False, "validate_guest_token", error="Invalid or expired token")
    except Exception as e:
        return ToolResult(False, "validate_guest_token", error=f"{type(e).__name__}: {e}")


async def open_conflict(
    title: str,
    description: str,
    type: str,
    parties: List[Dict[str, Any]],
    severity: Optional[str] = None,
    reported_by: str = "",
) -> ToolResult:
    try:
        from .collaboration import get_conflict_resolver
        from .conflict_resolution import ConflictType, ConflictSeverity
        
        conflicts = get_conflict_resolver()
        conflict_id = conflicts.open_conflict(
            title=title,
            description=description,
            type=type,
            parties=parties,
            severity=severity,
            reported_by=reported_by,
        )
        return ToolResult(True, "open_conflict", data={"conflict_id": conflict_id})
    except Exception as e:
        return ToolResult(False, "open_conflict", error=f"{type(e).__name__}: {e}")


async def assign_mediator(conflict_id: str, mediator_id: str) -> ToolResult:
    try:
        from .collaboration import get_conflict_resolver
        
        conflicts = get_conflict_resolver()
        success = conflicts.assign_mediator(conflict_id, mediator_id)
        return ToolResult(True, "assign_mediator", data={"success": success})
    except Exception as e:
        return ToolResult(False, "assign_mediator", error=f"{type(e).__name__}: {e}")


async def resolve_conflict(
    conflict_id: str,
    resolution: str,
    agreed_actions: List[str],
) -> ToolResult:
    try:
        from .collaboration import get_conflict_resolver
        
        conflicts = get_conflict_resolver()
        success = conflicts.complete_mediation(conflict_id, resolution, agreed_actions)
        return ToolResult(True, "resolve_conflict", data={"success": success})
    except Exception as e:
        return ToolResult(False, "resolve_conflict", error=f"{type(e).__name__}: {e}")


async def give_kudos(
    from_agent: str,
    to_agent: str,
    category: str,
    message: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    visibility: str = "team",
) -> ToolResult:
    try:
        from .collaboration import get_social_features
        from .social import KudosCategory
        
        social = get_social_features()
        kudos = social.give_kudos(
            from_agent=from_agent,
            to_agent=to_agent,
            category=category,
            message=message,
            project_id=project_id,
            task_id=task_id,
            visibility=visibility,
        )
        if kudos:
            return ToolResult(True, "give_kudos", data={"kudos_id": kudos.id})
        return ToolResult(False, "give_kudos", error="Failed to give kudos")
    except Exception as e:
        return ToolResult(False, "give_kudos", error=f"{type(e).__name__}: {e}")


async def update_streak(agent_id: str, streak_type: str, increment: bool = True) -> ToolResult:
    try:
        from .collaboration import get_social_features
        
        social = get_social_features()
        streak = social.update_streak(agent_id, streak_type, increment)
        if streak:
            return ToolResult(True, "update_streak", data={"streak": streak.__dict__})
        return ToolResult(False, "update_streak", error="Failed to update streak")
    except Exception as e:
        return ToolResult(False, "update_streak", error=f"{type(e).__name__}: {e}")


async def award_achievement(
    agent_id: str,
    type: str,
    title: str,
    description: str,
    icon: str = "🏆",
) -> ToolResult:
    try:
        from .collaboration import get_social_features
        from .social import AchievementType
        
        social = get_social_features()
        achievement = social.award_achievement(
            agent_id=agent_id,
            type=type,
            title=title,
            description=description,
            icon=icon,
        )
        return ToolResult(True, "award_achievement", data={"achievement_id": achievement.id})
    except Exception as e:
        return ToolResult(False, "award_achievement", error=f"{type(e).__name__}: {e}")


async def record_velocity(
    team_id: str,
    completed_tasks: int,
    completed_story_points: int,
    cycle_times_hours: List[float],
    lead_times_hours: List[float],
    quality_metrics: Dict[str, float],
    collaboration_data: Dict[str, Any],
) -> ToolResult:
    try:
        from .collaboration import get_social_features
        
        social = get_social_features()
        velocity = social.record_team_velocity(
            team_id=team_id,
            completed_tasks=completed_tasks,
            completed_story_points=completed_story_points,
            cycle_times_hours=cycle_times_hours,
            lead_times_hours=lead_times_hours,
            quality_metrics=quality_metrics,
            collaboration_data=collaboration_data,
        )
        return ToolResult(True, "record_velocity", data={"velocity": velocity.__dict__})
    except Exception as e:
        return ToolResult(False, "record_velocity", error=f"{type(e).__name__}: {e}")


async def get_leaderboard(metric: str = "kudos_received", limit: int = 10) -> ToolResult:
    try:
        from .collaboration import get_social_features
        
        social = get_social_features()
        leaderboard = social.get_leaderboard(metric, limit)
        return ToolResult(True, "get_leaderboard", data={"leaderboard": leaderboard})
    except Exception as e:
        return ToolResult(False, "get_leaderboard", error=f"{type(e).__name__}: {e}")
