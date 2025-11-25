"""
Gymnasium Environment for Sentient Trader
Integrates with Grok AI and PPI trust scoring
"""

import gymnasium as gym
import numpy as np
from typing import Dict, Any, Optional, Tuple
import requests
import os
from datetime import datetime

class SentientTraderEnv(gym.Env):
    """
    A Gymnasium environment for training AI trading agents with PPI trust scoring.
    
    Observation Space: [price, volatility, capital, progress, sentiment]
    Action Space: Discrete(3) - 0=hold, 1=buy, 2=sell
    """
    
    metadata = {"render_modes": ["human"]}

    def __init__(self, api_base_url: Optional[str] = None):
        super().__init__()
        
        # Action space: 0=hold, 1=buy, 2=sell
        self.action_space = gym.spaces.Discrete(3)
        
        # Observation space: [price, volatility, capital, progress, sentiment]
        self.observation_space = gym.spaces.Box(
            low=np.array([0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([1e6, 1.0, 1e6, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )
        
        # Environment state
        self.capital = 1.0  # BTC
        self.price = 112000.0
        self.volatility = 0.03
        self.step_count = 0
        self.max_steps = 1000
        self.initial_capital = 1.0
        
        # Trading history
        self.trades = []
        self.pnl_history = []
        self.drawdown_history = []
        self.max_capital = 1.0
        
        # API configuration
        self.api_base_url = api_base_url or os.getenv("NEXT_PUBLIC_TRADER_API_URL", "http://localhost:3000")
        
        # Report data for comprehensive episode analysis
        self.report_data = {
            "mood_snapshot": "Neutral",
            "mental_debris": "",
            "trigger_watch": "",
            "affirmation": "",
            "market_summary": {
                "prev_close": 0,
                "change": 0,
                "drivers": ""
            },
            "ppi_composite": 0,
            "macro_bias": "Neutral",
            "short_term_risk": "Moderate",
            "recommendation": "",
            "silos": []  # List of dicts {name, score, inputs}
        }

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment to initial state."""
        super().reset(seed=seed)
        
        # Reset state
        self.capital = 1.0
        self.step_count = 0
        self.price = 112000.0 + np.random.randn() * 5000
        self.volatility = 0.03 + np.random.rand() * 0.02
        self.initial_capital = self.capital
        self.max_capital = self.capital
        
        # Clear history
        self.trades = []
        self.pnl_history = []
        self.drawdown_history = []
        
        # Reset report data
        self.report_data["mood_snapshot"] = (
            "Neutral with cautious optimism" if self.volatility < 0.05 
            else "Bearish alert - high volatility detected"
        )
        self.report_data["mental_debris"] = "Processing ETF inflows and whale accumulation patterns"
        self.report_data["trigger_watch"] = "Alert for volatility spike from Fed policy uncertainty"
        self.report_data["affirmation"] = self._call_grok_affirmation()
        self.report_data["market_summary"]["prev_close"] = self.price
        self.report_data["market_summary"]["drivers"] = "Institutional accumulation, macro uncertainty"
        self.report_data["silos"] = []
        
        return self._get_obs(), {"report": self.report_data}

    def _get_obs(self) -> np.ndarray:
        """Get current observation."""
        sentiment = np.random.rand()  # Mock sentiment (0-1)
        return np.array([
            self.price,
            self.volatility,
            self.capital,
            self.step_count / self.max_steps,
            sentiment
        ], dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: 0=hold, 1=buy, 2=sell
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        # 1. Get Grok AI recommendation
        grok_action = self._call_grok_api()
        grok_vote = {"buy": 1, "sell": 2, "hold": 0}.get(grok_action.get("action", "hold"), 0)
        
        # 2. Hybrid decision: 50% Grok, 50% RL agent
        final_action = grok_vote if np.random.rand() < 0.5 else action
        action_name = ["hold", "buy", "sell"][final_action]
        
        # 3. Execute trade
        size = 0.1  # Trade 10% of capital
        trade_value = 0
        
        if final_action == 1:  # buy
            trade_value = size * self.price
            self.capital -= size
            self.trades.append({
                "step": self.step_count,
                "action": "buy",
                "size": size,
                "price": self.price,
                "value": trade_value
            })
        elif final_action == 2:  # sell
            trade_value = size * self.price
            self.capital += size
            self.trades.append({
                "step": self.step_count,
                "action": "sell",
                "size": size,
                "price": self.price,
                "value": trade_value
            })
        
        # 4. Update market state (random walk with drift)
        price_change = np.random.randn() * 0.01
        self.price *= np.exp(price_change)
        self.volatility = 0.03 + np.random.rand() * 0.02
        self.step_count += 1
        
        # 5. Calculate PnL and metrics
        current_value = self.capital * self.price
        pnl = current_value - self.initial_capital * self.price
        pnl_pct = (pnl / (self.initial_capital * self.price)) * 100
        
        self.pnl_history.append(pnl_pct)
        self.max_capital = max(self.max_capital, current_value)
        drawdown = ((self.max_capital - current_value) / self.max_capital) * 100
        self.drawdown_history.append(drawdown)
        
        # 6. Calculate PPI trust score
        ppi_score = self._calculate_ppi(pnl_pct, drawdown)
        
        # 7. Calculate reward: log return + PPI bonus
        reward = np.log1p(pnl / 1000) + 0.1 * (ppi_score / 100)
        
        # 8. Update report data
        self._update_report(pnl_pct, ppi_score, action_name, grok_action)
        
        # 9. Check if episode is done
        terminated = self.step_count >= self.max_steps
        truncated = False
        
        info = {
            "ppi": ppi_score,
            "action": action_name,
            "grok_action": grok_action.get("action", "hold"),
            "grok_reasoning": grok_action.get("reasoning", ""),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "drawdown": drawdown,
            "price": self.price,
            "volatility": self.volatility,
            "report": self.report_data if terminated else None
        }
        
        return self._get_obs(), reward, terminated, truncated, info

    def _call_grok_api(self) -> Dict[str, Any]:
        """Call Grok API for trading decision."""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/grok/trade",
                json={
                    "price": float(self.price),
                    "volatility": float(self.volatility),
                    "capital": float(self.capital),
                    "ppi_tier": self._get_ppi_tier()
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[Gym] Grok API error: {e}")
        
        # Fallback to random action
        return {
            "action": np.random.choice(["buy", "sell", "hold"]),
            "size": 0.1,
            "reasoning": "Fallback random action due to API error"
        }

    def _call_grok_affirmation(self) -> str:
        """Get trading affirmation from Grok."""
        affirmations = [
            "Today I act from data and plan, not from reactions.",
            "I trust my system and honor my risk limits.",
            "Patience and discipline compound into lasting success.",
            "I embrace uncertainty as the price of opportunity.",
            "My edge is consistency, not perfection."
        ]
        return np.random.choice(affirmations)

    def _get_ppi_tier(self) -> str:
        """Determine current PPI Maslow tier based on performance."""
        if not self.pnl_history:
            return "safety"
        
        avg_pnl = np.mean(self.pnl_history)
        avg_drawdown = np.mean(self.drawdown_history) if self.drawdown_history else 0
        
        if avg_drawdown > 10 or self.volatility > 0.05:
            return "safety"
        elif avg_pnl < 0:
            return "belonging"
        elif avg_pnl < 5:
            return "esteem"
        else:
            return "self_actualization"

    def _calculate_ppi(self, pnl_pct: float, drawdown: float) -> float:
        """
        Calculate PPI trust score based on Maslow hierarchy.
        
        Tiers:
        - Safety (40%): volatility < 5%, drawdown < 10%
        - Belonging (20%): community engagement (mock)
        - Esteem (20%): consistent alpha > benchmark
        - Self-Actualization (20%): regenerative energy use
        """
        # Safety tier (40%)
        safety_score = 0
        if self.volatility < 0.05:
            safety_score += 50
        if drawdown < 10:
            safety_score += 50
        safety_score = (safety_score / 100) * 40
        
        # Belonging tier (20%) - mock community upvotes
        belonging_score = np.random.uniform(0.6, 1.0) * 20
        
        # Esteem tier (20%) - alpha generation
        esteem_score = 0
        if pnl_pct > 0:
            esteem_score = min(pnl_pct / 10, 1.0) * 20
        
        # Self-Actualization tier (20%) - regenerative energy (mock solar %)
        solar_pct = np.random.uniform(0.7, 1.0)  # Mock: 70-100% solar
        self_actualization_score = solar_pct * 20
        
        total_ppi = safety_score + belonging_score + esteem_score + self_actualization_score
        return np.clip(total_ppi, 0, 100)

    def _update_report(self, pnl_pct: float, ppi_score: float, action: str, grok_action: Dict):
        """Update report data with current step information."""
        # Update market summary
        prev_close = self.report_data["market_summary"]["prev_close"]
        self.report_data["market_summary"]["change"] = ((self.price - prev_close) / prev_close) * 100
        
        # Update PPI composite
        self.report_data["ppi_composite"] = ppi_score
        
        # Update macro bias
        if pnl_pct > 5:
            self.report_data["macro_bias"] = "Bullish"
        elif pnl_pct < -5:
            self.report_data["macro_bias"] = "Bearish"
        else:
            self.report_data["macro_bias"] = "Neutral"
        
        # Update risk assessment
        avg_drawdown = np.mean(self.drawdown_history) if self.drawdown_history else 0
        if avg_drawdown > 15:
            self.report_data["short_term_risk"] = "High"
        elif avg_drawdown > 8:
            self.report_data["short_term_risk"] = "Moderate"
        else:
            self.report_data["short_term_risk"] = "Low"
        
        # Add silo data
        self.report_data["silos"].append({
            "name": "Sentiment",
            "score": 3.5,
            "inputs": f"MPT 40%, Grok: {grok_action.get('action', 'hold')}"
        })
        
        # Final recommendation
        if pnl_pct > 10:
            self.report_data["recommendation"] = "Take partial profits, maintain core position"
        elif pnl_pct < -10:
            self.report_data["recommendation"] = "Scale out and reassess risk parameters"
        else:
            self.report_data["recommendation"] = "Hold core positions, monitor volatility"

    def render(self):
        """Render the environment (optional)."""
        if self.step_count % 100 == 0:
            print(f"\n=== Step {self.step_count} ===")
            print(f"Price: ${self.price:.2f}")
            print(f"Capital: {self.capital:.4f} BTC")
            print(f"Volatility: {self.volatility:.2%}")
            if self.pnl_history:
                print(f"PnL: {self.pnl_history[-1]:.2f}%")
            if self.drawdown_history:
                print(f"Drawdown: {self.drawdown_history[-1]:.2f}%")


# Example usage
if __name__ == "__main__":
    env = SentientTraderEnv()
    obs, info = env.reset()
    
    print("Starting Sentient Trader Environment...")
    print(f"Initial observation: {obs}")
    print(f"Affirmation: {info['report']['affirmation']}")
    
    for i in range(10):
        action = env.action_space.sample()  # Random action
        obs, reward, terminated, truncated, info = env.step(action)
        
        print(f"\nStep {i+1}:")
        print(f"  Action: {info['action']} (Grok: {info['grok_action']})")
        print(f"  Reward: {reward:.4f}")
        print(f"  PPI: {info['ppi']:.1f}")
        print(f"  PnL: {info['pnl_pct']:.2f}%")
        
        if terminated:
            print("\nEpisode completed!")
            print(f"Final report: {info['report']}")
            break
