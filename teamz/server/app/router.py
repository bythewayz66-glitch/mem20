from __future__ import annotations

import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx

from .config import settings
from .providers.base import Attempt, ProviderResult, RouteContext, StreamEvent
from .providers.common import is_dead_local_error
from .providers.llm7 import LLM7Provider
from .providers.local_runtime import LocalOpenAIProvider
from .providers.ovhcloud import OVHCloudProvider
from .providers.pollinations import PollinationsProvider


def build_providers(cfg=settings) -> List[Any]:
    providers: List[Any] = []
    # Keyless-first order: providers that can work without keys come early
    providers.append(PollinationsProvider(
        base_url=cfg.pollinations_base_url,
        keyed_base_url=cfg.pollinations_keyed_base_url,
        api_key=cfg.pollinations_api_key,
    ))
    providers.append(LLM7Provider(base_url=cfg.llm7_base_url, api_key=cfg.llm7_api_key))
    providers.append(OVHCloudProvider(base_url=cfg.ovh_base_url, api_key=cfg.ovh_api_key))
    for i, url in enumerate(cfg.local_openai_base_urls, start=1):
        if url:
            providers.append(LocalOpenAIProvider(url, index=i))
    # If keyless_first, ensure providers with keys are not deprioritized incorrectly?
    # "Keyless-first" means prefer keyless-capable paths/providers when available.
    if cfg.keyless_first:
        providers.sort(key=lambda p: 0 if getattr(p, "keyless", False) and not getattr(p, "api_key", "") else 1)
    return providers


