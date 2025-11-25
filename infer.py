"""
Sentient Trader - Inference Script
Test trained PPO agent and generate comprehensive report
"""

from train_sentient_trader import SentientTraderEnv, PPO
import json
import sys

def main():
    print("="*60)
    print("SENTIENT TRADER - Inference Mode")
    print("="*60)
    
    # Load model
    try:
        model = PPO.load("sentient_trader_ppo")
        print("✓ Model loaded: sentient_trader_ppo.zip")
    except FileNotFoundError:
        print("✗ Model not found. Train first with: python train_sentient_trader.py")
        sys.exit(1)
    
    # Create environment
    env = SentientTraderEnv()
    
    # Run episode
    print("\nRunning episode...")
    obs, _ = env.reset()
    done = False
    step = 0
    total_reward = 0
    
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _, info = env.step(action)
        total_reward += reward
        step += 1
        
        if step % 100 == 0:
            print(f"Step {step}/1000 | Portfolio: {info['portfolio']:.4f} | PPI: {info['ppi']:.1f}")
    
    # Print final report
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(json.dumps(info["report"], indent=2))
    print("\n" + "="*60)
    print(f"Total Reward: {total_reward:.4f}")
    print(f"Final Portfolio Value: {info['portfolio']:.4f}")
    print(f"Return: {(info['portfolio'] - 1.0) * 100:.2f}%")
    print(f"PPI Score: {info['ppi']:.1f}/100")
    print("="*60)

if __name__ == "__main__":
    main()
