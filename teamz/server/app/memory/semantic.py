"""Semantic memory: project glossary, architecture decisions (ADRs), concepts."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .vector import VectorMemory, VectorMemoryConfig, get_vector_memory


class ConceptType(str, Enum):
    """Types of semantic concepts."""
    GLOSSARY_TERM = "glossary_term"
    ARCHITECTURE_DECISION = "architecture_decision"
    DESIGN_PATTERN = "design_pattern"
    API_ENDPOINT = "api_endpoint"
    DATABASE_SCHEMA = "database_schema"
    CONFIGURATION = "configuration"
    BUSINESS_RULE = "business_rule"
    TECHNOLOGY = "technology"
    CUSTOM = "custom"


class SemanticMemoryConfig(BaseModel):
    """Configuration for semantic memory."""
    vector_config: Optional[VectorMemoryConfig] = None
    auto_link_concepts: bool = True
    max_related_concepts: int = 10


@dataclass
class SemanticConcept:
    """A semantic memory concept."""
    id: str
    name: str
    type: ConceptType
    definition: str
    context: str  # When/where this applies
    examples: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)  # concept IDs
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None  # File, URL, person who defined it
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: Optional[str] = None
    version: int = 1

    def to_search_text(self) -> str:
        """Convert to searchable text."""
        parts = [
            f"Concept: {self.name}",
            f"Type: {self.type.value}",
            f"Definition: {self.definition}",
            f"Context: {self.context}",
        ]
        if self.examples:
            parts.append(f"Examples: {'; '.join(self.examples)}")
        if self.related_concepts:
            parts.append(f"Related: {', '.join(self.related_concepts)}")
        return "\n".join(parts)

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "version": self.version,
            "semantic_type": "concept",
        }


@dataclass
class ArchitectureDecision:
    """An Architecture Decision Record (ADR)."""
    id: str
    title: str
    status: str  # proposed, accepted, deprecated, superseded
    context: str
    decision: str
    consequences: List[str]
    alternatives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: Optional[str] = None
    superseded_by: Optional[str] = None

    def to_search_text(self) -> str:
        parts = [
            f"ADR: {self.title}",
            f"Status: {self.status}",
            f"Context: {self.context}",
            f"Decision: {self.decision}",
            f"Consequences: {'; '.join(self.consequences)}",
        ]
        if self.alternatives:
            parts.append(f"Alternatives: {'; '.join(self.alternatives)}")
        return "\n".join(parts)

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "status": self.status,
            "tags": self.tags,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "superseded_by": self.superseded_by,
            "semantic_type": "adr",
        }


class SemanticMemory:
    """Semantic memory for project knowledge."""

    def __init__(self, config: Optional[SemanticMemoryConfig] = None) -> None:
        self.config = config or SemanticMemoryConfig()
        self._vector_memory: Optional[VectorMemory] = None
        self._concepts: Dict[str, SemanticConcept] = {}
        self._adrs: Dict[str, ArchitectureDecision] = {}
        self._name_index: Dict[str, str] = {}  # name -> concept_id

    async def initialize(self) -> None:
        if self._vector_memory is None:
            self._vector_memory = get_vector_memory(self.config.vector_config)
            await self._vector_memory.initialize()

    async def close(self) -> None:
        if self._vector_memory:
            await self._vector_memory.close()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hex_digest = hash_obj.hexdigest()
        vec = []
        # Create 1536-dim vector by repeating and mixing the hash
        for i in range(1536):
            # Use different parts of the hash for each dimension
            chunk_idx = (i * 2) % len(hex_digest)
            chunk = hex_digest[chunk_idx:chunk_idx+2]
            if len(chunk) == 2:
                val = int(chunk, 16) / 255.0
            else:
                # Wrap around for odd-length chunks
                val = int(chunk + hex_digest[0], 16) / 255.0
            vec.append(val)
        return vec

    # --- Concepts ---

    async def add_concept(
        self,
        name: str,
        type: ConceptType,
        definition: str,
        context: str,
        examples: Optional[List[str]] = None,
        related_concepts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
        created_by: Optional[str] = None,
    ) -> str:
        """Add a semantic concept."""
        await self.initialize()

        # Check for existing
        existing_id = self._name_index.get(name.lower())
        if existing_id:
            return await self.update_concept(existing_id, {
                "definition": definition,
                "context": context,
                "examples": examples,
                "related_concepts": related_concepts,
                "tags": tags,
                "source": source,
                "confidence": confidence,
            })

        concept = SemanticConcept(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            definition=definition,
            context=context,
            examples=examples or [],
            related_concepts=related_concepts or [],
            tags=tags or [],
            source=source,
            confidence=confidence,
            created_by=created_by,
        )

        # Store in vector memory
        search_text = concept.to_search_text()
        embedding = self._get_embedding(search_text)
        await self._vector_memory.add(
            content=search_text,
            embedding=embedding,
            metadata=concept.to_metadata(),
            importance=confidence,
            id=concept.id,
        )

        # Update indexes
        self._concepts[concept.id] = concept
        self._name_index[name.lower()] = concept.id

        # Auto-link related concepts
        if self.config.auto_link_concepts and related_concepts:
            for related_id in related_concepts:
                if related_id in self._concepts:
                    related = self._concepts[related_id]
                    if concept.id not in related.related_concepts:
                        related.related_concepts.append(concept.id)
                        related.updated_at = time.time()
                        await self._update_in_vector(related)

        return concept.id

    async def update_concept(self, concept_id: str, updates: Dict[str, Any]) -> str:
        """Update an existing concept."""
        concept = self._concepts.get(concept_id)
        if not concept:
            raise ValueError(f"Concept not found: {concept_id}")

        old_name = concept.name.lower()
        for key, value in updates.items():
            if hasattr(concept, key):
                setattr(concept, key, value)

        concept.updated_at = time.time()
        concept.version += 1

        # Update name index if name changed
        if "name" in updates:
            new_name = updates["name"].lower()
            if old_name in self._name_index:
                del self._name_index[old_name]
            self._name_index[new_name] = concept_id

        # Update in vector memory
        await self._update_in_vector(concept)

        return concept_id

    async def _update_in_vector(self, concept: SemanticConcept) -> None:
        search_text = concept.to_search_text()
        embedding = self._get_embedding(search_text)
        await self._vector_memory.add(
            content=search_text,
            embedding=embedding,
            metadata=concept.to_metadata(),
            importance=concept.confidence,
            id=concept.id,
        )

    async def get_concept(self, concept_id: str) -> Optional[SemanticConcept]:
        """Get a concept by ID."""
        return self._concepts.get(concept_id)

    async def get_concept_by_name(self, name: str) -> Optional[SemanticConcept]:
        """Get a concept by name."""
        concept_id = self._name_index.get(name.lower())
        if concept_id:
            return self._concepts.get(concept_id)
        return None

    async def search_concepts(
        self,
        query: str,
        top_k: int = 10,
        concept_type: Optional[ConceptType] = None,
        tags: Optional[List[str]] = None,
    ) -> List[SemanticConcept]:
        """Search for concepts."""
        await self.initialize()

        filter_metadata = {"semantic_type": "concept"}
        if concept_type:
            filter_metadata["type"] = concept_type.value

        query_embedding = self._get_embedding(query)
        results = await self._vector_memory.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        concepts = []
        for vec, score in results:
            if vec.metadata.get("semantic_type") == "concept":
                concept = self._concepts.get(vec.id)
                if concept:
                    concepts.append(concept)

        return concepts

    async def list_concepts(
        self,
        concept_type: Optional[ConceptType] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[SemanticConcept]:
        """List concepts with optional filters."""
        concepts = list(self._concepts.values())
        if concept_type:
            concepts = [c for c in concepts if c.type == concept_type]
        if tags:
            concepts = [c for c in concepts if any(t in c.tags for t in tags)]
        return concepts[:limit]

    # --- ADRs ---

    async def add_adr(
        self,
        title: str,
        status: str,
        context: str,
        decision: str,
        consequences: List[str],
        alternatives: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> str:
        """Add an Architecture Decision Record."""
        await self.initialize()

        adr = ArchitectureDecision(
            id=str(uuid.uuid4()),
            title=title,
            status=status,
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives=alternatives or [],
            tags=tags or [],
            created_by=created_by,
        )

        # Store in vector memory
        search_text = adr.to_search_text()
        embedding = self._get_embedding(search_text)
        await self._vector_memory.add(
            content=search_text,
            embedding=embedding,
            metadata=adr.to_metadata(),
            importance=1.0,
            id=adr.id,
        )

        self._adrs[adr.id] = adr
        return adr.id

    async def update_adr(self, adr_id: str, updates: Dict[str, Any]) -> str:
        """Update an ADR."""
        adr = self._adrs.get(adr_id)
        if not adr:
            raise ValueError(f"ADR not found: {adr_id}")

        for key, value in updates.items():
            if hasattr(adr, key):
                setattr(adr, key, value)

        adr.updated_at = time.time()

        # Update in vector memory
        search_text = adr.to_search_text()
        embedding = self._get_embedding(search_text)
        await self._vector_memory.add(
            content=search_text,
            embedding=embedding,
            metadata=adr.to_metadata(),
            importance=1.0,
            id=adr.id,
        )

        return adr_id

    async def get_adr(self, adr_id: str) -> Optional[ArchitectureDecision]:
        """Get an ADR by ID."""
        return self._adrs.get(adr_id)

    async def search_adrs(
        self,
        query: str,
        top_k: int = 10,
        status: Optional[str] = None,
    ) -> List[ArchitectureDecision]:
        """Search ADRs."""
        await self.initialize()

        filter_metadata = {"semantic_type": "adr"}
        if status:
            filter_metadata["status"] = status

        query_embedding = self._get_embedding(query)
        results = await self._vector_memory.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        adrs = []
        for vec, score in results:
            if vec.metadata.get("semantic_type") == "adr":
                adr = self._adrs.get(vec.id)
                if adr:
                    adrs.append(adr)

        return adrs

    async def list_adrs(self, status: Optional[str] = None, limit: int = 100) -> List[ArchitectureDecision]:
        """List ADRs."""
        adrs = list(self._adrs.values())
        if status:
            adrs = [a for a in adrs if a.status == status]
        return adrs[:limit]

    # --- General search ---

    async def search(
        self,
        query: str,
        top_k: int = 10,
        include_concepts: bool = True,
        include_adrs: bool = True,
    ) -> Dict[str, List[Any]]:
        """Search both concepts and ADRs."""
        results: Dict[str, List[Any]] = {}
        if include_concepts:
            results["concepts"] = await self.search_concepts(query, top_k)
        if include_adrs:
            results["adrs"] = await self.search_adrs(query, top_k)
        return results


# Global instance
_semantic_memory: Optional[SemanticMemory] = None


def get_semantic_memory(config: Optional[SemanticMemoryConfig] = None) -> SemanticMemory:
    """Get global semantic memory instance."""
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory(config)
    return _semantic_memory