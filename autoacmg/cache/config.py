"""Cache configuration for AutoACMG."""

from __future__ import annotations

import os
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Cache configuration settings."""

    enabled: bool = True
    cache_dir: str = Field(
        default_factory=lambda: os.path.expanduser("~/.autoacmg/cache")
    )
    default_ttl: int = 604800  # 7 days
    max_entries: int = 100000
    cleanup_on_start: bool = False

    def get_cache_path(self, source: str = "") -> str:
        """Get cache file path for a source.

        Args:
            source: Database source name.

        Returns:
            Path to the cache file.
        """
        if source:
            return os.path.join(self.cache_dir, f"{source}_cache.db")
        return os.path.join(self.cache_dir, "autoacmg_cache.db")
