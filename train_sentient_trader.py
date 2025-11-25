"""
Sentient Trader - Stable Baselines3 Training Script
Trains a PPO agent with Grok AI hybrid policy and PPI trust scoring
"""

import gymnasium as gym
import numpy as np
import torch as th
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
import requests
import json
import time
from datetime import datetime
import os
from supabase import create_client
from typing import Dict, Any, Tuple, List

# === CONFIG ===
GROK_API_KEY = os.getenv("XAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
NEXT_API_URL = os.getenv("NEXT_PUBLIC_TRADER_API_URL", "http://localhost:3000")

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true"
FNG_URL = "https://api.alternative.me/fng/"

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# === PPI Calculation (Hybrid Silos) ===
def calculate_hybrid_ppi(episode_data: Dict[str, Any]) -> Tuple[float, List[Dict]]:
    """
    Calculate Hybrid PPI score with multi-factor silos
    Based on Maslow hierarchy: Safety, Belonging, Esteem, Self-Actualization
    """
    # Sentiment (40% weight) - Fear & Greed Index
    fear_greed = episode_data.get("fear_greed", 50)
    sentiment_score = fear_greed / 10  # 0-10 scale
    
    # Flow (20% weight) - ETF Inflows
    etf_inflows = episode_data.get("etf_inflows", 0)
    flow_score = min(etf_inflows / 1e9, 10)  # $1B = 10 points
    
    # Tech (15% weight) - Solar/Regenerative Energy
    solar_regen = episode_data.get("solar_regen", False)
    tech_score = 7.0 if solar_regen else 3.0
    
    # Macro (15% weight) - Whale Accumulation
    whale_accum = episode_data.get("whale_accum", 0)
    macro_score = 8.0 if whale_accum > 20000 else 4.0
    
    # Esteem (10% weight) - Sharpe Ratio
    sharpe = episode_data.get("sharpe", 0)
    esteem_score = 6.0 + (sharpe * 2)
    
    silos = [
        {
            "name": "Sentiment",
            "score": round(sentiment_score, 2),
            "weight": 0.4,
            "inputs": f"Fear & Greed: {fear_greed}, MPT 40%"
        },
        {
            "name": "Flow",
            "score": round(flow_score, 2),
            "weight": 0.2,
            "inputs": f"ETF Inflows: ${etf_inflows/1e9:.1f}B"
        },
        {
            "name": "Tech",
            "score": round(tech_score, 2),
            "weight": 0.15,
            "inputs": f"Solar Regen: {'Yes' if solar_regen else 'No'}"
        },
        {
            "name": "Macro",
            "score": round(macro_score, 2),
            "weight": 0.15,
            "inputs": f"Whale Accum: {whale_accum} BTC"
        },
        {
            "name": "Esteem",
            "score": round(esteem_score, 2),
            "weight": 0.1,
            "inputs": f"Sharpe: {sharpe:.2f}"
        }
    ]
    
    composite = sum(s["score"] * s["weight"] for s in silos) * 10  # Scale to 0-100
    return composite, silos


# === Grok Call ===
def call_grok(state: np.ndarray) -> Dict[str, Any]:
    """
    Call Grok AI via Next.js API endpoint for trading decision
    """
    price, vol, capital, step_ratio, sentiment = state
    
    try:
        response = requests.post(
            f"{NEXT_API_URL}/api/grok/trade",
            json={
                "price": float(price),
                "volatility": float(vol),
                "capital": float(capital),
                "sentiment": float(sentiment * 10),  # Scale back to 0-10
                "ppi_tier": "safety" if vol < 0.05 else "belonging"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "action": data.get("action", "hold"),
                "size": data.get("size", 0.1),
                "reasoning": data.get("reasoning", "API response")
            }
    except Exception as e:
        print(f"[v0] Grok API error: {e}")
    
    # Fallback to random action
    return {
        "action": np.random.choice(["buy", "sell", "hold"]),
        "size": 0.1,
        "reasoning": "API fallback - random action"
    }


# === Custom Environment ===
class SentientTraderEnv(gym.Env):
    """
    Custom Gymnasium environment for Sentient Trader
    Integrates Grok AI, PPI scoring, and real market data
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(self):
        super().__init__()
        self.action_space = gym.spaces.Discrete(3)  # 0=hold, 1=buy, 2=sell
        self.observation_space = gym.spaces.Box(
            low=0, high=1e6, shape=(5,), dtype=np.float32
        )
        
        self.capital = 1.0
        self.price = 112000
        self.volatility = 0.03
        self.step_count = 0
        self.max_steps = 1000
        self.episode_data = {}
        self.initial_capital = 1.0
        self.max_drawdown = 0.0
        self.peak_value = 1.0
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.capital = 1.0
        self.initial_capital = 1.0
        self.step_count = 0
        self.max_drawdown = 0.0
        self.peak_value = 1.0
        self.price = self._fetch_price()
        
        self.episode_data = {
            "start_time": datetime.utcnow().isoformat(),
            "etf_inflows": 26.9e9,  # Mock: $26.9B
            "whale_accum": 26430,   # Mock: 26,430 BTC
            "solar_regen": True,
            "fear_greed": self._fetch_fng(),
            "sharpe": 0.0
        }
        
        return self._get_obs(), {}
    
    def _fetch_price(self) -> float:
        """Fetch real BTC price from CoinGecko"""
        try:
            data = requests.get(COINGECKO_URL, timeout=5).json()
            return float(data["bitcoin"]["usd"])
        except:
            return 114335.0  # Fallback
    
    def _fetch_fng(self) -> int:
        """Fetch Fear & Greed Index"""
        try:
            data = requests.get(FNG_URL, timeout=5).json()
            return int(data["data"][0]["value"])
        except:
            return 50  # Neutral fallback
    
    def _get_obs(self) -> np.ndarray:
        """Get current observation state"""
        return np.array([
            self.price,
            self.volatility,
            self.capital,
            self.step_count / self.max_steps,
            self.episode_data["fear_greed"] / 100
        ], dtype=np.float32)
    
    def step(self, action: int):
        """Execute one step in the environment"""
        
        # === Grok Hybrid Policy (50/50 blend) ===
        grok_action = call_grok(self._get_obs())
        grok_vote = {"buy": 1, "sell": 2, "hold": 0}.get(grok_action["action"], 0)
        
        # 50% chance to use Grok's decision, 50% RL agent
        final_action = grok_vote if np.random.rand() < 0.5 else action
        
        # Execute trade
        size = grok_action.get("size", 0.1)
        btc_holdings = 1.0 - self.capital
        
        if final_action == 1 and self.capital >= size:  # Buy
            self.capital -= size
        elif final_action == 2 and btc_holdings >= size:  # Sell
            self.capital += size
        
        # Market update (random walk with drift)
        self.price *= np.exp(np.random.randn() * 0.01)
        self.volatility = 0.03 + np.random.rand() * 0.02
        self.step_count += 1
        
        # Calculate portfolio value
        btc_holdings = 1.0 - self.capital
        portfolio_value = self.capital + btc_holdings * (self.price / 112000)
        
        # Track drawdown
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        drawdown = (self.peak_value - portfolio_value) / self.peak_value
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # Calculate Sharpe (simplified)
        returns = (portfolio_value - self.initial_capital) / self.initial_capital
        self.episode_data["sharpe"] = returns / (self.volatility + 1e-6)
        
        # Calculate PPI
        ppi, silos = calculate_hybrid_ppi(self.episode_data)
        
        # Reward: log return + PPI bonus
        log_return = np.log(portfolio_value + 1e-6)
        ppi_bonus = 0.2 * (ppi / 100)
        reward = log_return + ppi_bonus
        
        done = self.step_count >= self.max_steps
        
        info = {
            "ppi": ppi,
            "action": final_action,
            "grok_reasoning": grok_action["reasoning"],
            "price": self.price,
            "portfolio": portfolio_value,
            "volatility": self.volatility,
            "max_drawdown": self.max_drawdown
        }
        
        if done:
            info["report"] = self._generate_report(ppi, portfolio_value, silos)
            self._log_episode(info)
        
        return self._get_obs(), reward, done, False, info
    
    def _generate_report(self, ppi: float, final_value: float, silos: List[Dict]) -> Dict:
        """Generate comprehensive episode report"""
        return {
            "mood_snapshot": "Neutral with cautious optimism" if ppi > 50 else "Bearish caution",
            "mental_debris": f"Processed ${self.episode_data['etf_inflows']/1e9:.1f}B ETF inflows",
            "trigger_watch": "Alert for vol from Fed; watch $114K support",
            "affirmation": "Today I act from data and plan, not from reactions.",
            "market_summary": {
                "asset": "BTC",
                "prev_close": 115148,
                "current": self.price,
                "change": (self.price - 115148) / 115148,
                "drivers": "Neutral sentiment; ETF buffer vs. Fed uncertainty"
            },
            "ppi_composite": round(ppi, 1),
            "macro_bias": "Bullish" if ppi > 60 else "Neutral" if ppi > 40 else "Bearish",
            "short_term_risk": "High" if self.volatility > 0.05 else "Moderate",
            "recommendation": "Hold core above $114K" if final_value > 1.0 else "Scale out",
            "silos": silos,
            "performance": {
                "final_value": final_value,
                "return": (final_value - 1.0) * 100,
                "sharpe": self.episode_data["sharpe"],
                "max_drawdown": self.max_drawdown * 100
            }
        }
    
    def _log_episode(self, info: Dict):
        """Log episode to Supabase"""
        if not supabase:
            return
        
        try:
            report = info.get("report", {})
            data = {
                "episode_number": int(time.time()),
                "total_reward": float(info.get("portfolio", 1.0) - 1.0),
                "steps": self.step_count,
                "ppi_score": float(info.get("ppi", 0)),
                "final_price": float(self.price),
                "volatility": float(self.volatility),
                "max_drawdown": float(self.max_drawdown),
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("episodes").insert(data).execute()
            print(f"[v0] Episode logged to Supabase: PPI={info.get('ppi', 0):.1f}")
        except Exception as e:
            print(f"[v0] Error logging episode: {e}")


# === Custom Callback for Logging ===
class SentientCallback(BaseCallback):
    """Custom callback for tracking training progress"""
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_ppi = []
        self.episode_count = 0
    
    def _on_step(self) -> bool:
        if self.locals.get("dones")[0]:
            info = self.locals["infos"][0]
            reward = self.locals["rewards"][0]
            
            self.episode_rewards.append(reward)
            self.episode_ppi.append(info.get("ppi", 0))
            self.episode_count += 1
            
            if self.episode_count % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_ppi = np.mean(self.episode_ppi[-10:])
                print(f"\n{'='*60}")
                print(f"Episode {self.episode_count}")
                print(f"Avg Reward (last 10): {avg_reward:.4f}")
                print(f"Avg PPI (last 10): {avg_ppi:.2f}")
                print(f"{'='*60}\n")
        
        return True


# === TRAIN ===
if __name__ == "__main__":
    print("="*60)
    print("SENTIENT TRADER - RL Training Pipeline")
    print("FinRL Integration + 42-dim Actor Simulation")
    print("="*60)
    print(f"Grok API: {'✓' if GROK_API_KEY else '✗'}")
    print(f"Supabase: {'✓' if supabase else '✗'}")
    print(f"Device: {'cuda' if th.cuda.is_available() else 'cpu'}")
    print("="*60)
    
    env = SentientTraderFinRLEnv()
    callback = SentientCallback()
    
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log="./sentient_trader_tensorboard/",
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gae_lambda=0.95,
        gamma=0.99,
        clip_range=0.2,
        policy_kwargs=dict(net_arch=[256, 256, 128]),  # Larger network for 42-dim input
        device="cuda" if th.cuda.is_available() else "cpu"
    )
    
    new_logger = configure("./sb3_log/", ["stdout", "csv", "tensorboard"])
    model.set_logger(new_logger)
    
    print("\nStarting training... (100k timesteps)")
    print("Press Ctrl+C to stop early\n")
    
    try:
        model.learn(total_timesteps=100_000, callback=callback)
        model.save("sentient_trader_ppo")
        print("\n✓ Model saved to sentient_trader_ppo.zip")
    except KeyboardInterrupt:
        print("\n\nTraining interrupted. Saving model...")
        model.save("sentient_trader_ppo_interrupted")
        print("✓ Model saved to sentient_trader_ppo_interrupted.zip")
    
    print("\nRun `python infer.py` to test the trained agent.")
