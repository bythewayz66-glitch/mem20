from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Attempt, Provider, ProviderResult, RouteContext, StreamEvent
from .common import (
    build_chat_payload,
    extract_error_message,
    is_chat_model_id,
    iter_sse_json,
    post_chat,
    usage_from_payload,
)


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        default_model: Optional[str] = None,
        timeout_s: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model or "llama3"
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    async def candidates(self, ctx: RouteContext, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Discover available models from Ollama."""
        try:
            response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except Exception:
            # Fallback to default model
            return [self._candidate(self.default_model)]

        models = data.get("models", [])
        candidates = []
        for model in models:
            name = model.get("name", "")
            if is_chat_model_id(name, keyless=True):
                candidates.append(self._candidate(name))
        return candidates or [self._candidate(self.default_model)]

    def _candidate(self, model: str) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "model": model,
            "base_url": self.base_url,
            "api_key": "",
            "keyless": True,
            "supports_streaming": True,
            "supports_function_calling": True,
        }

    async def complete(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> ProviderResult:
        started = time.perf_counter()
        model = candidate.get("model") or self.default_model

        payload = build_chat_payload(
            model=model,
            messages=ctx.messages,
            stream=False,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
        )

        headers = {"Content-Type": "application/json"}
        # Ollama doesn't require auth by default

        attempt = Attempt(provider="ollama", model=candidate.get("model"), keyless=True)
        started_at = time.perf_counter()

        try:
            response = await self._post_with_retry(f"{self.base_url}/api/chat", payload, client)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            attempt.finish("failed", error=str(e))
            return ProviderResult(
                text="",
                model=candidate.get("model") or self.default_model,
                provider="ollama",
                attempts=[attempt.finish("failed", error=str(e))],
            )

        message = data.get("message", {})
        text = message.get("content", "")
        usage = data.get("eval_count")  # Ollama returns eval_count for tokens

        attempt.finish("success", usage={"total_tokens": usage} if usage else None)
        return ProviderResult(
            text=text,
            model=candidate.get("model") or self.default_model,
            provider="ollama",
            attempts=[attempt],
            usage={"total_tokens": usage} if usage else None,
        )

    async def stream(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> AsyncIterator[StreamEvent]:
        model = candidate.get("model") or self.default_model

        payload = build_chat_payload(
            model=model,
            messages=ctx.messages,
            stream=True,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
        )

        headers = {"Content-Type": "application/json"}

        attempt = Attempt(provider="ollama", model=candidate.get("model"), keyless=True)

        async with client.stream("POST", f"{self.base_url}/api/chat", json=payload, headers=headers, timeout=60.0) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                yield StreamEvent("error", {"error": f"Ollama error: {error_text.decode()}"})
                return

            full_text = ""
            attempt.started_at = time.perf_counter()
            async for ev in iter_sse_json(response):
                if ev is None:
                    continue
                data, raw = ev
                if data is None:
                    continue
                
                if isinstance(data, dict):
                    # Check for done flag
                    if data.get("done"):
                        usage = data.get("eval_count")
                        yield StreamEvent("done", {
                            "text": "",
                            "provider": "ollama",
                            "model": candidate.get("model"),
                            "usage": {"total_tokens": usage} if usage else None,
                        })
                        return
                    
                    message = data.get("message", {})
                    delta = message.get("content", "")
                    if delta:
                        full_text += delta
                        yield StreamEvent("delta", {"delta": delta, "provider": "ollama", "model": candidate.get("model")})
                    elif "message" in data:
                        # Ollama sends messages incrementally
                        msg = data["message"]
                        content = msg.get("content", "")
                        if content:
                            full_text += content
                            yield StreamEvent("delta", {"delta": content, "provider": "ollama", "model": candidate.get("model")})

    async def _post_with_retry(self, url: str, payload: Dict[str, Any], client: httpx.AsyncClient) -> httpx.Response:
        last_error = None
        for attempt in range(3):
            try:
                response = await client.post(url, json=payload, timeout=60.0)
                if response.status_code < 500:
                    return response
            except Exception as e:
                pass
            await asyncio.sleep(0.5 * (attempt + 1))
        # Last attempt
        return await client.post(url, json=payload, timeout=60.0)