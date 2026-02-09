# Super Bowl LX Data Project

A comprehensive data pipeline and analysis system for Super Bowl LX, featuring live game data streaming, historical analysis, and LLM-powered querying capabilities.

## Project Overview

This repository contains three interconnected projects:

### 1. **live-data-stream** - Real-time NFL Data Pipeline

A FastAPI-based polling service that streams live NFL game data from ESPN's hidden API into Supabase.

**Features:**
- Polls ESPN API every 60 seconds for live game updates
- Transforms data into standardized TOON format
- Stores in Supabase with automatic timestamping
- Dockerized for easy deployment
- Comprehensive test coverage (40+ tests)

**Tech Stack:** Python 3.12+, FastAPI, httpx, Supabase, Pydantic, Docker

[Read more →](./live-data-stream/README.md)

### 2. **mcp-server** - LLM Data Access Layer

A Model Context Protocol (MCP) server that enables Claude, Gemini, and other LLMs to query NFL game data through natural language.

**Features:**
- 7 specialized tools for querying game data
- Live game filtering and status tracking
- Team statistics extraction
- Play-by-play retrieval
- Win probability data
- JSON-formatted responses for LLM consumption

**Tech Stack:** Python 3.12+, MCP SDK, Supabase, Pydantic

[Read more →](./mcp-server/README.md)

### 3. **historical-data** - Historical Analysis (Planned)

Future component for analyzing historical Super Bowl data and trends.

## Architecture

```
┌─────────────┐     Poll every      ┌──────────────────┐
│  ESPN API   │ ◄───── 60s ──────── │ live-data-stream │
└─────────────┘                     │   (FastAPI)      │
                                    └──────────────────┘
                                            │
                                            │ Store TOON format
                                            ▼
                                    ┌──────────────────┐
                                    │    Supabase      │
                                    │  (PostgreSQL)    │
                                    └──────────────────┘
                                            ▲
                                            │ Query
                                    ┌──────────────────┐
                                    │   MCP Server     │
                                    └──────────────────┘
                                            ▲
                                            │ Tool calls
                                    ┌──────────────────┐
                                    │ Claude / Gemini  │
                                    │   (LLM Client)   │
                                    └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Supabase account and project

### 1. Set Up Database

```bash
# Create the live_games table in Supabase
psql -h your-project.supabase.co -U postgres -d postgres -f live-data-stream/sql/create_tables.sql
```

### 2. Start Live Data Stream

```bash
cd live-data-stream
cp .env.example .env
# Edit .env with your Supabase credentials
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Configure MCP Server

```bash
cd mcp-server
cp .env.example .env
# Edit .env with your Supabase credentials
uv sync
```

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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
        "SUPABASE_ANON_KEY": "your-anon-key"
      }
    }
  }
}
```

### 4. Query with Claude

Open Claude Desktop and ask:
- "What games are currently live?"
- "Show me the stats for game 401772988"
- "What were the last 5 plays in the Super Bowl?"

## Data Format

### TOON Payload Structure

```json
{
  "source": "espn_live",
  "game": {
    "game_id": "401772988",
    "status": "In Progress",
    "quarter": 2,
    "clock": "5:23",
    "home_team": {
      "name": "Kansas City Chiefs",
      "abbreviation": "KC",
      "score": 14,
      "stats": { "totalYards": "245", "turnovers": "1" }
    },
    "away_team": { /* ... */ }
  },
  "events": [
    {
      "description": "Patrick Mahomes pass complete to Travis Kelce",
      "clock": "5:23",
      "possession": "KC",
      "win_probability": 0.67
    }
  ],
  "possession": "KC"
}
```

## Development

### Running Tests

```bash
# Live data stream tests
cd live-data-stream
uv run pytest tests/ -v

# MCP server tests
cd mcp-server
uv run pytest tests/ -v
```

### Linting

```bash
# Both projects use ruff
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

### Docker Deployment

```bash
cd live-data-stream
docker build -t nfl-live-stream .
docker run -e SUPABASE_URL=... -e SUPABASE_ANON_KEY=... -p 8000:8000 nfl-live-stream
```

## API Endpoints

### Live Data Stream

- `GET /health` - Health check endpoint
- `GET /games` - List all cached games (in-memory)

### MCP Server Tools

- `get_all_games` - All games with basic info
- `get_game_details` - Full game details with stats
- `get_live_games` - Currently live games only
- `get_games_by_status` - Filter by status
- `get_recent_updates` - Recently updated games
- `get_team_stats` - Team statistics for a game
- `get_play_by_play` - Recent plays and events

## Key Design Decisions

1. **ESPN Hidden API** - Selected over deprecated NFL.com LiveUpdate endpoints
2. **TOON Format** - Custom standardized format for game data
3. **Polling Strategy** - 60-second interval with exponential backoff on failures
4. **MCP Protocol** - Enables LLM access without custom API development
5. **Read-Only MCP** - Server only queries data, never writes
6. **Async-First** - Full async/await support in both services

## Known Limitations

- ESPN API is unofficial and subject to change without notice
- Score values from ESPN are strings and must be cast to integers
- Competitor array order is not guaranteed (filter by `homeAway` field)
- Win probability data only available during live games

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add license information]

## Acknowledgments

- ESPN for providing the hidden API
- Supabase for the database platform
- Model Context Protocol for the LLM integration standard
