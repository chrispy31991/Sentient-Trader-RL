"""
Test script for the Sentient Trader API
Run with: python scripts/test_api.py
"""
import requests
import json
import time
from datetime import datetime

# API base URLs
FASTAPI_URL = "http://localhost:8000"
NEXTJS_URL = "http://localhost:3000"

def test_grok_api():
    """Test the Grok API endpoint"""
    print("\n=== Testing Grok API (Next.js) ===")
    try:
        response = requests.post(
            f"{NEXTJS_URL}/api/grok/trade",
            json={
                "price": 45000.0,
                "volatility": 0.15,
                "ppiTier": "Esteem",
                "capital": 0.5
            },
            timeout=30
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Next.js server not running. Skipping Grok test.")
        return False
    except Exception as e:
        print(f"❌ Grok API error: {e}")
        return False

def test_start_episode():
    """Test starting a new episode"""
    print("\n=== Testing POST /start ===")
    response = requests.post(
        f"{FASTAPI_URL}/start",
        json={
            "agent_name": "Test-Agent-Grok",
            "initial_balance": 10000.0
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return data["episode_id"]

def test_take_step(episode_id: str, step_num: int):
    """Test taking a step with Grok integration"""
    print(f"\n=== Testing POST /step (Step {step_num}) ===")
    
    # Vary market conditions for interesting results
    price = 45000.0 + (step_num * 500) + ((-1) ** step_num * 200)
    sentiment = 0.5 + (step_num * 0.05) - 0.25
    sentiment = max(-1.0, min(1.0, sentiment))
    
    response = requests.post(
        f"{FASTAPI_URL}/step",
        json={
            "episode_id": episode_id,
            "market_state": {
                "price": price,
                "volume": 1000000.0 + (step_num * 50000),
                "sentiment": sentiment,
                "timestamp": datetime.now().isoformat()
            },
            "current_balance": 10000.0 - (step_num * 100),
            "current_position": 0.1 * step_num
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    
    # Pretty print the action with highlighting
    action = data.get("action", {})
    print(f"\n📊 Step {step_num} Results:")
    print(f"   Action: {action.get('type', 'N/A').upper()}")
    print(f"   Size: {action.get('size', 0):.3f}")
    print(f"   Confidence: {action.get('confidence', 0):.3f}")
    print(f"   Reasoning:\n{action.get('reasoning', 'N/A')}")
    
    return data

def test_end_episode(episode_id: str):
    """Test ending an episode"""
    print("\n=== Testing POST /end ===")
    response = requests.post(
        f"{FASTAPI_URL}/end",
        json={
            "episode_id": episode_id,
            "final_pnl": 750.0,
            "ppi_score": 82.5,
            "total_steps": 10,
            "total_reward": 35.5
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

def test_active_episodes():
    """Test getting active episodes"""
    print("\n=== Testing GET /episodes/active ===")
    response = requests.get(f"{FASTAPI_URL}/episodes/active")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

def run_full_test():
    """Run a complete test flow"""
    print("=" * 70)
    print("🤖 Sentient Trader API Test Suite (with Grok Integration)")
    print("=" * 70)
    
    # Test health check
    print("\n=== Testing GET / (Health Check) ===")
    try:
        response = requests.get(FASTAPI_URL)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI server not running!")
        return
    
    # Test Grok API
    grok_available = test_grok_api()
    if grok_available:
        print("✅ Grok API is available - hybrid decisions will be used")
    else:
        print("⚠️  Grok API unavailable - fallback to RL-only decisions")
    
    # Start episode
    episode_id = test_start_episode()
    
    # Take multiple steps to see Grok + RL blending
    print("\n" + "=" * 70)
    print("🎯 Running Trading Simulation (Grok + RL Hybrid)")
    print("=" * 70)
    
    for i in range(5):
        step_data = test_take_step(episode_id, i + 1)
        time.sleep(1)  # Delay to see Grok API in action
    
    # Check active episodes
    test_active_episodes()
    
    # End episode
    test_end_episode(episode_id)
    
    print("\n" + "=" * 70)
    print("✅ Test suite completed successfully!")
    print("=" * 70)
    print("\n💡 Tips:")
    print("   - Check the action reasoning to see Grok + RL blending")
    print("   - Start Next.js server for full Grok integration")
    print("   - View results in Supabase dashboard")

if __name__ == "__main__":
    try:
        run_full_test()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API.")
        print("Make sure the FastAPI server is running:")
        print("   cd api/trader && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
