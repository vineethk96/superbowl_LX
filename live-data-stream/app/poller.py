from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import structlog

from app.config import Settings
from app.fetcher import ESPNFetcher
from app.models import ToonPayload
from app.supabase_client import SupabaseStore
from app.transformer import transform_game

logger = structlog.get_logger()


class Poller:
    def __init__(
        self,
        fetcher: ESPNFetcher,
        store: SupabaseStore | None,
        settings: Settings,
    ) -> None:
        self._fetcher = fetcher
        self._store = store
        self._settings = settings
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._running = False
        self._consecutive_failures = 0
        self._latest_payloads: dict[str, ToonPayload] = {}

    @property
    def latest_payloads(self) -> dict[str, ToonPayload]:
        return dict(self._latest_payloads)

    def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("poller_started", interval=self._settings.poll_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("poller_stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            await self._poll_once()
            delay = self._get_delay()
            await asyncio.sleep(delay)

    async def _poll_once(self) -> None:
        if self._lock.locked():
            logger.warning("poll_skipped_overlap")
            return
        async with self._lock:
            await self._do_poll()

    async def _do_poll(self) -> None:
        try:
            scoreboard = await self._fetcher.fetch_scoreboard()
            live_ids = self._fetcher.extract_live_game_ids(scoreboard)
            logger.info("poll_cycle", live_games=len(live_ids))

            if not live_ids:
                self._consecutive_failures = 0
                return

            # Build a lookup of scoreboard events by ID
            events_by_id: dict[str, dict[str, Any]] = {}
            for event in scoreboard.get("events", []):
                events_by_id[event["id"]] = event

            for game_id in live_ids:
                try:
                    sb_event = events_by_id[game_id]
                    summary = await self._fetcher.fetch_game_summary(game_id)
                    payload = transform_game(sb_event, summary, self._settings)
                    self._latest_payloads[game_id] = payload

                    if self._store:
                        await self._store.upsert_game(payload)

                    logger.info(
                        "game_processed",
                        game_id=game_id,
                        status=payload.game.status,
                        score=f"{payload.game.home_team.score}-{payload.game.away_team.score}",
                    )
                except Exception:
                    logger.exception("game_failed", game_id=game_id)

            self._consecutive_failures = 0

        except Exception:
            self._consecutive_failures += 1
            logger.exception(
                "poll_cycle_failed",
                consecutive_failures=self._consecutive_failures,
            )

    def _get_delay(self) -> float:
        if self._consecutive_failures == 0:
            return float(self._settings.poll_interval_seconds)
        backoff = min(
            self._settings.backoff_initial_seconds
            * (self._settings.backoff_multiplier ** self._consecutive_failures),
            self._settings.backoff_max_seconds,
        )
        logger.info("backoff_delay", delay=backoff)
        return backoff
