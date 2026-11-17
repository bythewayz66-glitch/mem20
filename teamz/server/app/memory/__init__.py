"""Memory & Knowledge subsystem for Phase 10."""

from .vector import VectorMemory, VectorMemoryConfig, get_vector_memory
from .episodic import EpisodicMemory, EpisodicMemoryConfig, get_episodic_memory
from .semantic import SemanticMemory, SemanticMemoryConfig, get_semantic_memory
from .consolidation import MemoryConsolidator, ConsolidationConfig, get_consolidator
from .knowledge_graph import KnowledgeGraph, KnowledgeGraphConfig, get_knowledge_graph
from .rag import GitHistoryRAG, RAGConfig, get_git_history_rag
from .manager import MemoryManager, MemoryManagerConfig, get_memory_manager

__all__ = [
    "VectorMemory", "VectorMemoryConfig", "get_vector_memory",
    "EpisodicMemory", "EpisodicMemoryConfig", "get_episodic_memory",
    "SemanticMemory", "SemanticMemoryConfig", "get_semantic_memory",
    "MemoryConsolidator", "ConsolidationConfig", "get_consolidator",
    "KnowledgeGraph", "KnowledgeGraphConfig", "get_knowledge_graph",
    "GitHistoryRAG", "RAGConfig", "get_git_history_rag",
    "MemoryManager", "MemoryManagerConfig", "get_memory_manager",
]