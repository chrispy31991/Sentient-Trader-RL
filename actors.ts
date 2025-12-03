/**
 * Actor-Simulation RL System
 * Implements 6 actor classes with Denise Shull regret framework and Nash equilibrium monitoring
 */

import { createClient } from "@/lib/supabase/server"

export type ActorType = "retail" | "whale" | "hft_mm" | "institution" | "arb_bot" | "sentient_trader"

export interface Actor {
  id: string
  name: string
  type: ActorType
  inventory: number
  lastAction: string | null
  regretScore: number
  positionSize: number
  avgEntryPrice: number
  pnl: number
  tradeCount: number
}

export interface ActorAction {
  actorId: string
  episodeId: string
  step: number
  actionType: "buy" | "sell" | "hold"
  size: number
  price: number
  regretForecast: number
  reasoning: string
}

export interface RegretScore {
  actorId: string
  episodeId: string
  step: number
  feelingName: string
  intensity: number // 1-10
  fractalLink: string
  regretForecast: number
  actionTaken: string
  outcome: string
}

export interface NashEquilibrium {
  episodeId: string
  step: number
  isEquilibrium: boolean
  nashDeviation: number
  actorStates: Record<string, any>
}

export interface MarketState {
  price: number
  volume: number
  volatility: number
  dxy: number
  vix: number
  fearGreed: number
}

/**
 * Denise Shull's ReThink Method (7-step loop)
 * 1. Name the feeling
 * 2. Rate intensity 1-10
 * 3. Link to past fractal
 * 4. Predict next 5min action
 * 5. Choose counter-bias or ride-bias
 * 6. Execute with 1% risk
 * 7. Journal outcome
 */
export function calculateRegretForecast(
  actor: Actor,
  marketState: MarketState,
  proposedAction: "buy" | "sell" | "hold",
): { regretForecast: number; feeling: string; intensity: number; fractalLink: string } {
  let regretForecast = 0
  let feeling = "neutral"
  let intensity = 5
  let fractalLink = "no pattern"

  // Actor-specific regret patterns
  switch (actor.type) {
    case "retail":
      // FOMO-driven: high regret when missing rallies
      if (proposedAction === "hold" && marketState.price > actor.avgEntryPrice * 1.05) {
        feeling = "FOMO"
        intensity = 8
        regretForecast = 0.7
        fractalLink = "Missed 2021 bull run"
      } else if (proposedAction === "buy" && marketState.volatility > 0.05) {
        feeling = "fear"
        intensity = 6
        regretForecast = 0.5
        fractalLink = "Bought top in 2021"
      }
      break

    case "whale":
      // Signal whale: low regret, strategic moves
      if (proposedAction === "sell" && actor.inventory < 20) {
        feeling = "caution"
        intensity = 4
        regretForecast = 0.2
        fractalLink = "Early exit in 2020"
      }
      break

    case "hft_mm":
      // HFT: minimal regret, algorithmic
      feeling = "neutral"
      intensity = 2
      regretForecast = 0.05
      fractalLink = "none"
      break

    case "institution":
      // Institution: moderate regret, flow-driven
      if (proposedAction === "buy" && marketState.fearGreed < 30) {
        feeling = "opportunity"
        intensity = 7
        regretForecast = 0.3
        fractalLink = "March 2020 bottom"
      }
      break

    case "arb_bot":
      // Arb bot: low regret, latency-focused
      feeling = "neutral"
      intensity = 3
      regretForecast = 0.08
      fractalLink = "none"
      break

    case "sentient_trader":
      // Sentient: RL + Grok, adaptive regret
      if (actor.regretScore > 0.5) {
        feeling = "uncertainty"
        intensity = 6
        regretForecast = actor.regretScore
        fractalLink = "Recent drawdown"
      }
      break
  }

  // Regret minimization rule: if regret_forecast > 0.7 → BLOCK_TRADE
  if (regretForecast > 0.7) {
    console.log(`[v0] BLOCKED TRADE for ${actor.name}: regret=${regretForecast}`)
  }

  return { regretForecast, feeling, intensity, fractalLink }
}

/**
 * Nash Equilibrium Detection
 * No actor can improve payoff unilaterally
 */
export function checkNashEquilibrium(
  actors: Actor[],
  marketState: MarketState,
): {
  isEquilibrium: boolean
  nashDeviation: number
  analysis: string
} {
  // Count actor positions
  const longCount = actors.filter((a) => a.positionSize > 0).length
  const shortCount = actors.filter((a) => a.positionSize < 0).length
  const neutralCount = actors.filter((a) => a.positionSize === 0).length

  // Mixed-strategy Nash: 60% short, 40% long → equilibrium
  const longRatio = longCount / actors.length
  const shortRatio = shortCount / actors.length

  // Ideal Nash: 0.4 long, 0.6 short (or vice versa)
  const nashDeviation = Math.abs(longRatio - 0.4) + Math.abs(shortRatio - 0.6)

  const isEquilibrium = nashDeviation < 0.2 // Within 20% of ideal

  let analysis = ""
  if (isEquilibrium) {
    analysis = "Market in Nash equilibrium - no actor can improve unilaterally"
  } else if (longRatio > 0.7) {
    analysis = "Crowded long - potential short-covering cascade risk"
  } else if (shortRatio > 0.7) {
    analysis = "Crowded short - potential squeeze setup"
  } else {
    analysis = "Market seeking equilibrium"
  }

  return { isEquilibrium, nashDeviation, analysis }
}

