from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ESPN API
    espn_scoreboard_url: str = (
        "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    )
    espn_summary_url: str = (
        "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
    )

    # Polling
    poll_interval_seconds: int = 60
    request_timeout_seconds: int = 10
    backoff_initial_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    backoff_max_seconds: float = 300.0

    # Live game status values from ESPN
    live_statuses: list[str] = [
        "STATUS_IN_PROGRESS",
        "STATUS_HALFTIME",
        "STATUS_END_PERIOD",
    ]

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # How many recent plays to include in events
    max_recent_plays: int = 10
