# NFL Data MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides LLMs with access to live NFL game data stored in Supabase. This server enables Claude, Gemini, and other MCP-compatible LLMs to query real-time game information, statistics, and play-by-play data.

## Overview

This MCP server exposes NFL game data through a set of tools that LLMs can invoke to answer questions about:
- Live game scores and status
- Team statistics (yards, turnovers, etc.)
- Play-by-play events
- Win probability
- Recent game updates

The server connects to a Supabase database that is continuously updated by the `live-data-stream` polling service.

## Features

### Available Tools

1. **get_all_games** - Retrieve all games with basic info
2. **get_game_details** - Get full details for a specific game (stats, plays, win probability)
3. **get_live_games** - Filter games currently in progress or at halftime
4. **get_games_by_status** - Filter games by status (e.g., "Final", "Scheduled")
5. **get_recent_updates** - Get games updated in the last N minutes
6. **get_team_stats** - Extract team statistics for a specific game
7. **get_play_by_play** - Get recent plays/events for a game

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Access to a Supabase instance with the `live_games` table

### Setup

1. **Install dependencies:**

```bash
cd mcp-server
uv sync
```

2. **Configure environment:**

```bash
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

3. **Verify installation:**

```bash
uv run python -m src.server
```

The server should start and wait for MCP client connections via stdio.

## Usage

### Running the Server

The MCP server communicates via stdio (standard input/output), so it's typically not run directly but configured in an MCP client like Claude Desktop or Claude Code.

### Integration with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nfl-data": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/superbowl_LX/mcp-server",
        "run",
        "python",
        "-m",
        "src.server"
      ],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_ANON_KEY": "your-anon-key-here"
      }
    }
  }
}
```

**Note:** Replace `/absolute/path/to/superbowl_LX/mcp-server` with the actual absolute path to your mcp-server directory.

### Integration with Claude Code

Add to your MCP settings in Claude Code:

```json
{
  "nfl-data": {
    "command": "uv",
    "args": [
      "--directory",
      "/absolute/path/to/superbowl_LX/mcp-server",
      "run",
      "python",
      "-m",
      "src.server"
    ],
    "env": {
      "SUPABASE_URL": "https://your-project.supabase.co",
      "SUPABASE_ANON_KEY": "your-anon-key"
    }
  }
}
```

### Example Queries

Once configured, you can ask natural language questions that will be answered using the MCP tools:

**Live game queries:**
- "What games are currently live?"
- "Show me all games in progress right now"
- "What's the score of the Super Bowl?"

**Game details:**
- "Show me the full details for game 401772988"
- "What are the team stats for the Chiefs in game 401772988?"
- "How many total yards does the home team have?"

**Play-by-play:**
- "What were the last 5 plays in the Super Bowl?"
- "Show me recent plays for game 401772988"
- "What's the latest scoring play?"

**Status queries:**
- "What games finished in the last hour?"
- "Show me all final games"
- "Which games have been updated recently?"

**Statistics:**
- "Which team has more turnovers?"
- "What's the rushing yards for the away team?"
- "Compare the total yards for both teams"

## Development

### Running Tests

```bash
cd mcp-server
uv run pytest tests/ -v
```

### Linting

```bash
uv run ruff check src/ tests/
```

### Code Formatting

```bash
uv run ruff format src/ tests/
```

## Architecture

### Data Flow

```
ESPN API → live-data-stream (FastAPI) → Supabase → MCP Server → LLM Client
```

1. The `live-data-stream` service polls ESPN's API every 60 seconds
2. Data is transformed to TOON format and stored in Supabase
3. MCP server queries Supabase when tools are invoked
4. Results are returned as JSON to the LLM client

### Project Structure

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py       # Main MCP server (stdio communication)
│   ├── tools.py        # Tool definitions and handlers
│   ├── supabase.py     # Database query functions
│   └── config.py       # Settings and environment config
├── tests/
│   ├── __init__.py
│   └── test_tools.py   # Tool handler tests
├── pyproject.toml      # Dependencies and project metadata
├── .env.example        # Environment variable template
└── README.md           # This file
```

### Technology Stack

- **MCP SDK** - Official Python MCP implementation
- **Supabase** - PostgreSQL database with real-time capabilities
- **Pydantic** - Data validation and settings management
- **pytest** - Testing framework

## Database Schema

The server queries the `live_games` table with this structure:

```sql
CREATE TABLE live_games (
    game_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    quarter INTEGER,
    clock TEXT,
    home_score INTEGER,
    away_score INTEGER,
    toon_payload JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### TOON Payload Structure

The `toon_payload` JSONB column contains:
- `source` - Data source identifier ("espn_live")
- `game` - Game metadata (status, quarter, clock, teams)
- `home_team` / `away_team` - Team data with stats
- `events` - Play-by-play events
- `possession` - Current team with possession

## Security

- **Read-only access** - MCP server only queries data, never writes
- **Supabase anon key** - Uses the same read-only key as the live-data-stream service
- **No authentication** - Server runs locally, authenticated by the MCP client

## Troubleshooting

### Server not starting

- Verify `.env` file exists and has valid Supabase credentials
- Check Python version: `python --version` (should be 3.12+)
- Check uv installation: `uv --version`

### No data returned

- Verify the `live-data-stream` service is running and populating data
- Check Supabase connection with: `uv run python -c "from src.config import Settings; s = Settings(); print(s.supabase_url)"`
- Verify the `live_games` table exists in Supabase

### Tool errors in LLM client

- Check the MCP server logs (usually in the LLM client's logs)
- Verify the `command` and `args` in the MCP config point to the correct paths
- Ensure environment variables are set correctly in the MCP config

## Related Projects

- **live-data-stream** - FastAPI service that polls ESPN and updates Supabase
- **historical-data** - (Planned) Historical Super Bowl data and analysis

## Contributing

This is part of the Super Bowl LX data project. See the main repository README for contribution guidelines.

## License

See the main repository LICENSE file.
