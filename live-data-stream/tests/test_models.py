from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import EventData, GameData, TeamData, ToonPayload


def test_team_data() -> None:
    team = TeamData(id="12", name="Chiefs", score=21, stats={"totalYards": "310"})
    assert team.id == "12"
    assert team.score == 21
    assert team.stats["totalYards"] == "310"


def test_team_data_defaults() -> None:
    team = TeamData(id="1", name="T", score=0)
    assert team.stats == {}


def test_game_data() -> None:
    home = TeamData(id="1", name="Home", score=7)
    away = TeamData(id="2", name="Away", score=3)
    game = GameData(
        game_id="123",
        status="In Progress",
        quarter=2,
        clock="5:30",
        home_team=home,
        away_team=away,
    )
    assert game.game_id == "123"
    assert game.quarter == 2


def test_event_data() -> None:
    ev = EventData(
        event_id="5001",
        description="Pass for 15 yards",
        quarter=3,
        clock="7:23",
        possession="KC",
        win_probability=0.72,
    )
    assert ev.type == "play"
    assert ev.win_probability == 0.72


def test_event_data_win_prob_none() -> None:
    ev = EventData(
        event_id="5001",
        description="Pass",
        quarter=1,
        clock="10:00",
        possession="KC",
    )
    assert ev.win_probability is None


def test_toon_payload() -> None:
    home = TeamData(id="1", name="Home", score=7)
    away = TeamData(id="2", name="Away", score=3)
    game = GameData(
        game_id="123", status="In Progress", quarter=2, clock="5:30",
        home_team=home, away_team=away,
    )
    payload = ToonPayload(
        timestamp=datetime.now(UTC),
        game=game,
    )
    assert payload.type == "game_update"
    assert payload.source == "espn_live"
    assert payload.events == []


def test_toon_payload_json_serializable() -> None:
    home = TeamData(id="1", name="Home", score=7)
    away = TeamData(id="2", name="Away", score=3)
    game = GameData(
        game_id="123", status="In Progress", quarter=2, clock="5:30",
        home_team=home, away_team=away,
    )
    payload = ToonPayload(timestamp=datetime.now(UTC), game=game)
    data = payload.model_dump(mode="json")
    assert isinstance(data, dict)
    assert data["type"] == "game_update"
    assert isinstance(data["timestamp"], str)


def test_team_data_missing_required() -> None:
    with pytest.raises(ValidationError):
        TeamData(id="1", name="T")  # type: ignore[call-arg]  # missing score


def test_game_data_missing_required() -> None:
    with pytest.raises(ValidationError):
        GameData(game_id="123", status="X", quarter=1, clock="0:00")  # type: ignore[call-arg]  # missing teams
