"""BackendRegistry for pluggable vector backends.

Provides entry-point discovery via `importlib.metadata` group `mem20.vector_backends`
and explicit registration for built-in backends.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from memory_engine.backends.base import BackendConfig, VectorBackend


class BackendRegistry:
    """Thread-safe registry for vector backend factories.

    Backends can be registered explicitly or discovered via entry-points
    in the `mem20.vector_backends` group.

    Example entry-point in pyproject.toml:
        [project.entry-points."mem20.vector_backends"]
        faiss = "memory_engine.backends.faiss_backend:FaissBackend"
        pgvector = "memory_engine.backends.pgvector_backend:PgVectorBackend"
    """

    _instance: Optional[BackendRegistry] = None
    _lock = threading.Lock()

    def __new__(cls) -> BackendRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._factories: dict[str, Callable[[BackendConfig], VectorBackend]] = {}
        self._initialized = True
        self._discover_entry_points()

    def _discover_entry_points(self) -> None:
        """Discover backends via importlib.metadata entry-points."""
        try:
            from importlib.metadata import entry_points
        except ImportError:
            from importlib_metadata import entry_points  # type: ignore

        for ep in entry_points(group="mem20.vector_backends"):
            try:
                factory = ep.load()
                self.register(ep.name, factory)
            except Exception as e:
                # Log but don't fail — optional backends may have missing deps
                import logging
                logging.getLogger(__name__).debug(
                    "Failed to load backend entry-point %s: %s", ep.name, e
                )

    def register(
        self,
        name: str,
        factory: Callable[[BackendConfig], VectorBackend],
    ) -> None:
        """Register a backend factory.

        Args:
            name: Backend identifier (e.g., "faiss", "qdrant").
            factory: Callable that takes a BackendConfig and returns a VectorBackend instance.

        Raises:
            ValueError: If name already registered.
        """
        if name in self._factories:
            raise ValueError(f"Backend '{name}' already registered")
        self._factories[name] = factory

    def get(self, name: str) -> Callable[[BackendConfig], VectorBackend]:
        """Get a backend factory by name.

        Args:
            name: Backend identifier.

        Returns:
            Factory callable.

        Raises:
            KeyError: If backend not found.
        """
        try:
            return self._factories[name]
        except KeyError:
            available = ", ".join(sorted(self._factories.keys()))
            raise KeyError(
                f"Unknown backend '{name}'. Available: {available}"
            ) from None

    def create(self, config: BackendConfig) -> VectorBackend:
        """Create a backend instance from config.

        Args:
            config: BackendConfig with `backend` field set to the backend name.

        Returns:
            Initialized VectorBackend instance (not yet initialized).

        Raises:
            KeyError: If backend not registered.
        """
        factory = self.get(config.backend)
        return factory(config)

    def list(self) -> list[str]:
        """List all registered backend names."""
        return sorted(self._factories.keys())

    @property
    def default(self) -> str:
        """Default backend name (first registered, or 'faiss' if available)."""
        if "faiss" in self._factories:
            return "faiss"
        if "memory" in self._factories:
            return "memory"
        if self._factories:
            return next(iter(self._factories))
        raise RuntimeError("No backends registered")

    def __contains__(self, name: str) -> bool:
        return name in self._factories


# Global singleton instance
registry = BackendRegistry()

# Convenience functions
register = registry.register
get = registry.get
create = registry.create
list_backends = registry.list