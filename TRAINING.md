# Sentient Trader - RL Training Guide

## Overview

Train a PPO (Proximal Policy Optimization) agent that combines reinforcement learning with Grok AI for hybrid trading decisions. The agent learns to maximize risk-adjusted returns while maintaining high PPI (Prosocial Performance Index) trust scores.

## Architecture

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                    Training Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   RL Agent   │◄────►│   Grok AI    │                    │
│  │     (PPO)    │      │  (via API)   │                    │
│  └──────┬───────┘      └──────────────┘                    │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │   Hybrid Decision (50/50 blend)      │                  │
│  └──────┬───────────────────────────────┘                  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │   SentientTraderEnv (Gymnasium)      │                  │
│  │   • Market simulation                 │                  │
│  │   • PPI calculation                   │                  │
│  │   • Real market data (CoinGecko)     │                  │
│  └──────┬───────────────────────────────┘                  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │   Supabase Logging                    │                  │
│  │   • Episodes                          │                  │
│  │   • PPI scores                        │                  │
│  │   • Reports                           │                  │
│  └──────────────────────────────────────┘                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
\`\`\`

## Installation

\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install stable-baselines3 gymnasium torch supabase-py requests numpy tensorboard
\`\`\`

## Configuration

Set environment variables:

\`\`\`bash
export XAI_API_KEY=sk-...                    # xAI Grok API key
export SUPABASE_URL=https://xyz.supabase.co  # Supabase project URL
export SUPABASE_ANON_KEY=eyJ...              # Supabase anon key
export NEXT_PUBLIC_TRADER_API_URL=http://localhost:3000  # Next.js API URL
\`\`\`

Or create a `.env` file:

\`\`\`env
XAI_API_KEY=sk-...
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_TRADER_API_URL=http://localhost:3000
\`\`\`

## Training

### Basic Training (100k timesteps)

\`\`\`bash
python train_sentient_trader.py
\`\`\`

This will:
1. Initialize the PPO agent with MLP policy
2. Create the SentientTraderEnv with real market data
3. Train for 100,000 timesteps (~100 episodes)
4. Log progress every 10 episodes
5. Save model to `sentient_trader_ppo.zip`
6. Log episodes to Supabase

### Training Output

\`\`\`
============================================================
SENTIENT TRADER - RL Training Pipeline
============================================================
Grok API: ✓
Supabase: ✓
Device: cuda
============================================================

Starting training... (100k timesteps)
Press Ctrl+C to stop early

============================================================
Episode 10
Avg Reward (last 10): 0.1234
Avg PPI (last 10): 67.45
============================================================

[v0] Episode logged to Supabase: PPI=68.2
\`\`\`

### Monitor Training with TensorBoard

\`\`\`bash
tensorboard --logdir=./sentient_trader_tensorboard/
\`\`\`

Open http://localhost:6006 to view:
- Episode rewards
- Policy loss
- Value loss
- Entropy
- Learning rate

## Inference

Test the trained agent:

\`\`\`bash
python infer.py
\`\`\`

Output:

\`\`\`
============================================================
SENTIENT TRADER - Inference Mode
============================================================
✓ Model loaded: sentient_trader_ppo.zip

Running episode...
Step 100/1000 | Portfolio: 1.0234 | PPI: 65.3
Step 200/1000 | Portfolio: 1.0456 | PPI: 68.7
...

============================================================
FINAL REPORT
============================================================
{
  "mood_snapshot": "Neutral with cautious optimism",
  "mental_debris": "Processed $26.9B ETF inflows",
  "trigger_watch": "Alert for vol from Fed; watch $114K support",
  "affirmation": "Today I act from data and plan, not from reactions.",
  "market_summary": {
    "asset": "BTC",
    "prev_close": 115148,
    "current": 114335,
    "change": -0.006,
    "drivers": "Neutral sentiment; ETF buffer vs. Fed uncertainty"
  },
  "ppi_composite": 67.4,
  "macro_bias": "Bullish",
  "short_term_risk": "Moderate",
  "recommendation": "Hold core above $114K",
  "silos": [
    {"name": "Sentiment", "score": 5.2, "weight": 0.4, "inputs": "Fear & Greed: 52, MPT 40%"},
    {"name": "Flow", "score": 10.0, "weight": 0.2, "inputs": "ETF Inflows: $26.9B"},
    {"name": "Tech", "score": 7.0, "weight": 0.15, "inputs": "Solar Regen: Yes"},
    {"name": "Macro", "score": 8.0, "weight": 0.15, "inputs": "Whale Accum: 26430 BTC"},
    {"name": "Esteem", "score": 7.8, "weight": 0.1, "inputs": "Sharpe: 0.90"}
  ],
  "performance": {
    "final_value": 1.0456,
    "return": 4.56,
    "sharpe": 0.90,
    "max_drawdown": 2.3
  }
}

============================================================
Total Reward: 12.3456
Final Portfolio Value: 1.0456
Return: 4.56%
PPI Score: 67.4/100
============================================================
\`\`\`

## Hyperparameter Tuning

Edit `train_sentient_trader.py` to adjust:

\`\`\`python
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,      # Learning rate
    n_steps=2048,            # Steps per update
    batch_size=64,           # Batch size
    gae_lambda=0.95,         # GAE lambda
    gamma=0.99,              # Discount factor
    clip_range=0.2,          # PPO clip range
    ent_coef=0.01,           # Entropy coefficient
    vf_coef=0.5,             # Value function coefficient
)
\`\`\`

## PPI Calculation

The Hybrid PPI score combines 5 silos:

1. **Sentiment (40%)** - Fear & Greed Index (0-100)
2. **Flow (20%)** - ETF Inflows ($B)
3. **Tech (15%)** - Solar/Regenerative Energy (Yes/No)
4. **Macro (15%)** - Whale Accumulation (BTC)
5. **Esteem (10%)** - Sharpe Ratio

Formula:
\`\`\`
PPI = (Sentiment × 0.4 + Flow × 0.2 + Tech × 0.15 + Macro × 0.15 + Esteem × 0.1) × 10
\`\`\`

## Deployment

### Local Testing

\`\`\`bash
# Terminal 1: Start Next.js frontend
npm run dev

# Terminal 2: Start FastAPI backend
cd api/trader
uvicorn main:app --reload --port 8000

# Terminal 3: Train agent
python train_sentient_trader.py
\`\`\`

### Production Training (Cloud)

**Google Colab:**

\`\`\`python
!git clone https://github.com/your-repo/sentient-trader.git
%cd sentient-trader
!pip install -r requirements.txt

import os
os.environ["XAI_API_KEY"] = "sk-..."
os.environ["SUPABASE_URL"] = "https://..."
os.environ["SUPABASE_ANON_KEY"] = "eyJ..."

!python train_sentient_trader.py
\`\`\`

**AWS/GCP/Azure:**

Use GPU instances for faster training:
- AWS: `p3.2xlarge` (V100 GPU)
- GCP: `n1-standard-8` + `nvidia-tesla-v100`
- Azure: `NC6s_v3` (V100 GPU)

## Troubleshooting

### Grok API Errors

If Grok API fails, the agent falls back to random actions:

\`\`\`python
[v0] Grok API error: Connection timeout
\`\`\`

**Solution:** Check `XAI_API_KEY` and network connectivity.

### Supabase Connection Issues

\`\`\`python
[v0] Error logging episode: Connection refused
\`\`\`

**Solution:** Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY`.

### Low PPI Scores

If PPI scores are consistently low (<50):

1. Check market data sources (CoinGecko, Fear & Greed)
2. Adjust PPI weights in `calculate_hybrid_ppi()`
3. Increase training timesteps
4. Tune hyperparameters

## Next Steps

1. **Longer Training:** Increase to 1M+ timesteps for better convergence
2. **Hyperparameter Search:** Use Optuna for automated tuning
3. **Multi-Asset:** Extend to ETH, SOL, etc.
4. **Live Trading:** Connect to Alpaca/Binance APIs
5. **Ensemble Models:** Combine multiple trained agents

## Resources

- [Stable Baselines3 Docs](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Docs](https://gymnasium.farama.org/)
- [PPO Paper](https://arxiv.org/abs/1707.06347)
- [xAI Grok API](https://x.ai/api)
