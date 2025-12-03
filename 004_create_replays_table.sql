-- Create replays table for shareable episode recordings
create table if not exists public.replays (
  id uuid primary key default gen_random_uuid(),
  episode_id uuid references public.episodes(id) on delete cascade,
  agent_id uuid references public.agents(id) on delete cascade,
  title text not null,
  description text,
  irr numeric default 0,
  ppi_score numeric default 0,
  total_steps integer default 0,
  total_reward numeric default 0,
  replay_data jsonb not null, -- Full episode data including all actions, metrics, chart data
  thumbnail_url text,
  is_public boolean default true,
  views integer default 0,
  created_at timestamptz default now()
);

-- Create index for public replays
create index if not exists idx_replays_public on public.replays(is_public, created_at desc);
create index if not exists idx_replays_agent_id on public.replays(agent_id);

-- Enable RLS
alter table public.replays enable row level security;

-- Create policies
create policy "Allow public read access to public replays"
  on public.replays for select
  using (is_public = true);

create policy "Allow public insert to replays"
  on public.replays for insert
  with check (true);

create policy "Allow public update to replays"
  on public.replays for update
  using (true);
