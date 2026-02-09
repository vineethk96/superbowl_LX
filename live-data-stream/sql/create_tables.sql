-- Supabase table for live NFL game data (historical snapshots)
CREATE TABLE IF NOT EXISTS live_games (
    whalesync_postgres_id BIGSERIAL PRIMARY KEY,
    game_id   TEXT NOT NULL,
    status    TEXT NOT NULL,
    quarter   INTEGER NOT NULL DEFAULT 0,
    clock     TEXT NOT NULL DEFAULT '0:00',
    home_score INTEGER NOT NULL DEFAULT 0,
    away_score INTEGER NOT NULL DEFAULT 0,
    toon_payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for querying by game_id and timestamp
CREATE INDEX IF NOT EXISTS idx_live_games_game_id ON live_games (game_id, updated_at DESC);

-- Index for querying by status
CREATE INDEX IF NOT EXISTS idx_live_games_status ON live_games (status);

-- Enable Row-Level Security
ALTER TABLE live_games ENABLE ROW LEVEL SECURITY;

-- Allow anonymous reads (for the /games endpoint or front-end)
CREATE POLICY "Allow anonymous read access"
    ON live_games
    FOR SELECT
    USING (true);

-- Allow service-role inserts/updates (the poller uses the anon key;
-- adjust to service_role if you restrict writes)
CREATE POLICY "Allow anon insert and update"
    ON live_games
    FOR ALL
    USING (true)
    WITH CHECK (true);
