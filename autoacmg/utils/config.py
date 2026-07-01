"""Configuration management for AutoACMG.

Handles loading configuration from files and environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database connection settings."""

    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.5
    use_cache: bool = True
    cache_dir: Optional[str] = None

    def __init__(self, **data) -> None:
        super().__init__(**data)
        if self.cache_dir is None:
            self.cache_dir = os.path.expanduser("~/.autoacmg/cache")


class APIConfig(BaseModel):
    """API server settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False


class AppConfig(BaseModel):
    """Main application configuration."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def __init__(self, config_path: Optional[str] = None, **data) -> None:
        if config_path:
            data = self._load_yaml(config_path) or {}
        super().__init__(**data)

    @staticmethod
    def _load_yaml(path: str) -> Optional[dict[str, Any]]:
        """Load configuration from YAML file."""
        try:
            import yaml
            with open(path) as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, ImportError):
            return None


def get_config(config_path: Optional[str] = None) -> AppConfig:
    """Get application configuration.

    Args:
        config_path: Optional path to config YAML file.

    Returns:
        AppConfig instance.
    """
    env_config = {
        "log_level": os.environ.get("AUTOACMG_LOG_LEVEL", "INFO"),
    }

    config = AppConfig(config_path=config_path, **env_config)

    # Override with environment variables
    if os.environ.get("AUTOACMG_API_PORT"):
        config.api.port = int(os.environ["AUTOACMG_API_PORT"])
    if os.environ.get("AUTOACMG_API_HOST"):
        config.api.host = os.environ["AUTOACMG_API_HOST"]
    if os.environ.get("AUTOACMG_CACHE_DIR"):
        config.database.cache_dir = os.environ["AUTOACMG_CACHE_DIR"]

    return config