class Router:
    def __init__(self, providers: Optional[List[Any]] = None, *, cfg=settings) -> None:
        self.cfg = cfg
        self.providers = providers or build_providers(cfg)

    async def _gather_candidates(self, ctx: RouteContext, client: httpx.AsyncClient) -> List[Tuple[Any, Dict[str, Any], Attempt]]:
        out: List[Tuple[Any, Dict[str, Any], Attempt]] = []
        for provider in self.providers:
            try:
                cands = await provider.candidates(ctx, client)
            except Exception as e:
                # Candidate discovery failure should not kill routing; record as skipped and continue
                a = Attempt(provider=getattr(provider, "name", "unknown"), status="skipped", reason="candidate_discovery_failed", error=str(e))
                out.append((provider, {"__skip__": True}, a))
                continue
            for cand in cands:
                a = Attempt(provider=cand.get("provider", getattr(provider, "name", "unknown")), model=cand.get("model"), keyless=cand.get("keyless"))
                out.append((provider, cand, a))
        return out

    def _budget_allows(self, attempts_used: int, dead_skips: int) -> bool:
        # attempts_used counts real network attempts/failures that consume budget.
        # dead local runtime skips do not consume the whole/real attempt budget.
        return attempts_used < max(1, int(self.cfg.max_attempts))

    async def complete(self, ctx: RouteContext, client: Optional[httpx.AsyncClient] = None) -> ProviderResult:
        owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=httpx.Timeout(self.cfg.request_timeout_s, connect=self.cfg.connect_timeout_s))
        try:
            attempts: List[Attempt] = []
            attempts_used = 0
            candidates = await self._gather_candidates(ctx, client)
            last_error: Optional[str] = None

            for provider, cand, attempt in candidates:
                if cand.get("__skip__"):
                    attempt.finish("skipped")
                    attempts.append(attempt)
                    continue

                # Dead local runtime handling: probe quickly; if dead, skip without consuming main budget
                if cand.get("local_runtime"):
                    if not self._budget_allows(attempts_used, 0):
                        attempt.finish("skipped", reason="attempt_budget_exhausted")
                        attempts.append(attempt)
                        continue
                    try:
                        # Fast liveness probe: try models endpoint or a very short request timeout
                        probe_url = cand.get("base_url", "").rstrip("/") + "/models"
                        await client.get(probe_url, timeout=self.cfg.dead_runtime_timeout_s)
                    except Exception as e:
                        if is_dead_local_error(e, cand.get("base_url", "")):
                            attempt.finish("skipped", reason="dead_local_runtime", error=str(e))
                            attempts.append(attempt)
                            continue  # do not consume main attempt budget
                        # Non-dead local issue: treat as failed attempt below
                    # fall through to real attempt (counts toward budget)

                if not self._budget_allows(attempts_used, 0):
                    attempt.finish("skipped", reason="attempt_budget_exhausted")
                    attempts.append(attempt)
                    continue

                attempts.append(attempt)
                attempts_used += 1
                try:
                    result = await provider.complete(ctx, cand, client)
                    attempt.finish("success", usage=result.usage)
                    result.attempts = [a for a in attempts]
                    return result
                except Exception as e:
                    err = str(e)
                    last_error = err
                    # If this was a local runtime that turned out dead/unreachable, don't let it starve others?
                    # It already consumed one attempt slot; mark clearly.
                    reason = "dead_local_runtime" if cand.get("local_runtime") and is_dead_local_error(e, cand.get("base_url", "")) else "provider_error"
                    attempt.finish("failed", error=err, reason=reason)
                    continue

            raise RuntimeError(last_error or "No providers available")
        finally:
            if owns_client:
                await client.aclose()

    async def stream(self, ctx: RouteContext, client: Optional[httpx.AsyncClient] = None) -> AsyncIterator[StreamEvent]:
        owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=httpx.Timeout(self.cfg.request_timeout_s, connect=self.cfg.connect_timeout_s))
        attempts_meta: List[Dict[str, Any]] = []
        try:
            attempts_used = 0
            candidates = await self._gather_candidates(ctx, client)
            last_error: Optional[str] = None

            for provider, cand, attempt in candidates:
                if cand.get("__skip__"):
                    attempt.finish("skipped")
                    attempts_meta.append(attempt.to_dict())
                    yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                    continue

                if cand.get("local_runtime"):
                    if not self._budget_allows(attempts_used, 0):
                        attempt.finish("skipped", reason="attempt_budget_exhausted")
                        attempts_meta.append(attempt.to_dict())
                        yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                        continue
                    try:
                        probe_url = cand.get("base_url", "").rstrip("/") + "/models"
                        await client.get(probe_url, timeout=self.cfg.dead_runtime_timeout_s)
                    except Exception as e:
                        if is_dead_local_error(e, cand.get("base_url", "")):
                            attempt.finish("skipped", reason="dead_local_runtime", error=str(e))
                            attempts_meta.append(attempt.to_dict())
                            yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                            continue

                if not self._budget_allows(attempts_used, 0):
                    attempt.finish("skipped", reason="attempt_budget_exhausted")
                    attempts_meta.append(attempt.to_dict())
                    yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                    continue

                attempts_meta.append(attempt.to_dict())
                yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                attempts_used += 1

                got_delta = False
                got_done = False
                final_text = ""
                usage = None
                error_msg: Optional[str] = None
                try:
                    async for ev in provider.stream(ctx, cand, client):
                        if ev.type == "delta":
                            got_delta = True
                            delta = ev.data.get("delta") or ""
                            if delta:
                                final_text += delta
                            yield StreamEvent("delta", {**ev.data, "attempts": list(attempts_meta)})
                        elif ev.type == "done":
                            got_done = True
                            final_text = ev.data.get("text") or final_text
                            usage = ev.data.get("usage") or usage
                            # Do not yield done yet; mark success after loop
                            # but preserve provider info
                            done_data = {**ev.data, "attempts": list(attempts_meta)}
                            attempt.finish("success", usage=usage)
                            attempts_meta[-1] = attempt.to_dict()
                            yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                            # Ensure non-empty answer invariant for successful streams
                            if not (final_text and final_text.strip()):
                                error_msg = "empty_stream_response"
                                break
                            yield StreamEvent("done", {**done_data, "attempts": list(attempts_meta), "fallback_used": any(a.get("status") == "failed" for a in attempts_meta)})
                            return
                        elif ev.type == "error":
                            error_msg = str(ev.data.get("error") or "provider stream error")
                            break
                        else:
                            yield ev
                    # Stream ended without explicit done
                    if error_msg:
                        raise RuntimeError(error_msg)
                    if got_delta or final_text.strip():
                        attempt.finish("success", usage=usage)
                        attempts_meta[-1] = attempt.to_dict()
                        yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                        yield StreamEvent("done", {"text": final_text, "provider": cand.get("provider"), "model": cand.get("model"), "usage": usage, "attempts": list(attempts_meta), "fallback_used": any(a.get("status") == "failed" for a in attempts_meta)})
                        return
                    # No content produced at all -> treat as failure and try next provider
                    raise RuntimeError("empty_stream_response")
                except Exception as e:
                    err = str(e)
                    last_error = err
                    reason = "dead_local_runtime" if cand.get("local_runtime") and is_dead_local_error(e, cand.get("base_url", "")) else ("empty_stream" if err == "empty_stream_response" else "provider_error")
                    attempt.finish("failed", error=err, reason=reason)
                    attempts_meta[-1] = attempt.to_dict()
                    yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                    continue

            yield StreamEvent("error", {"error": last_error or "No providers available", "attempts": attempts_meta})
        finally:
            if owns_client:
                await client.aclose()
