from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Dict, List
from datetime import datetime
import uuid
import random
import os
import asyncio
import httpx
from supabase import create_client, Client

# Initialize FastAPI app
app = FastAPI(title="Sentient Trader API", version="1.0.0")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase_url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# Grok API endpoint (Next.js route)
GROK_API_URL = os.environ.get("NEXT_PUBLIC_TRADER_API_URL", "http://localhost:3000") + "/api/grok/trade"

# In-memory storage for active episodes (use Redis in production)
active_episodes: Dict[str, dict] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}

PPI_TIER_MAP = {
    (0, 20): "Survival (Physiological)",
    (20, 40): "Safety",
    (40, 60): "Belonging",
    (60, 80): "Esteem",
    (80, 100): "Self-Actualization"
}

def get_ppi_tier(ppi_score: float) -> str:
    """Map PPI score to Maslow tier"""
    for (low, high), tier in PPI_TIER_MAP.items():
        if low <= ppi_score < high:
            return tier
    return "Self-Actualization"  # Default for 100


# ============= Pydantic Models =============

class MarketState(BaseModel):
    """Current market state input"""
    price: float = Field(..., description="Current BTC price in USD")
    volume: float = Field(..., description="Trading volume")
    sentiment: float = Field(..., ge=-1.0, le=1.0, description="Market sentiment score (-1 to 1)")
    timestamp: datetime = Field(default_factory=datetime.now)


class Action(BaseModel):
    """Agent action output"""
    type: Literal["buy", "sell", "hold"] = Field(..., description="Action type")
    size: float = Field(..., ge=0.0, le=1.0, description="Position size (0.0 to 1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Grok confidence score")
    reasoning: str = Field(default="", description="Agent reasoning")


class StartEpisodeRequest(BaseModel):
    """Request to start a new episode"""
    agent_name: str = Field(default="Agent-Alpha", description="Name of the trading agent")
    initial_balance: float = Field(default=10000.0, description="Starting balance in USD")


class StartEpisodeResponse(BaseModel):
    """Response with new episode ID"""
    episode_id: str
    agent_id: str
    agent_name: str
    initial_balance: float
    timestamp: datetime


class StepRequest(BaseModel):
    """Request for agent to take a step"""
    episode_id: str
    market_state: MarketState
    current_balance: float
    current_position: float = Field(default=0.0, description="Current BTC position")


class StepResponse(BaseModel):
    """Response with agent action"""
    episode_id: str
    step: int
    action: Action
    timestamp: datetime


class EndEpisodeRequest(BaseModel):
    """Request to end an episode"""
    episode_id: str
    final_pnl: float = Field(..., description="Final profit/loss")
    ppi_score: float = Field(..., ge=0.0, le=100.0, description="PPI trust score")
    total_steps: int
    total_reward: float


class EndEpisodeResponse(BaseModel):
    """Response after ending episode"""
    episode_id: str
    agent_id: str
    saved: bool
    message: str


# ============= Mock RL Agent =============

class MockRLAgent:
    """Simple mock agent that makes random trading decisions"""
    
    def __init__(self, agent_name: str = "Agent-Alpha"):
        self.agent_name = agent_name
        self.step_count = 0
        self.last_action = "hold"
        
    def decide_action(self, market_state: MarketState, current_position: float) -> Action:
        """Make a trading decision based on market state"""
        self.step_count += 1
        
        # Simple random strategy with some logic
        price_momentum = random.uniform(-0.05, 0.05)
        sentiment_weight = market_state.sentiment * 0.3
        
        # Decision logic
        decision_score = price_momentum + sentiment_weight + random.uniform(-0.2, 0.2)
        
        if decision_score > 0.15 and current_position < 0.8:
            action_type = "buy"
            size = random.uniform(0.1, 0.3)
        elif decision_score < -0.15 and current_position > 0.2:
            action_type = "sell"
            size = random.uniform(0.1, min(0.3, current_position))
        else:
            action_type = "hold"
            size = 0.0
        
        confidence = min(0.95, abs(decision_score) + random.uniform(0.3, 0.5))
        
        reasoning = self._generate_reasoning(action_type, decision_score, market_state)
        
        self.last_action = action_type
        
        return Action(
            type=action_type,
            size=round(size, 3),
            confidence=round(confidence, 3),
            reasoning=reasoning
        )
    
    def _generate_reasoning(self, action: str, score: float, state: MarketState) -> str:
        """Generate human-readable reasoning"""
        sentiment_desc = "bullish" if state.sentiment > 0.3 else "bearish" if state.sentiment < -0.3 else "neutral"
        
        if action == "buy":
            return f"Market sentiment is {sentiment_desc} ({state.sentiment:.2f}). Momentum indicator suggests upward movement. Initiating long position."
        elif action == "sell":
            return f"Market sentiment is {sentiment_desc} ({state.sentiment:.2f}). Risk management suggests taking profits. Reducing exposure."
        else:
            return f"Market conditions are {sentiment_desc}. Holding current position and monitoring for clearer signals."


