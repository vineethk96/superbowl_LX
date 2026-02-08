from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import Settings
from app.fetcher import ESPNFetcher
from app.poller import Poller


@pytest.fixture
def mock_fetcher(
    settings: Settings,
    scoreboard_response: dict[str, Any],
    summary_response: dict[str, Any],
) -> ESPNFetcher:
    fetcher = MagicMock(spec=ESPNFetcher)
    fetcher.fetch_scoreboard = AsyncMock(return_value=scoreboard_response)
    fetcher.fetch_game_summary = AsyncMock(return_value=summary_response)
    fetcher.extract_live_game_ids = MagicMock(return_value=["401547417"])
    return fetcher


@pytest.fixture
def poller(mock_fetcher: ESPNFetcher, settings: Settings) -> Poller:
    return Poller(mock_fetcher, store=None, settings=settings)


async def test_do_poll_success(
    poller: Poller,
    mock_fetcher: ESPNFetcher,
) -> None:
    await poller._do_poll()
    assert "401547417" in poller.latest_payloads
    payload = poller.latest_payloads["401547417"]
    assert payload.game.game_id == "401547417"
    assert payload.game.home_team.name == "Kansas City Chiefs"


async def test_do_poll_no_live_games(
    poller: Poller,
    mock_fetcher: ESPNFetcher,
) -> None:
    mock_fetcher.extract_live_game_ids = MagicMock(return_value=[])
    await poller._do_poll()
    assert poller.latest_payloads == {}


async def test_per_game_failure_isolation(
    settings: Settings,
    scoreboard_response: dict[str, Any],
) -> None:
    """One game failing should not stop other games."""
    fetcher = MagicMock(spec=ESPNFetcher)
    fetcher.fetch_scoreboard = AsyncMock(return_value=scoreboard_response)
    fetcher.extract_live_game_ids = MagicMock(return_value=["401547417"])
    fetcher.fetch_game_summary = AsyncMock(side_effect=Exception("network error"))

    poller = Poller(fetcher, store=None, settings=settings)
    await poller._do_poll()
    # Should not crash; game just won't be in payloads
    assert "401547417" not in poller.latest_payloads
    assert poller._consecutive_failures == 0  # per-game failure, not cycle failure


async def test_cycle_failure_increments_counter(
    settings: Settings,
) -> None:
    fetcher = MagicMock(spec=ESPNFetcher)
    fetcher.fetch_scoreboard = AsyncMock(side_effect=Exception("total failure"))

    poller = Poller(fetcher, store=None, settings=settings)
    await poller._do_poll()
    assert poller._consecutive_failures == 1


def test_backoff_calculation(settings: Settings) -> None:
    fetcher = MagicMock(spec=ESPNFetcher)
    poller = Poller(fetcher, store=None, settings=settings)

    # No failures → normal interval
    assert poller._get_delay() == 60.0

    # 1 failure → initial * multiplier^1
    poller._consecutive_failures = 1
    expected = settings.backoff_initial_seconds * settings.backoff_multiplier
    assert poller._get_delay() == expected

    # Many failures → capped at max
    poller._consecutive_failures = 100
    assert poller._get_delay() == settings.backoff_max_seconds


async def test_start_stop(poller: Poller) -> None:
    poller.start()
    assert poller._running is True
    assert poller._task is not None
    await poller.stop()
    assert poller._running is False


async def test_store_upsert_called(
    mock_fetcher: ESPNFetcher,
    settings: Settings,
) -> None:
    store = MagicMock()
    store.upsert_game = AsyncMock()
    poller = Poller(mock_fetcher, store=store, settings=settings)

    await poller._do_poll()
    store.upsert_game.assert_called_once()
    payload = store.upsert_game.call_args[0][0]
    assert payload.game.game_id == "401547417"
