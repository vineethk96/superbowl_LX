from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TeamData(BaseModel):
    id: str
    name: str
    score: int
    stats: dict[str, str] = Field(default_factory=dict)


class GameData(BaseModel):
    game_id: str
    status: str
    quarter: int
    clock: str
    home_team: TeamData
    away_team: TeamData


class EventData(BaseModel):
    event_id: str
    type: str = "play"
    description: str
    quarter: int
    clock: str
    possession: str
    win_probability: float | None = None


class ToonPayload(BaseModel):
    type: str = "game_update"
    source: str = "espn_live"
    timestamp: datetime
    game: GameData
    events: list[EventData] = Field(default_factory=list)
