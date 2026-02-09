"""MCP tool definitions and handlers for NFL data queries."""

import json
from typing import Any

from mcp.types import Tool

from .config import Settings
from .supabase import SupabaseClient

# Define all available tools
TOOLS = [
    Tool(
        name="get_all_games",
        description=(
            "Retrieve all NFL games from the database with basic info "
            "(game_id, status, scores, timestamps)"
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_game_details",
        description=(
            "Get full details for a specific game including team stats, "
            "recent plays, and win probability"
        ),
        inputSchema={
            "type": "object",
            "properties": {"game_id": {"type": "string", "description": "ESPN game ID"}},
            "required": ["game_id"],
        },
    ),
    Tool(
        name="get_live_games",
        description="Filter games that are currently in progress or at halftime",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_games_by_status",
        description="Filter games by status (e.g., 'In Progress', 'Final', 'Scheduled')",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": (
                        "Game status to filter by "
                        "(e.g., 'In Progress', 'Final', 'Scheduled')"
                    ),
                }
            },
            "required": ["status"],
        },
    ),
    Tool(
        name="get_recent_updates",
        description="Get games updated in the last N minutes",
        inputSchema={
            "type": "object",
            "properties": {
                "minutes": {
                    "type": "integer",
                    "description": "Time window in minutes (default: 5)",
                    "default": 5,
                }
            },
            "required": [],
        },
    ),
    Tool(
        name="get_team_stats",
        description="Extract team statistics for a specific game (totalYards, turnovers, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "game_id": {"type": "string", "description": "ESPN game ID"},
                "team": {
                    "type": "string",
                    "description": "Team to get stats for ('home' or 'away')",
                    "enum": ["home", "away"],
                },
            },
            "required": ["game_id", "team"],
        },
    ),
    Tool(
        name="get_play_by_play",
        description=(
            "Get recent plays/events for a game with descriptions, clock, "
            "possession, and win probability"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "game_id": {"type": "string", "description": "ESPN game ID"},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of plays to return (default: 10)",
                    "default": 10,
                },
            },
            "required": ["game_id"],
        },
    ),
]


async def handle_tool_call(name: str, arguments: dict[str, Any], settings: Settings) -> str:
    """Route tool calls to appropriate handlers and return JSON response.

    Args:
        name: Tool name to invoke
        arguments: Tool arguments as dict
        settings: Configuration settings

    Returns:
        JSON string with results or error message
    """
    client = SupabaseClient(settings)

    # Map tool names to handler functions
    handlers = {
        "get_all_games": lambda: client.fetch_all_games(),
        "get_game_details": lambda: client.fetch_game_by_id(arguments["game_id"]),
        "get_live_games": lambda: client.fetch_live_games(),
        "get_games_by_status": lambda: client.fetch_games_by_status(arguments["status"]),
        "get_recent_updates": lambda: client.fetch_recent_games(
            arguments.get("minutes", 5)
        ),
        "get_team_stats": lambda: client.fetch_team_stats(
            arguments["game_id"], arguments["team"]
        ),
        "get_play_by_play": lambda: client.fetch_play_by_play(
            arguments["game_id"], arguments.get("limit", 10)
        ),
    }

    if name not in handlers:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = handlers[name]()
        # default=str handles datetime serialization
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name, "arguments": arguments})
