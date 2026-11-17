from __future__ import annotations

import time
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx

from .config import settings
from .providers.base import Attempt, ProviderResult, RouteContext, StreamEvent
from .providers.common import is_dead_local_error
from .providers.registry import build_providers
from .providers.health import get_health_monitor, score_providers
from .providers.cache import get_prompt_cache
from .providers.structured import StructuredOutputEnforcer
from .providers.functions import FunctionCallingShim
from .providers.templates import get_template_manager


class Router:
    def __init__(
        self,
        providers: Optional[List[Any]] = None,
        *,
        cfg=settings,
        enable_health_monitoring: bool = True,
        enable_caching: bool = True,
        enable_structured_output: bool = True,
        enable_function_calling: bool = True,
        enable_templates: bool = True,
    ) -> None:
        self.cfg = cfg
        self.providers = providers or build_providers(cfg)
        self.enable_health_monitoring = enable_health_monitoring
        self.enable_caching = enable_caching
        self.enable_structured_output = enable_structured_output
        self.enable_function_calling = enable_function_calling
        self.enable_templates = enable_templates

        # Initialize subsystems
        self._health_monitor = get_health_monitor() if enable_health_monitoring else None
        self._prompt_cache = get_prompt_cache() if enable_caching else None
        self._structured_enforcer = StructuredOutputEnforcer() if enable_structured_output else None
        self._function_shim = FunctionCallingShim() if enable_function_calling else None
        self._template_manager = get_template_manager() if enable_templates else None

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

    async def _apply_template(self, ctx: RouteContext, provider_id: str, model: str) -> RouteContext:
        """Apply model-specific prompt template."""
        if not self._template_manager:
            return ctx

        # Get system prompt from context
        system_prompt = None
        for msg in ctx.messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content")
                break

        # Format messages using template
        formatted_messages = self._template_manager.format_messages(
            provider_id=provider_id,
            model=model,
            messages=ctx.messages,
            system_prompt=system_prompt,
        )

        # Create new context with formatted messages
        return RouteContext(
            conversationKind=ctx.conversationKind,
            conversationName=ctx.conversationName,
            topic=ctx.topic,
            otherAgents=ctx.otherAgents,
            directed=ctx.directed,
            conversationId=ctx.conversationId,
            workspace=ctx.workspace,
            model=ctx.model,
            messages=formatted_messages,
            stream=ctx.stream,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
            agent=ctx.agent,
            conversation=ctx.conversation,
            metadata=ctx.metadata,
            strict_model=ctx.strict_model,
        )

    async def _check_cache(self, provider_id: str, model: str, messages: List[Dict[str, Any]]) -> Optional[ProviderResult]:
        """Check if response is cached."""
        if not self._prompt_cache:
            return None

        cached = await self._prompt_cache.get(provider_id, model, messages)
        if cached:
            return ProviderResult(
                text=cached.get("text", ""),
                model=model,
                provider=provider_id,
                attempts=[],
                usage=cached.get("usage"),
                cached=True,
            )
        return None

    async def _store_cache(self, provider_id: str, model: str, messages: List[Dict[str, Any]], result: ProviderResult) -> None:
        """Store response in cache."""
        if not self._prompt_cache:
            return

        response_dict = {
            "text": result.text,
            "usage": result.usage,
        }
        await self._prompt_cache.set(provider_id, model, messages, response_dict)

    async def _record_health(self, attempt: Attempt) -> None:
        """Record attempt for health monitoring."""
        if self._health_monitor:
            await self._health_monitor.record_attempt(attempt)

    def _get_routing_config(self) -> Dict[str, Any]:
        """Get routing configuration from settings/state."""
        # This would typically come from state store
        return {
            "strategy": getattr(self.cfg, "routing_strategy", "priority"),
            "cost_weight": getattr(self.cfg, "routing_cost_weight", 0.3),
            "latency_weight": getattr(self.cfg, "routing_latency_weight", 0.4),
            "quality_weight": getattr(self.cfg, "routing_quality_weight", 0.3),
            "prefer_keyless": getattr(self.cfg, "routing_prefer_keyless", True),
            "prefer_local": getattr(self.cfg, "routing_prefer_local", True),
        }

    async def _select_candidates(
        self,
        candidates: List[Tuple[Any, Dict[str, Any], Attempt]],
        ctx: RouteContext,
    ) -> List[Tuple[Any, Dict[str, Any], Attempt]]:
        """Select and order candidates based on routing strategy."""
        routing_config = self._get_routing_config()
        strategy = routing_config.get("strategy", "priority")

        if strategy == "priority":
            # Already in priority order
            return candidates

        # For other strategies, we need health scores
        if self._health_monitor:
            provider_ids = [cand[1].get("provider", "") for cand in candidates]
            scored = await score_providers(
                provider_ids,
                cost_weight=routing_config.get("cost_weight", 0.3),
                latency_weight=routing_config.get("latency_weight", 0.4),
                quality_weight=routing_config.get("quality_weight", 0.3),
            )

            # Create score map
            score_map = {s["provider_id"]: s["score"] for s in scored}

            if strategy == "cost_optimized":
                candidates.sort(key=lambda x: score_map.get(x[1].get("provider", ""), 0), reverse=True)
            elif strategy == "latency_optimized":
                candidates.sort(key=lambda x: score_map.get(x[1].get("provider", ""), 0), reverse=True)
            elif strategy == "quality_optimized":
                candidates.sort(key=lambda x: score_map.get(x[1].get("provider", ""), 0), reverse=True)
            elif strategy == "round_robin":
                # Could implement round-robin state tracking
                pass

        return candidates

    async def complete(self, ctx: RouteContext, client: Optional[httpx.AsyncClient] = None) -> ProviderResult:
        owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=httpx.Timeout(self.cfg.request_timeout_s, connect=self.cfg.connect_timeout_s))
        try:
            attempts: List[Attempt] = []
            attempts_used = 0

            # Gather and select candidates
            candidates = await self._gather_candidates(ctx, client)
            candidates = await self._select_candidates(candidates, ctx)

            # Check cache first
            if candidates and self.enable_caching:
                first_provider = candidates[0][1].get("provider", "")
                first_model = candidates[0][1].get("model", "")
                cached = await self._check_cache(first_provider, first_model, ctx.messages)
                if cached:
                    return cached

            last_error: Optional[str] = None

            for provider, cand, attempt in candidates:
                if cand.get("__skip__"):
                    attempt.finish("skipped")
                    attempts.append(attempt)
                    continue

                provider_id = cand.get("provider", getattr(provider, "name", "unknown"))
                model = cand.get("model", "")

                # Apply template if enabled
                if self.enable_templates:
                    ctx = await self._apply_template(ctx, provider_id, model)

                # Dead local runtime handling
                if cand.get("local_runtime"):
                    if not self._budget_allows(attempts_used, 0):
                        attempt.finish("skipped", reason="attempt_budget_exhausted")
                        attempts.append(attempt)
                        continue
                    try:
                        probe_url = cand.get("base_url", "").rstrip("/") + "/models"
                        await client.get(probe_url, timeout=self.cfg.dead_runtime_timeout_s)
                    except Exception as e:
                        if is_dead_local_error(e, cand.get("base_url", "")):
                            attempt.finish("skipped", reason="dead_local_runtime", error=str(e))
                            attempts.append(attempt)
                            continue
                        # Non-dead local issue: treat as failed attempt below

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

                    # Record health metrics
                    await self._record_health(attempt)

                    # Cache the result
                    await self._store_cache(provider_id, model, ctx.messages, result)

                    return result
                except Exception as e:
                    err = str(e)
                    last_error = err
                    reason = "dead_local_runtime" if cand.get("local_runtime") and is_dead_local_error(e, cand.get("base_url", "")) else "provider_error"
                    attempt.finish("failed", error=err, reason=reason)
                    await self._record_health(attempt)
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

            # Gather and select candidates
            candidates = await self._gather_candidates(ctx, client)
            candidates = await self._select_candidates(candidates, ctx)

            # Check cache first
            if candidates and self.enable_caching:
                first_provider = candidates[0][1].get("provider", "")
                first_model = candidates[0][1].get("model", "")
                cached = await self._check_cache(first_provider, first_model, ctx.messages)
                if cached:
                    yield StreamEvent("delta", {"delta": cached.text, "provider": first_provider, "model": first_model, "cached": True})
                    yield StreamEvent("done", {"text": cached.text, "provider": first_provider, "model": first_model, "usage": cached.usage, "attempts": [], "cached": True})
                    return

            last_error: Optional[str] = None

            for provider, cand, attempt in candidates:
                if cand.get("__skip__"):
                    attempt.finish("skipped")
                    attempts_meta.append(attempt.to_dict())
                    yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                    continue

                provider_id = cand.get("provider", getattr(provider, "name", "unknown"))
                model = cand.get("model", "")

                # Apply template if enabled
                if self.enable_templates:
                    ctx = await self._apply_template(ctx, provider_id, model)

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
                            done_data = {**ev.data, "attempts": list(attempts_meta)}
                            attempt.finish("success", usage=usage)
                            attempts_meta[-1] = attempt.to_dict()
                            yield StreamEvent("meta", {"attempt": attempt.to_dict(), "attempts": list(attempts_meta)})
                            if not (final_text and final_text.strip()):
                                error_msg = "empty_stream_response"
                                break
                            yield StreamEvent("done", {**done_data, "attempts": list(attempts_meta), "fallback_used": any(a.get("status") == "failed" for a in attempts_meta)})
                            # Record health and cache
                            await self._record_health(attempt)
                            await self._store_cache(provider_id, model, ctx.messages, ProviderResult(
                                text=final_text,
                                model=model,
                                provider=provider_id,
                                attempts=[a for a in attempts_meta],
                                usage=usage,
                            ))
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
                        yield StreamEvent("done", {"text": final_text, "provider": provider_id, "model": model, "usage": usage, "attempts": list(attempts_meta), "fallback_used": any(a.get("status") == "failed" for a in attempts_meta)})
                        await self._record_health(attempt)
                        await self._store_cache(provider_id, model, ctx.messages, ProviderResult(
                            text=final_text,
                            model=model,
                            provider=provider_id,
                            attempts=[a for a in attempts_meta],
                            usage=usage,
                        ))
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
                    await self._record_health(attempt)
                    continue

            yield StreamEvent("error", {"error": last_error or "No providers available", "attempts": attempts_meta})
        finally:
            if owns_client:
                await client.aclose()

    async def complete_structured(
        self,
        ctx: RouteContext,
        schema: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
    ) -> ProviderResult:
        """Complete with structured output enforcement."""
        if not self._structured_enforcer:
            raise RuntimeError("Structured output not enabled")

        result = await self.complete(ctx, client)
        if not result.text:
            raise RuntimeError("Empty response from provider")

        # Enforce structured output
        validated = self._structured_enforcer.enforce(result.text, schema)

        # Return new result with validated data
        return ProviderResult(
            text=json.dumps(validated),
            model=result.model,
            provider=result.provider,
            attempts=result.attempts,
            usage=result.usage,
            structured_data=validated,
        )

    async def complete_with_functions(
        self,
        ctx: RouteContext,
        functions: List[Dict[str, Any]],
        client: Optional[httpx.AsyncClient] = None,
        max_iterations: int = 5,
    ) -> ProviderResult:
        """Complete with function calling support."""
        if not self._function_shim:
            raise RuntimeError("Function calling not enabled")

        # Register functions
        for func in functions:
            self._function_shim.register_function(
                name=func["function"]["name"],
                description=func["function"]["description"],
                parameters=func["function"]["parameters"],
            )

        # Inject functions into context
        messages = self._function_shim.inject_functions_prompt(ctx.messages)
        ctx = RouteContext(
            conversationKind=ctx.conversationKind,
            conversationName=ctx.conversationName,
            topic=ctx.topic,
            otherAgents=ctx.otherAgents,
            directed=ctx.directed,
            conversationId=ctx.conversationId,
            workspace=ctx.workspace,
            model=ctx.model,
            messages=messages,
            stream=ctx.stream,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
            agent=ctx.agent,
            conversation=ctx.conversation,
            metadata=ctx.metadata,
            strict_model=ctx.strict_model,
        )

        # Complete with function calling loop
        iteration = 0
        all_function_results = []

        while iteration < max_iterations:
            result = await self.complete(ctx, client)
            if not result.text:
                break

            # Extract function calls
            calls = self._function_shim.extract_function_calls(result.text)
            if not calls:
                return result  # No function calls, return result

            # Execute function calls
            func_results = await self._function_shim.execute_function_calls(calls)
            all_function_results.extend(func_results)

            # Add function results to context for next iteration
            results_text = self._function_shim.format_function_results(func_results)
            ctx.messages.append({"role": "assistant", "content": result.text})
            ctx.messages.append({"role": "function", "content": results_text})

            iteration += 1

        # Return final result
        final_result = await self.complete(ctx, client)
        return final_result

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for all providers."""
        if not self._health_monitor:
            return {}
        # This would need to be async in real usage
        return {}

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._prompt_cache:
            return {}
        # This would need to be async in real usage
        return {}
