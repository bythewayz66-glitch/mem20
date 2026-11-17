"""Memory Manager: unified interface for all memory systems."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Awaitable

from pydantic import BaseModel, Field

from .vector import VectorMemory, VectorMemoryConfig, get_vector_memory
from .episodic import EpisodicMemory, EpisodicMemoryConfig, get_episodic_memory
from .semantic import SemanticMemory, SemanticMemoryConfig, get_semantic_memory
from .consolidation import MemoryConsolidator, ConsolidationConfig, get_consolidator
from .knowledge_graph import KnowledgeGraph, KnowledgeGraphConfig, get_knowledge_graph
from .rag import GitHistoryRAG, RAGConfig, get_git_history_rag
from ..config import settings


class MemoryManagerConfig(BaseModel):
    """Configuration for memory manager."""
    vector_config: Optional[VectorMemoryConfig] = None
    episodic_config: Optional[EpisodicMemoryConfig] = None
    semantic_config: Optional[SemanticMemoryConfig] = None
    consolidation_config: Optional[ConsolidationConfig] = None
    knowledge_graph_config: Optional[KnowledgeGraphConfig] = None
    rag_config: Optional[RAGConfig] = None
    enable_auto_consolidation: bool = True
    consolidation_interval_hours: int = 24


@dataclass
class MemoryPin:
    """A pinned memory item ('Remember this')."""
    id: str
    agent_id: str
    content: str
    context: Dict[str, Any]
    source: str  # conversation_id, message_id, etc.
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0
    created_at: float = field(default_factory=time.time)
    created_by: Optional[str] = None


class MemoryManager:
    """Unified memory manager coordinating all memory subsystems."""

    def __init__(self, config: Optional[MemoryManagerConfig] = None) -> None:
        self.config = config or MemoryManagerConfig()
        self._vector_memory: Optional[VectorMemory] = None
        self._episodic_memory: Optional[EpisodicMemory] = None
        self._semantic_memory: Optional[SemanticMemory] = None
        self._consolidator: Optional[MemoryConsolidator] = None
        self._knowledge_graph: Optional[KnowledgeGraph] = None
        self._git_history_rag: Optional[GitHistoryRAG] = None
        self._pins: Dict[str, MemoryPin] = {}
        self._agent_pins: Dict[str, List[str]] = {}  # agent_id -> pin_ids
        self._initialized = False
        self._llm_summarizer: Optional[Callable[[str], Awaitable[str]]] = None

    def set_llm_summarizer(self, summarizer: Callable[[str], Awaitable[str]]) -> None:
        """Set the LLM function for summarization."""
        self._llm_summarizer = summarizer

    async def initialize(self) -> None:
        if self._initialized:
            return

        # Initialize subsystems
        self._vector_memory = get_vector_memory(self.config.vector_config)
        self._episodic_memory = get_episodic_memory(self.config.episodic_config)
        self._semantic_memory = get_semantic_memory(self.config.semantic_config)
        self._consolidator = get_consolidator(self.config.consolidation_config)
        self._knowledge_graph = get_knowledge_graph(self.config.knowledge_graph_config)
        self._git_history_rag = get_git_history_rag(self.config.rag_config)

        await self._vector_memory.initialize()
        await self._episodic_memory.initialize()
        await self._semantic_memory.initialize()
        await self._consolidator.initialize()
        await self._knowledge_graph.initialize()
        await self._git_history_rag.initialize()

        # Set LLM summarizer for consolidator
        if self._llm_summarizer:
            self._consolidator.set_llm_summarizer(self._llm_summarizer)

        # Start auto-consolidation
        if self.config.enable_auto_consolidation:
            await self._consolidator.start_scheduler()

        self._initialized = True

    async def close(self) -> None:
        if self._consolidator:
            await self._consolidator.stop_scheduler()
        if self._vector_memory:
            await self._vector_memory.close()
        if self._episodic_memory:
            await self._episodic_memory.close()
        if self._semantic_memory:
            await self._semantic_memory.close()
        if self._consolidator:
            await self._consolidator.close()
        if self._knowledge_graph:
            await self._knowledge_graph.close()
        if self._git_history_rag:
            await self._git_history_rag.close()
        self._initialized = False

    # --- "Remember this" functionality ---

    async def pin_memory(
        self,
        agent_id: str,
        content: str,
        context: Dict[str, Any],
        source: str,
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        created_by: Optional[str] = None,
    ) -> str:
        """Pin a memory item for long-term retention ('Remember this')."""
        pin = MemoryPin(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            content=content,
            context=context,
            source=source,
            tags=tags or ["pinned"],
            importance=importance,
            created_by=created_by,
        )

        self._pins[pin.id] = pin
        self._agent_pins.setdefault(agent_id, []).append(pin.id)

        # Also store in episodic memory for retrieval
        await self._episodic_memory.record_episode(
            agent_id=agent_id,
            task_description=f"Pinned: {content[:100]}",
            context=context,
            actions=[{"type": "pin", "content": content}],
            outcome="Memory pinned for long-term retention",
            success=True,
            lessons_learned=[],
            tags=["pinned"] + (tags or []),
            importance=importance,
        )

        # Store in vector memory for search
        embedding = self._get_embedding(content)
        await self._vector_memory.add(
            content=content,
            embedding=embedding,
            metadata={
                "type": "pin",
                "agent_id": agent_id,
                "source": source,
                "tags": tags or [],
                "importance": importance,
                "created_at": pin.created_at,
            },
            importance=importance,
            id=f"pin:{pin.id}",
        )

        return pin.id

    async def get_pins(self, agent_id: str, limit: int = 50) -> List[MemoryPin]:
        """Get pinned memories for an agent."""
        pin_ids = self._agent_pins.get(agent_id, [])[-limit:]
        return [self._pins[pid] for pid in pin_ids if pid in self._pins]

    async def unpin_memory(self, pin_id: str) -> bool:
        """Unpin a memory item."""
        pin = self._pins.pop(pin_id, None)
        if pin:
            if pin.agent_id in self._agent_pins:
                self._agent_pins[pin.agent_id] = [
                    pid for pid in self._agent_pins[pin.agent_id] if pid != pin_id
                ]
            await self._vector_memory.delete([f"pin:{pin_id}"])
            return True
        return False

    # --- Unified search ---

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hex_digest = hash_obj.hexdigest()
        vec = []
        for i in range(1536):
            chunk_idx = (i * 2) % len(hex_digest)
            chunk = hex_digest[chunk_idx:chunk_idx+2]
            if len(chunk) == 2:
                val = int(chunk, 16) / 255.0
            else:
                val = int(chunk + hex_digest[0], 16) / 255.0
            vec.append(val)
        return vec

    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        top_k: int = 10,
        include_episodic: bool = True,
        include_semantic: bool = True,
        include_pins: bool = True,
        include_knowledge_graph: bool = True,
        include_git_history: bool = False,
    ) -> Dict[str, List[Any]]:
        """Search across all memory systems."""
        await self.initialize()

        results = {}

        if include_pins:
            # Search pinned memories
            filter_metadata = {"type": "pin"}
            if agent_id:
                filter_metadata["agent_id"] = agent_id
            query_embedding = self._get_embedding(query)
            pin_results = await self._vector_memory.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )
            results["pins"] = [
                {"pin": self._pins.get(vec.id.replace("pin:", "")), "score": score}
                for vec, score in pin_results
                if vec.id.startswith("pin:") and vec.id.replace("pin:", "") in self._pins
            ]

        if include_episodic and agent_id:
            results["episodic"] = await self._episodic_memory.recall(agent_id, query, top_k)

        if include_semantic:
            sem_results = await self._semantic_memory.search(query, top_k)
            results["semantic"] = sem_results

        if include_knowledge_graph:
            kg_results = await self._knowledge_graph.search_entities(query, top_k)
            results["knowledge_graph"] = kg_results

        if include_git_history:
            git_results = await self._git_history_rag.query(query, top_k)
            results["git_history"] = git_results

        return results

    # --- Episodic memory delegation ---

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
        """Record an episodic memory."""
        return await self._episodic_memory.record_episode(
            agent_id=agent_id,
            task_description=task_description,
            context=context,
            actions=actions,
            outcome=outcome,
            success=success,
            lessons_learned=lessons_learned,
            tags=tags,
            importance=importance,
        )

    async def recall_episodes(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Any]:
        """Recall episodic memories."""
        return await self._episodic_memory.recall(agent_id, query, top_k)

    # --- Semantic memory delegation ---

    async def add_concept(
        self,
        name: str,
        type: str,
        definition: str,
        context: str,
        **kwargs,
    ) -> str:
        """Add a semantic concept."""
        from .semantic import ConceptType
        return await self._semantic_memory.add_concept(
            name=name,
            type=ConceptType(type),
            definition=definition,
            context=context,
            **kwargs,
        )

    async def add_adr(
        self,
        title: str,
        status: str,
        context: str,
        decision: str,
        consequences: List[str],
        **kwargs,
    ) -> str:
        """Add an ADR."""
        return await self._semantic_memory.add_adr(
            title=title,
            status=status,
            context=context,
            decision=decision,
            consequences=consequences,
            **kwargs,
        )

    async def search_concepts(self, query: str, **kwargs) -> List[Any]:
        """Search semantic concepts."""
        return await self._semantic_memory.search_concepts(query, **kwargs)

    # --- Knowledge graph delegation ---

    async def add_code_entity(
        self,
        type: str,
        name: str,
        qualified_name: str,
        properties: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Add a code entity to the knowledge graph."""
        from .knowledge_graph import EntityType
        return await self._knowledge_graph.add_entity(
            type=EntityType(type),
            name=name,
            qualified_name=qualified_name,
            properties=properties,
            source=source,
        )

    async def add_code_relation(
        self,
        source_id: str,
        target_id: str,
        type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a code relation."""
        from .knowledge_graph import RelationType
        return await self._knowledge_graph.add_relation(
            source_id=source_id,
            target_id=target_id,
            type=RelationType(type),
            properties=properties,
        )

    async def find_code_path(
        self,
        source_name: str,
        target_name: str,
    ) -> Optional[List[Tuple[Any, Any]]]:
        """Find path between two code entities."""
        source = await self._knowledge_graph.get_entity_by_name(source_name)
        target = await self._knowledge_graph.get_entity_by_name(target_name)
        if source and target:
            return await self._knowledge_graph.find_path(source.id, target.id)
        return None

    # --- Git history RAG delegation ---

    async def explain_code_change(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
    ) -> Dict[str, Any]:
        """Explain why code was changed."""
        return await self._git_history_rag.explain_code(file_path, start_line, end_line)

    async def query_git_history(self, question: str, **kwargs) -> Dict[str, List[Any]]:
        """Query git history."""
        return await self._git_history_rag.query(question, **kwargs)

    # --- Consolidation ---

    async def run_consolidation(self) -> Dict[str, Any]:
        """Run memory consolidation."""
        return await self._consolidator.run_consolidation()

    async def summarize_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        agent_id: str,
    ) -> Optional[str]:
        """Summarize a conversation."""
        return await self._consolidator.summarize_conversation(conversation_id, messages, agent_id)

    async def extract_knowledge_from_content(
        self,
        content: str,
        source: str,
        context: str = "",
    ) -> List[str]:
        """Extract knowledge from content."""
        return await self._consolidator.extract_knowledge(content, source, context)

    # --- Memory packs (export/import) ---

    async def export_memory_pack(
        self,
        agent_id: Optional[str] = None,
        include_episodic: bool = True,
        include_semantic: bool = True,
        include_pins: bool = True,
        include_knowledge_graph: bool = False,
    ) -> Dict[str, Any]:
        """Export memory as a portable pack."""
        pack = {
            "version": 1,
            "exported_at": time.time(),
            "agent_id": agent_id,
        }

        if include_episodic:
            episodes = await self._episodic_memory.get_agent_episodes(agent_id or "", limit=1000)
            pack["episodes"] = [ep.__dict__ for ep in episodes]

        if include_semantic:
            concepts = await self._semantic_memory.list_concepts(limit=1000)
            adrs = await self._semantic_memory.list_adrs(limit=1000)
            pack["concepts"] = [c.__dict__ for c in concepts]
            pack["adrs"] = [a.__dict__ for a in adrs]

        if include_pins:
            pins = await self.get_pins(agent_id or "", limit=1000)
            pack["pins"] = [p.__dict__ for p in pins]

        if include_knowledge_graph:
            entities = await self._knowledge_graph.list_entities(limit=1000)
            pack["entities"] = [e.__dict__ for e in entities]

        return pack

    async def import_memory_pack(
        self,
        pack: Dict[str, Any],
        agent_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """Import a memory pack."""
        counts = {"episodes": 0, "concepts": 0, "adrs": 0, "pins": 0, "entities": 0}

        target_agent = agent_id or pack.get("agent_id")

        if "episodes" in pack:
            for ep_data in pack["episodes"]:
                # Reconstruct episode and store
                await self._episodic_memory.record_episode(
                    agent_id=target_agent or ep_data.get("agent_id", ""),
                    task_description=ep_data.get("task_description", ""),
                    context=ep_data.get("context", {}),
                    actions=ep_data.get("actions", []),
                    outcome=ep_data.get("outcome", ""),
                    success=ep_data.get("success", True),
                    lessons_learned=ep_data.get("lessons_learned", []),
                    tags=ep_data.get("tags", []),
                    importance=ep_data.get("importance", 1.0),
                )
                counts["episodes"] += 1

        if "concepts" in pack:
            for c_data in pack["concepts"]:
                from .semantic import ConceptType
                await self._semantic_memory.add_concept(
                    name=c_data.get("name", ""),
                    type=ConceptType(c_data.get("type", "custom")),
                    definition=c_data.get("definition", ""),
                    context=c_data.get("context", ""),
                    examples=c_data.get("examples"),
                    related_concepts=c_data.get("related_concepts"),
                    tags=c_data.get("tags"),
                    source=c_data.get("source"),
                    confidence=c_data.get("confidence", 1.0),
                    created_by=c_data.get("created_by"),
                )
                counts["concepts"] += 1

        if "adrs" in pack:
            for a_data in pack["adrs"]:
                await self._semantic_memory.add_adr(
                    title=a_data.get("title", ""),
                    status=a_data.get("status", "proposed"),
                    context=a_data.get("context", ""),
                    decision=a_data.get("decision", ""),
                    consequences=a_data.get("consequences", []),
                    alternatives=a_data.get("alternatives", []),
                    tags=a_data.get("tags", []),
                    created_by=a_data.get("created_by"),
                )
                counts["adrs"] += 1

        if "pins" in pack:
            for p_data in pack["pins"]:
                await self.pin_memory(
                    agent_id=target_agent or p_data.get("agent_id", ""),
                    content=p_data.get("content", ""),
                    context=p_data.get("context", {}),
                    source=p_data.get("source", "imported"),
                    tags=p_data.get("tags", ["imported"]),
                    importance=p_data.get("importance", 1.0),
                    created_by=p_data.get("created_by"),
                )
                counts["pins"] += 1

        if "entities" in pack:
            for e_data in pack["entities"]:
                from .knowledge_graph import EntityType
                await self._knowledge_graph.add_entity(
                    type=EntityType(e_data.get("type", "custom")),
                    name=e_data.get("name", ""),
                    qualified_name=e_data.get("qualified_name", ""),
                    properties=e_data.get("properties", {}),
                    source=e_data.get("source"),
                    confidence=e_data.get("confidence", 1.0),
                )
                counts["entities"] += 1

        return counts

    # --- Statistics ---

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "vector_memory": {
                "initialized": self._vector_memory is not None and self._vector_memory._initialized,
            },
            "episodic_memory": {
                "total_episodes": len(self._episodic_memory._episodes) if self._episodic_memory else 0,
            },
            "semantic_memory": {
                "total_concepts": len(self._semantic_memory._concepts) if self._semantic_memory else 0,
                "total_adrs": len(self._semantic_memory._adrs) if self._semantic_memory else 0,
            },
            "consolidator": {
                "jobs_completed": len([j for j in self._consolidator._jobs.values() if j.status == "completed"]) if self._consolidator else 0,
            },
            "knowledge_graph": {
                "total_entities": len(self._knowledge_graph._entities) if self._knowledge_graph else 0,
                "total_relations": len(self._knowledge_graph._relations) if self._knowledge_graph else 0,
            },
            "pins": {
                "total": len(self._pins),
                "by_agent": {aid: len(pids) for aid, pids in self._agent_pins.items()},
            },
        }


# Global instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(config: Optional[MemoryManagerConfig] = None) -> MemoryManager:
    """Get global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(config)
    return _memory_manager