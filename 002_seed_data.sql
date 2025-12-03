-- Insert sample agents
insert into public.agents (name, irr, sharpe, ppi_score, episodes_trained) values
  ('Alpha Trader', 0.42, 1.8, 87.5, 1250),
  ('Beta Bot', 0.35, 1.5, 82.3, 980),
  ('Gamma AI', 0.51, 2.1, 91.2, 1580),
  ('Delta Neural', 0.28, 1.2, 76.8, 750),
  ('Epsilon Agent', 0.39, 1.6, 84.1, 1100)
on conflict (id) do nothing;

-- Insert default settings
insert into public.settings (xai_api_key, alpaca_api_key, ppi_weights) values
  ('', '', '{"physiological": 0.2, "safety": 0.2, "belonging": 0.2, "esteem": 0.2, "self_actualization": 0.2}'::jsonb)
on conflict (id) do nothing;
