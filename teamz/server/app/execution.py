"""Agent execution tools: real shell, real file editing, GitHub/gh.

These are the "hands" the agents use to do work themselves instead of telling
the user what to type. Everything runs server-side inside the configured
workspace root, and every call returns a structured, JSON-safe result.
"""

from __future__ import annotations

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


def execute_tool(name: str, args: Optional[Dict[str, Any]] = None) -> ToolResult:
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
        return ToolResult(False, tool or "unknown", error=f"unknown tool: {name}")
    except ToolError as e:
        return ToolResult(False, tool or "unknown", error=str(e))
    except Exception as e:
        return ToolResult(False, tool or "unknown", error=f"{type(e).__name__}: {e}")


def execute_actions(actions: Any, *, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
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
        results.append(execute_tool(str(name), args).to_dict())
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
    ]
