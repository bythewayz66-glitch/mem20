"""Fleet integration for teamz: namespaces, kanban, A2A, rules enforcement."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .config import settings


@dataclass
class FleetNamespace:
    """Isolated mem20 namespace for a teamz agent."""
    agent_name: str
    store_path: str
    created_at: str
    status: str = "active"
    agent_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


@dataclass
class KanbanCard:
    """Kanban card synced from teamz goal/channel."""
    id: str
    title: str
    column: str  # backlog, todo, in_progress, review, done
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    goal_text: Optional[str] = None
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2APeer:
    """A2A peer agent configuration."""
    name: str
    url: str
    capabilities: List[str] = field(default_factory=list)
    health_check_url: Optional[str] = None
    last_seen: Optional[str] = None
    status: str = "unknown"


@dataclass
class FleetDecision:
    """A decision that must be persisted per fleetwide rules."""
    id: str
    agent_name: str
    conversation_id: Optional[str]
    decision: str
    rationale: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tags: List[str] = field(default_factory=list)
    outcome: Optional[str] = None


class FleetClient:
    """Client for fleet-wide services (gateway, kanban, A2A)."""

    def __init__(self, gateway_url: str = None):
        self.gateway_url = gateway_url or settings.fleet_gateway_url
        self._client: Optional[httpx.AsyncClient] = None
        self._namespace_cache: Dict[str, FleetNamespace] = {}
        self._kanban_cache: Dict[str, KanbanCard] = {}
        self._a2a_peers: Dict[str, A2APeer] = {}
        self._decisions: List[FleetDecision] = []

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ========================================================================
    # Namespace Management (Step 6: fleetwide_mem20 Phase 3)
    # ========================================================================

    async def create_namespace(self, agent_name: str) -> FleetNamespace:
        """Create isolated mem20 namespace for a teamz agent."""
        client = await self._get_client()
        try:
            resp = await client.post(
                f"{self.gateway_url}/namespace/create",
                json={"agent_name": agent_name}
            )
            resp.raise_for_status()
            data = resp.json()
            namespace = FleetNamespace(
                agent_name=data["agent_name"],
                store_path=data["store_path"],
                created_at=data["created_at"],
                status=data.get("status", "active"),
            )
            self._namespace_cache[agent_name] = namespace
            return namespace
        except Exception as e:
            # Fallback: create local namespace tracking
            namespace = FleetNamespace(
                agent_name=agent_name,
                store_path=f"~/.mem20/fleet/{agent_name}",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._namespace_cache[agent_name] = namespace
            return namespace

    async def get_namespace(self, agent_name: str) -> FleetNamespace:
        """Get namespace for agent, creating if needed."""
        if agent_name in self._namespace_cache:
            return self._namespace_cache[agent_name]
        client = await self._get_client()
        try:
            resp = await client.get(f"{self.gateway_url}/namespace/get/{agent_name}")
            if resp.status_code == 200:
                data = resp.json()
                namespace = FleetNamespace(
                    agent_name=data["agent_name"],
                    store_path=data["store_path"],
                    created_at=data["created_at"],
                    status=data.get("status", "active"),
                )
                self._namespace_cache[agent_name] = namespace
                return namespace
        except Exception:
            pass
        return await self.create_namespace(agent_name)

    async def list_namespaces(self) -> List[FleetNamespace]:
        """List all agent namespaces."""
        client = await self._get_client()
        try:
            resp = await client.get(f"{self.gateway_url}/namespace/list")
            resp.raise_for_status()
            # Gateway returns text output, not JSON
            return list(self._namespace_cache.values())
        except Exception:
            return list(self._namespace_cache.values())

    def get_store_path(self, agent_name: str) -> str:
        """Get the MEM20_STORE_PATH for an agent."""
        ns = self._namespace_cache.get(agent_name)
        if ns:
            return ns.store_path
        return f"~/.mem20/fleet/{agent_name}"

    # ========================================================================
    # Kanban Integration (Step 7)
    # ========================================================================

    async def sync_goal_to_kanban(self, conversation_id: str, goal_text: str, agent_id: str = None) -> KanbanCard:
        """Sync a teamz goal to kanban as a card."""
        card = KanbanCard(
            id=f"goal-{conversation_id}",
            title=goal_text[:100],
            column="backlog",
            conversation_id=conversation_id,
            agent_id=agent_id,
            goal_text=goal_text,
            tags=["teamz", "goal", f"conv:{conversation_id}"],
        )
        self._kanban_cache[card.id] = card
        # In production, would POST to kanban MCP
        return card

    async def update_kanban_card(self, card_id: str, column: str = None, **updates) -> Optional[KanbanCard]:
        """Update kanban card (move column, update fields)."""
        card = self._kanban_cache.get(card_id)
        if not card:
            return None
        if column:
            card.column = column
        for key, value in updates.items():
            if hasattr(card, key):
                setattr(card, key, value)
        card.updated_at = datetime.now(timezone.utc).isoformat()
        return card

    async def get_kanban_cards(self, conversation_id: str = None) -> List[KanbanCard]:
        """Get all kanban cards, optionally filtered by conversation."""
        cards = list(self._kanban_cache.values())
        if conversation_id:
            cards = [c for c in cards if c.conversation_id == conversation_id]
        return cards

    # ========================================================================
    # A2A Setup (Step 8)
    # ========================================================================

    def register_a2a_peer(self, peer: A2APeer) -> None:
        """Register an A2A peer agent."""
        self._a2a_peers[peer.name] = peer

    async def health_check_a2a_peers(self) -> Dict[str, str]:
        """Health check all A2A peers."""
        results = {}
        client = await self._get_client()
        for name, peer in self._a2a_peers.items():
            try:
                url = peer.health_check_url or f"{peer.url}/health"
                resp = await client.get(url, timeout=5.0)
                peer.status = "healthy" if resp.status_code == 200 else "unhealthy"
                peer.last_seen = datetime.now(timezone.utc).isoformat()
            except Exception:
                peer.status = "unreachable"
            results[name] = peer.status
        return results

    def get_a2a_peers(self) -> List[A2APeer]:
        """Get all registered A2A peers."""
        return list(self._a2a_peers.values())

    # ========================================================================
    # Fleetwide Rules Enforcement (Step 9)
    # ========================================================================

    async def record_decision(
        self,
        agent_name: str,
        decision: str,
        rationale: str,
        conversation_id: str = None,
        tags: List[str] = None,
    ) -> FleetDecision:
        """Record a decision per fleetwide decision persistence rule."""
        fleet_decision = FleetDecision(
            id=f"dec-{uuid.uuid4().hex[:12]}",
            agent_name=agent_name,
            conversation_id=conversation_id,
            decision=decision,
            rationale=rationale,
            tags=tags or ["teamz", "decision"],
        )
        self._decisions.append(fleet_decision)
        # Also store in mem20 for persistence
        if settings.mem20_enabled:
            try:
                from .mem20 import get_mem20_client
                client = get_mem20_client()
                await client.memory_store(
                    f"FLEET DECISION [{fleet_decision.id}]: {decision} | Rationale: {rationale}",
                    category="fleet",
                    tags=["fleet", "decision", f"agent:{agent_name}"] + (tags or []),
                )
            except Exception:
                pass
        return fleet_decision

    async def review_fail_logs(self, agent_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Review failure logs per fleetwide fail log review rule."""
        from .mem20 import get_mem20_client
        client = get_mem20_client()
        try:
            query = "fleet failure error"
            if agent_name:
                query = f"{agent_name} {query}"
            items = await client.recall_texts(query, limit=limit)
            return items
        except Exception:
            return []

    def get_decisions(self, agent_name: str = None) -> List[FleetDecision]:
        """Get recorded decisions, optionally filtered by agent."""
        decisions = self._decisions
        if agent_name:
            decisions = [d for d in decisions if d.agent_name == agent_name]
        return decisions


# Global fleet client instance
_fleet_client: Optional[FleetClient] = None


def get_fleet_client() -> FleetClient:
    global _fleet_client
    if _fleet_client is None:
        _fleet_client = FleetClient()
    return _fleet_client


async def init_fleet_integration() -> FleetClient:
    """Initialize fleet integration on startup."""
    client = get_fleet_client()
    
    if settings.fleet_enabled:
        # Create namespace for this orchestrator
        await client.create_namespace(settings.fleet_agent_name)
        
        # Register known A2A peers from config
        if settings.a2a_peer_config:
            try:
                peers = json.loads(settings.a2a_peer_config)
                for peer_data in peers:
                    client.register_a2a_peer(A2APeer(**peer_data))
            except Exception:
                pass
    
    return client


async def shutdown_fleet_integration():
    """Shutdown fleet integration."""
    global _fleet_client
    if _fleet_client:
        await _fleet_client.close()
        _fleet_client = None