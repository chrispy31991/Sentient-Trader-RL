A hybrid RL-Grok trading backend for episode-based decision blending. This repo is the public backbone—clone it to experiment with the core API structure, mock RL logic, and Grok integration via a Next.js proxy.
Important Disclaimer:
This is a demo-ready skeleton for educational and starter purposes only. The full project includes proprietary components like real RL training (PPO agents via Gym environments), live market data hooks (e.g., yfinance/Polygon integrations), backtesting modules, and episode analytics dashboards. These are housed in private forks to protect ongoing development and integrations with two companion apps (a data feeder and portfolio visualizer). If you're cloning to build on this, focus on extending the hybrid logic—PRs welcome for public enhancements! For the complete "sentient" trader (with alpha-proven strategies and regenerative PPI ethics), reach out via DM or issues for collab discussions.
Quick Start:

Clone and install: pip install -r requirements.txt
Set env vars for Supabase and Grok proxy.
Run: uvicorn main:app --reload
Test endpoints with the included script: python scripts/test_api.py

Not financial advice—trade at your own risk. Built solo while juggling farms and AI apps. 🚀

# Sentient Trader FastAPI Backend

Python FastAPI backend for the Sentient Trader RL trading platform with **Grok AI integration**.

## Features

- **POST /start** - Start a new RL trading episode
- **POST /step** - Agent takes a step and returns action (Grok + RL hybrid)
- **POST /end** - End episode and save results to Supabase
- **WebSocket /ws/episode/{id}** - Real-time episode updates
- **GET /episodes/active** - List active episodes
- **GET /agent/{id}/stats** - Get agent statistics

## 🤖 Hybrid AI Decision System

The backend implements a **50/50 weighted voting system** that blends:

1. **Mock RL Agent** - Traditional reinforcement learning with momentum and sentiment analysis
2. **Grok AI** - xAI's Grok model via Next.js API route with regenerative trust optimization

### How It Works

Each `/step` request:
1. Gets decision from RL agent (buy/sell/hold + size)
2. Calls Grok API with market state and PPI tier
3. Blends both decisions with 50/50 weighting
4. Returns hybrid action with combined reasoning

**Action Blending Logic:**
- Actions mapped to numeric values: buy=1, hold=0, sell=-1
- Weighted average determines final action
- Position sizes averaged between both agents
- Confidence adjusted based on agreement level

**Fallback:** If Grok API fails (network/timeout), system defaults to RL-only decision with fallback reasoning.

## Mock RL Agent

The `MockRLAgent` class implements a simple random trading strategy:
- Analyzes market sentiment and price momentum
- Makes buy/sell/hold decisions with position sizing
- Generates human-readable reasoning for each action
- Tracks confidence scores

## Grok Integration

The system calls the Next.js Grok API endpoint at `/api/grok/trade`:

**Request:**
\`\`\`json
{
  "price": 45000.0,
  "volatility": 0.15,
  "ppiTier": "Esteem",
  "capital": 0.5
}
\`\`\`

**Response:**
\`\`\`json
{
  "action": "buy",
  "size": 0.3,
  "reasoning": "Market conditions favorable..."
}
\`\`\`

**Features:**
- Retry logic with exponential backoff (3 attempts)
- Response caching (last 5 decisions)
- PPI tier mapping (Maslow hierarchy)
- Graceful fallback on failure

## Deployment Options

### Option 1: Railway (Recommended for WebSockets)

1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Add environment variables:
   \`\`\`bash
   railway variables set NEXT_PUBLIC_SUPABASE_URL=your_url
   railway variables set SUPABASE_SERVICE_ROLE_KEY=your_key
   railway variables set NEXT_PUBLIC_TRADER_API_URL=https://your-nextjs-app.vercel.app
   \`\`\`
5. Deploy: `railway up`

### Option 2: Render

1. Connect your GitHub repo to Render
2. Create a new Web Service
3. Use the `render.yaml` configuration
4. Add environment variables in Render dashboard
5. Deploy automatically on push

### Option 3: Vercel Serverless (Limited WebSocket Support)

**Note:** Vercel Serverless Functions have limitations with WebSockets. For full WebSocket support, use Railway or Render.

1. The `vercel.json` is already configured
2. Deploy: `vercel --prod`
3. WebSocket endpoint may not work; consider using polling or Server-Sent Events instead

## Local Development

\`\`\`bash
cd api/trader
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
\`\`\`

**Important:** Make sure your Next.js app is running on port 3000 for Grok integration:
\`\`\`bash
npm run dev
\`\`\`

Visit http://localhost:8000/docs for interactive API documentation.

## Environment Variables

Required:
- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for server-side operations)
- `NEXT_PUBLIC_TRADER_API_URL` - Next.js app URL (default: http://localhost:3000)

## API Usage Examples

### Start Episode
\`\`\`bash
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "Agent-Alpha", "initial_balance": 10000}'
\`\`\`

### Take Step (with Grok + RL Hybrid)
\`\`\`bash
curl -X POST http://localhost:8000/step \
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
\`\`\`

**Response includes hybrid reasoning:**
\`\`\`json
{
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
\`\`\`

### End Episode
\`\`\`bash
curl -X POST http://localhost:8000/end \
  -H "Content-Type: application/json" \
  -d '{
    "episode_id": "uuid-here",
    "final_pnl": 500,
    "ppi_score": 75.5,
    "total_steps": 100,
    "total_reward": 25.5
  }'
\`\`\`

### WebSocket Connection
\`\`\`javascript
const ws = new WebSocket('ws://localhost:8000/ws/episode/uuid-here');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
\`\`\`

## Testing

Run the comprehensive test suite:

\`\`\`bash
python scripts/test_api.py
\`\`\`

This will:
- Test health check endpoint
- Verify Grok API connectivity
- Start a trading episode
- Execute 5 steps with hybrid decisions
- Display detailed reasoning from both agents
- End episode and save to Supabase

## Integration with Next.js Frontend

Update your Next.js environment variables:

\`\`\`env
NEXT_PUBLIC_TRADER_API_URL=https://your-api-url.railway.app
NEXT_PUBLIC_TRADER_WS_URL=wss://your-api-url.railway.app
\`\`\`

Then use in your frontend:
\`\`\`typescript
const response = await fetch(`${process.env.NEXT_PUBLIC_TRADER_API_URL}/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ agent_name: 'Agent-Alpha', initial_balance: 10000 })
});
\`\`\`

## Architecture

\`\`\`
┌─────────────────┐
│   Next.js App   │
│  (Port 3000)    │
│                 │
│  /api/grok/     │◄─────┐
│    trade        │      │
└─────────────────┘      │
                         │ HTTP Request
                         │
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
\`\`\`

## PPI Trust Score

The system tracks PPI (Positive Planetary Impact) scores based on Maslow's hierarchy:

- **0-20**: Survival (Physiological)
- **20-40**: Safety
- **40-60**: Belonging
- **60-80**: Esteem
- **80-100**: Self-Actualization

Grok receives the current PPI tier to optimize for regenerative trust while maximizing returns.
