-- Updated schema to match user's exact specification with regret_score, inventory_btc, nash_stable, shull_fractal
-- Create actors table for Actor-Simulation RL
CREATE TABLE IF NOT EXISTS actors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  regret_score NUMERIC(3,2) DEFAULT 0.00 CHECK (regret_score >= 0 AND regret_score <= 1.00),
  inventory_btc NUMERIC DEFAULT 1.0,
  last_action INT DEFAULT 0 CHECK (last_action >= 0 AND last_action <= 8),
  nash_stable BOOLEAN DEFAULT FALSE,
  shull_fractal TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create actor_actions table for tracking all actor decisions
CREATE TABLE IF NOT EXISTS actor_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id UUID REFERENCES actors(id) ON DELETE CASCADE,
  episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
  step INTEGER NOT NULL,
  action_type TEXT NOT NULL,
  size DECIMAL NOT NULL,
  price DECIMAL NOT NULL,
  regret_forecast DECIMAL DEFAULT 0,
  reasoning TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create nash_equilibrium_log table
CREATE TABLE IF NOT EXISTS nash_equilibrium_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
  step INTEGER NOT NULL,
  is_equilibrium BOOLEAN DEFAULT FALSE,
  nash_deviation DECIMAL DEFAULT 0,
  actor_states JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create regret_scores table for Denise Shull framework
CREATE TABLE IF NOT EXISTS regret_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id UUID REFERENCES actors(id) ON DELETE CASCADE,
  episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
  step INTEGER NOT NULL,
  feeling_name TEXT,
  intensity INTEGER CHECK (intensity BETWEEN 1 AND 10),
  fractal_link TEXT,
  regret_forecast DECIMAL,
  action_taken TEXT,
  outcome TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_regret ON actors(regret_score);
CREATE INDEX IF NOT EXISTS idx_nash ON actors(nash_stable);
CREATE INDEX IF NOT EXISTS idx_actor_actions_episode ON actor_actions(episode_id);
CREATE INDEX IF NOT EXISTS idx_actor_actions_actor ON actor_actions(actor_id);
CREATE INDEX IF NOT EXISTS idx_nash_log_episode ON nash_equilibrium_log(episode_id);
CREATE INDEX IF NOT EXISTS idx_regret_scores_actor ON regret_scores(actor_id);

-- Enable RLS
ALTER TABLE actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE actor_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE nash_equilibrium_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE regret_scores ENABLE ROW LEVEL SECURITY;

-- RLS Policies (public read for demo)
CREATE POLICY "Allow public read access to actors" ON actors FOR SELECT USING (true);
CREATE POLICY "Allow public read access to actor_actions" ON actor_actions FOR SELECT USING (true);
CREATE POLICY "Allow public read access to nash_log" ON nash_equilibrium_log FOR SELECT USING (true);
CREATE POLICY "Allow public read access to regret_scores" ON regret_scores FOR SELECT USING (true);
