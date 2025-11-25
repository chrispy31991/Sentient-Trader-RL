from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
from supabase import create_client

router = APIRouter()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None


@router.post("/report/{episode_id}")
async def generate_report(episode_id: str) -> Dict[str, Any]:
    """
    Generate a comprehensive report for a completed episode.
    Loads episode data from Supabase and returns formatted report.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Load episode from Supabase
        response = supabase.table("episodes").select("*").eq("id", episode_id).single().execute()
        episode = response.data
        
        if not episode:
            raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")
        
        # Load associated actions
        actions_response = supabase.table("actions").select("*").eq("episode_id", episode_id).execute()
        actions = actions_response.data
        
        # Calculate metrics
        total_steps = len(actions)
        buy_actions = sum(1 for a in actions if a["action_type"] == "buy")
        sell_actions = sum(1 for a in actions if a["action_type"] == "sell")
        hold_actions = sum(1 for a in actions if a["action_type"] == "hold")
        
        # Load PPI scores
        ppi_response = supabase.table("ppi_scores").select("*").eq("episode_id", episode_id).order("created_at", desc=True).limit(1).execute()
        ppi_data = ppi_response.data[0] if ppi_response.data else None
        
        # Generate report
        report = {
            "episode_id": episode_id,
            "mood_snapshot": _get_mood_snapshot(episode, ppi_data),
            "mental_debris": f"Processed {total_steps} steps with {buy_actions} buys, {sell_actions} sells",
            "trigger_watch": _get_trigger_watch(episode),
            "affirmation": "Today I act from data and plan, not from reactions.",
            "market_summary": {
                "asset": "BTC",
                "prev_close": 115148,
                "current": episode.get("final_price", 114335),
                "change": ((episode.get("final_price", 114335) - 115148) / 115148) if episode.get("final_price") else 0,
                "drivers": "Neutral sentiment; ETF buffer vs. Fed uncertainty"
            },
            "ppi_composite": ppi_data["composite_score"] if ppi_data else 0,
            "macro_bias": _get_macro_bias(ppi_data),
            "short_term_risk": _get_risk_level(episode),
            "recommendation": _get_recommendation(episode, ppi_data),
            "silos": ppi_data["tier_breakdown"] if ppi_data else [],
            "performance": {
                "total_reward": episode.get("total_reward", 0),
                "steps": total_steps,
                "irr": episode.get("irr", 0),
                "sharpe": episode.get("sharpe", 0),
                "actions": {
                    "buy": buy_actions,
                    "sell": sell_actions,
                    "hold": hold_actions
                }
            }
        }
        
        # Save report to database
        supabase.table("reports").insert({
            "episode_id": episode_id,
            "report_data": report,
            "generated_at": "now()"
        }).execute()
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


def _get_mood_snapshot(episode: Dict, ppi_data: Dict) -> str:
    """Generate mood snapshot based on episode performance"""
    ppi = ppi_data["composite_score"] if ppi_data else 0
    reward = episode.get("total_reward", 0)
    
    if ppi > 70 and reward > 0:
        return "Bullish with strong confidence"
    elif ppi > 50:
        return "Neutral with cautious optimism"
    else:
        return "Bearish caution - risk management mode"


def _get_trigger_watch(episode: Dict) -> str:
    """Generate trigger watch alerts"""
    volatility = episode.get("volatility", 0.03)
    if volatility > 0.05:
        return "High volatility alert - watch for Fed announcements"
    return "Alert for vol from Fed; watch key support levels"


def _get_macro_bias(ppi_data: Dict) -> str:
    """Determine macro bias from PPI score"""
    if not ppi_data:
        return "Neutral"
    
    ppi = ppi_data["composite_score"]
    if ppi > 70:
        return "Bullish"
    elif ppi > 50:
        return "Neutral"
    else:
        return "Bearish"


def _get_risk_level(episode: Dict) -> str:
    """Assess short-term risk level"""
    volatility = episode.get("volatility", 0.03)
    drawdown = episode.get("max_drawdown", 0)
    
    if volatility > 0.05 or drawdown > 0.1:
        return "High"
    elif volatility > 0.03 or drawdown > 0.05:
        return "Moderate"
    return "Low"


def _get_recommendation(episode: Dict, ppi_data: Dict) -> str:
    """Generate trading recommendation"""
    ppi = ppi_data["composite_score"] if ppi_data else 0
    reward = episode.get("total_reward", 0)
    
    if ppi > 70 and reward > 0:
        return "Accumulate on dips; maintain core position"
    elif ppi > 50:
        return "Hold core positions; wait for clearer signals"
    else:
        return "Scale out; preserve capital in risk-off mode"
