-- Create agents table
create table if not exists public.agents (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  irr numeric default 0,
  sharpe numeric default 0,
  ppi_score numeric default 0 check (ppi_score >= 0 and ppi_score <= 100),
  episodes_trained integer default 0,
  created_at timestamptz default now()
);

-- Create episodes table
create table if not exists public.episodes (
  id uuid primary key default gen_random_uuid(),
  agent_id uuid references public.agents(id) on delete cascade,
  episode_number integer not null,
  total_reward numeric default 0,
  steps integer default 0,
  ppi_score numeric default 0,
  created_at timestamptz default now()
);

-- Create actions table
create table if not exists public.actions (
  id uuid primary key default gen_random_uuid(),
  episode_id uuid references public.episodes(id) on delete cascade,
  step integer not null,
  action_type text not null check (action_type in ('buy', 'sell', 'hold')),
  size numeric default 0,
  price numeric default 0,
  reward numeric default 0,
  grok_confidence numeric default 0,
  timestamp timestamptz default now()
);

-- Create settings table
create table if not exists public.settings (
  id uuid primary key default gen_random_uuid(),
  xai_api_key text,
  alpaca_api_key text,
  ppi_weights jsonb default '{"physiological": 0.2, "safety": 0.2, "belonging": 0.2, "esteem": 0.2, "self_actualization": 0.2}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Create indexes for better query performance
create index if not exists idx_episodes_agent_id on public.episodes(agent_id);
create index if not exists idx_actions_episode_id on public.actions(episode_id);
create index if not exists idx_agents_ppi_score on public.agents(ppi_score desc);
create index if not exists idx_agents_irr on public.agents(irr desc);

-- Enable Row Level Security (RLS)
alter table public.agents enable row level security;
alter table public.episodes enable row level security;
alter table public.actions enable row level security;
alter table public.settings enable row level security;

-- Create policies for public read access (no auth required for this demo)
create policy "Allow public read access to agents"
  on public.agents for select
  using (true);

create policy "Allow public insert to agents"
  on public.agents for insert
  with check (true);

create policy "Allow public update to agents"
  on public.agents for update
  using (true);

create policy "Allow public read access to episodes"
  on public.episodes for select
  using (true);

create policy "Allow public insert to episodes"
  on public.episodes for insert
  with check (true);

create policy "Allow public read access to actions"
  on public.actions for select
  using (true);

create policy "Allow public insert to actions"
  on public.actions for insert
  with check (true);

create policy "Allow public read access to settings"
  on public.settings for select
  using (true);

create policy "Allow public insert to settings"
  on public.settings for insert
  with check (true);

create policy "Allow public update to settings"
  on public.settings for update
  using (true);
