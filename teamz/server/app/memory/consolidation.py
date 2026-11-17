"""Memory consolidation: nightly summarization + embedding."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Awaitable

from pydantic import BaseModel, Field

from .vector import VectorMemory, get_vector_memory
from .episodic import EpisodicMemory, get_episodic_memory
from .semantic import SemanticMemory, get_semantic_memory
from ..config import settings


class ConsolidationConfig(BaseModel):
    """Configuration for memory consolidation."""
    enabled: bool = True
    interval_hours: int = 24
    max_items_per_run: int = 100
    summarization_model: str = "gpt-4o-mini"
    importance_threshold: float = 0.5
    min_access_count: int = 2
    decay_factor: float = 0.95  # Importance decay per period
    create_semantic_concepts: bool = True
    create_episodic_summaries: bool = True


@dataclass
class ConsolidationJob:
    """A consolidation job."""
    id: str
    type: str  # summarize, decay, link, prune
    status: str  # pending, running, completed, failed
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    items_processed: int = 0
    error: Optional[str] = None


class MemoryConsolidator:
    """Consolidates memories: summarizes, links, decays importance, prunes."""

    def __init__(
        self,
        config: Optional[ConsolidationConfig] = None,
        vector_memory: Optional[VectorMemory] = None,
        episodic_memory: Optional[EpisodicMemory] = None,
        semantic_memory: Optional[SemanticMemory] = None,
    ) -> None:
        self.config = config or ConsolidationConfig()
        self._vector_memory = vector_memory
        self._episodic_memory = episodic_memory
        self._semantic_memory = semantic_memory
        self._jobs: Dict[str, ConsolidationJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._llm_summarizer: Optional[Callable[[str], Awaitable[str]]] = None

    def set_llm_summarizer(self, summarizer: Callable[[str], Awaitable[str]]) -> None:
        """Set the LLM function for summarization."""
        self._llm_summarizer = summarizer

    async def initialize(self) -> None:
        if self._vector_memory is None:
            self._vector_memory = get_vector_memory()
        if self._episodic_memory is None:
            self._episodic_memory = get_episodic_memory()
        if self._semantic_memory is None:
            self._semantic_memory = get_semantic_memory()

        await self._vector_memory.initialize()
        await self._episodic_memory.initialize()
        await self._semantic_memory.initialize()

    async def start_scheduler(self) -> None:
        """Start the periodic consolidation scheduler."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())

    async def stop_scheduler(self) -> None:
        """Stop the periodic consolidation scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_scheduler(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self.config.interval_hours * 3600)
                if self._running:
                    await self.run_consolidation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MemoryConsolidator] Scheduler error: {e}")

    async def run_consolidation(self) -> Dict[str, Any]:
        """Run a full consolidation cycle."""
        if not self.config.enabled:
            return {"skipped": True, "reason": "consolidation disabled"}

        job_id = str(uuid.uuid4())
        job = ConsolidationJob(
            id=job_id,
            type="full_consolidation",
            status="running",
            created_at=time.time(),
            started_at=time.time(),
        )
        self._jobs[job_id] = job

        results = {
            "summarized_episodes": 0,
            "decayed_items": 0,
            "linked_concepts": 0,
            "pruned_items": 0,
            "errors": [],
        }

        try:
            # 1. Summarize episodic memories
            if self.config.create_episodic_summaries:
                summarized = await self._summarize_episodes()
                results["summarized_episodes"] = summarized
                job.items_processed += summarized

            # 2. Decay importance scores
            decayed = await self._decay_importance()
            results["decayed_items"] = decayed
            job.items_processed += decayed

            # 3. Link related concepts
            linked = await self._link_concepts()
            results["linked_concepts"] = linked
            job.items_processed += linked

            # 4. Prune low-importance items
            pruned = await self._prune_low_importance()
            results["pruned_items"] = pruned
            job.items_processed += pruned

            job.status = "completed"
            job.completed_at = time.time()

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
            results["errors"].append(str(e))

        return results

    async def _summarize_episodes(self) -> int:
        """Summarize recent episodes into semantic concepts."""
        if not self._llm_summarizer:
            return 0

        # Get episodes that haven't been summarized
        # This is a simplified implementation
        summarized = 0

        # In a real implementation:
        # 1. Get recent episodes with high access counts
        # 2. Group by task similarity
        # 3. Use LLM to create summaries
        # 4. Store as semantic concepts

        return summarized

    async def _decay_importance(self) -> int:
        """Decay importance scores for old/unused memories."""
        decayed = 0

        # Decay vector memory items
        # This would need a scan operation - simplified here
        # In production, use a background job to iterate all items

        return decayed

    async def _link_concepts(self) -> int:
        """Auto-link related semantic concepts."""
        linked = 0

        if not self._semantic_memory:
            return 0

        # Get all concepts
        concepts = await self._semantic_memory.list_concepts(limit=1000)

        # Find similar concepts and link them
        for concept in concepts:
            if len(concept.related_concepts) >= self.config.max_related_concepts:
                continue

            # Search for similar concepts
            similar = await self._semantic_memory.search_concepts(
                concept.definition,
                top_k=5,
            )

            for similar_concept in similar:
                if similar_concept.id != concept.id:
                    if similar_concept.id not in concept.related_concepts:
                        concept.related_concepts.append(similar_concept.id)
                        linked += 1

            if linked > 0:
                await self._semantic_memory._update_in_vector(concept)

        return linked

    async def _prune_low_importance(self) -> int:
        """Prune memories below importance threshold."""
        pruned = 0

        if self._episodic_memory:
            pruned += await self._episodic_memory.prune_low_importance(self.config.importance_threshold)

        if self._vector_memory:
            pruned += await self._vector_memory.prune_expired()

        return pruned

    # --- Manual consolidation operations ---

    async def summarize_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        agent_id: str,
    ) -> Optional[str]:
        """Summarize a conversation into an episodic memory."""
        if not self._llm_summarizer:
            return None

        # Format messages for summarization
        conversation_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])

        prompt = f"""Summarize this conversation for future reference. 
