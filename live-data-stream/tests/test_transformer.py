from __future__ import annotations

import copy
from typing import Any

from app.config import Settings
from app.transformer import transform_game


def test_game_id_mapped(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    assert payload.game.game_id == "401547417"


def test_game_status_fields(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    assert payload.game.status == "In Progress"
    assert payload.game.quarter == 3
    assert payload.game.clock == "7:23"


def test_home_team(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    home = payload.game.home_team
    assert home.id == "12"
    assert home.name == "Kansas City Chiefs"
    assert home.score == 21
    assert isinstance(home.score, int)


def test_away_team(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    away = payload.game.away_team
    assert away.id == "22"
    assert away.name == "Philadelphia Eagles"
    assert away.score == 14
    assert isinstance(away.score, int)


def test_score_cast_from_string(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    """Scores come as strings from ESPN — must be cast to int."""
    payload = transform_game(scoreboard_event, summary_response, settings)
    assert payload.game.home_team.score == 21
    assert payload.game.away_team.score == 14


def test_competitor_order_independence(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    """Competitor array order is NOT guaranteed — must use homeAway field."""
    event = copy.deepcopy(scoreboard_event)
    # Reverse competitor order
    event["competitions"][0]["competitors"].reverse()

    payload = transform_game(event, summary_response, settings)
    assert payload.game.home_team.name == "Kansas City Chiefs"
    assert payload.game.away_team.name == "Philadelphia Eagles"


def test_home_team_stats_filtered(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    stats = payload.game.home_team.stats
    assert stats["totalYards"] == "310"
    assert stats["rushingYards"] == "88"
    assert stats["netPassingYards"] == "222"
    assert stats["turnovers"] == "0"
    assert stats["thirdDownEff"] == "5-10"
    # irrelevantStat should NOT be present
    assert "irrelevantStat" not in stats


def test_away_team_stats_filtered(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    stats = payload.game.away_team.stats
    assert stats["totalYards"] == "285"
    assert "irrelevantStat" not in stats


def test_events_extracted(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    assert len(payload.events) > 0
    # Current drive play should be present
    play_ids = [e.event_id for e in payload.events]
    assert "5001" in play_ids


def test_event_fields(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    # Find the current drive play
    ev = next(e for e in payload.events if e.event_id == "5001")
    assert ev.type == "play"
    assert ev.description == "P.Mahomes pass to T.Kelce for 15 yards"
    assert ev.quarter == 3
    assert ev.clock == "7:23"
    assert ev.possession == "KC"


def test_win_probability_mapped(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    ev = next(e for e in payload.events if e.event_id == "5001")
    assert ev.win_probability == 0.72


def test_win_probability_missing(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    """Plays not in winprobability array should have None."""
    summary = copy.deepcopy(summary_response)
    summary["winprobability"] = []  # No win prob data
    payload = transform_game(scoreboard_event, summary, settings)
    for ev in payload.events:
        assert ev.win_probability is None


def test_empty_drives(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    """No drives → empty events list."""
    summary = copy.deepcopy(summary_response)
    summary["drives"] = {}
    payload = transform_game(scoreboard_event, summary, settings)
    assert payload.events == []


def test_payload_defaults(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    payload = transform_game(scoreboard_event, summary_response, settings)
    assert payload.type == "game_update"
    assert payload.source == "espn_live"
    assert payload.timestamp is not None


def test_max_plays_respected(
    scoreboard_event: dict[str, Any],
    settings: Settings,
) -> None:
    """Should respect max_recent_plays limit."""
    # Build a summary with many plays
    plays = [
        {
            "id": str(i),
            "text": f"Play {i}",
            "period": {"number": 1},
            "clock": {"displayValue": "10:00"},
            "start": {"team": {"id": "12"}},
        }
        for i in range(20)
    ]
    summary: dict[str, Any] = {
        "boxscore": {"teams": []},
        "drives": {
            "current": {"plays": plays},
        },
        "winprobability": [],
    }
    settings.max_recent_plays = 5
    payload = transform_game(scoreboard_event, summary, settings)
    assert len(payload.events) == 5


def test_boxscore_order_independence(
    scoreboard_event: dict[str, Any],
    summary_response: dict[str, Any],
    settings: Settings,
) -> None:
    """Boxscore teams[] order is NOT guaranteed — must match by homeAway."""
    summary = copy.deepcopy(summary_response)
    summary["boxscore"]["teams"].reverse()

    payload = transform_game(scoreboard_event, summary, settings)
    assert payload.game.home_team.stats["totalYards"] == "310"
    assert payload.game.away_team.stats["totalYards"] == "285"
