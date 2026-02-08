# Plan: Live NFL Polling Service (FastAPI + Supabase)

## Context

The repository is empty (no Python code yet). The goal is to build a production-ready FastAPI service that polls live NFL game data every 60 seconds, converts it into "TOON format," and upserts it into Supabase.

**Key pivot:** The NFL LiveUpdate endpoints (`scores.json`, `_gtd.json`) specified in REQUIREMENTS.md are deprecated/restricted. We'll use **ESPN's hidden API** instead, which is free, unauthenticated, and provides richer data (including win probability).

## ESPN API Endpoints

| Endpoint | URL |
|---|---|
| Scoreboard | `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard` |
| Game Summary | `https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={gameId}` |

**Live game detection:** `events[].competitions[0].status.type.name` in `["STATUS_IN_PROGRESS", "STATUS_HALFTIME", "STATUS_END_PERIOD"]`

## File Structure

All code under `live-data-stream/`:

```
live-data-stream/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, lifespan, /health + /games endpoints
│   ├── poller.py           # Async poll loop, backoff, overlap prevention
│   ├── fetcher.py          # httpx async calls to ESPN API
│   ├── transformer.py      # ESPN JSON → TOON format mapping (most complex file)
│   ├── models.py           # Pydantic v2 models for TOON schema
│   ├── supabase_client.py  # Supabase client + upsert logic
│   └── config.py           # pydantic-settings for env vars
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures (mock ESPN responses)
│   ├── test_transformer.py # Core mapping tests
│   ├── test_fetcher.py     # HTTP mocking tests
│   ├── test_poller.py      # Polling lifecycle tests
│   └── test_models.py      # Pydantic validation tests
├── sql/
│   └── create_tables.sql   # Supabase table DDL
├── pyproject.toml           # uv-managed deps
├── Dockerfile               # Two-stage build (uv + python:3.12-slim)
├── .env.example
└── README.md
```

## Implementation Order

