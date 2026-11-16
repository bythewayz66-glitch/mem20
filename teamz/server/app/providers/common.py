from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx

from ..extract import extract_delta, extract_text


CHAT_EXCLUDE_RE = re.compile(
    r"whisper|transcri|speech|tts|embed|embedding|rerank|moderation|image|vision-only|dall|flux|stable|audio|realtime-preview-transcribe",
    re.IGNORECASE,
)
PRO_TIER_RE = re.compile(r"\bpro\b|preview-pro|gpt-5\.4-pro|claude-opus|o1-pro", re.IGNORECASE)


def is_chat_model_id(model_id: str, *, keyless: bool = False) -> bool:
    if not model_id:
        return False
    mid = model_id.strip()
    if not mid:
        return False
    if CHAT_EXCLUDE_RE.search(mid):
        return False
    # Pro-tier models must not be learned/routed in keyless contexts (commit bug: probe learned pro-tier models)
    if keyless and PRO_TIER_RE.search(mid):
        return False
    return True


def normalize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role") or "user"
        content = m.get("content", "")
        # Ensure JSON-serializable content for OpenAI-compatible APIs
        if content is None:
            content = ""
        msg: Dict[str, Any] = {"role": role, "content": content}
        if m.get("name"):
            msg["name"] = m["name"]
        out.append(msg)
    return out


def build_chat_payload(
    model: str,
    messages: List[Dict[str, Any]],
    *,
    stream: bool,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": normalize_messages(messages),
        "stream": bool(stream),
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if extra:
        payload.update(extra)
    return payload


def is_dead_local_error(exc: Exception, base_url: str) -> bool:
    url = (base_url or "").lower()
    local = "localhost" in url or "127.0.0.1" in url or url.startswith("http://0.0.0.0")
    if not local:
        return False
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.TimeoutException)):
        return True
    msg = str(exc).lower()
    return "connection refused" in msg or "all connection attempts failed" in msg or "timed out" in msg


def usage_from_payload(payload: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return None
    u = payload.get("usage")
    if not isinstance(u, dict):
        return None
    out: Dict[str, Any] = {}
    for k in ("prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"):
        v = u.get(k)
        if isinstance(v, (int, float)):
            out[k] = int(v)
    # Normalize common aliases
    if "prompt_tokens" not in out and "input_tokens" in out:
        out["prompt_tokens"] = out["input_tokens"]
    if "completion_tokens" not in out and "output_tokens" in out:
        out["completion_tokens"] = out["output_tokens"]
    if out.get("total_tokens") is None and out.get("prompt_tokens") is not None and out.get("completion_tokens") is not None:
        out["total_tokens"] = int(out["prompt_tokens"]) + int(out["completion_tokens"])
    return out or None


async def post_chat(
    client: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float,
) -> httpx.Response:
    return await client.post(url, headers=headers, json=payload, timeout=timeout)


async def iter_sse_json(response: httpx.Response) -> AsyncIterator[Tuple[Optional[Dict[str, Any]], Optional[str]]]:
    """Yield (json_obj_or_none, raw_data_str_or_none) for SSE data events."""
    buffer = ""
    async for chunk in response.aiter_text():
        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip("\r")
            if not line or line.startswith(":"):
                continue
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            if data == "[DONE]":
                yield None, "[DONE]"
                return
            try:
                yield json.loads(data), data
            except Exception:
                yield None, data
    # flush remainder
    if buffer.strip().startswith("data:"):
        data = buffer.strip()[5:].strip()
        if data == "[DONE]":
            yield None, "[DONE]"
        elif data:
            try:
                yield json.loads(data), data
            except Exception:
                yield None, data


def extract_error_message(payload: Any, fallback: str = "Request failed") -> str:
    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            msg = err.get("message") or err.get("detail") or err.get("error")
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
        if isinstance(err, str) and err.strip():
            return err.strip()
        msg = payload.get("message") or payload.get("detail")
        if isinstance(msg, str) and msg.strip():
            return msg.strip()
    if isinstance(payload, str) and payload.strip():
        return payload.strip()[:300]
    return fallback
