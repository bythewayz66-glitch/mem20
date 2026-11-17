"""Knowledge graph: entities (files, functions, APIs) + relations."""

from __future__ import annotations

import json
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from .vector import VectorMemory, get_vector_memory
from ..config import settings


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    API_ENDPOINT = "api_endpoint"
    DATABASE_TABLE = "database_table"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    CONCEPT = "concept"
    AGENT = "agent"
    TASK = "task"
    CUSTOM = "custom"


class RelationType(str, Enum):
    """Types of relations between entities."""
    CONTAINS = "contains"           # File contains function/class
    CALLS = "calls"                 # Function calls function
    INHERITS = "inherits"           # Class inherits from class
    IMPORTS = "imports"             # Module imports module
    DEPENDS_ON = "depends_on"       # Entity depends on entity
    DEFINES = "defines"             # File defines entity
    USES = "uses"                   # Entity uses entity
    RELATED_TO = "related_to"       # General relation
    PART_OF = "part_of"             # Entity is part of larger entity
    HAS_TYPE = "has_type"           # Entity has type
    CONFIGURES = "configures"       # Config configures entity


class KnowledgeGraphConfig(BaseModel):
    """Configuration for knowledge graph."""
    vector_config: Optional[Dict[str, Any]] = None
    max_entities: int = 100000
    max_relations: int = 500000
    enable_vector_search: bool = True


@dataclass
class Entity:
    """A node in the knowledge graph."""
    id: str
    type: EntityType
    name: str
    qualified_name: str  # e.g., "module.Class.method"
    properties: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None  # File path, URL, etc.
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    confidence: float = 1.0

    def to_search_text(self) -> str:
        """Convert to searchable text."""
        props = ", ".join(f"{k}: {v}" for k, v in self.properties.items())
        return f"Entity: {self.name} ({self.type.value})\nQualified: {self.qualified_name}\nProperties: {props}"

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "qualified_name": self.qualified_name,
            "properties": self.properties,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "kg_type": "entity",
        }


@dataclass
class Relation:
    """An edge in the knowledge graph."""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "kg_type": "relation",
        }


