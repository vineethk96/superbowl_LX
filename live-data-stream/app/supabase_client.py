from __future__ import annotations

import asyncio
from typing import Any

import structlog
from supabase import Client, create_client

from app.config import Settings
from app.models import ToonPayload

logger = structlog.get_logger()

TABLE = "live_games"


class SupabaseStore:
    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(
            settings.supabase_url, settings.supabase_anon_key
        )

    def _upsert_sync(self, payload: ToonPayload) -> None:
        game = payload.game
        row: dict[str, Any] = {
            "game_id": game.game_id,
            "status": game.status,
            "quarter": game.quarter,
            "clock": game.clock,
            "home_score": game.home_team.score,
            "away_score": game.away_team.score,
            "toon_payload": payload.model_dump(mode="json"),
            "updated_at": payload.timestamp.isoformat(),
        }
        self._client.table(TABLE).upsert(row, on_conflict="game_id").execute()

    async def upsert_game(self, payload: ToonPayload) -> None:
        await asyncio.to_thread(self._upsert_sync, payload)
        logger.info("upserted_game", game_id=payload.game.game_id)

    def _get_all_sync(self) -> list[dict[str, Any]]:
        resp = self._client.table(TABLE).select("*").execute()
        return resp.data  # type: ignore[no-any-return]

    async def get_all_games(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_sync)
