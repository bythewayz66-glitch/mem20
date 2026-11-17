from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol

import httpx


@dataclass
class Attempt:
    provider: str
    model: Optional[str] = None
    status: str = "started"  # started|success|failed|skipped
    latency_ms: Optional[int] = None
    reason: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    keyless: Optional[bool] = None
    started_at: float = field(default_factory=time.perf_counter)

    def finish(self, status: str, *, error: Optional[str] = None, reason: Optional[str] = None, usage: Optional[Dict[str, Any]] = None) -> "Attempt":
        self.status = status
        self.error = error
        self.reason = reason
        if usage is not None:
            self.usage = usage
        self.latency_ms = int((time.perf_counter() - self.started_at) * 1000)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "reason": self.reason,
            "error": self.error,
            "usage": self.usage,
            "keyless": self.keyless,
        }


@dataclass
class RouteContext:
    messages: List[Dict[str, Any]]
    requested_model: Optional[str] = None
    strict_model: bool = False
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    # Extended fields for compatibility with models.RouteContext
    conversationKind: Optional[str] = None
    conversationName: Optional[str] = None
    topic: Optional[str] = None
    otherAgents: Optional[List[Dict[str, str]]] = None
    directed: Optional[bool] = None
    conversationId: Optional[str] = None
    workspace: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    agent: Optional[Dict[str, Any]] = None
    conversation: Optional[Dict[str, Any]] = None


@dataclass
class ProviderResult:
    text: str
    model: str
    provider: str
    attempts: List[Attempt] = field(default_factory=list)
    usage: Optional[Dict[str, Any]] = None
    raw: Optional[Any] = None
    structured_data: Optional[Dict[str, Any]] = None
    cached: bool = False

    @property
    def fallback_used(self) -> bool:
        return any(a.status == "failed" for a in self.attempts) and any(a.status == "success" for a in self.attempts)


@dataclass
class StreamEvent:
    type: str  # meta|delta|done|error
    data: Dict[str, Any]


class Provider(Protocol):
    name: str

    async def candidates(self, ctx: RouteContext, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        ...

    async def complete(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> ProviderResult:
        ...

    async def stream(self, ctx: RouteContext, candidate: Dict[str, Any], client: httpx.AsyncClient) -> AsyncIterator[StreamEvent]:
        ...
