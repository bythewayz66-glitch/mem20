from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .base import Attempt, Provider, ProviderResult, RouteContext, StreamEvent
from .common import iter_sse_json


class TGIProvider(Provider):
    name = "tgi"

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
        self.default_model = default_model or "tgi"
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    async def candidates(self, ctx: RouteContext, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Discover available models from TGI server."""
        try:
            response = await client.get(f"{self.base_url}/info", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            model_id = data.get("model_id", "tgi-model")
            return [self._candidate(model_id)]
        except Exception:
            return [self._candidate(self.default_model)]

    def _candidate(self, model: str) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "model": model,
            "base_url": self.base_url,
            "api_key": "",
            "keyless": True,
            "supports_streaming": True,
            "supports_function_calling": False,  # TGI doesn't support function calling natively
        }

    async def complete(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> ProviderResult:
        started = time.perf_counter()
        model = candidate.get("model") or self.default_model

        # TGI uses a different API format
        payload = {
            "inputs": self._format_messages(ctx.messages),
            "parameters": {
                "temperature": ctx.temperature,
                "max_new_tokens": ctx.max_tokens,
                "return_full_text": False,
            },
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        attempt = Attempt(provider="tgi", model=candidate.get("model"), keyless=True)
        started_at = time.perf_counter()

        try:
            response = await self._post_with_retry(f"{self.base_url}/generate", payload, client)
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            attempt.finish("failed", error=str(e))
            return ProviderResult(
                text="",
                model=candidate.get("model") or self.default_model,
                provider="tgi",
                attempts=[attempt.finish("failed", error=str(e))],
            )

        text = data.get("generated_text", "")
        # TGI doesn't return token usage in the same way
        usage = {"total_tokens": len(text.split())}  # rough estimate

        attempt.finish("success", usage=usage)
        return ProviderResult(
            text=text,
            model=candidate.get("model") or self.default_model,
            provider="tgi",
            attempts=[attempt],
            usage=usage,
        )

    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for TGI chat template."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                formatted.append(f"<|system|>\n{content}")
            elif role == "user":
                formatted.append(f"<|user|>\n{content}")
            elif role == "assistant":
                formatted.append(f"<|assistant|>\n{content}")
            else:
                formatted.append(f"<|user|>\n{content}")
        formatted.append("<|assistant|>\n")
        return "\n".join(formatted)

    async def stream(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> AsyncIterator[StreamEvent]:
        model = candidate.get("model") or self.default_model

        payload = {
            "inputs": self._format_messages(ctx.messages),
            "parameters": {
                "temperature": ctx.temperature,
                "max_new_tokens": ctx.max_tokens,
                "return_full_text": False,
            },
            "stream": True,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        attempt = Attempt(provider="tgi", model=candidate.get("model"), keyless=True)

        async with client.stream(
            "POST",
            f"{self.base_url}/generate_stream",
            json=payload,
            headers=headers,
            timeout=60.0,
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                yield StreamEvent("error", {"error": f"TGI error: {error_text.decode()}"})
                return

            attempt.started_at = time.perf_counter()
            full_text = ""
            async for ev in iter_sse_json(response):
                if ev is None:
                    continue
                data, raw = ev
                if data is None:
                    continue

                if isinstance(data, dict):
                    # TGI streaming format
                    if "token" in data:
                        token = data["token"]
                        if token.get("text"):
                            text = token["text"]
                            full_text += text
                            yield StreamEvent("delta", {"delta": text, "provider": "tgi", "model": candidate.get("model")})

                    if data.get("details"):
                        details = data["details"]
                        if details.get("finish_reason"):
                            yield StreamEvent("done", {
                                "text": "",
                                "provider": "tgi",
                                "model": candidate.get("model"),
                                "usage": {"total_tokens": len(full_text.split())},
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