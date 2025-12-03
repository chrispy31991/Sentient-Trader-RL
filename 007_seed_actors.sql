-- Updated to match new schema with regret_score, inventory_btc, last_action, nash_stable, shull_fractal
-- Seed 6 actors with Denise Shull fractals
INSERT INTO actors (name, regret_score, inventory_btc, last_action, nash_stable, shull_fractal) VALUES
  ('Retail', 0.85, 0.5, 0, FALSE, 'Mother abandoned me at $60K - fear of missing out drives every decision'),
  ('Whale', 0.15, 26430.0, 0, TRUE, 'I moved markets in 2017 - I know when retail panics'),
  ('HFT-MM', 0.05, 100.0, 0, TRUE, 'Latency is life - every millisecond is profit'),
  ('Institution', 0.20, 1200.0, 1, TRUE, 'BlackRock never sells the rip - we accumulate on dips'),
  ('Arb Bot', 0.10, 50.0, 0, TRUE, 'Exploit 0.3% spreads across exchanges - pure math'),
  ('Sentient Trader', 0.30, 1.0, 0, FALSE, 'I read the regrets of others and find Nash equilibrium')
ON CONFLICT DO NOTHING;
