from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.config import Settings

logger = structlog.get_logger()


class ESPNFetcher:
    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def fetch_scoreboard(self) -> dict[str, Any]:
        resp = await self._client.get(
            self._settings.espn_scoreboard_url,
            timeout=self._settings.request_timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    async def fetch_game_summary(self, game_id: str) -> dict[str, Any]:
        resp = await self._client.get(
            self._settings.espn_summary_url,
            params={"event": game_id},
            timeout=self._settings.request_timeout_seconds,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def extract_live_game_ids(self, scoreboard: dict[str, Any]) -> list[str]:
        live_ids: list[str] = []
        for event in scoreboard.get("events", []):
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            status_name = (
                competitions[0].get("status", {}).get("type", {}).get("name", "")
            )
            if status_name in self._settings.live_statuses:
                live_ids.append(event["id"])
        return live_ids