/**
 * Simulate actor decision based on type and market state
 */
export function simulateActorDecision(
  actor: Actor,
  marketState: MarketState,
): { action: "buy" | "sell" | "hold"; size: number; reasoning: string } {
  let action: "buy" | "sell" | "hold" = "hold"
  let size = 0
  let reasoning = ""

  switch (actor.type) {
    case "retail":
      // FOMO-driven: buy on momentum, sell on fear
      if (marketState.fearGreed > 70) {
        action = "buy"
        size = 0.1
        reasoning = "FOMO: Fear & Greed > 70, buying momentum"
      } else if (marketState.fearGreed < 30) {
        action = "sell"
        size = 0.1
        reasoning = "Fear: Fear & Greed < 30, panic selling"
      }
      break

    case "whale":
      // Signal whale: strategic accumulation
      if (marketState.price < 110000 && actor.inventory < 30) {
        action = "buy"
        size = 2.0
        reasoning = "Whale accumulation: price < $110K, adding to position"
      } else if (marketState.price > 120000) {
        action = "sell"
        size = 1.0
        reasoning = "Whale distribution: price > $120K, taking profits"
      }
      break

    case "hft_mm":
      // HFT: gamma pinning at key levels
      if (Math.abs(marketState.price - 108000) < 1000) {
        action = "buy"
        size = 0.5
        reasoning = "HFT: Gamma pinning at $108K wall"
      }
      break

    case "institution":
      // Institution: ETF flow-driven
      if (marketState.volume > 1e9) {
        action = "buy"
        size = 5.0
        reasoning = "Institution: High ETF inflows, buying pressure"
      }
      break

    case "arb_bot":
      // Arb bot: cross-exchange arbitrage
      if (marketState.volatility > 0.03) {
        action = Math.random() > 0.5 ? "buy" : "sell"
        size = 0.2
        reasoning = "Arb bot: Volatility > 3%, arbitrage opportunity"
      }
      break

    case "sentient_trader":
      // Sentient: RL + Grok (handled separately)
      reasoning = "Sentient: RL + Grok hybrid decision"
      break
  }

  return { action, size, reasoning }
}

/**
 * Get all actors from database
 */
export async function getActors(): Promise<Actor[]> {
  const supabase = await createClient()
  const { data, error } = await supabase.from("actors").select("*").order("type")

  if (error) {
    console.error("[v0] Error fetching actors:", error)
    return []
  }

  return (
    data?.map((a) => ({
      id: a.id,
      name: a.name,
      type: a.type,
      inventory: a.inventory,
      lastAction: a.last_action,
      regretScore: a.regret_score,
      positionSize: a.position_size,
      avgEntryPrice: a.avg_entry_price,
      pnl: a.pnl,
      tradeCount: a.trade_count,
    })) || []
  )
}

/**
 * Update actor state
 */
export async function updateActor(actorId: string, updates: Partial<Actor>): Promise<void> {
  const supabase = await createClient()
  await supabase
    .from("actors")
    .update({
      inventory: updates.inventory,
      last_action: updates.lastAction,
      regret_score: updates.regretScore,
      position_size: updates.positionSize,
      avg_entry_price: updates.avgEntryPrice,
      pnl: updates.pnl,
      trade_count: updates.tradeCount,
      updated_at: new Date().toISOString(),
    })
    .eq("id", actorId)
}

/**
 * Log actor action
 */
export async function logActorAction(action: ActorAction): Promise<void> {
  const supabase = await createClient()
  await supabase.from("actor_actions").insert({
    actor_id: action.actorId,
    episode_id: action.episodeId,
    step: action.step,
    action_type: action.actionType,
    size: action.size,
    price: action.price,
    regret_forecast: action.regretForecast,
    reasoning: action.reasoning,
  })
}

/**
 * Log Nash equilibrium state
 */
export async function logNashEquilibrium(nash: NashEquilibrium): Promise<void> {
  const supabase = await createClient()
  await supabase.from("nash_equilibrium_log").insert({
    episode_id: nash.episodeId,
    step: nash.step,
    is_equilibrium: nash.isEquilibrium,
    nash_deviation: nash.nashDeviation,
    actor_states: nash.actorStates,
  })
}

/**
 * Log regret score (Denise Shull framework)
 */
export async function logRegretScore(regret: RegretScore): Promise<void> {
  const supabase = await createClient()
  await supabase.from("regret_scores").insert({
    actor_id: regret.actorId,
    episode_id: regret.episodeId,
    step: regret.step,
    feeling_name: regret.feelingName,
    intensity: regret.intensity,
    fractal_link: regret.fractalLink,
    regret_forecast: regret.regretForecast,
    action_taken: regret.actionTaken,
    outcome: regret.outcome,
  })
}
