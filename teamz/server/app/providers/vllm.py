from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Attempt, Provider, ProviderResult, RouteContext, StreamEvent
from .common import iter_sse_json, post_chat


class VLLMProvider(Provider):
    name = "vllm"

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
        self.default_model = default_model or "meta-llama/Meta-Llama-3-8B-Instruct"
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    async def candidates(self, ctx: RouteContext, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Discover available models from vLLM server."""
        try:
            response = await client.get(f"{self.base_url}/v1/models", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            candidates = []
            for model in models:
                name = model.get("id", "")
                if name:
                    candidates.append(self._candidate(name))
            return candidates or [self._candidate(self.default_model)]
        except Exception:
            return [self._candidate(self.default_model)]

    def _candidate(self, model: str) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "model": model,
            "base_url": self.base_url,
            "api_key": "",
            "keyless": bool(not self.api_key),
            "supports_streaming": True,
            "supports_function_calling": True,
        }

    async def complete(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> ProviderResult:
        started = time.perf_counter()
        model = candidate.get("model") or self.default_model

        payload = {
            "model": model,
            "messages": ctx.messages,
            "stream": False,
            "temperature": ctx.temperature,
            "max_tokens": ctx.max_tokens,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        attempt = Attempt(provider="vllm", model=candidate.get("model"), keyless=not bool(self.api_key))
        started_at = time.perf_counter()

        try:
            response = await self._post_with_retry(f"{self.base_url}/v1/chat/completions", payload, client)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            attempt.finish("failed", error=str(e))
            return ProviderResult(
                text="",
                model=candidate.get("model") or self.default_model,
                provider="vllm",
                attempts=[attempt.finish("failed", error=str(e))],
            )

        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = data.get("usage")

        attempt.finish("success", usage=usage)
        return ProviderResult(
            text=text,
            model=candidate.get("model") or self.default_model,
            provider="vllm",
            attempts=[attempt],
            usage=usage,
        )

    async def stream(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> AsyncIterator[StreamEvent]:
        model = candidate.get("model") or self.default_model

        payload = {
            "model": model,
            "messages": ctx.messages,
            "stream": True,
            "temperature": ctx.temperature,
            "max_tokens": ctx.max_tokens,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        attempt = Attempt(provider="vllm", model=candidate.get("model"), keyless=not bool(self.api_key))

        async with client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60.0,
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                yield StreamEvent("error", {"error": f"vLLM error: {error_text.decode()}"})
                return

            attempt.started_at = time.perf_counter()
            async for ev in iter_sse_json(response):
                if ev is None:
                    continue
                data, raw = ev
                if data is None:
                    continue

                if isinstance(data, dict):
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield StreamEvent("delta", {"delta": content, "provider": "vllm", "model": candidate.get("model")})

                    if data.get("choices") and choices[0].get("finish_reason"):
                        usage = data.get("usage")
                        yield StreamEvent("done", {
                            "text": "",
                            "provider": "vllm",
                            "model": candidate.get("model"),
                            "usage": usage,
                        })
                        return

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
        return await client.post(url, json=payload, timeout=60.0)