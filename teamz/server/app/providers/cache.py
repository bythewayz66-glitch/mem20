"""Prompt caching system for repeated context (Anthropic / OpenAI)."""

from __future__ import annotations

import hashlib
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..models import PromptCacheConfig


@dataclass
class CacheEntry:
    """A cached prompt-response pair."""
    key: str
    prompt_hash: str
    messages: List[Dict[str, Any]]
    response: Dict[str, Any]
    provider: str
    model: str
    created_at: float
    expires_at: float
    token_count: int
    hit_count: int = 0


class PromptCache:
    """In-memory prompt cache with TTL and size limits."""

    def __init__(self, config: Optional[PromptCacheConfig] = None) -> None:
        self.config = config or PromptCacheConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._total_size_bytes = 0

    def _hash_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Create a hash of the messages for cache key."""
        # Normalize messages for consistent hashing
        normalized = []
        for msg in messages:
            normalized.append({
                "role": msg.get("role", ""),
                "content": msg.get("content", ""),
            })
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _make_key(self, provider: str, model: str, messages: List[Dict[str, Any]]) -> str:
        """Create a cache key."""
        prompt_hash = self._hash_messages(messages)
        return f"{self.config.cache_key_prefix}:{provider}:{model}:{prompt_hash}"

    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Rough token estimation."""
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return total_chars // 4  # Rough approximation

    async def get(self, provider: str, model: str, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        if not self.config.enabled:
            return None

        # Check if provider supports caching
        if provider not in self.config.cache_providers:
            return None

        # Check minimum token threshold
        token_count = self._estimate_tokens(messages)
        if token_count < self.config.min_tokens_for_caching:
            return None

        key = self._make_key(provider, model, messages)
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            # Check expiration
            if time.time() > entry.expires_at:
                await self._remove_entry(key)
                return None

            # Cache hit
            entry.hit_count += 1
            return entry.response

    async def set(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        response: Dict[str, Any],
    ) -> None:
        """Cache a prompt-response pair."""
        if not self.config.enabled:
            return

        if provider not in self.config.cache_providers:
            return

        token_count = self._estimate_tokens(messages)
        if token_count < self.config.min_tokens_for_caching:
            return

        key = self._make_key(provider, model, messages)
        now = time.time()
        expires_at = now + self.config.cache_ttl_seconds

        async with self._lock:
            # Check size limit
            entry_size = len(json.dumps(response).encode())
            max_size = self.config.max_cache_size_mb * 1024 * 1024

            # Evict old entries if needed
            while self._total_size_bytes + entry_size > max_size and self._cache:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
                await self._remove_entry(oldest_key)

            entry = CacheEntry(
                key=key,
                prompt_hash=self._hash_messages(messages),
                messages=messages,
                response=response,
                provider=provider,
                model=model,
                created_at=now,
                expires_at=expires_at,
                token_count=token_count,
            )
            self._cache[key] = entry
            self._total_size_bytes += entry_size

    async def _remove_entry(self, key: str) -> None:
        """Remove an entry from cache."""
        entry = self._cache.pop(key, None)
        if entry:
            self._total_size_bytes -= len(json.dumps(entry.response).encode())

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._total_size_bytes = 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_hits = sum(e.hit_count for e in self._cache.values())
            return {
                "entries": len(self._cache),
                "total_size_mb": self._total_size_bytes / (1024 * 1024),
                "max_size_mb": self.config.max_cache_size_mb,
                "total_hits": total_hits,
                "hit_rate": total_hits / max(len(self._cache), 1),
            }

    async def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        now = time.time()
        removed = 0
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry.expires_at
            ]
            for key in expired_keys:
                await self._remove_entry(key)
                removed += 1
        return removed


# Global cache instance
_prompt_cache: Optional[PromptCache] = None


def get_prompt_cache(config: Optional[PromptCacheConfig] = None) -> PromptCache:
    """Get the global prompt cache instance."""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCache(config)
    return _prompt_cache


async def periodic_cleanup(cache: PromptCache, interval_seconds: int = 300) -> None:
    """Periodically clean up expired cache entries."""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            removed = await cache.cleanup_expired()
            if removed > 0:
                print(f"[PromptCache] Cleaned up {removed} expired entries")
        except Exception as e:
            print(f"[PromptCache] Cleanup error: {e}")