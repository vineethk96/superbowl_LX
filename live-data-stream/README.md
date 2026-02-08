# Live NFL Polling Service

FastAPI service that polls live NFL game data from ESPN's API every 60 seconds, transforms it into TOON format, and upserts to Supabase.

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Create the database table (run in Supabase SQL editor)
# See sql/create_tables.sql
```

## Run locally

```bash
uv run uvicorn app.main:app --reload
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/games` | Latest cached TOON payloads |

## TOON Format

The service transforms ESPN's API data into the following TOON (Team-Oriented Object Notation) format:

```json
{
  "type": "game_update",
  "source": "espn_live",
  "timestamp": "2026-02-08T23:45:30.123456Z",
  "game": {
    "game_id": "401772988",
    "status": "In Progress",
    "quarter": 3,
    "clock": "7:23",
    "home_team": {
      "id": "17",
      "name": "New England Patriots",
      "score": 21,
      "stats": {
        "totalYards": "310",
        "rushingYards": "88",
        "netPassingYards": "222",
        "turnovers": "0",
        "firstDowns": "18",
        "thirdDownEff": "5-10",
        "fourthDownEff": "1-1",
        "totalPenaltiesYards": "35",
        "possessionTime": "18:45"
      }
    },
    "away_team": {
      "id": "26",
      "name": "Seattle Seahawks",
      "score": 14,
      "stats": {
        "totalYards": "285",
        "rushingYards": "102",
        "netPassingYards": "183",
        "turnovers": "1",
        "firstDowns": "16"
      }
    }
  },
  "events": [
    {
      "event_id": "5001",
      "type": "play",
      "description": "T.Brady pass to R.Gronkowski for 15 yards",
      "quarter": 3,
      "clock": "7:23",
      "possession": "NE",
      "win_probability": 0.72
    },
    {
      "event_id": "5002",
      "type": "play",
      "description": "R.Wilson sacked for -7 yards",
      "quarter": 3,
      "clock": "8:15",
      "possession": "SEA",
      "win_probability": 0.65
    }
  ]
}
```

### Field Descriptions

**Top-level:**
- `type`: Always `"game_update"`
- `source`: Always `"espn_live"`
- `timestamp`: ISO 8601 timestamp when the data was fetched

**Game object:**
- `game_id`: ESPN's unique game identifier
- `status`: Human-readable status (e.g., "In Progress", "Halftime", "Final")
- `quarter`: Current quarter/period (0 = pre-game, 5 = overtime)
- `clock`: Game clock display (e.g., "7:23")

**Team objects (home_team, away_team):**
- `id`: ESPN team ID
- `name`: Full team display name
- `score`: Current score (integer)
- `stats`: Dictionary of game statistics (values are strings)

**Event objects (plays):**
- `event_id`: Unique play identifier
- `type`: Always `"play"`
- `description`: Play-by-play text
- `quarter`: Quarter when play occurred
- `clock`: Game clock when play started
- `possession`: Team abbreviation with possession (e.g., "NE", "SEA")
- `win_probability`: ESPN's win probability for home team (0.0-1.0), or `null` if unavailable

### Stats Included

The service extracts these statistics when available:
- `totalYards`, `netPassingYards`, `rushingYards`
- `turnovers`, `fumblesLost`, `interceptions`
- `firstDowns`, `passingFirstDowns`, `rushingFirstDowns`
- `thirdDownEff`, `fourthDownEff`
- `totalPenaltiesYards`, `possessionTime`
- `completionAttempts`, `sacksYardsLost`, `rushingAttempts`
- `totalDrives`

## Tests

```bash
uv run pytest tests/ -v
```

## Lint

```bash
uv run ruff check app/
```

## Docker

### Build the Image

```bash
docker build -t nfl-poller .
```

This creates a production-ready image using:
- Two-stage build (builder + runtime)
- Python 3.12 slim base
- uv for fast dependency installation
- Only production dependencies included

### Run the Container

**Option 1: Use .env file (recommended)**

```bash
docker run --env-file .env -p 8000:8000 nfl-poller
```

**Option 2: Pass credentials directly**

```bash
docker run \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_ANON_KEY=your-anon-key-here \
  -p 8000:8000 \
  nfl-poller
```

**Option 3: Run in detached mode (background)**

```bash
docker run -d \
  --name nfl-poller \
  --env-file .env \
  -p 8000:8000 \
  nfl-poller
```

### Verify It's Running

```bash
# Health check
curl http://localhost:8000/health

# Check for live games
curl http://localhost:8000/games
```

### View Logs

```bash
# If running in detached mode
docker logs -f nfl-poller

# View last 100 lines
docker logs --tail 100 nfl-poller
```

### Stop the Container

```bash
docker stop nfl-poller
docker rm nfl-poller
```

### Advanced Configuration

**Custom polling interval:**
```bash
docker run --env-file .env \
  -e POLL_INTERVAL_SECONDS=30 \
  -p 8000:8000 \
  nfl-poller
```

**Enable JSON logging:**
```bash
docker run --env-file .env \
  -e LOG_JSON=true \
  -e LOG_LEVEL=DEBUG \
  -p 8000:8000 \
  nfl-poller
```

**Run with restart policy (production):**
```bash
docker run -d \
  --name nfl-poller \
  --restart unless-stopped \
  --env-file .env \
  -p 8000:8000 \
  nfl-poller
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
services:
  nfl-poller:
    build: .
    container_name: nfl-poller
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

Then run:

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Troubleshooting

**Container exits immediately:**
- Check logs: `docker logs nfl-poller`
- Verify Supabase credentials are set
- Ensure port 8000 is not already in use

**Cannot connect to Docker daemon:**
```bash
# Start Docker Desktop
systemctl --user start docker-desktop

# Or start system Docker
sudo systemctl start docker
```

**Rebuild after code changes:**
```bash
docker build --no-cache -t nfl-poller .
```
