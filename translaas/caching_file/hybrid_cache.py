"""Hybrid cache provider for the Translaas SDK.

This module provides a two-level caching strategy combining memory cache (L1)
and file cache (L2) for optimal performance and offline support.
"""

from typing import Dict, Optional, Union

from translaas.caching.memory import MemoryCacheProvider
from translaas.caching_file.file_cache import FileCacheProvider
from translaas.models.options import HybridCacheOptions
from translaas.models.protocols import ITranslaasCacheProvider


class HybridCacheProvider(ITranslaasCacheProvider):
    """Hybrid cache provider combining memory (L1) and file (L2) caches.

    Provides a two-level caching strategy:
    - L1 (memory): Fast but limited in size, checked first
    - L2 (file): Slower but persistent, checked if L1 misses
    - Cache promotion: L2 hits are promoted to L1 for better performance

    Attributes:
        l1_cache: Memory cache provider (L1).
        l2_cache: File cache provider (L2).
        options: Hybrid cache configuration options.
        l1_hits: Number of L1 cache hits.
        l1_misses: Number of L1 cache misses.
        l2_hits: Number of L2 cache hits.
        l2_misses: Number of L2 cache misses.
    """

    def __init__(
        self,
        l2_cache: FileCacheProvider,
        options: Optional[HybridCacheOptions] = None,
        l1_cache: Optional[MemoryCacheProvider] = None,
    ) -> None:
        """Initialize the hybrid cache provider.

        Args:
            l2_cache: File cache provider for L2 (persistent storage).
            options: Optional hybrid cache configuration options.
            l1_cache: Optional memory cache provider for L1. If not provided,
                a new MemoryCacheProvider will be created based on options.
        """
        self.l2_cache = l2_cache
        self.options = options or HybridCacheOptions()

        # Initialize L1 cache
        if l1_cache is not None:
            self.l1_cache = l1_cache
        else:
            max_size = self.options.max_memory_cache_entries
            self.l1_cache = MemoryCacheProvider(
                max_size=max_size,
                enable_statistics=True,
            )

        # Statistics
        self.l1_hits = 0
        self.l1_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0

        # Warmup if enabled
        if self.options.warmup_on_startup:
            self._warmup()

    def get(self, key: str) -> Optional[str]:
        """Get a value from the cache using L1/L2 strategy.

        Strategy:
        1. Check L1 cache first (fast)
        2. If L1 miss, check L2 cache (slower but persistent)
        3. If L2 hit, promote to L1 for future access

        Args:
            key: The cache key.

        Returns:
            The cached value if found in L1 or L2, or None if not found.
        """
        # Try L1 first
        try:
            value = self.l1_cache.get(key)
            if value is not None:
                self.l1_hits += 1
                return value
            self.l1_misses += 1
        except Exception:
            # L1 error, continue to L2
            self.l1_misses += 1
            pass

        # L1 miss, try L2
        try:
            value = self.l2_cache.get(key)
            if value is not None:
                self.l2_hits += 1
                # Promote L2 hit to L1
                self._promote_to_l1(key, value)
                return value
            self.l2_misses += 1
            return None
        except Exception:
            # L2 error, return None
            self.l2_misses += 1
            return None

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set a value in both L1 and L2 caches.

        Args:
            key: The cache key.
            value: The value to cache.
            absolute_expiration_ms: Optional absolute expiration time in milliseconds.
            sliding_expiration_ms: Optional sliding expiration time in milliseconds.
        """
        # Set in L1
        try:
            self.l1_cache.set(key, value, absolute_expiration_ms, sliding_expiration_ms)
        except Exception:
            # L1 error, continue to L2
            pass

        # Set in L2
        try:
            self.l2_cache.set(key, value, absolute_expiration_ms, sliding_expiration_ms)
        except Exception:
            # L2 error, continue (at least L1 was updated)
            pass

    def remove(self, key: str) -> None:
        """Remove a value from both L1 and L2 caches.

        Args:
            key: The cache key to remove.
        """
        # Remove from L1
        try:
            self.l1_cache.remove(key)
        except Exception:
            pass

        # Remove from L2
        try:
            self.l2_cache.remove(key)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear all values from both L1 and L2 caches."""
        try:
            self.l1_cache.clear()
        except Exception:
            pass

        try:
            self.l2_cache.clear()
        except Exception:
            pass

        # Reset statistics
        self.l1_hits = 0
        self.l1_misses = 0
        self.l2_hits = 0
        self.l2_misses = 0

    def _promote_to_l1(self, key: str, value: str) -> None:
        """Promote an L2 hit to L1 cache.

        Args:
            key: The cache key.
            value: The cached value.
        """
        try:
            # Calculate expiration for L1 if configured
            absolute_expiration_ms = None
            if self.options.memory_cache_expiration is not None:
                absolute_expiration_ms = int(
                    self.options.memory_cache_expiration.total_seconds() * 1000
                )

            self.l1_cache.set(key, value, absolute_expiration_ms=absolute_expiration_ms)
        except Exception:
            # Promotion failed, continue (L2 still has the value)
            pass

    def _warmup(self) -> None:
        """Warm up the cache by loading entries from L2 into L1.

        This is called on startup if warmup_on_startup is enabled.
        Note: This is a basic implementation. A full warmup would require
        knowing which keys to warm up, which may require additional context.
        """
        # Basic warmup: cleanup expired entries in L2
        try:
            self.l2_cache.cleanup_expired()
        except Exception:
            pass

    def get_statistics(self) -> Dict[str, Union[int, float]]:
        """Get cache statistics for both L1 and L2.

        Returns:
            Dictionary with cache statistics including hits, misses, and hit rates.
        """
        l1_total = self.l1_hits + self.l1_misses
        l2_total = self.l2_hits + self.l2_misses
        # Total unique requests = L1 requests (L2 requests are subset of L1 misses)
        total_requests = l1_total

        l1_hit_rate = (self.l1_hits / l1_total * 100) if l1_total > 0 else 0.0
        l2_hit_rate = (self.l2_hits / l2_total * 100) if l2_total > 0 else 0.0
        # Overall hit rate = (L1 hits + L2 hits) / total unique requests
        overall_hit_rate = (
            ((self.l1_hits + self.l2_hits) / total_requests * 100) if total_requests > 0 else 0.0
        )

        # Get L1 cache statistics if available
        l1_stats = {}
        if hasattr(self.l1_cache, "get_statistics"):
            l1_stats = self.l1_cache.get_statistics()

        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "l1_hit_rate": round(l1_hit_rate, 2),
            "l2_hit_rate": round(l2_hit_rate, 2),
            "overall_hit_rate": round(overall_hit_rate, 2),
            "l1_size": l1_stats.get("size", 0),
            "l1_max_size": l1_stats.get("max_size", -1),
        }

    def cleanup_expired(self) -> int:
        """Clean up expired entries in both L1 and L2 caches.

        Returns:
            Total number of expired entries removed.
        """
        removed_count = 0

        # Cleanup L1
        try:
            if hasattr(self.l1_cache, "cleanup_expired"):
                removed_count += self.l1_cache.cleanup_expired()
        except Exception:
            pass

        # Cleanup L2
        try:
            removed_count += self.l2_cache.cleanup_expired()
        except Exception:
            pass

        return removed_count
