"""Episodic memory: agent recalls 'how I solved X last time'."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .vector import VectorMemory, VectorMemoryConfig, get_vector_memory
from ..config import settings


class EpisodicMemoryConfig(BaseModel):
    """Configuration for episodic memory."""
    vector_config: Optional[VectorMemoryConfig] = None
    max_episodes_per_agent: int = 1000
    auto_summarize: bool = True
    min_importance_to_keep: float = 0.3


@dataclass
class Episode:
    """An episodic memory entry."""
    id: str
    agent_id: str
    task_description: str
    context: Dict[str, Any]  # What was the situation
    actions: List[Dict[str, Any]]  # What did the agent do
    outcome: str  # What happened
    success: bool
    lessons_learned: List[str]
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def to_search_text(self) -> str:
        """Convert to searchable text for vector embedding."""
        parts = [
            f"Task: {self.task_description}",
            f"Context: {json.dumps(self.context)}",
            f"Actions: {json.dumps(self.actions)}",
            f"Outcome: {self.outcome}",
            f"Lessons: {', '.join(self.lessons_learned)}",
        ]
        return "\n".join(parts)

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_description": self.task_description,
            "success": self.success,
            "tags": self.tags,
            "importance": self.importance,
            "created_at": self.created_at,
            "type": "episode",
        }


class EpisodicMemory:
    """Episodic memory for agents to recall past experiences."""

    def __init__(self, config: Optional[EpisodicMemoryConfig] = None) -> None:
        self.config = config or EpisodicMemoryConfig()
        self._vector_memory: Optional[VectorMemory] = None
        self._episodes: Dict[str, Episode] = {}
        self._agent_index: Dict[str, List[str]] = {}  # agent_id -> episode_ids

    async def initialize(self) -> None:
        if self._vector_memory is None:
            self._vector_memory = get_vector_memory(self.config.vector_config)
            await self._vector_memory.initialize()

    async def close(self) -> None:
        if self._vector_memory:
            await self._vector_memory.close()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text. In production, use an embedding model."""
        # Placeholder - in real implementation, call embedding API
        # For now, return a deterministic hash-based vector
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hex_digest = hash_obj.hexdigest()
        vec = []
        # Create 1536-dim vector by repeating and mixing the hash
        for i in range(1536):
            chunk_idx = (i * 2) % len(hex_digest)
            chunk = hex_digest[chunk_idx:chunk_idx+2]
            if len(chunk) == 2:
                val = int(chunk, 16) / 255.0
            else:
                val = int(chunk + hex_digest[0], 16) / 255.0
            vec.append(val)
        return vec

    async def record_episode(
        self,
        agent_id: str,
        task_description: str,
        context: Dict[str, Any],
        actions: List[Dict[str, Any]],
        outcome: str,
        success: bool,
        lessons_learned: List[str],
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
    ) -> str:
        """Record a new episodic memory."""
        await self.initialize()

        episode = Episode(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            task_description=task_description,
            context=context,
            actions=actions,
            outcome=outcome,
            success=success,
            lessons_learned=lessons_learned,
            tags=tags or [],
            importance=importance,
        )

        # Store in vector memory
        search_text = episode.to_search_text()
        embedding = self._get_embedding(search_text)
        await self._vector_memory.add(
            content=search_text,
            embedding=embedding,
            metadata=episode.to_metadata(),
            importance=importance,
            id=episode.id,
        )

        # Update local index
        self._episodes[episode.id] = episode
        self._agent_index.setdefault(agent_id, []).append(episode.id)

        # Enforce max episodes per agent
        agent_episodes = self._agent_index.get(agent_id, [])
        if len(agent_episodes) > self.config.max_episodes_per_agent:
            # Remove oldest low-importance episodes
            agent_episodes.sort(key=lambda eid: self._episodes[eid].importance)
            to_remove = agent_episodes[:len(agent_episodes) - self.config.max_episodes_per_agent]
            for eid in to_remove:
                await self._vector_memory.delete([eid])
                del self._episodes[eid]
                agent_episodes.remove(eid)

        return episode.id

    async def recall(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
        min_importance: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> List[Episode]:
        """Recall relevant episodes for a query."""
        await self.initialize()

        filter_metadata = {"agent_id": agent_id, "type": "episode"}
        if tags:
            filter_metadata["tags"] = tags

        query_embedding = self._get_embedding(query)
        results = await self._vector_memory.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
            threshold=min_importance,
        )

        episodes = []
        for vec, score in results:
            if vec.metadata.get("type") == "episode":
                episode = self._episodes.get(vec.id)
                if episode:
                    episode.access_count += 1
                    episode.last_accessed = time.time()
                    episodes.append(episode)

        return episodes

    async def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Get a specific episode by ID."""
        return self._episodes.get(episode_id)

    async def get_agent_episodes(self, agent_id: str, limit: int = 100) -> List[Episode]:
        """Get recent episodes for an agent."""
        episode_ids = self._agent_index.get(agent_id, [])[-limit:]
        return [self._episodes[eid] for eid in episode_ids if eid in self._episodes]

    async def update_importance(self, episode_id: str, importance: float) -> bool:
        """Update importance of an episode."""
        episode = self._episodes.get(episode_id)
        if episode:
            episode.importance = importance
            episode.updated_at = time.time()
            await self._vector_memory.update_importance(episode_id, importance)
            return True
        return False

    async def add_tags(self, episode_id: str, tags: List[str]) -> bool:
        """Add tags to an episode."""
        episode = self._episodes.get(episode_id)
        if episode:
            for tag in tags:
                if tag not in episode.tags:
                    episode.tags.append(tag)
            episode.updated_at = time.time()
            # Update in vector memory
            vecs = await self._vector_memory.get([episode_id])
            if vecs[0]:
                vecs[0].metadata["tags"] = episode.tags
                await self._vector_memory._backend.upsert(vecs)  # type: ignore
            return True
        return False

    async def prune_low_importance(self, threshold: Optional[float] = None) -> int:
        """Remove episodes below importance threshold."""
        threshold = threshold or self.config.min_importance_to_keep
        to_remove = [
            eid for eid, ep in self._episodes.items()
            if ep.importance < threshold
        ]
        if to_remove:
            await self._vector_memory.delete(to_remove)
            for eid in to_remove:
                ep = self._episodes.pop(eid, None)
                if ep and ep.agent_id in self._agent_index:
                    self._agent_index[ep.agent_id] = [
                        x for x in self._agent_index[ep.agent_id] if x != eid
                    ]
        return len(to_remove)


# Global instance
_episodic_memory: Optional[EpisodicMemory] = None


def get_episodic_memory(config: Optional[EpisodicMemoryConfig] = None) -> EpisodicMemory:
    """Get global episodic memory instance."""
    global _episodic_memory
    if _episodic_memory is None:
        _episodic_memory = EpisodicMemory(config)
    return _episodic_memory