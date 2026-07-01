"""AutoACMG FastAPI server.

Provides a REST API for variant annotation and classification.
Serves a professional web UI for clinical variant classification.
"""

from __future__ import annotations

import logging
import pathlib
from contextlib import asynccontextmanager
from typing import Optional

from autoacmg.core.classifier import ACMGClassifier
from autoacmg.core.evidence import EvidenceGatherer
from autoacmg.utils.logging_config import setup_logging
from autoacmg.utils.config import get_config

logger = logging.getLogger(__name__)

# Resolve web directory relative to this package
_WEB_DIR = pathlib.Path(__file__).resolve().parent.parent / "web"


# Global state
_app_state: dict = {
    "classifier": None,
    "gatherer": None,
    "startup_time": None,
}


@asynccontextmanager
async def lifespan(app):
    """Application lifespan handler."""
    from datetime import datetime

    setup_logging(level="INFO")
    _app_state["startup_time"] = datetime.utcnow().isoformat()
    _app_state["classifier"] = ACMGClassifier()
    _app_state["gatherer"] = EvidenceGatherer()
    logger.info("AutoACMG server started")
    yield
    logger.info("AutoACMG server shutting down")


def create_app() -> "fastapi.FastAPI":
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    import fastapi
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    app = fastapi.FastAPI(
        title="AutoACMG API",
        description="Automated ACMG/AMP variant classification service",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Import and register API routes
    from autoacmg.api.routes import router
    app.include_router(router, prefix="/api/v1")

    # Serve static UI assets (CSS, JS)
    if (_WEB_DIR / "styles.css").exists():
        app.mount("/static", StaticFiles(directory=str(_WEB_DIR)), name="static")

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "version": "0.1.0",
            "startup_time": _app_state.get("startup_time"),
        }

    @app.get("/")
    async def root():
        """Serve the web UI index page."""
        index_path = _WEB_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        # Fallback JSON response if UI files are missing
        return {
            "name": "AutoACMG API",
            "version": "0.1.0",
            "docs": "/docs",
            "endpoints": {
                "annotate": "/api/v1/annotate",
                "batch": "/api/v1/batch",
                "status": "/api/v1/status",
                "health": "/health",
            },
        }

    return app


# Module-level app for uvicorn CLI (e.g. `uvicorn autoacmg.api.server:app`)
app = create_app()


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 1,
    reload: bool = False,
) -> None:
    """Run the AutoACMG API server.

    Args:
        host: Bind host.
        port: Bind port.
        workers: Number of worker processes.
        reload: Enable auto-reload for development.
    """
    import uvicorn

    server_app = create_app()
    uvicorn.run(
        server_app,
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info",
    )