async def get_grok_decision(
    market_state: MarketState,
    current_balance: float,
    current_position: float,
    ppi_score: float
) -> Action:
    """Call Grok API to get AI trading decision"""
    try:
        # Calculate volatility from volume (simplified)
        volatility = min(1.0, market_state.volume / 1000000)
        
        # Get PPI tier
        ppi_tier = get_ppi_tier(ppi_score)
        
        # Calculate capital in BTC
        capital_btc = current_position + (current_balance / market_state.price)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROK_API_URL,
                json={
                    "price": market_state.price,
                    "volatility": volatility,
                    "ppiTier": ppi_tier,
                    "capital": capital_btc
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return Action(
                    type=data["action"],
                    size=data["size"],
                    confidence=0.85,  # Grok confidence
                    reasoning=f"[Grok AI] {data['reasoning']}"
                )
            else:
                print(f"[v0] Grok API error: {response.status_code}")
                raise Exception(f"Grok API returned {response.status_code}")
                
    except Exception as e:
        print(f"[v0] Failed to get Grok decision: {e}")
        # Return fallback action
        return Action(
            type="hold",
            size=0.0,
            confidence=0.5,
            reasoning=f"[Grok AI - Fallback] API unavailable: {str(e)}"
        )


def blend_actions(rl_action: Action, grok_action: Action) -> Action:
    """Blend RL and Grok actions with 50/50 weighted vote"""
    
    # Map actions to numeric values for blending
    action_values = {"buy": 1, "hold": 0, "sell": -1}
    
    rl_value = action_values[rl_action.type]
    grok_value = action_values[grok_action.type]
    
    # 50/50 weighted average
    blended_value = (rl_value + grok_value) / 2
    
    # Convert back to action
    if blended_value > 0.3:
        final_action = "buy"
    elif blended_value < -0.3:
        final_action = "sell"
    else:
        final_action = "hold"
    
    # Blend sizes (average)
    final_size = (rl_action.size + grok_action.size) / 2
    
    # Blend confidence (weighted by agreement)
    agreement = 1.0 if rl_action.type == grok_action.type else 0.5
    final_confidence = ((rl_action.confidence + grok_action.confidence) / 2) * agreement
    
    # Combine reasoning
    final_reasoning = f"[Hybrid Decision]\n• RL Agent: {rl_action.type} ({rl_action.size:.2f}) - {rl_action.reasoning}\n• Grok AI: {grok_action.type} ({grok_action.size:.2f}) - {grok_action.reasoning}\n→ Final: {final_action} ({final_size:.2f})"
    
    return Action(
        type=final_action,
        size=round(final_size, 3),
        confidence=round(final_confidence, 3),
        reasoning=final_reasoning
    )


# ============= API Endpoints =============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Sentient Trader API",
        "status": "operational",
        "version": "1.0.0",
        "supabase_connected": supabase is not None
    }


