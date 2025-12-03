-- Create ppi_scores table for detailed Maslow tier breakdown
create table if not exists public.ppi_scores (
  id uuid primary key default gen_random_uuid(),
  episode_id uuid references public.episodes(id) on delete cascade,
  agent_id uuid references public.agents(id) on delete cascade,
  
  -- Overall PPI score (0-100)
  total_score numeric not null check (total_score >= 0 and total_score <= 100),
  
  -- Tier scores (0-100 each)
  safety_score numeric not null check (safety_score >= 0 and safety_score <= 100),
  belonging_score numeric not null check (belonging_score >= 0 and belonging_score <= 100),
  esteem_score numeric not null check (esteem_score >= 0 and esteem_score <= 100),
  self_actualization_score numeric not null check (self_actualization_score >= 0 and self_actualization_score <= 100),
  
  -- Tier weights (should sum to 1.0)
  safety_weight numeric default 0.4,
  belonging_weight numeric default 0.2,
  esteem_weight numeric default 0.2,
  self_actualization_weight numeric default 0.2,
  
  -- Raw metrics used for calculation
  volatility numeric,
  max_drawdown numeric,
  community_upvotes integer default 0,
  alpha_vs_benchmark numeric,
  solar_energy_percent numeric,
  
  created_at timestamptz default now()
);

-- Create indexes
create index if not exists idx_ppi_scores_episode_id on public.ppi_scores(episode_id);
create index if not exists idx_ppi_scores_agent_id on public.ppi_scores(agent_id);
create index if not exists idx_ppi_scores_total_score on public.ppi_scores(total_score desc);

-- Enable RLS
alter table public.ppi_scores enable row level security;

-- Create policies
create policy "Allow public read access to ppi_scores"
  on public.ppi_scores for select
  using (true);

create policy "Allow public insert to ppi_scores"
  on public.ppi_scores for insert
  with check (true);

create policy "Allow public update to ppi_scores"
  on public.ppi_scores for update
  using (true);
