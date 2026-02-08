from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from fastapi import FastAPI

from app.config import Settings
from app.fetcher import ESPNFetcher
from app.poller import Poller
from app.supabase_client import SupabaseStore


def _configure_logging(settings: Settings) -> None:
    import logging

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.log_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Convert log level string to int
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


_poller: Poller | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _poller  # noqa: PLW0603

    settings = Settings()
    _configure_logging(settings)
    logger = structlog.get_logger()

    async with httpx.AsyncClient() as client:
        fetcher = ESPNFetcher(client, settings)

        store: SupabaseStore | None = None
        if settings.supabase_url and settings.supabase_anon_key:
            store = SupabaseStore(settings)
            logger.info("supabase_connected")
        else:
            logger.warning("supabase_not_configured")

        _poller = Poller(fetcher, store, settings)
        _poller.start()

        yield

        await _poller.stop()


app = FastAPI(title="NFL Live Poller", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@app.get("/games")
async def games() -> dict[str, Any]:
    if _poller is None:
        return {"games": []}
    payloads = _poller.latest_payloads
    return {
        "games": [p.model_dump(mode="json") for p in payloads.values()],
    }