### Step 1: Project scaffolding
- **`pyproject.toml`** — Dependencies: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic`, `pydantic-settings`, `supabase`, `structlog`. Dev deps: `pytest`, `pytest-asyncio`, `respx`, `ruff`, `mypy`.
- **`app/__init__.py`**, **`tests/__init__.py`** — Empty init files.
- Run `uv sync` to install everything.

### Step 2: `app/config.py` — Settings
- `pydantic-settings` `BaseSettings` class with: ESPN URLs, polling interval (60s), request timeout (10s), backoff params, Supabase URL/key, log level, list of live status strings.
- Reads from `.env` file.

### Step 3: `app/models.py` — TOON Pydantic Models
- `TeamData(id, name, score: int, stats: dict[str, str])`
- `GameData(game_id, status, quarter: int, clock, home_team: TeamData, away_team: TeamData)`
- `EventData(event_id, type="play", description, quarter: int, clock, possession, win_probability: float | None)`
- `ToonPayload(type="game_update", source="espn_live", timestamp: datetime, game: GameData, events: list[EventData])`

### Step 4: `app/fetcher.py` — ESPN HTTP Client
- `ESPNFetcher` class taking `httpx.AsyncClient` + `Settings`.
- `fetch_scoreboard()` → raw dict.
- `fetch_game_summary(game_id)` → raw dict.
- `extract_live_game_ids(scoreboard)` → list of game ID strings.
- Raises on HTTP errors/timeouts (caller handles).

### Step 5: `app/transformer.py` — ESPN → TOON Mapping (critical file)

**Field mapping:**

| TOON Field | ESPN Source |
|---|---|
| `game.game_id` | `event["id"]` |
| `game.status` | `event["competitions"][0]["status"]["type"]["description"]` |
| `game.quarter` | `event["competitions"][0]["status"]["period"]` |
| `game.clock` | `event["competitions"][0]["status"]["displayClock"]` |
| `home_team.id` | `competitor["team"]["id"]` where `homeAway == "home"` |
| `home_team.name` | `competitor["team"]["displayName"]` where `homeAway == "home"` |
| `home_team.score` | `int(competitor["score"])` — **must cast from string** |
| `home_team.stats` | `boxscore.teams[i].statistics[]` → `{stat["name"]: stat["displayValue"]}` filtered to key stats |
| `events[].event_id` | `play["id"]` from most recent drives/plays |
| `events[].description` | `play["text"]` |
| `events[].quarter` | `play["period"]["number"]` |
| `events[].clock` | `play["clock"]["displayValue"]` |
| `events[].possession` | Team abbreviation via `play["start"]["team"]["id"]` lookup |
| `events[].win_probability` | `winprobability[]` matched by `playId` → `homeWinPercentage` (null if missing) |

Key stats extracted: `totalYards`, `netPassingYards`, `rushingYards`, `turnovers`, `fumblesLost`, `interceptions`, `firstDowns`, `thirdDownEff`, `possessionTime`, `completionAttempts`, etc.

**Important gotchas:**
- Competitor array order is NOT guaranteed — must filter by `homeAway` field.
- `competitor["score"]` is a string — cast to `int`.
- Boxscore `teams[]` also unordered — match on `homeAway`.
- For plays: check `drives.current` (live drive) first, then `drives.previous[-1]` (last completed drive). Take last ~10 plays.

### Step 6: `app/supabase_client.py` — Supabase Integration
- `SupabaseStore` wrapping `create_client(url, key)`.
- `upsert_game(payload: ToonPayload)` — builds row dict, upserts on `game_id` conflict. Uses `asyncio.to_thread()` since `supabase-py` is synchronous.
- `get_all_games()` — fetches all rows (optional fallback for `/games`).

### Step 7: `app/poller.py` — Async Polling Loop
- `Poller` class with `start()`, `stop()`, `_poll_loop()`, `_poll_once()`, `_do_poll()`.
- `asyncio.Lock` prevents overlapping runs.
- Per-game try/except — one game failure doesn't stop others.
- Exponential backoff: `min(initial * (multiplier ^ failures), max_backoff)`. Resets on success.
- In-memory `_latest_payloads` dict caches latest TOON per game for `/games`.

### Step 8: `app/main.py` — FastAPI App
- `lifespan` async context manager: creates `httpx.AsyncClient`, wires all services, starts poller on enter, stops on exit.
- `GET /health` — returns `{"status": "ok", "timestamp": "..."}`.
- `GET /games` — returns cached TOON payloads from poller.
- Configures `structlog` with JSON or console rendering.

### Step 9: Tests
- **`conftest.py`**: Fixture dicts mimicking ESPN scoreboard + summary responses. Mock settings with dummy Supabase creds.
- **`test_transformer.py`** (most important): Validates every TOON field mapping, empty drives, missing win probability, score casting, competitor order independence, stats filtering.
- **`test_fetcher.py`**: Uses `respx` to mock httpx. Tests success, timeout, 500 errors, live game ID extraction.
- **`test_poller.py`**: Tests poll success, per-game failure isolation, overlap skip, backoff calculation, graceful shutdown.
- **`test_models.py`**: Validates Pydantic model construction, required fields, defaults, JSON serialization.

### Step 10: Deployment artifacts
- **`sql/create_tables.sql`** — `live_games` table with `game_id` PK, JSONB `toon_payload`, `updated_at`, RLS enabled.
- **`Dockerfile`** — Two-stage: `uv sync --no-dev` in builder, copy `.venv` to `python:3.12-slim` runtime. Runs `uvicorn app.main:app`.
- **`.env.example`** — Template with `SUPABASE_URL`, `SUPABASE_ANON_KEY`, polling config.
- **`README.md`** — Setup and run instructions.

## Verification

1. **Unit tests**: `cd live-data-stream && uv run pytest tests/ -v`
2. **Local run**: `cp .env.example .env`, fill in Supabase creds, `uv run uvicorn app.main:app --reload`
3. **Health check**: `curl http://localhost:8000/health`
4. **Games endpoint**: `curl http://localhost:8000/games` (will be empty if no live games; populated during NFL game days)
5. **Lint/type check**: `uv run ruff check app/` and `uv run mypy app/`
6. **Docker**: `docker build -t nfl-poller .` then `docker run --env-file .env -p 8000:8000 nfl-poller`
