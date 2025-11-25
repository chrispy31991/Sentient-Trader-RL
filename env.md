# Sentient Trader Gymnasium Environment

A fully-featured Gymnasium environment for training reinforcement learning agents to trade Bitcoin with PPI (Prosocial Performance Index) trust scoring.

## Features

- **Hybrid Decision Making**: 50/50 blend of RL agent and Grok AI recommendations
- **PPI Trust Scoring**: Maslow hierarchy-based trust evaluation across 4 tiers
- **Comprehensive Reporting**: Mood snapshots, mental debris tracking, trigger alerts, and affirmations
- **Market Simulation**: Realistic price dynamics with volatility modeling
- **Trade History**: Full tracking of all trades, PnL, and drawdowns

## Installation

\`\`\`bash
pip install gymnasium numpy requests
\`\`\`

## Usage

### Basic Training Loop

\`\`\`python
from api.env import SentientTraderEnv

# Create environment
env = SentientTraderEnv(api_base_url="http://localhost:3000")

# Reset environment
obs, info = env.reset()
print(f"Affirmation: {info['report']['affirmation']}")

# Training loop
for episode in range(100):
    obs, info = env.reset()
    total_reward = 0
    
    for step in range(1000):
        # Your RL agent selects action
        action = agent.select_action(obs)
        
        # Step environment
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        if terminated:
            print(f"Episode {episode} completed!")
            print(f"Total Reward: {total_reward:.2f}")
            print(f"Final PPI: {info['ppi']:.1f}")
            print(f"PnL: {info['pnl_pct']:.2f}%")
            break
\`\`\`

### With Stable-Baselines3

\`\`\`python
from stable_baselines3 import PPO
from api.env import SentientTraderEnv

# Create environment
env = SentientTraderEnv()

# Train PPO agent
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100000)

# Save model
model.save("sentient_trader_ppo")

# Test trained agent
obs, info = env.reset()
for _ in range(1000):
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated:
        break
\`\`\`

## Observation Space

5-dimensional continuous space:
- `price`: Current BTC price (USD)
- `volatility`: Market volatility (0-1)
- `capital`: Current capital (BTC)
- `progress`: Episode progress (0-1)
- `sentiment`: Market sentiment proxy (0-1)

## Action Space

Discrete(3):
- `0`: Hold
- `1`: Buy (10% of capital)
- `2`: Sell (10% of capital)

## Reward Function

\`\`\`python
reward = log(PnL) + 0.1 * (PPI_score / 100)
\`\`\`

Combines:
- **Log PnL**: Logarithmic profit/loss for stable gradients
- **PPI Bonus**: 10% weight on trust score to encourage prosocial behavior

## PPI Trust Scoring

Based on Maslow's hierarchy:

1. **Safety (40%)**: Volatility < 5%, Drawdown < 10%
2. **Belonging (20%)**: Community engagement (mock upvotes)
3. **Esteem (20%)**: Consistent alpha > benchmark
4. **Self-Actualization (20%)**: Regenerative energy use (solar %)

## Report Data

Each episode generates a comprehensive report:

\`\`\`python
{
    "mood_snapshot": "Neutral with cautious optimism",
    "mental_debris": "Processing ETF inflows...",
    "trigger_watch": "Alert for Fed uncertainty",
    "affirmation": "Today I act from data and plan",
    "market_summary": {
        "prev_close": 112000,
        "change": 2.5,
        "drivers": "Institutional accumulation"
    },
    "ppi_composite": 85.5,
    "macro_bias": "Bullish",
    "short_term_risk": "Moderate",
    "recommendation": "Hold core positions",
    "silos": [
        {"name": "Sentiment", "score": 3.5, "inputs": "MPT 40%"}
    ]
}
\`\`\`

## Integration with Grok AI

The environment calls the Grok API for hybrid decision-making:

\`\`\`python
# Grok provides reasoning and action
grok_action = {
    "action": "buy",
    "size": 0.1,
    "reasoning": "Strong momentum with low volatility"
}

# 50% chance to use Grok's recommendation
final_action = grok_vote if random() < 0.5 else rl_action
\`\`\`

## Configuration

Set environment variables:

\`\`\`bash
export NEXT_PUBLIC_TRADER_API_URL="http://localhost:3000"
\`\`\`

Or pass directly:

\`\`\`python
env = SentientTraderEnv(api_base_url="https://your-app.vercel.app")
\`\`\`

## Example Output

\`\`\`
=== Step 100 ===
Price: $113,245.67
Capital: 1.0234 BTC
Volatility: 3.45%
PnL: 2.34%
Drawdown: 1.23%

Step 101:
  Action: buy (Grok: buy)
  Reward: 0.0234
  PPI: 87.5
  PnL: 2.45%
\`\`\`

## Advanced Features

### Custom Reward Shaping

\`\`\`python
class CustomSentientTraderEnv(SentientTraderEnv):
    def step(self, action):
        obs, reward, terminated, truncated, info = super().step(action)
        
        # Add custom reward shaping
        if info['drawdown'] > 15:
            reward -= 0.5  # Penalize high drawdown
        
        return obs, reward, terminated, truncated, info
\`\`\`

### Multi-Asset Support (Future)

\`\`\`python
env = SentientTraderEnv(assets=["BTC", "ETH", "SOL"])
\`\`\`

## Deployment

The environment integrates seamlessly with the Sentient Trader dashboard:

1. Start the Next.js app: `npm run dev`
2. Run the Python backend: `uvicorn api.trader.main:app --reload`
3. Train your agent: `python train.py`
4. View results in the dashboard: `http://localhost:3000/arena`

## License

MIT