Extract: key decisions, code patterns used, problems solved, and lessons learned.

Conversation:
{conversation_text}

Provide a structured summary with:
1. Task description
2. Key actions taken
3. Outcome
4. Lessons learned (bullet points)"""

        try:
            summary = await self._llm_summarizer(prompt)

            # Parse summary and create episode
            # This is simplified - real implementation would parse structured output
            episode_id = await self._episodic_memory.record_episode(
                agent_id=agent_id,
                task_description=f"Conversation {conversation_id}",
                context={"conversation_id": conversation_id, "message_count": len(messages)},
                actions=[{"type": "conversation", "summary": summary}],
                outcome="Conversation completed",
                success=True,
                lessons_learned=[],
                tags=["conversation", "auto-summarized"],
                importance=0.7,
            )

            return episode_id
        except Exception as e:
            print(f"[MemoryConsolidator] Summarization failed: {e}")
            return None

    async def extract_knowledge(
        self,
        content: str,
        source: str,
        context: str = "",
    ) -> List[str]:
        """Extract semantic concepts from content (code, docs, etc.)."""
        if not self._llm_summarizer:
            return []

        prompt = f"""Extract key concepts, terms, and definitions from this content.
For each concept, provide: name, type, definition, and context.

Content source: {source}
Context: {context}

Content:
{content[:8000]}

Return as JSON array of concepts with fields: name, type, definition, context, examples."""

        try:
            result = await self._llm_summarizer(prompt)
            # Parse JSON and create concepts
            concepts = json.loads(result)
            created_ids = []

            for concept_data in concepts:
                concept_id = await self._semantic_memory.add_concept(
                    name=concept_data["name"],
                    type=concept_data.get("type", "custom"),
                    definition=concept_data["definition"],
                    context=concept_data.get("context", context),
                    examples=concept_data.get("examples"),
                    source=source,
                    confidence=concept_data.get("confidence", 0.8),
                )
                created_ids.append(concept_id)

            return created_ids
        except Exception as e:
            print(f"[MemoryConsolidator] Knowledge extraction failed: {e}")
            return []

    def get_job_status(self, job_id: str) -> Optional[ConsolidationJob]:
        """Get status of a consolidation job."""
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50) -> List[ConsolidationJob]:
        """List recent consolidation jobs."""
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]


# Global instance
_consolidator: Optional[MemoryConsolidator] = None


def get_consolidator(config: Optional[ConsolidationConfig] = None) -> MemoryConsolidator:
    """Get global memory consolidator instance."""
    global _consolidator
    if _consolidator is None:
        _consolidator = MemoryConsolidator(config)
    return _consolidator