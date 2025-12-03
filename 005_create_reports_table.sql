-- Create reports table for storing generated episode reports
CREATE TABLE IF NOT EXISTS reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  episode_id UUID NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  
  -- Pre-Session Mindset
  mood_snapshot TEXT NOT NULL,
  mental_debris TEXT,
  trigger_watch TEXT,
  affirmation TEXT,
  
  -- Market Summary
  market_data JSONB NOT NULL DEFAULT '{}',
  
  -- PPI Composite
  ppi_composite DECIMAL(5,2) NOT NULL,
  macro_bias TEXT NOT NULL,
  short_term_risk TEXT NOT NULL,
  recommendation TEXT,
  
  -- Multi-Factor Silos
  silos JSONB NOT NULL DEFAULT '[]',
  
  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_reports_episode_id ON reports(episode_id);
CREATE INDEX idx_reports_agent_id ON reports(agent_id);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);

-- Enable RLS
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Reports are viewable by everyone"
  ON reports FOR SELECT
  USING (true);

CREATE POLICY "Reports are insertable by authenticated users"
  ON reports FOR INSERT
  WITH CHECK (true);
