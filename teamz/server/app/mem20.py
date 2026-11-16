from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import settings


class Mem20Error(RuntimeError):
    pass


@dataclass
class _Pending:
    future: asyncio.Future


class Mem20Client:
    """Minimal async MCP stdio client for mem20 (tools/list, tools/call)."""

    def __init__(
        self,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        *,
        timeout_s: Optional[float] = None,
    ) -> None:
        self.command = command or settings.mem20_mcp_command
        self.args = list(args if args is not None else settings.mem20_mcp_args)
        self.timeout_s = timeout_s or settings.mem20_timeout_s
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._pending: Dict[str, _Pending] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._tools_cache: Optional[List[str]] = None
        self._stderr_lines: List[str] = []

    async def start(self) -> None:
        async with self._lock:
            if self._proc and self._proc.returncode is None:
                return
            env = os.environ.copy()
            env.setdefault("PYTHONUNBUFFERED", "1")
            try:
                self._proc = await asyncio.create_subprocess_exec(
                    self.command,
                    *self.args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
            except Exception as e:
                raise Mem20Error(f"Failed to start mem20 MCP process: {e}") from e
            self._initialized = False
            self._tools_cache = None
            self._pending.clear()
            self._stderr_lines.clear()
            self._reader_task = asyncio.create_task(self._reader_loop(), name="mem20-reader")
            self._stderr_task = asyncio.create_task(self._stderr_loop(), name="mem20-stderr")
            try:
                await self._initialize()
            except Exception:
                await self.close()
                raise

    async def _stderr_loop(self) -> None:
        assert self._proc and self._proc.stderr
        try:
            while True:
                line = await self._proc.stderr.readline()
                if not line:
                    break
                s = line.decode("utf-8", errors="replace").rstrip()
                if s:
                    self._stderr_lines.append(s)
                    if len(self._stderr_lines) > 200:
                        self._stderr_lines = self._stderr_lines[-200:]
        except Exception:
            return

    async def _reader_loop(self) -> None:
        assert self._proc and self._proc.stdout
        try:
            while True:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line.decode("utf-8", errors="replace"))
                except Exception:
                    continue
                if not isinstance(msg, dict):
                    continue
                msg_id = msg.get("id")
                if msg_id is None:
                    # notification; ignore
                    continue
                key = str(msg_id)
                pending = self._pending.pop(key, None)
                if not pending or pending.future.done():
                    continue
                if "error" in msg and msg["error"]:
                    err = msg["error"]
                    if isinstance(err, dict):
                        message = err.get("message") or str(err)
                        code = err.get("code")
                        data = err.get("data")
                        e = Mem20Error(message)
                        setattr(e, "code", code)
                        setattr(e, "data", data)
                        pending.future.set_exception(e)
                    else:
                        pending.future.set_exception(Mem20Error(str(err)))
                else:
                    pending.future.set_result(msg.get("result"))
        except Exception as e:
            for p in list(self._pending.values()):
                if not p.future.done():
                    p.future.set_exception(Mem20Error(f"mem20 transport error: {e}"))
            self._pending.clear()
        finally:
            # fail any remaining pending on EOF
            for p in list(self._pending.values()):
                if not p.future.done():
                    p.future.set_exception(Mem20Error("mem20 process closed"))
            self._pending.clear()

    async def _send(self, payload: Dict[str, Any]) -> None:
        if not self._proc or self._proc.stdin is None or self._proc.returncode is not None:
            raise Mem20Error("mem20 process not running")
        data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        async with self._write_lock:
            self._proc.stdin.write(data)
            await self._proc.stdin.drain()

    async def request(self, method: str, params: Optional[Dict[str, Any]] = None, *, timeout: Optional[float] = None) -> Any:
        await self.start()
        req_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = _Pending(fut)
        await self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
        try:
            return await asyncio.wait_for(fut, timeout=timeout or self.timeout_s)
        except asyncio.TimeoutError as e:
            self._pending.pop(req_id, None)
            raise Mem20Error(f"mem20 request timed out: {method}") from e

    async def notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        await self.start()
        await self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    async def _initialize(self) -> None:
        if self._initialized:
            return
        await self.request(
            "initialize",
            {
                "protocolVersion": os.getenv("MEM20_PROTOCOL_VERSION", "2025-06-18"),
                "capabilities": {},
                "clientInfo": {"name": "teamz-orchestrator", "version": "0.1.0"},
            },
        )
        await self.notify("notifications/initialized", {})
        self._initialized = True

    async def ensure(self) -> None:
        await self.start()

    async def tools(self, refresh: bool = False) -> List[str]:
        await self.ensure()
        if self._tools_cache is not None and not refresh:
            return list(self._tools_cache)
        result = await self.request("tools/list", {})
        tools = []
        if isinstance(result, dict):
            for t in result.get("tools") or []:
                if isinstance(t, dict) and isinstance(t.get("name"), str):
                    tools.append(t["name"])
        self._tools_cache = tools
        return list(tools)

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        await self.ensure()
        return await self.request("tools/call", {"name": name, "arguments": arguments or {}})

    async def memory_store(self, content: str, *, category: str = "teamz", tags: Any = None) -> Any:
        return await self.call_tool(
            "memory_store",
            {"content": content, "category": category, "tags": tags if tags is not None else []},
        )

    async def memory_recall(self, query: str, *, limit: int = 5) -> Any:
        return await self.call_tool("memory_recall", {"query": query, "limit": max(1, int(limit))})

    @staticmethod
    def extract_text(result: Any) -> str:
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            content = result.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: List[str] = []
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        parts.append(item["text"])
                    elif isinstance(item, str):
                        parts.append(item)
                if parts:
                    return "\n".join(parts)
            for k in ("text", "result", "message"):
                v = result.get(k)
                if isinstance(v, str):
                    return v
            return json.dumps(result, ensure_ascii=False)
        return str(result)

    async def recall_texts(self, query: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            res = await self.memory_recall(query, limit=limit)
        except Exception:
            return []
        # Try to normalize common shapes
        items: List[Any] = []
        if isinstance(res, dict):
            for key in ("memories", "results", "items", "matches", "data"):
                v = res.get(key)
                if isinstance(v, list):
                    items = v
                    break
            if not items and isinstance(res.get("content"), list):
                # MCP tool envelope with text content - best effort parse
                text = self.extract_text(res)
                if text.strip():
                    return [{"text": text.strip()}]
            if not items and any(k in res for k in ("content", "text", "summary")):
                items = [res]
        elif isinstance(res, list):
            items = res
        else:
            text = self.extract_text(res).strip()
            return [{"text": text}] if text else []

        out: List[Dict[str, Any]] = []
        for item in items[: max(1, int(limit))]:
            if isinstance(item, str):
                out.append({"text": item})
                continue
            if isinstance(item, dict):
                text = (
                    item.get("content")
                    or item.get("text")
                    or item.get("memory")
                    or item.get("value")
                    or item.get("summary")
                    or ""
                )
                if isinstance(text, (dict, list)):
                    text = json.dumps(text, ensure_ascii=False)
                entry = {"text": str(text)} if text else {"text": json.dumps(item, ensure_ascii=False)}
                for k in ("id", "category", "tags", "score", "created_at", "timestamp"):
                    if k in item:
                        entry[k] = item[k]
                out.append(entry)
            else:
                out.append({"text": str(item)})
        return [x for x in out if x.get("text")]

    async def close(self) -> None:
        proc = self._proc
        self._proc = None
        self._initialized = False
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except Exception:
                pass
            self._reader_task = None
        if self._stderr_task:
            self._stderr_task.cancel()
            try:
                await self._stderr_task
            except Exception:
                pass
            self._stderr_task = None
        if proc and proc.returncode is None:
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                await asyncio.wait_for(proc.wait(), timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        for p in list(self._pending.values()):
            if not p.future.done():
                p.future.set_exception(Mem20Error("mem20 client closed"))
        self._pending.clear()


_mem20_client: Optional[Mem20Client] = None


def get_mem20_client() -> Mem20Client:
    global _mem20_client
    if _mem20_client is None:
        _mem20_client = Mem20Client()
    return _mem20_client
