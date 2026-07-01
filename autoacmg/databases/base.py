"""Base class for all database connectors.

Provides common functionality for database queries including:
- Caching via SQLite
- Retry logic with exponential backoff
- Rate limiting
- Timeout handling
- Error logging
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests

from autoacmg.core.variant import Variant
from autoacmg.utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseDBConnector(ABC):
    """Abstract base class for database connectors.

    All database connectors inherit from this class to get consistent
    caching, retry, and error handling behavior.
    """

    NAME: str = "base"
    BASE_URL: str = ""
    RATE_LIMIT: float = 0.5  # seconds between requests

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        use_cache: bool = True,
    ) -> None:
        """Initialize the connector.

        Args:
            cache_dir: Directory for SQLite cache database.
            timeout: HTTP request timeout in seconds.
            max_retries: Number of retry attempts on failure.
            use_cache: Whether to use caching.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"AutoACMG/0.1.0 ({self.NAME} connector)",
            "Accept": "application/json",
        })

        # Cache
        self._cache: dict[str, Any] = {}
        self._cache_dir = cache_dir
        self._cache_db = None

        if use_cache and cache_dir:
            self._init_cache()

    def _init_cache(self) -> None:
        """Initialize SQLite cache."""
        try:
            import sqlite3
            import os
            os.makedirs(self._cache_dir, exist_ok=True)
            cache_path = f"{self._cache_dir}/{self.NAME}_cache.db"
            self._cache_db = sqlite3.connect(cache_path)
            self._cache_db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp REAL
                )
            """)
            self._cache_db.commit()
            logger.debug("Cache initialized: %s", cache_path)
        except Exception as e:
            logger.warning("Failed to initialize cache: %s", e)
            self._cache_db = None

    def _cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_from_cache(self, url: str) -> Optional[Any]:
        """Retrieve cached result."""
        if not self._cache_db:
            return None
        key = self._cache_key(url)
        try:
            cursor = self._cache_db.execute("SELECT value FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        except Exception as e:
            logger.debug("Cache read error: %s", e)
        return None

    def _save_to_cache(self, url: str, data: Any) -> None:
        """Save result to cache."""
        if not self._cache_db:
            return
        key = self._cache_key(url)
        try:
            import time as _time
            self._cache_db.execute(
                "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                (key, json.dumps(data), _time.time()),
            )
            self._cache_db.commit()
        except Exception as e:
            logger.debug("Cache write error: %s", e)

    def _fetch_url(
        self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Optional[dict]:
        """Fetch URL with retry logic and caching.

        Args:
            url: The URL to fetch.
            params: URL query parameters.
            headers: Additional headers.

        Returns:
            Parsed JSON response or None on failure.
        """
        # Check cache first
        if self.use_cache:
            cached = self._get_from_cache(url)
            if cached is not None:
                return cached

        for attempt in range(1, self.max_retries + 1):
            try:
                req_headers = dict(self.session.headers)
                if headers:
                    req_headers.update(headers)

                response = self.session.get(
                    url,
                    params=params,
                    headers=req_headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()
                self._save_to_cache(url, data)
                return data

            except requests.exceptions.Timeout:
                logger.warning("Timeout fetching %s (attempt %d/%d)", url, attempt, self.max_retries)
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else 0
                if status == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning("Rate limited, waiting %ds", wait_time)
                    time.sleep(wait_time)
                    continue
                elif status == 404:
                    logger.debug("Resource not found: %s", url)
                    return None
                else:
                    logger.warning("HTTP error %d for %s", status, url)
                    if attempt >= self.max_retries:
                        return None
            except requests.exceptions.RequestException as e:
                logger.warning("Request failed for %s: %s", url, e)
                if attempt >= self.max_retries:
                    return None

            # Exponential backoff
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)

        logger.error("All retries exhausted for %s", url)
        return None

    @abstractmethod
    def query(self, variant: Variant) -> Optional[dict]:
        """Query the database for variant information.

        Args:
            variant: The variant to query.

        Returns:
            Dictionary with database results, or None.
        """

    def close(self) -> None:
        """Close the connector and release resources."""
        self.session.close()
        if self._cache_db:
            self._cache_db.close()
