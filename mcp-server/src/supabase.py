"""Supabase client for querying NFL game data."""

from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import Client, create_client

from .config import Settings


class SupabaseClient:
    """Client for querying NFL game data from Supabase."""

    def __init__(self, settings: Settings):
        """Initialize the Supabase client.

        Args:
            settings: Configuration settings with Supabase credentials
        """
        self._client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)

    def fetch_all_games(self) -> list[dict[str, Any]]:
        """Get all games with basic info.

        Returns:
            List of game summaries with game_id, status, scores, and timestamps
        """
        response = (
            self._client.table("live_games")
            .select("game_id, status, quarter, clock, home_score, away_score, updated_at")
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data

    def fetch_game_by_id(self, game_id: str) -> dict[str, Any] | None:
        """Get full game details including TOON payload.

        Args:
            game_id: ESPN game ID

        Returns:
            Complete game record or None if not found
        """
        response = self._client.table("live_games").select("*").eq("game_id", game_id).execute()
        return response.data[0] if response.data else None

    def fetch_live_games(self) -> list[dict[str, Any]]:
        """Get games currently in progress.

        Returns:
            List of live games with current scores and status
        """
        live_statuses = ["In Progress", "Halftime"]
        response = (
            self._client.table("live_games")
            .select("game_id, status, quarter, clock, home_score, away_score, updated_at")
            .in_("status", live_statuses)
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data

    def fetch_games_by_status(self, status: str) -> list[dict[str, Any]]:
        """Filter games by status.

        Args:
            status: Game status to filter by (e.g., "In Progress", "Final", "Scheduled")

        Returns:
            List of matching games
        """
        response = (
            self._client.table("live_games")
            .select("game_id, status, quarter, clock, home_score, away_score, updated_at")
            .eq("status", status)
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data

    def fetch_recent_games(self, minutes: int = 5) -> list[dict[str, Any]]:
        """Get games updated in the last N minutes.

        Args:
            minutes: Time window in minutes (default: 5)

        Returns:
            List of recently updated games
        """
        cutoff = datetime.now(UTC) - timedelta(minutes=minutes)
        response = (
            self._client.table("live_games")
            .select("game_id, status, quarter, clock, home_score, away_score, updated_at")
            .gt("updated_at", cutoff.isoformat())
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data

    def fetch_team_stats(self, game_id: str, team: str) -> dict[str, Any]:
        """Extract team stats from TOON payload.

        Args:
            game_id: ESPN game ID
            team: Team to get stats for ("home" or "away")

        Returns:
            Dict with team name, score, and stats, or error dict
        """
        game = self.fetch_game_by_id(game_id)
        if not game or "toon_payload" not in game:
            return {"error": "Game not found"}

        payload = game["toon_payload"]
        team_key = f"{team}_team"  # home_team or away_team

        if "game" not in payload or team_key not in payload["game"]:
            return {"error": f"Team '{team}' not found"}

        team_data = payload["game"][team_key]
        return {
            "name": team_data.get("name"),
            "abbreviation": team_data.get("abbreviation"),
            "score": team_data.get("score"),
            "stats": team_data.get("stats", {}),
        }

    def fetch_play_by_play(self, game_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent plays for a game.

        Args:
            game_id: ESPN game ID
            limit: Maximum number of plays to return (default: 10)

        Returns:
            List of EventData objects with play descriptions and metadata
        """
        game = self.fetch_game_by_id(game_id)
        if not game or "toon_payload" not in game:
            return []

        payload = game["toon_payload"]
        events = payload.get("events", [])
        return events[:limit]
