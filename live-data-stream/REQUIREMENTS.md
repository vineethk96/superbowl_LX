# Live NFL Polling Service – FastAPI + Supabase

You are a senior backend engineer.

Build a production-ready Python service using **FastAPI** that polls live NFL game data from the official NFL.com LiveUpdate JSON feeds once per minute, converts the data into TOON format, and upserts the transformed data into a Supabase database.

The system must be modular, robust, and ready for deployment.

---

## 1️⃣ Data Source

Use the NFL LiveUpdate feeds:

### Scoreboard
https://www.nfl.com/liveupdate/scores/scores.json

### Game Center (detailed play-by-play + stats)
https://www.nfl.com/liveupdate/game-center/{GAME_ID}/{GAME_ID}_gtd.json

The service should:

- Poll the scoreboard first
- Identify live/active games only
- Extract `GAME_ID`
- Fetch corresponding `{GAME_ID}_gtd.json`
- Process all active games

---

## 2️⃣ Polling Requirements

- Poll once every 60 seconds
- Use an async background task (`asyncio.create_task`)
- Prevent overlapping runs
- Implement exponential backoff on failure
- Log structured JSON logs
- Continue running even if one game fetch fails

---

## 3️⃣ TOON Format

Convert NFL JSON into the following TOON schema:

```json
{
  "type": "game_update",
  "source": "nfl_liveupdate",
  "timestamp": "<ISO8601>",
  "game": {
    "game_id": "string",
    "status": "string",
    "quarter": "number",
    "clock": "string",
    "home_team": {
      "id": "string",
      "name": "string",
      "score": "number",
      "stats": {}
    },
    "away_team": {
      "id": "string",
      "name": "string",
      "score": "number",
      "stats": {}
    }
  },
  "events": [
    {
      "event_id": "string",
      "type": "play",
      "description": "string",
      "quarter": "number",
      "clock": "string",
      "possession": "string",
      "win_probability": "number | null"
    }
  ]
}
````

### Requirements

* Extract latest play from play-by-play feed
* Include team stats (passing yards, rushing yards, turnovers if available)
* If win probability is unavailable, set to null
* Strictly conform to schema
* Use Pydantic models for validation

---

## 4️⃣ Supabase Integration

Use the official Python client:

```python
from supabase import create_client
```

Use environment variables:

* `SUPABASE_URL`
* `SUPABASE_ANON_KEY`

### Table: `live_games`

Columns:

* `game_id` (primary key)
* `status`
* `quarter`
* `clock`
* `home_score`
* `away_score`
* `toon_payload` (JSONB)
* `updated_at` (timestamp)

### Behavior

* Upsert on `game_id`
* Store full TOON object in `toon_payload`
* Update `updated_at` on every poll
* Ensure idempotency

---

## 5️⃣ Architecture Requirements

Use the following structure:

```
app/
├── main.py
├── poller.py
├── fetcher.py
├── transformer.py
├── models.py
├── supabase_client.py
└── config.py
```

### Requirements

* Use `httpx` (async) for HTTP calls
* Use Pydantic models
* Type hints everywhere
* Strict error handling
* Clean separation of concerns
* Validate TOON payload before DB write

---

## 6️⃣ FastAPI Requirements

* Expose `/health` endpoint
* Expose `/games` endpoint returning latest cached TOON payloads
* Start polling automatically on startup event
* Graceful shutdown handling

---

## 7️⃣ Reliability & Safety

Handle:

* Network failures
* JSON decode errors
* Missing fields
* Skip non-live games
* Timeout requests after 10 seconds
* Structured logging

---

## 8️⃣ Deliverables

Provide:

* Full working FastAPI implementation
* Supabase SQL table creation script
* `requirements.txt`
* `.env.example`
* Instructions to run locally
* Optional Dockerfile

The output must contain complete working code.
No pseudocode.
Production-ready quality.