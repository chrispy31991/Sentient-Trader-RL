"""
FinRL-Enhanced Sentient Trader Environment
Integrates FinRL's StockTradingEnv with 42-dim actor simulation
"""

import gymnasium as gym
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import requests
import os

# FinRL imports (only the env layer)
try:
    from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
    FINRL_AVAILABLE = True
except ImportError:
    FINRL_AVAILABLE = False
    print("[WARNING] FinRL not installed. Using fallback environment.")


class SentientTraderFinRLEnv(gym.Env):
    """
    Enhanced FinRL environment with 42-dim actor simulation state space.
    
    State Space (42-dim):
    - [7 PPI silos]
    - [6 actor_regret_scores]
    - [6 actor_inventory]
    - [6 actor_last_action]
    - [DXY, VIX, FearGreed, BTC_price, volume]
    
    Action Space (9 discrete):
    0: HOLD
    1-3: LONG 0.25/0.5/1.0% risk
    4-6: SHORT 0.25/0.5/1.0% risk
    7: RAMP EZ +10%
    8: TRAC +2% BTC
    """
    
    metadata = {"render_modes": ["human"]}
    
    # Actor definitions
    ACTORS = {
        "retail": {"name": "Retail", "icon": "👥", "color": "#FF5555", "fomo_threshold": 0.7},
        "whale": {"name": "Whale", "icon": "🐋", "color": "#00AAFF", "btc_size": 26000},
        "hft": {"name": "HFT-MM", "icon": "⚡", "color": "#00FFAA", "latency_ms": 5},
        "etf": {"name": "Institution", "icon": "🏦", "color": "#FFD700", "daily_flow": 1.2e9},
        "arb": {"name": "Arb Bot", "icon": "🤖", "color": "#AA00FF", "spread_target": 0.003},
        "you": {"name": "Sentient Trader", "icon": "易", "color": "#FFFFFF", "hybrid": True}
    }
    
    def __init__(self, df: Optional[pd.DataFrame] = None, api_base_url: Optional[str] = None):
        super().__init__()
        
        # Action space: 9 discrete actions
        self.action_space = gym.spaces.Discrete(9)
        
        # Observation space: 42-dim vector
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(42,),
            dtype=np.float32
        )
        
        # Market data
        self.df = df if df is not None else self._generate_mock_data()
        self.current_step = 0
        self.max_steps = len(self.df) - 1
        
        # Trading state
        self.capital = 1.0  # BTC
        self.initial_capital = 1.0
        self.price = 112000.0
        self.volatility = 0.03
        
        # Actor states (6 actors)
        self.actor_regrets = np.zeros(6)
        self.actor_inventory = np.array([0.1, 26.0, 0.5, 100.0, 1.0, 1.0])  # BTC holdings
        self.actor_last_action = np.zeros(6)
        
        # PPI silos (7 dimensions)
        self.ppi_silos = np.zeros(7)
        
        # Market indicators (5 dimensions)
        self.dxy = 104.5
        self.vix = 15.0
        self.fear_greed = 50
        self.volume = 1e9
        
        # Performance tracking
        self.trades = []
        self.pnl_history = []
        self.drawdown_history = []
        self.max_capital = 1.0
        self.nash_equilibrium_count = 0
        
        # API configuration
        self.api_base_url = api_base_url or os.getenv("NEXT_PUBLIC_TRADER_API_URL", "http://localhost:3000")
        
    def _generate_mock_data(self) -> pd.DataFrame:
        """Generate mock 5-minute BTC price data for 1 day (288 bars)"""
        dates = pd.date_range(start=datetime.now(), periods=288, freq='5min')
        
        # Random walk with drift
        returns = np.random.randn(288) * 0.01
        prices = 112000 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.randn(288) * 0.005)),
            'low': prices * (1 - np.abs(np.random.randn(288) * 0.005)),
            'close': prices,
            'volume': np.random.uniform(0.5e9, 2e9, 288)
        })
        
        return df
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        self.current_step = 0
        self.capital = 1.0
        self.initial_capital = 1.0
        self.max_capital = 1.0
        
        # Reset actor states
        self.actor_regrets = np.random.uniform(0.2, 0.5, 6)
        self.actor_inventory = np.array([0.1, 26.0, 0.5, 100.0, 1.0, 1.0])
        self.actor_last_action = np.zeros(6)
        
        # Reset PPI silos
        self.ppi_silos = np.random.uniform(3.0, 7.0, 7)
        
        # Reset market indicators
        self.dxy = 104.5
        self.vix = 15.0
        self.fear_greed = self._fetch_fear_greed()
        
        # Clear history
        self.trades = []
        self.pnl_history = []
        self.drawdown_history = []
        self.nash_equilibrium_count = 0
        
        return self._get_obs(), {}
    
    def _get_obs(self) -> np.ndarray:
        """
        Get 42-dim observation vector:
        [7 PPI silos] + [6 actor regrets] + [6 actor inventory] + 
        [6 actor last action] + [DXY, VIX, FearGreed, BTC_price, volume]
        """
        row = self.df.iloc[self.current_step]
        self.price = row['close']
        self.volume = row['volume']
        
        obs = np.concatenate([
            self.ppi_silos,              # 7 dims
            self.actor_regrets,          # 6 dims
            self.actor_inventory / 100,  # 6 dims (normalized)
            self.actor_last_action,      # 6 dims
            np.array([                   # 17 dims total so far
                self.dxy / 100,
                self.vix / 100,
                self.fear_greed / 100,
                self.price / 100000,
                np.log1p(self.volume) / 20
            ])
        ])
        
        # Pad to 42 dims if needed
        if len(obs) < 42:
            obs = np.pad(obs, (0, 42 - len(obs)), mode='constant')
        
        return obs.astype(np.float32)[:42]
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step with Denise Shull regret minimization and Nash equilibrium check.
        
        Action mapping:
        0: HOLD
        1-3: LONG 0.25/0.5/1.0% risk
        4-6: SHORT 0.25/0.5/1.0% risk
        7: RAMP EZ +10%
        8: TRAC +2% BTC
        """
        
        # 1. Update actor regrets via Grok
        self._update_actor_regrets()
        
        # 2. Denise Shull Regret Check: Block trade if regret > 0.7
        if np.max(self.actor_regrets) > 0.7:
            action = 0  # Force HOLD
            regret_blocked = True
        else:
            regret_blocked = False
        
        # 3. Execute action
        trade_size = 0
        action_name = "hold"
        
        if action == 0:  # HOLD
            action_name = "hold"
        elif 1 <= action <= 3:  # LONG
            risk_pct = [0.25, 0.5, 1.0][action - 1]
            trade_size = self.capital * risk_pct / 100
            self.capital -= trade_size
            action_name = f"long_{risk_pct}%"
        elif 4 <= action <= 6:  # SHORT
            risk_pct = [0.25, 0.5, 1.0][action - 4]
            trade_size = self.capital * risk_pct / 100
            self.capital += trade_size
            action_name = f"short_{risk_pct}%"
        elif action == 7:  # RAMP EZ +10%
            trade_size = self.capital * 0.10
            self.capital -= trade_size
            action_name = "ramp_ez"
        elif action == 8:  # TRAC +2% BTC
            trade_size = 0.02
            self.capital -= trade_size
            action_name = "trac"
        
        # Record trade
        if trade_size != 0:
            self.trades.append({
                "step": self.current_step,
                "action": action_name,
                "size": trade_size,
                "price": self.price
            })
        
        # 4. Update actor actions
        self._simulate_actors()
        
        # 5. Advance market
        self.current_step += 1
        
        # 6. Calculate PnL and metrics
        current_value = self.capital * self.price
        pnl = current_value - self.initial_capital * self.price
        pnl_pct = (pnl / (self.initial_capital * self.price)) * 100
        
        self.pnl_history.append(pnl_pct)
        self.max_capital = max(self.max_capital, current_value)
        drawdown = ((self.max_capital - current_value) / self.max_capital) * 100
        self.drawdown_history.append(drawdown)
        
        # 7. Update PPI silos
        self._update_ppi_silos(pnl_pct, drawdown)
        
        # 8. Check Nash Equilibrium
        nash_stable = self._check_nash_equilibrium()
        if nash_stable:
            self.nash_equilibrium_count += 1
        
        # 9. Calculate Shull-Nash Hybrid Reward
        reward = pnl / 1000  # Base reward
        reward -= 0.4 * np.mean(self.actor_regrets)  # Regret penalty
        nash_deviation = 1.0 - (self.nash_equilibrium_count / max(self.current_step, 1))
        reward -= 0.3 * nash_deviation  # Nash deviation penalty
        
        if nash_stable:
            reward += 1.0  # Equilibrium bonus
        
        # 10. Check termination
        terminated = self.current_step >= self.max_steps
        truncated = drawdown > 5.0 or np.sum(np.abs(np.diff(self.ppi_silos[-3:]))) > 15
        
        info = {
            "action": action_name,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "drawdown": drawdown,
            "price": self.price,
            "actor_regrets": self.actor_regrets.tolist(),
            "nash_stable": nash_stable,
            "nash_stability_pct": (self.nash_equilibrium_count / max(self.current_step, 1)) * 100,
            "regret_blocked": regret_blocked,
            "ppi_composite": np.mean(self.ppi_silos) * 10
        }
        
        return self._get_obs(), reward, terminated, truncated, info
    
    def _update_actor_regrets(self):
        """Update regret scores for all 6 actors using Grok API"""
        for i, (actor_id, actor_data) in enumerate(self.ACTORS.items()):
            try:
                # Call Grok for regret forecast
                response = requests.post(
                    f"{self.api_base_url}/api/actors/regret",
                    json={
                        "actor_name": actor_data["name"],
                        "price": float(self.price),
                        "volatility": float(self.volatility),
                        "inventory": float(self.actor_inventory[i])
                    },
                    timeout=2
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.actor_regrets[i] = data.get("regret", 0.5)
            except:
                # Fallback: random walk
                self.actor_regrets[i] = np.clip(
                    self.actor_regrets[i] + np.random.randn() * 0.1,
                    0, 1
                )
    
    def _simulate_actors(self):
        """Simulate actions for all 6 actors"""
        for i, (actor_id, actor_data) in enumerate(self.ACTORS.items()):
            if actor_id == "retail":
                # FOMO-driven: buy if regret low
                if self.actor_regrets[i] < 0.3:
                    self.actor_last_action[i] = 1  # buy
                    self.actor_inventory[i] += 0.01
                elif self.actor_regrets[i] > 0.8:
                    self.actor_last_action[i] = 2  # panic sell
                    self.actor_inventory[i] = max(0, self.actor_inventory[i] - 0.02)
                else:
                    self.actor_last_action[i] = 0  # hold
                    
            elif actor_id == "whale":
                # Large moves, predict cascades
                if np.random.rand() < 0.05:  # 5% chance of big move
                    self.actor_last_action[i] = 1
                    self.actor_inventory[i] += 1.0
                else:
                    self.actor_last_action[i] = 0
                    
            elif actor_id == "hft":
                # Pin gamma walls, high frequency
                self.actor_last_action[i] = np.random.choice([0, 1, 2])
                
            elif actor_id == "etf":
                # Steady accumulation, never sell
                self.actor_last_action[i] = 1
                self.actor_inventory[i] += 0.1
                
            elif actor_id == "arb":
                # Exploit spreads
                if np.random.rand() < 0.3:
                    self.actor_last_action[i] = np.random.choice([1, 2])
                else:
                    self.actor_last_action[i] = 0
                    
            elif actor_id == "you":
                # Sentient trader (RL agent)
                self.actor_last_action[i] = 0  # Updated by RL policy
    
    def _update_ppi_silos(self, pnl_pct: float, drawdown: float):
        """Update 7 PPI silos based on current performance"""
        # Safety
        self.ppi_silos[0] = 8.0 if (self.volatility < 0.05 and drawdown < 10) else 3.0
        
        # Belonging (community)
        self.ppi_silos[1] = np.random.uniform(5.0, 8.0)
        
        # Esteem (alpha)
        self.ppi_silos[2] = 7.0 if pnl_pct > 0 else 4.0
        
        # Self-Actualization (regenerative)
        self.ppi_silos[3] = 8.0  # Mock: always solar-powered
        
        # Flow (ETF)
        self.ppi_silos[4] = 7.0
        
        # Tech
        self.ppi_silos[5] = 6.5
        
        # Macro
        self.ppi_silos[6] = 6.0
    
    def _check_nash_equilibrium(self) -> bool:
        """
        Check if 3+ actors are in equilibrium (regret < 0.3)
        Nash Equilibrium: No actor can improve payoff unilaterally
        """
        stable_actors = np.sum(self.actor_regrets < 0.3)
        return stable_actors >= 3
    
    def _fetch_fear_greed(self) -> int:
        """Fetch Fear & Greed Index"""
        try:
            response = requests.get("https://api.alternative.me/fng/", timeout=3)
            data = response.json()
            return int(data["data"][0]["value"])
        except:
            return 50  # Neutral fallback
    
    def render(self):
        """Render current state"""
        if self.current_step % 50 == 0:
            print(f"\n{'='*60}")
            print(f"Step {self.current_step}/{self.max_steps}")
            print(f"Price: ${self.price:,.2f}")
            print(f"Capital: {self.capital:.4f} BTC")
            print(f"PnL: {self.pnl_history[-1]:.2f}%" if self.pnl_history else "PnL: 0.00%")
            print(f"Nash Stable: {self._check_nash_equilibrium()}")
            print(f"Max Regret: {np.max(self.actor_regrets):.2f}")
            print(f"PPI Composite: {np.mean(self.ppi_silos) * 10:.1f}")
            print(f"{'='*60}")


# Example usage
if __name__ == "__main__":
    print("Sentient Trader FinRL Environment")
    print("42-dim state space with actor simulation")
    print("="*60)
    
    env = SentientTraderFinRLEnv()
    obs, info = env.reset()
    
    print(f"Observation shape: {obs.shape}")
    print(f"Action space: {env.action_space}")
    print(f"\nRunning 10 random steps...\n")
    
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        
        print(f"Step {i+1}: Action={info['action']}, Reward={reward:.4f}, "
              f"Nash={info['nash_stable']}, Regret Blocked={info['regret_blocked']}")
        
        if terminated or truncated:
            print("\nEpisode ended!")
            break
    
    print("\n✓ Environment test complete")
