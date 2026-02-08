from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from app.config import Settings
from app.models import EventData, GameData, TeamData, ToonPayload

logger = structlog.get_logger()

STAT_KEYS = frozenset(
    {
        "totalYards",
        "netPassingYards",
        "rushingYards",
        "turnovers",
        "fumblesLost",
        "interceptions",
        "firstDowns",
        "thirdDownEff",
        "fourthDownEff",
        "totalPenaltiesYards",
        "possessionTime",
        "completionAttempts",
        "sacksYardsLost",
        "rushingAttempts",
        "passingFirstDowns",
        "rushingFirstDowns",
        "totalDrives",
    }
)


def _find_competitor(
    competitors: list[dict[str, Any]], side: str
) -> dict[str, Any]:
    """Find the home or away competitor. Order is NOT guaranteed."""
    for comp in competitors:
        if comp.get("homeAway") == side:
            return comp
    raise ValueError(f"No competitor with homeAway={side!r}")


def _build_team_id_to_abbr(
    competitors: list[dict[str, Any]],
) -> dict[str, str]:
    """Map team ID → abbreviation for possession lookup."""
    mapping: dict[str, str] = {}
    for comp in competitors:
        team = comp.get("team", {})
        team_id = team.get("id", "")
        abbr = team.get("abbreviation", "")
        if team_id and abbr:
            mapping[team_id] = abbr
    return mapping


def _extract_team(
    competitor: dict[str, Any],
    boxscore_teams: list[dict[str, Any]],
) -> TeamData:
    team = competitor.get("team", {})
    side = competitor.get("homeAway", "")

    # Find matching boxscore team by homeAway
    stats: dict[str, str] = {}
    for bt in boxscore_teams:
        if bt.get("homeAway") == side:
            for stat in bt.get("statistics", []):
                if stat.get("name") in STAT_KEYS:
                    stats[stat["name"]] = stat.get("displayValue", "")
            break

    return TeamData(
        id=team.get("id", ""),
        name=team.get("displayName", ""),
        score=int(competitor.get("score", "0")),
        stats=stats,
    )


def _extract_plays(
    summary: dict[str, Any],
    team_id_to_abbr: dict[str, str],
    max_plays: int,
) -> list[dict[str, Any]]:
    """Get the most recent plays from drives (current + previous)."""
    drives = summary.get("drives", {})
    raw_plays: list[dict[str, Any]] = []

    # Current (live) drive first
    current = drives.get("current")
    if current and isinstance(current, dict):
        raw_plays.extend(current.get("plays", []))

    # Then previous drives in reverse order (most recent first)
    for drive in reversed(drives.get("previous", [])):
        raw_plays.extend(reversed(drive.get("plays", [])))
        if len(raw_plays) >= max_plays:
            break

    # Keep most recent N, preserving chronological order
    recent = raw_plays[:max_plays]
    recent.reverse()
    return recent


def _build_win_prob_lookup(
    summary: dict[str, Any],
) -> dict[str, float]:
    """Map playId → homeWinPercentage from the winprobability array."""
    lookup: dict[str, float] = {}
    for entry in summary.get("winprobability", []):
        play_id = entry.get("playId")
        pct = entry.get("homeWinPercentage")
        if play_id and pct is not None:
            lookup[str(play_id)] = float(pct)
    return lookup


def _play_to_event(
    play: dict[str, Any],
    team_id_to_abbr: dict[str, str],
    win_prob_lookup: dict[str, float],
) -> EventData:
    play_id = str(play.get("id", ""))
    period = play.get("period", {})
    clock = play.get("clock", {})
    start = play.get("start", {})
    poss_team_id = str(start.get("team", {}).get("id", ""))

    return EventData(
        event_id=play_id,
        type="play",
        description=play.get("text", ""),
        quarter=int(period.get("number", 0)),
        clock=clock.get("displayValue", "0:00"),
        possession=team_id_to_abbr.get(poss_team_id, ""),
        win_probability=win_prob_lookup.get(play_id),
    )


def transform_game(
    scoreboard_event: dict[str, Any],
    summary: dict[str, Any],
    settings: Settings,
) -> ToonPayload:
    """Transform ESPN scoreboard event + summary into a ToonPayload."""
    competition = scoreboard_event["competitions"][0]
    competitors = competition["competitors"]
    status = competition.get("status", {})

    # Team lookup for possession
    team_id_to_abbr = _build_team_id_to_abbr(competitors)

    # Boxscore teams (may be empty pre-game)
    boxscore = summary.get("boxscore", {})
    boxscore_teams: list[dict[str, Any]] = boxscore.get("teams", [])

    home_comp = _find_competitor(competitors, "home")
    away_comp = _find_competitor(competitors, "away")

    game = GameData(
        game_id=scoreboard_event["id"],
        status=status.get("type", {}).get("description", ""),
        quarter=int(status.get("period", 0)),
        clock=status.get("displayClock", "0:00"),
        home_team=_extract_team(home_comp, boxscore_teams),
        away_team=_extract_team(away_comp, boxscore_teams),
    )

    # Plays → events
    win_prob_lookup = _build_win_prob_lookup(summary)
    raw_plays = _extract_plays(summary, team_id_to_abbr, settings.max_recent_plays)
    events = [
        _play_to_event(p, team_id_to_abbr, win_prob_lookup) for p in raw_plays
    ]

    return ToonPayload(
        timestamp=datetime.now(UTC),
        game=game,
        events=events,
    )
