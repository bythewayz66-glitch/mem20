from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from ..extract import extract_delta, extract_text
from .base import Attempt, ProviderResult, RouteContext, StreamEvent
from .common import (
    build_chat_payload,
    extract_error_message,
    is_chat_model_id,
    is_dead_local_error,
    iter_sse_json,
    post_chat,
    usage_from_payload,
)


class OpenAICompatProviderBase:
    name: str = "openai-compat"

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str = "",
        keyless: bool = True,
        default_model: Optional[str] = None,
        preferred_models: Optional[List[str]] = None,
        chat_path: str = "/chat/completions",
        models_path: str = "/models",
        extra_headers: Optional[Dict[str, str]] = None,
        local_runtime: bool = False,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = (api_key or "").strip()
        self.keyless = keyless if not self.api_key else False
        self.default_model = default_model
        self.preferred_models = preferred_models or ([] if not default_model else [default_model])
        self.chat_path = chat_path
        self.models_path = models_path
        self.extra_headers = extra_headers or {}
        self.local_runtime = local_runtime
        self._cached_models: Optional[List[str]] = None

    @property
    def chat_url(self) -> str:
        # If base_url already ends with /openai or chat endpoint path is absolute-ish
        if self.chat_path.startswith("http://") or self.chat_path.startswith("https://"):
            return self.chat_path
        if self.base_url.endswith("/openai") and self.chat_path == "/chat/completions":
            # Pollinations anon style: https://text.pollinations.ai/openai expects POST to that URL
            return self.base_url
        return f"{self.base_url}{self.chat_path if self.chat_path.startswith('/') else '/' + self.chat_path}"

    @property
    def models_url(self) -> str:
        if self.models_path.startswith("http://") or self.models_path.startswith("https://"):
            return self.models_path
        if self.base_url.endswith("/openai"):
            # Not a standard /v1/models endpoint; caller may override
            return self.base_url.replace("/openai", "/models")
        return f"{self.base_url}{self.models_path if self.models_path.startswith('/') else '/' + self.models_path}"

    def headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        h.update(self.extra_headers)
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _is_usable_model(self, model_id: str) -> bool:
        return is_chat_model_id(model_id, keyless=self.keyless and not self.api_key)

    async def _probe_models(self, client: httpx.AsyncClient, timeout: float) -> List[str]:
        try:
            resp = await client.get(self.models_url, headers=self.headers(), timeout=timeout)
            if resp.status_code >= 400:
                return []
            data = resp.json()
        except Exception:
            return []
        ids: List[str] = []
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            for item in data["data"]:
                if isinstance(item, dict):
                    mid = item.get("id") or item.get("name")
                    if isinstance(mid, str):
                        ids.append(mid)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    ids.append(item)
                elif isinstance(item, dict):
                    mid = item.get("id") or item.get("name")
                    if isinstance(mid, str):
                        ids.append(mid)
        # Filter: only chat-capable, no whisper/pro-tier in keyless learnings
        filtered = [m for m in ids if self._is_usable_model(m)]
        return filtered

    async def candidates(self, ctx: RouteContext, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        # Determine models to try for this request.
        requested = (ctx.requested_model or "").strip() or None
        models: List[str] = []

        # Prefer learned/probed models if available, else static preferences
        if self._cached_models is None:
            # Lazy probe with short timeout; if it fails, fall back to preferred/default
            probed = await self._probe_models(client, timeout=min(3.0, 5.0))
            self._cached_models = probed
        available = list(self._cached_models or [])

        if requested:
            # Agent/model string is a preference/hint, not a hard filter causing outage.
            # If requested model looks usable, try it first; always include fallbacks.
            if self._is_usable_model(requested):
                models.append(requested)
            # Also try exact requested even if filter would exclude in keyless probe learning?
            # "agent's model string was a hard filter, causing a total outage" -> don't fail if unavailable;
            # but we must not route chat at whisper/pro-tier inappropriately. If explicitly requested and
            # clearly non-chat (whisper/embed), better to deprioritize/skip; but keep fallbacks.
            elif requested not in models and not self.local_runtime:
                # allow explicit non-preferred request as a hint attempt but not as only option
                models.append(requested)

        # Add preferred/available chat models
        for m in (available or self.preferred_models):
            if m and m not in models and self._is_usable_model(m):
                models.append(m)
        if self.default_model and self.default_model not in models and self._is_usable_model(self.default_model):
            models.append(self.default_model)

        # Final safety: ensure at least one candidate if provider might work
        if not models and self.default_model:
            models = [self.default_model]
        elif not models and available:
            models = [available[0]]

        # De-dup preserving order
        seen = set()
        uniq: List[str] = []
        for m in models:
            if m in seen:
                continue
            seen.add(m)
            uniq.append(m)

        # Strict model means try only requested (or closest) without broad fallback to other models on same provider
        if ctx.strict_model and requested:
            uniq = [m for m in uniq if m == requested] or ([requested] if requested else uniq[:1])

        return [
            {
                "provider": self.name,
                "model": m,
                "url": self.chat_url,
                "headers": self.headers(),
                "keyless": self.keyless and not self.api_key,
                "base_url": self.base_url,
                "local_runtime": self.local_runtime,
            }
            for m in uniq
        ]

    async def complete(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> ProviderResult:
        model = candidate["model"]
        payload = build_chat_payload(
            model,
            ctx.messages,
            stream=False,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
        )
        resp = await post_chat(client, candidate["url"], candidate["headers"], payload, timeout=60.0)
        ct = resp.headers.get("content-type", "")
        data: Any
        if "application/json" in ct or resp.text.strip().startswith("{"):
            try:
                data = resp.json()
            except Exception:
                data = resp.text
        else:
            data = resp.text
        if resp.status_code >= 400:
            raise RuntimeError(extract_error_message(data, f"HTTP {resp.status_code}"))
        text = extract_text(data)
        if not text:
            # Some providers may return success with empty/odd payload
            raise RuntimeError("Empty response text")
        usage = usage_from_payload(data if isinstance(data, dict) else None)
        return ProviderResult(text=text, model=model, provider=self.name, usage=usage, raw=data)

    async def stream(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> AsyncIterator[StreamEvent]:
        model = candidate["model"]
        payload = build_chat_payload(
            model,
            ctx.messages,
            stream=True,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
        )
        async with client.stream("POST", candidate["url"], headers=candidate["headers"], json=payload, timeout=60.0) as resp:
            ct = resp.headers.get("content-type", "")
            if resp.status_code >= 400:
                body = await resp.aread()
                msg = body.decode("utf-8", errors="replace")
                try:
                    msg = extract_error_message(json.loads(msg), msg)
                except Exception:
                    msg = extract_error_message(msg, f"HTTP {resp.status_code}")
                yield StreamEvent("error", {"error": msg, "provider": self.name, "model": model})
                return

            # If provider returns non-SSE (JSON) despite stream request, synthesize stream events.
            if "text/event-stream" not in ct:
                body = await resp.aread()
                data: Any
                try:
                    data = json.loads(body.decode("utf-8", errors="replace"))
                except Exception:
                    data = body.decode("utf-8", errors="replace")
                text = extract_text(data) or ""
                usage = usage_from_payload(data if isinstance(data, dict) else None)
                if text:
                    yield StreamEvent("delta", {"delta": text, "provider": self.name, "model": model})
                yield StreamEvent("done", {"text": text, "provider": self.name, "model": model, "usage": usage, "raw_non_sse": True})
                return

            full = ""
            usage = None
            async for obj, raw in iter_sse_json(resp):
                if raw == "[DONE]":
                    break
                if not isinstance(obj, dict):
                    continue
                if obj.get("error"):
                    yield StreamEvent("error", {"error": extract_error_message(obj, "Stream error"), "provider": self.name, "model": model})
                    return
                u = usage_from_payload(obj)
                if u:
                    usage = u
                delta = extract_delta(obj)
                if delta:
                    full += delta
                    yield StreamEvent("delta", {"delta": delta, "provider": self.name, "model": model})
                # Some streams include full message in final chunk
                if not delta:
                    text = extract_text(obj)
                    if text and text != full:
                        # emit only missing suffix if possible
                        if text.startswith(full):
                            suffix = text[len(full):]
                            if suffix:
                                full = text
                                yield StreamEvent("delta", {"delta": suffix, "provider": self.name, "model": model})
                        elif not full:
                            full = text
                            yield StreamEvent("delta", {"delta": text, "provider": self.name, "model": model})
            yield StreamEvent("done", {"text": full, "provider": self.name, "model": model, "usage": usage})
