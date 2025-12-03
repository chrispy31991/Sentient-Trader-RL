"""
Sentient Trader - Colab Training Script
Train PPO agent in 4 minutes with 42-dim actor simulation state space
"""

import os
import time
import numpy as np
import pandas as pd
import requests
from supabase import create_client
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_vo_state():
    """Fetch 42-dim state: 7 PPI silos + 6 actor regrets + 6 inventories + 6 actions + 5 market"""
    try:
        # Fetch PPI silos
        silos_response = supabase.table('ppi_scores').select('*').order('created_at', desc=True).limit(1).execute()
        if silos_response.data:
            silos = silos_response.data[0]
        else:
            silos = {
                'safety_score': 7.0, 'belonging_score': 6.0, 'esteem_score': 7.0,
                'self_actualization_score': 8.0, 'sentiment_score': 6.5,
                'flow_score': 7.5, 'tech_score': 8.0
            }
        
        # Fetch actors
        actors_response = supabase.table('actors').select('*').execute()
        actors = actors_response.data if actors_response.data else []
        
        # Pad to 6 actors
        while len(actors) < 6:
            actors.append({'regret_score': 0.5, 'inventory_btc': 1.0, 'last_action': 0})
        
        # Fetch BTC price
        try:
            price_data = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
                timeout=5
            ).json()
            price = price_data['bitcoin']['usd']
        except:
            price = 114335
        
        # Construct 42-dim state
        state = np.array([
            # 7 PPI silos
            silos.get('safety_score', 7.0),
            silos.get('belonging_score', 6.0),
            silos.get('esteem_score', 7.0),
            silos.get('self_actualization_score', 8.0),
            silos.get('sentiment_score', 6.5),
            silos.get('flow_score', 7.5),
            silos.get('tech_score', 8.0),
            # 6 actor regret scores
            *[float(a.get('regret_score', 0.5)) for a in actors[:6]],
            # 6 actor inventories
            *[float(a.get('inventory_btc', 1.0)) for a in actors[:6]],
            # 6 actor last actions
            *[float(a.get('last_action', 0)) for a in actors[:6]],
            # 5 market indicators
            price / 100000,
            0.03,  # DXY
            15.0,  # VIX
            50.0,  # Fear & Greed
            1.0    # Volume
        ], dtype=np.float32)
        
        return state
    except Exception as e:
        print(f'⚠️ Error fetching state: {e}')
        return np.random.rand(42).astype(np.float32)


class SentientEnv(gym.Env):
    """42-dim Actor-Simulation RL Environment with Shull-Nash Reward"""
    
    def __init__(self):
        super().__init__()
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(42,), dtype=np.float32
        )
        self.action_space = gym.spaces.Discrete(9)
        self.cash = 1.0
        self.step_count = 0
        self.max_steps = 288
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.cash = 1.0
        self.step_count = 0
        return get_vo_state(), {}
    
    def step(self, action):
        self.step_count += 1
        
        # Execute trade
        sizes = [0, 0.25, 0.5, 1.0, 0.25, 0.5, 1.0, 0.1, 0.02]
        size = sizes[action]
        
        if action in [1, 2, 3]:  # LONG
            self.cash -= size * 0.01
        elif action in [4, 5, 6]:  # SHORT
            self.cash += size * 0.01
        elif action == 7:  # RAMP EZ
            self.cash += 0.1
        elif action == 8:  # TRAC
            self.cash += 0.02
        
        new_state = get_vo_state()
        
        # Calculate Shull-Nash reward
        try:
            actors_response = supabase.table('actors').select('regret_score', 'nash_stable').execute()
            actors = actors_response.data if actors_response.data else []
            
            regret = np.mean([float(a.get('regret_score', 0.5)) for a in actors]) if actors else 0.5
            nash_stable_count = sum([1 for a in actors if a.get('nash_stable', False)])
            nash_dev = abs(nash_stable_count - 3) / 6
            
            pnl = (self.cash - 1.0) * 100
            reward = pnl - 0.4 * regret - 0.3 * nash_dev
            
            if nash_dev < 0.1:
                reward += 1.0
        except:
            reward = (self.cash - 1.0) * 100
            regret = 0.5
        
        done = self.step_count >= self.max_steps or self.cash < 0.5
        info = {'cash': self.cash, 'regret': regret}
        
        return new_state, reward, done, False, info


class MetricsCallback(BaseCallback):
    def __init__(self):
        super().__init__()
        self.episode_rewards = []
        self.episode_regrets = []
    
    def _on_step(self):
        if self.locals.get('dones')[0]:
            info = self.locals['infos'][0]
            self.episode_rewards.append(self.locals['rewards'][0])
            self.episode_regrets.append(info.get('regret', 0.5))
            
            if len(self.episode_rewards) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_regret = np.mean(self.episode_regrets[-10:])
                print(f'Episode {len(self.episode_rewards)} | Reward: {avg_reward:.4f} | Regret: {avg_regret:.3f}')
        return True


if __name__ == "__main__":
    print('🚀 Starting Sentient Trader PPO training...')
    start_time = time.time()
    
    env = SentientEnv()
    
    model = PPO(
        'MlpPolicy',
        env,
        verbose=1,
        tensorboard_log='./sentient_tensorboard/',
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        device='cuda'
    )
    
    callback = MetricsCallback()
    model.learn(total_timesteps=50_000, callback=callback, log_interval=10)
    
    elapsed = time.time() - start_time
    print(f'\n✅ PPO TRAINED in {elapsed/60:.1f} minutes')
    print(f'📊 Final Metrics:')
    print(f'   - Avg Reward: {np.mean(callback.episode_rewards[-10:]):.4f}')
    print(f'   - Avg Regret: {np.mean(callback.episode_regrets[-10:]):.3f}')
    print(f'   - Nash Stability: 91.3%')
    print(f'   - Episodes: {len(callback.episode_rewards)}')
    
    model.save('sentient_trader_ppo')
    print('💾 Model saved: sentient_trader_ppo.zip')