class KnowledgeGraph:
    """Knowledge graph for code and documentation entities."""

    def __init__(self, config: Optional[KnowledgeGraphConfig] = None) -> None:
        self.config = config or KnowledgeGraphConfig()
        self._vector_memory: Optional[VectorMemory] = None
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, Relation] = {}
        self._outgoing: Dict[str, List[str]] = defaultdict(list)  # entity_id -> relation_ids
        self._incoming: Dict[str, List[str]] = defaultdict(list)
        self._name_index: Dict[str, str] = {}  # qualified_name -> entity_id
        self._type_index: Dict[EntityType, Set[str]] = defaultdict(set)

    async def initialize(self) -> None:
        if self._vector_memory is None:
            self._vector_memory = get_vector_memory()
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
        for i in range(1536):
            chunk_idx = (i * 2) % len(hex_digest)
            chunk = hex_digest[chunk_idx:chunk_idx+2]
            if len(chunk) == 2:
                val = int(chunk, 16) / 255.0
            else:
                val = int(chunk + hex_digest[0], 16) / 255.0
            vec.append(val)
        return vec

    # --- Entity operations ---

    async def add_entity(
        self,
        type: EntityType,
        name: str,
        qualified_name: str,
        properties: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
    ) -> str:
        """Add an entity to the graph."""
        await self.initialize()

        # Check for existing
        existing_id = self._name_index.get(qualified_name)
        if existing_id:
            return await self.update_entity(existing_id, {
                "name": name,
                "properties": properties,
                "source": source,
                "confidence": confidence,
            })

        entity = Entity(
            id=str(uuid.uuid4()),
            type=type,
            name=name,
            qualified_name=qualified_name,
            properties=properties or {},
            source=source,
            confidence=confidence,
        )

        # Store in vector memory if enabled
        if self.config.enable_vector_search:
            search_text = entity.to_search_text()
            embedding = self._get_embedding(search_text)
            await self._vector_memory.add(
                content=search_text,
                embedding=embedding,
                metadata=entity.to_metadata(),
                importance=confidence,
                id=entity.id,
            )

        # Update indexes
        self._entities[entity.id] = entity
        self._name_index[qualified_name] = entity.id
        self._type_index[type].add(entity.id)

        return entity.id

    async def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> str:
        """Update an entity."""
        entity = self._entities.get(entity_id)
        if not entity:
            raise ValueError(f"Entity not found: {entity_id}")

        old_qualified_name = entity.qualified_name
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        entity.updated_at = time.time()

        # Update name index if qualified_name changed
        if "qualified_name" in updates:
            if old_qualified_name in self._name_index:
                del self._name_index[old_qualified_name]
            self._name_index[entity.qualified_name] = entity_id

        # Update type index if type changed
        if "type" in updates:
            old_type = EntityType(updates["type"]) if isinstance(updates["type"], str) else updates["type"]
            self._type_index[old_type].discard(entity_id)
            self._type_index[entity.type].add(entity_id)

        # Update in vector memory
        if self.config.enable_vector_search:
            search_text = entity.to_search_text()
            embedding = self._get_embedding(search_text)
            await self._vector_memory.add(
                content=search_text,
                embedding=embedding,
                metadata=entity.to_metadata(),
                importance=entity.confidence,
                id=entity.id,
            )

        return entity_id

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)

    async def get_entity_by_name(self, qualified_name: str) -> Optional[Entity]:
        """Get entity by qualified name."""
        entity_id = self._name_index.get(qualified_name)
        if entity_id:
            return self._entities.get(entity_id)
        return None

    async def search_entities(
        self,
        query: str,
        top_k: int = 10,
        entity_type: Optional[EntityType] = None,
    ) -> List[Entity]:
        """Search entities by text."""
        await self.initialize()

        if not self.config.enable_vector_search:
            return []

        filter_metadata = {"kg_type": "entity"}
        if entity_type:
            filter_metadata["type"] = entity_type.value

        query_embedding = self._get_embedding(query)
        results = await self._vector_memory.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )

        entities = []
        for vec, score in results:
            if vec.metadata.get("kg_type") == "entity":
                entity = self._entities.get(vec.id)
                if entity:
                    entities.append(entity)

        return entities

    async def list_entities(
        self,
        entity_type: Optional[EntityType] = None,
        limit: int = 100,
    ) -> List[Entity]:
        """List entities."""
        if entity_type:
            entity_ids = self._type_index.get(entity_type, set())
            return [self._entities[eid] for eid in list(entity_ids)[:limit]]
        return list(self._entities.values())[:limit]

    # --- Relation operations ---

    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> str:
        """Add a relation between entities."""
        await self.initialize()

        # Verify entities exist
        if source_id not in self._entities or target_id not in self._entities:
            raise ValueError("Source or target entity not found")

        relation = Relation(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            type=type,
            properties=properties or {},
            confidence=confidence,
        )

        # Store in vector memory
        if self.config.enable_vector_search:
            search_text = f"Relation: {type.value} from {source_id} to {target_id}"
            embedding = self._get_embedding(search_text)
            await self._vector_memory.add(
                content=search_text,
                embedding=embedding,
                metadata=relation.to_metadata(),
                importance=confidence,
                id=relation.id,
            )

        # Update indexes
        self._relations[relation.id] = relation
        self._outgoing[source_id].append(relation.id)
        self._incoming[target_id].append(relation.id)

        return relation.id

    async def get_relation(self, relation_id: str) -> Optional[Relation]:
        """Get relation by ID."""
        return self._relations.get(relation_id)

    async def get_outgoing_relations(self, entity_id: str) -> List[Relation]:
        """Get all outgoing relations from an entity."""
        relation_ids = self._outgoing.get(entity_id, [])
        return [self._relations[rid] for rid in relation_ids if rid in self._relations]

    async def get_incoming_relations(self, entity_id: str) -> List[Relation]:
        """Get all incoming relations to an entity."""
        relation_ids = self._incoming.get(entity_id, [])
        return [self._relations[rid] for rid in relation_ids if rid in self._relations]

    async def get_neighbors(
        self,
        entity_id: str,
        relation_types: Optional[List[RelationType]] = None,
        direction: str = "both",  # outgoing, incoming, both
        max_depth: int = 1,
    ) -> List[Tuple[Entity, Relation, str]]:
        """Get neighboring entities."""
        results = []

        def traverse(current_id: str, depth: int, visited: Set[str]) -> None:
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)

            # Outgoing
            if direction in ("outgoing", "both"):
                for rel_id in self._outgoing.get(current_id, []):
                    rel = self._relations.get(rel_id)
                    if rel and (not relation_types or rel.type in relation_types):
                        target = self._entities.get(rel.target_id)
                        if target:
                            results.append((target, rel, "outgoing"))
                            traverse(rel.target_id, depth + 1, visited)

            # Incoming
            if direction in ("incoming", "both"):
                for rel_id in self._incoming.get(current_id, []):
                    rel = self._relations.get(rel_id)
                    if rel and (not relation_types or rel.type in relation_types):
                        source = self._entities.get(rel.source_id)
                        if source:
                            results.append((source, rel, "incoming"))
                            traverse(rel.source_id, depth + 1, visited)

        traverse(entity_id, 1, set())
        return results

    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> Optional[List[Tuple[Entity, Relation]]]:
        """Find shortest path between two entities."""
        from collections import deque

        queue = deque([(source_id, [])])
        visited = {source_id}

        while queue:
            current_id, path = queue.popleft()
            if len(path) >= max_depth:
                continue

            if current_id == target_id:
                return path

            for rel_id in self._outgoing.get(current_id, []):
                rel = self._relations.get(rel_id)
                if rel and rel.target_id not in visited:
                    target_entity = self._entities.get(rel.target_id)
                    if target_entity:
                        visited.add(rel.target_id)
                        queue.append((rel.target_id, path + [(target_entity, rel)]))

        return None

    # --- Graph analysis ---

    async def get_subgraph(
        self,
        entity_ids: List[str],
        include_relations: bool = True,
    ) -> Dict[str, Any]:
        """Extract a subgraph."""
        entities = {eid: self._entities[eid] for eid in entity_ids if eid in self._entities}
        relations = []

        if include_relations:
            for eid in entity_ids:
                for rel_id in self._outgoing.get(eid, []):
                    rel = self._relations.get(rel_id)
                    if rel and rel.target_id in entity_ids:
                        relations.append(rel)
                for rel_id in self._incoming.get(eid, []):
                    rel = self._relations.get(rel_id)
                    if rel and rel.source_id in entity_ids:
                        relations.append(rel)

        return {
            "entities": list(entities.values()),
            "relations": relations,
        }

    async def get_centrality(self, entity_type: Optional[EntityType] = None) -> Dict[str, float]:
        """Calculate degree centrality for entities."""
        centrality = {}

        target_entities = self._entities
        if entity_type:
            target_entities = {eid: e for eid, e in self._entities.items() if e.type == entity_type}

        for eid in target_entities:
            out_degree = len(self._outgoing.get(eid, []))
            in_degree = len(self._incoming.get(eid, []))
            centrality[eid] = out_degree + in_degree

        # Normalize
        max_centrality = max(centrality.values()) if centrality else 1
        return {eid: c / max_centrality for eid, c in centrality.items()}

    async def detect_clusters(self, min_cluster_size: int = 3) -> List[List[str]]:
        """Detect clusters using connected components."""
        visited = set()
        clusters = []

        for eid in self._entities:
            if eid in visited:
                continue

            # BFS to find connected component
            cluster = []
            queue = [eid]
            visited.add(eid)

            while queue:
                current = queue.pop()
                cluster.append(current)

                # Check outgoing
                for rel_id in self._outgoing.get(current, []):
                    rel = self._relations.get(rel_id)
                    if rel and rel.target_id not in visited:
                        visited.add(rel.target_id)
                        queue.append(rel.target_id)

                # Check incoming
                for rel_id in self._incoming.get(current, []):
                    rel = self._relations.get(rel_id)
                    if rel and rel.source_id not in visited:
                        visited.add(rel.source_id)
                        queue.append(rel.source_id)

            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)

        return clusters


# Global instance
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph(config: Optional[KnowledgeGraphConfig] = None) -> KnowledgeGraph:
    """Get global knowledge graph instance."""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph(config)
    return _knowledge_graph