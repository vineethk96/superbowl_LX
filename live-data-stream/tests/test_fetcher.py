from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from app.config import Settings
from app.fetcher import ESPNFetcher


@pytest.fixture
def fetcher(settings: Settings) -> ESPNFetcher:
    client = httpx.AsyncClient()
    return ESPNFetcher(client, settings)


@respx.mock
async def test_fetch_scoreboard(fetcher: ESPNFetcher, settings: Settings) -> None:
    mock_data = {"events": []}
    respx.get(settings.espn_scoreboard_url).respond(200, json=mock_data)
    result = await fetcher.fetch_scoreboard()
    assert result == mock_data


@respx.mock
async def test_fetch_game_summary(fetcher: ESPNFetcher, settings: Settings) -> None:
    mock_data = {"boxscore": {}, "drives": {}}
    respx.get(settings.espn_summary_url).respond(200, json=mock_data)
    result = await fetcher.fetch_game_summary("12345")
    assert result == mock_data


@respx.mock
async def test_fetch_scoreboard_timeout(
    fetcher: ESPNFetcher, settings: Settings
) -> None:
    respx.get(settings.espn_scoreboard_url).side_effect = httpx.ReadTimeout(
        "timed out"
    )
    with pytest.raises(httpx.ReadTimeout):
        await fetcher.fetch_scoreboard()


@respx.mock
async def test_fetch_scoreboard_server_error(
    fetcher: ESPNFetcher, settings: Settings
) -> None:
    respx.get(settings.espn_scoreboard_url).respond(500)
    with pytest.raises(httpx.HTTPStatusError):
        await fetcher.fetch_scoreboard()


def test_extract_live_game_ids(
    fetcher: ESPNFetcher, scoreboard_response: dict[str, Any]
) -> None:
    ids = fetcher.extract_live_game_ids(scoreboard_response)
    assert ids == ["401547417"]


def test_extract_live_game_ids_empty(fetcher: ESPNFetcher) -> None:
    ids = fetcher.extract_live_game_ids({"events": []})
    assert ids == []


def test_extract_live_game_ids_halftime(fetcher: ESPNFetcher) -> None:
    scoreboard: dict[str, Any] = {
        "events": [
            {
                "id": "111",
                "competitions": [
                    {
                        "status": {
                            "type": {"name": "STATUS_HALFTIME", "description": "Halftime"}
                        }
                    }
                ],
            }
        ]
    }
    ids = fetcher.extract_live_game_ids(scoreboard)
    assert ids == ["111"]


def test_extract_live_game_ids_final(fetcher: ESPNFetcher) -> None:
    """Final games should NOT be considered live."""
    scoreboard: dict[str, Any] = {
        "events": [
            {
                "id": "222",
                "competitions": [
                    {
                        "status": {
                            "type": {"name": "STATUS_FINAL", "description": "Final"}
                        }
                    }
                ],
            }
        ]
    }
    ids = fetcher.extract_live_game_ids(scoreboard)
    assert ids == []
