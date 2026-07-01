"""SQLite-based caching layer for AutoACMG.

Provides persistent caching of database query results to avoid
redundant API calls and speed up subsequent analyses.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, Optional

from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class SQLiteCache:
    """SQLite-based cache for AutoACMG database queries.

    Stores query results with timestamps for TTL-based expiration.
    Thread-safe for single-writer scenarios.
    """

    def __init__(
        self,
        cache_path: str,
        default_ttl: int = 86400 * 7,  # 7 days default
    ) -> None:
        """Initialize the SQLite cache.

        Args:
            cache_path: Path to the SQLite database file.
            default_ttl: Default time-to-live in seconds.
        """
        self.cache_path = cache_path
        self.default_ttl = default_ttl
        os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the cache database."""
        self._conn = sqlite3.connect(self.cache_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                ttl INTEGER NOT NULL DEFAULT 604800
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_created
            ON cache_entries(created_at)
        """)
        self._conn.commit()
        logger.debug("Cache initialized at %s", self.cache_path)

    def get(self, key: str, source: str = "") -> Optional[Any]:
        """Retrieve a cached value.

        Args:
            key: Cache key.
            source: Optional source identifier to match.

        Returns:
            Cached value or None if not found/expired.
        """
        if self._conn is None:
            return None

        now = time.time()
        query = "SELECT value FROM cache_entries WHERE key = ?"
        params: list = [key]

        if source:
            query += " AND source = ?"
            params.append(source)

        cursor = self._conn.execute(query, params)
        row = cursor.fetchone()

        if row is None:
            return None

        value = json.loads(row[0])
        return value

    def set(
        self,
        key: str,
        value: Any,
        source: str = "",
        ttl: Optional[int] = None,
    ) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache (must be JSON-serializable).
            source: Source identifier.
            ttl: Time-to-live in seconds (overrides default).
        """
        if self._conn is None:
            return

        try:
            json_value = json.dumps(value)
            effective_ttl = ttl if ttl is not None else self.default_ttl
            self._conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries (key, value, source, created_at, ttl)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, json_value, source, time.time(), effective_ttl),
            )
            self._conn.commit()
        except (TypeError, ValueError) as e:
            logger.debug("Failed to cache value for key '%s': %s", key, e)

    def invalidate(self, key: str) -> bool:
        """Remove a key from the cache.

        Args:
            key: Cache key to remove.

        Returns:
            True if the key was found and removed.
        """
        if self._conn is None:
            return False

        self._conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        self._conn.commit()
        return self._conn.changes > 0

    def clear(self) -> int:
        """Clear all cached entries.

        Returns:
            Number of entries cleared.
        """
        if self._conn is None:
            return 0

        cursor = self._conn.execute("SELECT COUNT(*) FROM cache_entries")
        count = cursor.fetchone()[0]

        self._conn.execute("DELETE FROM cache_entries")
        self._conn.commit()
        logger.info("Cleared %d cache entries", count)
        return count

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed.
        """
        if self._conn is None:
            return 0

        now = time.time()
        self._conn.execute(
            "DELETE FROM cache_entries WHERE created_at + ttl < ?",
            (now,),
        )
        removed = self._conn.changes
        self._conn.commit()

        if removed > 0:
            logger.info("Cleaned up %d expired cache entries", removed)
        return removed

    def stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        if self._conn is None:
            return {}

        cursor = self._conn.execute("SELECT COUNT(*) FROM cache_entries")
        total = cursor.fetchone()[0]

        cursor = self._conn.execute(
            "SELECT source, COUNT(*) FROM cache_entries GROUP BY source"
        )
        by_source = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total_entries": total,
            "by_source": by_source,
            "cache_path": self.cache_path,
        }

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __del__(self) -> None:
        """Cleanup on destruction."""
        try:
            self.close()
        except Exception:
            pass