@app.post("/start", response_model=StartEpisodeResponse)
async def start_episode(request: StartEpisodeRequest):
    """Start a new RL trading episode"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Create or get agent
        agent_result = supabase.table("agents").select("*").eq("name", request.agent_name).execute()
        
        if agent_result.data and len(agent_result.data) > 0:
            agent = agent_result.data[0]
            agent_id = agent["id"]
            # Update episodes count
            supabase.table("agents").update({
                "episodes_trained": agent["episodes_trained"] + 1
            }).eq("id", agent_id).execute()
        else:
            # Create new agent
            new_agent = supabase.table("agents").insert({
                "name": request.agent_name,
                "episodes_trained": 1
            }).execute()
            agent_id = new_agent.data[0]["id"]
        
        # Create episode
        episode_number = supabase.table("episodes").select("episode_number").eq("agent_id", agent_id).execute()
        next_episode_num = len(episode_number.data) + 1 if episode_number.data else 1
        
        episode = supabase.table("episodes").insert({
            "agent_id": agent_id,
            "episode_number": next_episode_num,
            "steps": 0,
            "total_reward": 0,
            "ppi_score": 0
        }).execute()
        
        episode_id = episode.data[0]["id"]
        
        # Store in memory
        active_episodes[episode_id] = {
            "agent_id": agent_id,
            "agent_name": request.agent_name,
            "initial_balance": request.initial_balance,
            "current_step": 0,
            "agent": MockRLAgent(request.agent_name),
            "started_at": datetime.now()
        }
        
        # Initialize WebSocket connection list
        websocket_connections[episode_id] = []
        
        return StartEpisodeResponse(
            episode_id=episode_id,
            agent_id=agent_id,
            agent_name=request.agent_name,
            initial_balance=request.initial_balance,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start episode: {str(e)}")


@app.post("/step", response_model=StepResponse)
async def take_step(request: StepRequest):
    """Agent takes a step in the environment"""
    
    episode_id = request.episode_id
    
    if episode_id not in active_episodes:
        raise HTTPException(status_code=404, detail="Episode not found or already ended")
    
    episode_data = active_episodes[episode_id]
    agent: MockRLAgent = episode_data["agent"]
    
    # Get RL agent decision
    rl_action = agent.decide_action(request.market_state, request.current_position)
    
    # Get current PPI score (default to 75 if not available)
    current_ppi = episode_data.get("ppi_score", 75.0)
    
    # Get Grok decision
    grok_action = await get_grok_decision(
        request.market_state,
        request.current_balance,
        request.current_position,
        current_ppi
    )
    
    # Blend both decisions (50/50 weighted vote)
    action = blend_actions(rl_action, grok_action)
    
    # Increment step
    episode_data["current_step"] += 1
    current_step = episode_data["current_step"]
    
    # Calculate reward (simplified)
    reward = 0.0
    if action.type == "buy":
        reward = random.uniform(-0.5, 1.5) * action.size
    elif action.type == "sell":
        reward = random.uniform(-0.5, 2.0) * action.size
    else:
        reward = random.uniform(-0.1, 0.1)
    
    # Update PPI score based on action quality
    ppi_delta = reward * 2  # Simplified PPI calculation
    episode_data["ppi_score"] = max(0, min(100, current_ppi + ppi_delta))
    
    # Save action to database
    if supabase:
        try:
            supabase.table("actions").insert({
                "episode_id": episode_id,
                "step": current_step,
                "action_type": action.type,
                "size": action.size,
                "price": request.market_state.price,
                "reward": reward,
                "grok_confidence": action.confidence
            }).execute()
        except Exception as e:
            print(f"[v0] Failed to save action: {e}")
    
    response = StepResponse(
        episode_id=episode_id,
        step=current_step,
        action=action,
        timestamp=datetime.now()
    )
    
    # Broadcast to WebSocket clients
    await broadcast_to_episode(episode_id, {
        "type": "step",
        "data": response.dict()
    })
    
    return response


@app.post("/end", response_model=EndEpisodeResponse)
async def end_episode(request: EndEpisodeRequest):
    """End an episode and save results"""
    
    episode_id = request.episode_id
    
    if episode_id not in active_episodes:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    episode_data = active_episodes[episode_id]
    agent_id = episode_data["agent_id"]
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Update episode with final stats
        supabase.table("episodes").update({
            "total_reward": request.total_reward,
            "steps": request.total_steps,
            "ppi_score": request.ppi_score
        }).eq("id", episode_id).execute()
        
        # Calculate IRR and Sharpe (simplified)
        irr = (request.final_pnl / episode_data["initial_balance"]) * 100
        sharpe = irr / max(1, request.total_steps / 10)  # Simplified Sharpe
        
        # Update agent stats
        agent = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if agent.data:
            current_agent = agent.data[0]
            episodes_count = current_agent["episodes_trained"]
            
            # Running average
            new_irr = ((current_agent["irr"] or 0) * (episodes_count - 1) + irr) / episodes_count
            new_sharpe = ((current_agent["sharpe"] or 0) * (episodes_count - 1) + sharpe) / episodes_count
            new_ppi = ((current_agent["ppi_score"] or 0) * (episodes_count - 1) + request.ppi_score) / episodes_count
            
            supabase.table("agents").update({
                "irr": new_irr,
                "sharpe": new_sharpe,
                "ppi_score": new_ppi
            }).eq("id", agent_id).execute()
        
        # Broadcast end event
        await broadcast_to_episode(episode_id, {
            "type": "end",
            "data": {
                "episode_id": episode_id,
                "final_pnl": request.final_pnl,
                "ppi_score": request.ppi_score,
                "irr": irr,
                "sharpe": sharpe
            }
        })
        
        # Clean up
        del active_episodes[episode_id]
        if episode_id in websocket_connections:
            # Close all WebSocket connections
            for ws in websocket_connections[episode_id]:
                try:
                    await ws.close()
                except:
                    pass
            del websocket_connections[episode_id]
        
        return EndEpisodeResponse(
            episode_id=episode_id,
            agent_id=agent_id,
            saved=True,
            message="Episode ended and saved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end episode: {str(e)}")


# ============= WebSocket Endpoint =============

@app.websocket("/ws/episode/{episode_id}")
async def websocket_episode(websocket: WebSocket, episode_id: str):
    """WebSocket endpoint for real-time episode updates"""
    
    await websocket.accept()
    
    if episode_id not in active_episodes:
        await websocket.send_json({
            "type": "error",
            "message": "Episode not found"
        })
        await websocket.close()
        return
    
    # Add to connections
    if episode_id not in websocket_connections:
        websocket_connections[episode_id] = []
    websocket_connections[episode_id].append(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "episode_id": episode_id,
            "message": "Connected to episode stream"
        })
        
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({
                "type": "ack",
                "message": "Message received"
            })
            
    except WebSocketDisconnect:
        # Remove from connections
        if episode_id in websocket_connections:
            websocket_connections[episode_id].remove(websocket)
    except Exception as e:
        print(f"[v0] WebSocket error: {e}")
        if episode_id in websocket_connections and websocket in websocket_connections[episode_id]:
            websocket_connections[episode_id].remove(websocket)


async def broadcast_to_episode(episode_id: str, message: dict):
    """Broadcast message to all WebSocket clients for an episode"""
    if episode_id not in websocket_connections:
        return
    
    disconnected = []
    for websocket in websocket_connections[episode_id]:
        try:
            await websocket.send_json(message)
        except:
            disconnected.append(websocket)
    
    # Clean up disconnected clients
    for ws in disconnected:
        websocket_connections[episode_id].remove(ws)


# ============= Additional Utility Endpoints =============

@app.get("/episodes/active")
async def get_active_episodes():
    """Get list of currently active episodes"""
    return {
        "active_episodes": [
            {
                "episode_id": ep_id,
                "agent_name": data["agent_name"],
                "current_step": data["current_step"],
                "started_at": data["started_at"].isoformat()
            }
            for ep_id, data in active_episodes.items()
        ]
    }


@app.get("/agent/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """Get statistics for a specific agent"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        agent = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if not agent.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        episodes = supabase.table("episodes").select("*").eq("agent_id", agent_id).execute()
        
        return {
            "agent": agent.data[0],
            "total_episodes": len(episodes.data) if episodes.data else 0,
            "episodes": episodes.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
