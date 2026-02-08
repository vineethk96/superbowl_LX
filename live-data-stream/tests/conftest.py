from __future__ import annotations

from typing import Any

import pytest

from app.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        supabase_url="https://fake.supabase.co",
        supabase_anon_key="fake-key",
        max_recent_plays=5,
    )


@pytest.fixture
def scoreboard_response() -> dict[str, Any]:
    """Minimal ESPN scoreboard response with one live game."""
    return {
        "events": [
            {
                "id": "401547417",
                "competitions": [
                    {
                        "status": {
                            "period": 3,
                            "displayClock": "7:23",
                            "type": {
                                "name": "STATUS_IN_PROGRESS",
                                "description": "In Progress",
                            },
                        },
                        "competitors": [
                            {
                                "homeAway": "home",
                                "score": "21",
                                "team": {
                                    "id": "12",
                                    "displayName": "Kansas City Chiefs",
                                    "abbreviation": "KC",
                                },
                            },
                            {
                                "homeAway": "away",
                                "score": "14",
                                "team": {
                                    "id": "22",
                                    "displayName": "Philadelphia Eagles",
                                    "abbreviation": "PHI",
                                },
                            },
                        ],
                    }
                ],
            },
            {
                "id": "401547418",
                "competitions": [
                    {
                        "status": {
                            "period": 0,
                            "displayClock": "0:00",
                            "type": {
                                "name": "STATUS_SCHEDULED",
                                "description": "Scheduled",
                            },
                        },
                        "competitors": [
                            {
                                "homeAway": "home",
                                "score": "0",
                                "team": {
                                    "id": "1",
                                    "displayName": "Team A",
                                    "abbreviation": "TA",
                                },
                            },
                            {
                                "homeAway": "away",
                                "score": "0",
                                "team": {
                                    "id": "2",
                                    "displayName": "Team B",
                                    "abbreviation": "TB",
                                },
                            },
                        ],
                    }
                ],
            },
        ]
    }


@pytest.fixture
def summary_response() -> dict[str, Any]:
    """Minimal ESPN summary response with boxscore, drives, and winprobability."""
    return {
        "boxscore": {
            "teams": [
                {
                    "homeAway": "away",
                    "team": {"id": "22", "abbreviation": "PHI"},
                    "statistics": [
                        {"name": "totalYards", "displayValue": "285"},
                        {"name": "rushingYards", "displayValue": "102"},
                        {"name": "netPassingYards", "displayValue": "183"},
                        {"name": "turnovers", "displayValue": "1"},
                        {"name": "firstDowns", "displayValue": "15"},
                        {"name": "irrelevantStat", "displayValue": "999"},
                    ],
                },
                {
                    "homeAway": "home",
                    "team": {"id": "12", "abbreviation": "KC"},
                    "statistics": [
                        {"name": "totalYards", "displayValue": "310"},
                        {"name": "rushingYards", "displayValue": "88"},
                        {"name": "netPassingYards", "displayValue": "222"},
                        {"name": "turnovers", "displayValue": "0"},
                        {"name": "firstDowns", "displayValue": "18"},
                        {"name": "thirdDownEff", "displayValue": "5-10"},
                    ],
                },
            ]
        },
        "drives": {
            "current": {
                "plays": [
                    {
                        "id": "5001",
                        "text": "P.Mahomes pass to T.Kelce for 15 yards",
                        "period": {"number": 3},
                        "clock": {"displayValue": "7:23"},
                        "start": {"team": {"id": "12"}},
                    },
                ]
            },
            "previous": [
                {
                    "plays": [
                        {
                            "id": "4001",
                            "text": "J.Hurts rush for 8 yards",
                            "period": {"number": 3},
                            "clock": {"displayValue": "9:45"},
                            "start": {"team": {"id": "22"}},
                        },
                        {
                            "id": "4002",
                            "text": "J.Hurts pass incomplete",
                            "period": {"number": 3},
                            "clock": {"displayValue": "9:10"},
                            "start": {"team": {"id": "22"}},
                        },
                    ]
                },
                {
                    "plays": [
                        {
                            "id": "3001",
                            "text": "P.Mahomes pass to R.Rice for 22 yards",
                            "period": {"number": 2},
                            "clock": {"displayValue": "0:45"},
                            "start": {"team": {"id": "12"}},
                        },
                    ]
                },
            ],
        },
        "winprobability": [
            {"playId": "5001", "homeWinPercentage": 0.72},
            {"playId": "4002", "homeWinPercentage": 0.65},
            {"playId": "4001", "homeWinPercentage": 0.60},
            {"playId": "3001", "homeWinPercentage": 0.58},
        ],
    }


@pytest.fixture
def scoreboard_event(scoreboard_response: dict[str, Any]) -> dict[str, Any]:
    """The live event extracted from the scoreboard."""
    return scoreboard_response["events"][0]
