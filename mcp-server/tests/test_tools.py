"""Tests for MCP tool handlers."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.config import Settings
from src.tools import handle_tool_call


@pytest.fixture
def mock_settings():
    """Mock Settings object."""
    return Settings(
        supabase_url="https://test.supabase.co", supabase_anon_key="test-key"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock SupabaseClient."""
    with patch("src.tools.SupabaseClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.mark.asyncio
async def test_get_all_games(mock_settings, mock_supabase_client):
    """Test get_all_games tool."""
    # Setup mock response
    expected_games = [
        {
            "game_id": "401772988",
            "status": "Final",
            "quarter": 4,
            "clock": "0:00",
            "home_score": 24,
            "away_score": 21,
        }
    ]
    mock_supabase_client.fetch_all_games.return_value = expected_games

    # Call tool
    result = await handle_tool_call("get_all_games", {}, mock_settings)
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_games
    mock_supabase_client.fetch_all_games.assert_called_once()


@pytest.mark.asyncio
async def test_get_game_details(mock_settings, mock_supabase_client):
    """Test get_game_details tool."""
    # Setup mock response
    expected_game = {
        "game_id": "401772988",
        "status": "Final",
        "toon_payload": {"game": {"status": "Final"}},
    }
    mock_supabase_client.fetch_game_by_id.return_value = expected_game

    # Call tool
    result = await handle_tool_call(
        "get_game_details", {"game_id": "401772988"}, mock_settings
    )
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_game
    mock_supabase_client.fetch_game_by_id.assert_called_once_with("401772988")


@pytest.mark.asyncio
async def test_get_live_games(mock_settings, mock_supabase_client):
    """Test get_live_games tool."""
    # Setup mock response
    expected_games = [
        {
            "game_id": "401772988",
            "status": "In Progress",
            "quarter": 2,
            "clock": "5:23",
        }
    ]
    mock_supabase_client.fetch_live_games.return_value = expected_games

    # Call tool
    result = await handle_tool_call("get_live_games", {}, mock_settings)
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_games
    mock_supabase_client.fetch_live_games.assert_called_once()


@pytest.mark.asyncio
async def test_get_games_by_status(mock_settings, mock_supabase_client):
    """Test get_games_by_status tool."""
    # Setup mock response
    expected_games = [{"game_id": "401772988", "status": "Final"}]
    mock_supabase_client.fetch_games_by_status.return_value = expected_games

    # Call tool
    result = await handle_tool_call(
        "get_games_by_status", {"status": "Final"}, mock_settings
    )
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_games
    mock_supabase_client.fetch_games_by_status.assert_called_once_with("Final")


@pytest.mark.asyncio
async def test_get_recent_updates(mock_settings, mock_supabase_client):
    """Test get_recent_updates tool with default minutes."""
    # Setup mock response
    expected_games = [{"game_id": "401772988", "updated_at": "2026-02-08T20:00:00"}]
    mock_supabase_client.fetch_recent_games.return_value = expected_games

    # Call tool with default minutes
    result = await handle_tool_call("get_recent_updates", {}, mock_settings)
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_games
    mock_supabase_client.fetch_recent_games.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_get_recent_updates_custom_minutes(mock_settings, mock_supabase_client):
    """Test get_recent_updates tool with custom minutes."""
    # Setup mock response
    expected_games = [{"game_id": "401772988"}]
    mock_supabase_client.fetch_recent_games.return_value = expected_games

    # Call tool with custom minutes
    result = await handle_tool_call(
        "get_recent_updates", {"minutes": 15}, mock_settings
    )
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_games
    mock_supabase_client.fetch_recent_games.assert_called_once_with(15)


@pytest.mark.asyncio
async def test_get_team_stats(mock_settings, mock_supabase_client):
    """Test get_team_stats tool."""
    # Setup mock response
    expected_stats = {
        "name": "Kansas City Chiefs",
        "abbreviation": "KC",
        "score": 24,
        "stats": {"totalYards": "350", "turnovers": "1"},
    }
    mock_supabase_client.fetch_team_stats.return_value = expected_stats

    # Call tool
    result = await handle_tool_call(
        "get_team_stats", {"game_id": "401772988", "team": "home"}, mock_settings
    )
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_stats
    mock_supabase_client.fetch_team_stats.assert_called_once_with("401772988", "home")


@pytest.mark.asyncio
async def test_get_play_by_play(mock_settings, mock_supabase_client):
    """Test get_play_by_play tool."""
    # Setup mock response
    expected_plays = [
        {
            "description": "Patrick Mahomes pass complete to Travis Kelce for 15 yards",
            "clock": "12:34",
            "possession": "KC",
        }
    ]
    mock_supabase_client.fetch_play_by_play.return_value = expected_plays

    # Call tool with default limit
    result = await handle_tool_call(
        "get_play_by_play", {"game_id": "401772988"}, mock_settings
    )
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_plays
    mock_supabase_client.fetch_play_by_play.assert_called_once_with("401772988", 10)


@pytest.mark.asyncio
async def test_get_play_by_play_custom_limit(mock_settings, mock_supabase_client):
    """Test get_play_by_play tool with custom limit."""
    # Setup mock response
    expected_plays = [{"description": "Play 1"}, {"description": "Play 2"}]
    mock_supabase_client.fetch_play_by_play.return_value = expected_plays

    # Call tool with custom limit
    result = await handle_tool_call(
        "get_play_by_play", {"game_id": "401772988", "limit": 5}, mock_settings
    )
    parsed = json.loads(result)

    # Verify
    assert parsed == expected_plays
    mock_supabase_client.fetch_play_by_play.assert_called_once_with("401772988", 5)


@pytest.mark.asyncio
async def test_unknown_tool(mock_settings, mock_supabase_client):
    """Test handling of unknown tool name."""
    result = await handle_tool_call("unknown_tool", {}, mock_settings)
    parsed = json.loads(result)

    # Verify error response
    assert "error" in parsed
    assert "Unknown tool" in parsed["error"]


@pytest.mark.asyncio
async def test_tool_exception(mock_settings, mock_supabase_client):
    """Test handling of exceptions during tool execution."""
    # Setup mock to raise exception
    mock_supabase_client.fetch_all_games.side_effect = Exception("Database error")

    # Call tool
    result = await handle_tool_call("get_all_games", {}, mock_settings)
    parsed = json.loads(result)

    # Verify error response
    assert "error" in parsed
    assert parsed["error"] == "Database error"
    assert parsed["tool"] == "get_all_games"
