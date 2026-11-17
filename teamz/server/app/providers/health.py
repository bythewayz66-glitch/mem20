"""Provider health monitoring and scoring system."""

from __future__ import annotations

import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import defaultdict

from .base import Attempt


@dataclass
class ProviderMetrics:
    """Metrics for a single provider."""
    provider_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: float = 0.0
    last_error: Optional[str] = None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0
    cost_per_1k_tokens: float = 0.0
    error_rate: float = 0.0
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0

    def record_success(self, latency_ms: float, prompt_tokens: int = 0, completion_tokens: int = 0, cost_usd: float = 0.0) -> None:
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
        self.last_latency_ms = latency_ms
        self.consecutive_failures = 0
        self.consecutive_successes += 1
        self.last_check = time.time()
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost_usd += cost_usd
        self._recalculate()

    def record_failure(self, error: str, latency_ms: float = 0.0) -> None:
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.total_latency_ms += latency_ms
        self.last_latency_ms = latency_ms
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_check = time.time()
        self.last_error = error
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalculate derived metrics."""
        if self.total_requests > 0:
            self.error_rate = self.failed_requests / self.total_requests
            self.success_rate = self.successful_requests / self.total_requests
            self.avg_latency_ms = self.total_latency_ms / self.total_requests
        else:
            self.error_rate = 0.0
            self.success_rate = 1.0
            self.avg_latency_ms = 0.0

        total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        if total_tokens > 0:
            self.cost_per_1k_tokens = (self.total_cost_usd / total_tokens) * 1000
        else:
            self.cost_per_1k_tokens = 0.0

    @property
    def status(self) -> str:
        """Determine health status based on metrics."""
        if self.total_requests == 0:
            return "unknown"
        if self.error_rate >= 0.5 or self.consecutive_failures >= 5:
            return "unhealthy"
        if self.error_rate >= 0.2 or self.consecutive_failures >= 2 or self.avg_latency_ms > 30000:
            return "degraded"
        return "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider_id": self.provider_id,
            "status": self.status,
            "latency_ms": self.last_latency_ms,
            "error_rate": self.error_rate,
            "success_rate": self.success_rate,
            "last_check": int(self.last_check * 1000) if self.last_check else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_latency_ms": self.avg_latency_ms,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
        }


class HealthMonitor:
    """Monitor and score provider health."""

    def __init__(self) -> None:
        self._metrics: Dict[str, ProviderMetrics] = {}
        self._lock = asyncio.Lock()

    async def record_attempt(self, attempt: Attempt) -> None:
        """Record an attempt result."""
        async with self._lock:
            provider_id = attempt.provider
            if provider_id not in self._metrics:
                self._metrics[provider_id] = ProviderMetrics(provider_id=provider_id)

            metrics = self._metrics[provider_id]

            if attempt.status == "success":
                usage = attempt.usage or {}
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

                # Estimate cost if not provided
                cost_usd = usage.get("cost_usd", 0.0)

                metrics.record_success(
                    latency_ms=attempt.latency_ms or 0.0,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost_usd=cost_usd,
                )
            elif attempt.status == "failed":
                metrics.record_failure(
                    error=attempt.error or "Unknown error",
                    latency_ms=attempt.latency_ms or 0.0,
                )

    async def get_health(self, provider_id: str) -> Optional[ProviderMetrics]:
        """Get health metrics for a provider."""
        async with self._lock:
            return self._metrics.get(provider_id)

    async def get_all_health(self) -> Dict[str, ProviderMetrics]:
        """Get health metrics for all providers."""
        async with self._lock:
            return dict(self._metrics)

    async def get_healthy_providers(self) -> List[str]:
        """Get list of healthy provider IDs."""
        async with self._lock:
            return [
                pid for pid, metrics in self._metrics.items()
                if metrics.status == "healthy"
            ]

    async def get_degraded_providers(self) -> List[str]:
        """Get list of degraded provider IDs."""
        async with self._lock:
            return [
                pid for pid, metrics in self._metrics.items()
                if metrics.status == "degraded"
            ]

    async def get_unhealthy_providers(self) -> List[str]:
        """Get list of unhealthy provider IDs."""
        async with self._lock:
            return [
                pid for pid, metrics in self._metrics.items()
                if metrics.status == "unhealthy"
            ]


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


async def score_providers(providers: List[str], *, cost_weight: float = 0.3, latency_weight: float = 0.4, quality_weight: float = 0.3) -> List[Dict[str, Any]]:
    """Score providers based on health metrics for routing decisions."""
    monitor = get_health_monitor()
    all_health = await monitor.get_all_health()

    scored = []
    for provider_id in providers:
        metrics = all_health.get(provider_id)
        if metrics is None:
            # No metrics yet - neutral score
            scored.append({
                "provider_id": provider_id,
                "score": 0.5,
                "status": "unknown",
                "latency_score": 0.5,
                "cost_score": 0.5,
                "quality_score": 0.5,
            })
            continue

        # Latency score (lower is better, normalize to 0-1)
        latency_score = 1.0 - min(metrics.avg_latency_ms / 30000.0, 1.0) if metrics.avg_latency_ms > 0 else 0.5

        # Cost score (lower is better, normalize to 0-1)
        cost_score = 1.0 - min(metrics.cost_per_1k_tokens / 10.0, 1.0) if metrics.cost_per_1k_tokens > 0 else 0.5

        # Quality score (based on success rate)
        quality_score = metrics.success_rate

        # Weighted composite score
        composite = (
            cost_weight * cost_score +
            latency_weight * latency_score +
            quality_weight * quality_score
        )

        scored.append({
            "provider_id": provider_id,
            "score": composite,
            "status": metrics.status,
            "latency_score": latency_score,
            "cost_score": cost_score,
            "quality_score": quality_score,
            "avg_latency_ms": metrics.avg_latency_ms,
            "cost_per_1k_tokens": metrics.cost_per_1k_tokens,
            "error_rate": metrics.error_rate,
            "success_rate": metrics.success_rate,
        })

    # Sort by score descending (best first)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored