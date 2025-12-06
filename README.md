Sentient-Trader-RL
A hybrid RL-Grok trading backend for episode-based decision blending. This repo serves as the public backbone—clone it to experiment with the core API structure, mock RL logic, and Grok integration via a Next.js proxy.
Important Disclaimer:
This is a demo-ready skeleton for educational and starter purposes only. The full project includes proprietary components like real RL training (PPO agents via Gym environments), live market data hooks (e.g., yfinance/Polygon integrations), backtesting modules, and episode analytics dashboards. These are housed in private forks to protect ongoing development and integrations with two companion apps (a data feeder and portfolio visualizer). If you're cloning to build on this, focus on extending the hybrid logic—PRs welcome for public enhancements! For the complete "sentient" trader (with alpha-proven strategies and regenerative PPI ethics), reach out via DM or issues for collab discussions.
Features

POST /start: Initialize a new RL trading episode with agent configuration and initial balance.
POST /step: Execute a single trading step using hybrid RL-Grok decision blending.
POST /end: Conclude an episode and persist results to Supabase.
WebSocket /ws/episode/{id}: Real-time updates for episode progress and decisions.
GET /episodes/active: Retrieve list of active trading episodes.
GET /agent/{id}/stats: Fetch statistics for a specific agent.

Hybrid AI Decision System
The backend employs a 50/50 weighted voting system that combines:

Mock RL Agent: Traditional reinforcement learning simulation with momentum and sentiment analysis.
Grok AI: xAI's Grok model queried via a Next.js API route, optimized for regenerative trust.

How It Works
Each /step request:

Computes a decision from the RL agent (buy/sell/hold + position size).
Queries Grok API with market state and PPI tier.
Blends decisions with 50/50 weighting.
Returns hybrid action with combined reasoning.

Action Blending Logic:

Actions mapped numerically: buy=1, hold=0, sell=-1.
Weighted average determines final action and position size.
Confidence adjusted based on agent agreement.
Fallback: Defaults to RL-only on Grok failure, with cached priors.

Mock RL Agent
The MockRLAgent class simulates a basic trading strategy:

Analyzes market sentiment and price momentum.
Generates buy/sell/hold decisions with sizing and confidence.
Provides human-readable reasoning for each action.

Grok Integration
Integrates with a Next.js endpoint at /api/grok/trade:

Request Example:JSON{
  "price": 45000.0,
  "volatility": 0.15,
  "ppiTier": "Esteem",
  "capital": 0.5
}
Response Example:JSON{
  "action": "buy",
  "size": 0.3,
  "reasoning": "Market conditions favorable..."
}
Features: Retry with exponential backoff (3 attempts), response caching (last 5 decisions), PPI tier mapping.

Architecture
text┌─────────────────┐
│   Next.js App   │
│  (Port 3000)    │
│                 │
│  /api/grok/     │◄─────┐
│    trade        │      │
└─────────────────┘      │
          │              │
          │ HTTP Request │
          │              │
┌─────────────────┐      │
│  FastAPI        │      │
│  (Port 8000)    │──────┘
│                 │
│  /step endpoint │
│  - RL Agent     │
│  - Grok Call    │
│  - 50/50 Blend  │
└─────────────────┘
          │
          ▼
┌─────────────────┐
│   Supabase      │
│   Database      │
└─────────────────┘
PPI Trust Score
Tracks PPI (Positive Planetary Impact) scores based on Maslow's hierarchy:

0-20: Survival (Physiological)
20-40: Safety
40-60: Belonging
60-80: Esteem
80-100: Self-Actualization

Grok receives the current PPI tier to balance regenerative impact with returns.
Quick Start

Clone the repo:textgit clone https://github.com/chrispy31991/Sentient-Trader-RL.git
cd Sentient-Trader-RL
Install dependencies:textpip install -r requirements.txt
Set environment variables:textexport NEXT_PUBLIC_SUPABASE_URL=your_url
export SUPABASE_SERVICE_ROLE_KEY=your_key
export NEXT_PUBLIC_TRADER_API_URL=your_api_url  # Default: http://localhost:3000
Run the server:textuvicorn main:app --reload --port 8000
(Optional) Run the Next.js proxy for Grok integration:textcd path/to/nextjs-app  # Your separate Next.js repo
npm run dev  # Runs on port 3000
Test the API:textpython scripts/test_api.py

Visit http://localhost:8000/docs for interactive Swagger documentation.
API Usage Examples
Start Episode
textcurl -X POST "http://localhost:8000/start" \
-H "Content-Type: application/json" \
-d '{"agent_name": "Agent-Alpha", "initial_balance": 10000}'
Take Step
textcurl -X POST "http://localhost:8000/step" \
-H "Content-Type: application/json" \
-d '{
  "episode_id": "uuid-here",
  "market_state": {
    "price": 45000,
    "volume": 1000000,
    "sentiment": 0.5
  },
  "current_balance": 10000,
  "current_position": 0.0
}'
Response includes hybrid reasoning:
JSON{
  "episode_id": "uuid",
  "step": 1,
  "action": {
    "type": "buy",
    "size": 0.25,
    "confidence": 0.78,
    "reasoning": "[Hybrid Decision]\n• RL Agent: buy (0.2) - Market sentiment is bullish...\n• Grok AI: buy (0.3) - Favorable conditions for accumulation...\n→ Final: buy (0.25)"
  },
  "timestamp": "2025-01-15T10:30:00"
}
End Episode
textcurl -X POST "http://localhost:8000/end" \
-H "Content-Type: application/json" \
-d '{
  "episode_id": "uuid-here",
  "final_pnl": 500,
  "ppi_score": 75.5,
  "total_steps": 100,
  "total_reward": 25.5
}'
WebSocket Connection (JavaScript Example)
JavaScriptconst ws = new WebSocket('ws://localhost:8000/ws/episode/uuid-here');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
Testing
The test suite (scripts/test_api.py) verifies:

Health checks
Grok connectivity
Full episode lifecycle (start, 5 steps with hybrid decisions, end)
Supabase persistence

Run with:
textpython scripts/test_api.py
Deployment Options
Railway (Recommended for WebSockets)

Install Railway CLI: npm i -g @railway/cli
Initialize: railway init
Set env vars: railway variables set ... (see above)
Deploy: railway up

Render

Connect GitHub repo to Render.
Create Web Service with render.yaml.
Add env vars in dashboard.
Auto-deploy on push.

Vercel Serverless (Limited WebSocket Support)
Note: Vercel has WebSocket limitations; use polling/SSE for alternatives.

Use vercel.json config.
Deploy: vercel --prod

Local Development
Backend:
textuvicorn main:app --reload --port 8000
Frontend Proxy (Next.js):
textnpm run dev  # Port 3000
Environment Variables

NEXT_PUBLIC_SUPABASE_URL: Supabase project URL
SUPABASE_SERVICE_ROLE_KEY: Supabase service role key
NEXT_PUBLIC_TRADER_API_URL: Next.js app URL (default: http://localhost:3000)

Contributing
Fork, extend the hybrid logic, and submit PRs for public enhancements. For private collab on full sentient features, open an issue or DM.
Not financial advice—trade at your own risk. Built solo while juggling farms and AI apps. 🚀
