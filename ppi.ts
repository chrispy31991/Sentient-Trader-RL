import { createClient } from "@/lib/supabase/server"

/**
 * Maslow-PPI Trust Engine
 * Calculates a 0-100 trust score based on 4 Maslow hierarchy tiers
 */

export interface EpisodeStats {
  episodeId: string
  agentId: string

  // Safety metrics
  volatility: number // Portfolio volatility %
  maxDrawdown: number // Maximum drawdown %

  // Belonging metrics
  communityUpvotes: number // Mock social engagement

  // Esteem metrics
  alphaVsBenchmark: number // Alpha vs BTC buy-and-hold %

  // Self-Actualization metrics
  solarEnergyPercent: number // % of compute powered by renewable energy
}

export interface PPITierBreakdown {
  safety: {
    score: number // 0-100
    weight: number // 0.4
    metrics: {
      volatility: number
      maxDrawdown: number
      volatilityPass: boolean
      drawdownPass: boolean
    }
  }
  belonging: {
    score: number // 0-100
    weight: number // 0.2
    metrics: {
      communityUpvotes: number
      engagementLevel: "low" | "medium" | "high" | "viral"
    }
  }
  esteem: {
    score: number // 0-100
    weight: number // 0.2
    metrics: {
      alphaVsBenchmark: number
      consistencyLevel: "negative" | "neutral" | "positive" | "exceptional"
    }
  }
  selfActualization: {
    score: number // 0-100
    weight: number // 0.2
    metrics: {
      solarEnergyPercent: number
      sustainabilityLevel: "fossil" | "mixed" | "renewable" | "carbon-negative"
    }
  }
}

export interface PPIResult {
  totalScore: number // 0-100 weighted average
  tierBreakdown: PPITierBreakdown
  grade: "F" | "D" | "C" | "B" | "A" | "S"
  recommendation: string
}

/**
 * Calculate Safety tier score (40% weight)
 * Criteria: volatility < 5%, drawdown < 10%
 */
function calculateSafetyScore(volatility: number, maxDrawdown: number): number {
  let score = 100

  // Volatility penalty (target: < 5%)
  if (volatility > 5) {
    const volatilityPenalty = Math.min((volatility - 5) * 10, 50)
    score -= volatilityPenalty
  }

  // Drawdown penalty (target: < 10%)
  if (maxDrawdown > 10) {
    const drawdownPenalty = Math.min((maxDrawdown - 10) * 5, 50)
    score -= drawdownPenalty
  }

  return Math.max(0, Math.min(100, score))
}

/**
 * Calculate Belonging tier score (20% weight)
 * Criteria: community engagement and social proof
 */
function calculateBelongingScore(communityUpvotes: number): number {
  // Logarithmic scale for social engagement
  // 0 upvotes = 0, 10 = 50, 100 = 75, 1000+ = 100
  if (communityUpvotes === 0) return 0
  if (communityUpvotes < 10) return communityUpvotes * 5
  if (communityUpvotes < 100) return 50 + (communityUpvotes - 10) * 0.28
  if (communityUpvotes < 1000) return 75 + (communityUpvotes - 100) * 0.028
  return 100
}

/**
 * Calculate Esteem tier score (20% weight)
 * Criteria: consistent alpha generation vs benchmark
 */
function calculateEsteemScore(alphaVsBenchmark: number): number {
  // Alpha-based scoring
  // < 0% = 0-40, 0-5% = 40-60, 5-20% = 60-85, > 20% = 85-100
  if (alphaVsBenchmark < 0) {
    return Math.max(0, 40 + alphaVsBenchmark * 4)
  } else if (alphaVsBenchmark < 5) {
    return 40 + alphaVsBenchmark * 4
  } else if (alphaVsBenchmark < 20) {
    return 60 + (alphaVsBenchmark - 5) * 1.67
  } else {
    return Math.min(100, 85 + (alphaVsBenchmark - 20) * 0.75)
  }
}

/**
 * Calculate Self-Actualization tier score (20% weight)
 * Criteria: regenerative energy use (solar %)
 */
function calculateSelfActualizationScore(solarEnergyPercent: number): number {
  // Linear scale: 0% = 0, 50% = 50, 100% = 100
  return Math.max(0, Math.min(100, solarEnergyPercent))
}

/**
 * Get engagement level label
 */
function getEngagementLevel(upvotes: number): "low" | "medium" | "high" | "viral" {
  if (upvotes < 10) return "low"
  if (upvotes < 100) return "medium"
  if (upvotes < 1000) return "high"
  return "viral"
}

/**
 * Get consistency level label
 */
function getConsistencyLevel(alpha: number): "negative" | "neutral" | "positive" | "exceptional" {
  if (alpha < 0) return "negative"
  if (alpha < 5) return "neutral"
  if (alpha < 20) return "positive"
  return "exceptional"
}

/**
 * Get sustainability level label
 */
function getSustainabilityLevel(solar: number): "fossil" | "mixed" | "renewable" | "carbon-negative" {
  if (solar < 25) return "fossil"
  if (solar < 75) return "mixed"
  if (solar < 100) return "renewable"
  return "carbon-negative"
}

/**
 * Get letter grade from score
 */
function getGrade(score: number): "F" | "D" | "C" | "B" | "A" | "S" {
  if (score < 40) return "F"
  if (score < 55) return "D"
  if (score < 70) return "C"
  if (score < 85) return "B"
  if (score < 95) return "A"
  return "S"
}

/**
 * Generate recommendation based on score and tier breakdown
 */
function generateRecommendation(result: PPIResult): string {
  const { totalScore, tierBreakdown } = result
  const weakestTier = Object.entries({
    safety: tierBreakdown.safety.score,
    belonging: tierBreakdown.belonging.score,
    esteem: tierBreakdown.esteem.score,
    selfActualization: tierBreakdown.selfActualization.score,
  }).sort((a, b) => a[1] - b[1])[0]

  if (totalScore >= 80) {
    return "Excellent trust score! Agent demonstrates strong regenerative principles across all tiers."
  } else if (totalScore >= 60) {
    return `Good performance. Focus on improving ${weakestTier[0]} metrics to reach elite status.`
  } else if (totalScore >= 40) {
    return `Moderate trust. Significant improvement needed in ${weakestTier[0]} to build community confidence.`
  } else {
    return `Low trust score. Critical issues in ${weakestTier[0]}. Consider retraining with adjusted parameters.`
  }
}

/**
 * Calculate PPI score from episode statistics
 */
export async function calculatePPI(stats: EpisodeStats): Promise<PPIResult> {
  // Calculate individual tier scores
  const safetyScore = calculateSafetyScore(stats.volatility, stats.maxDrawdown)
  const belongingScore = calculateBelongingScore(stats.communityUpvotes)
  const esteemScore = calculateEsteemScore(stats.alphaVsBenchmark)
  const selfActualizationScore = calculateSelfActualizationScore(stats.solarEnergyPercent)

  // Define weights
  const weights = {
    safety: 0.4,
    belonging: 0.2,
    esteem: 0.2,
    selfActualization: 0.2,
  }

  // Calculate weighted total
  const totalScore =
    safetyScore * weights.safety +
    belongingScore * weights.belonging +
    esteemScore * weights.esteem +
    selfActualizationScore * weights.selfActualization

  // Build tier breakdown
  const tierBreakdown: PPITierBreakdown = {
    safety: {
      score: safetyScore,
      weight: weights.safety,
      metrics: {
        volatility: stats.volatility,
        maxDrawdown: stats.maxDrawdown,
        volatilityPass: stats.volatility < 5,
        drawdownPass: stats.maxDrawdown < 10,
      },
    },
    belonging: {
      score: belongingScore,
      weight: weights.belonging,
      metrics: {
        communityUpvotes: stats.communityUpvotes,
        engagementLevel: getEngagementLevel(stats.communityUpvotes),
      },
    },
    esteem: {
      score: esteemScore,
      weight: weights.esteem,
      metrics: {
        alphaVsBenchmark: stats.alphaVsBenchmark,
        consistencyLevel: getConsistencyLevel(stats.alphaVsBenchmark),
      },
    },
    selfActualization: {
      score: selfActualizationScore,
      weight: weights.selfActualization,
      metrics: {
        solarEnergyPercent: stats.solarEnergyPercent,
        sustainabilityLevel: getSustainabilityLevel(stats.solarEnergyPercent),
      },
    },
  }

  const result: PPIResult = {
    totalScore: Math.round(totalScore * 100) / 100,
    tierBreakdown,
    grade: getGrade(totalScore),
    recommendation: "",
  }

  result.recommendation = generateRecommendation(result)

  return result
}

/**
 * Save PPI score to Supabase
 */
export async function savePPIScore(
  stats: EpisodeStats,
  result: PPIResult,
): Promise<{ success: boolean; error?: string }> {
  try {
    const supabase = await createClient()

    const { error } = await supabase.from("ppi_scores").insert({
      episode_id: stats.episodeId,
      agent_id: stats.agentId,
      total_score: result.totalScore,
      safety_score: result.tierBreakdown.safety.score,
      belonging_score: result.tierBreakdown.belonging.score,
      esteem_score: result.tierBreakdown.esteem.score,
      self_actualization_score: result.tierBreakdown.selfActualization.score,
      safety_weight: result.tierBreakdown.safety.weight,
      belonging_weight: result.tierBreakdown.belonging.weight,
      esteem_weight: result.tierBreakdown.esteem.weight,
      self_actualization_weight: result.tierBreakdown.selfActualization.weight,
      volatility: stats.volatility,
      max_drawdown: stats.maxDrawdown,
      community_upvotes: stats.communityUpvotes,
      alpha_vs_benchmark: stats.alphaVsBenchmark,
      solar_energy_percent: stats.solarEnergyPercent,
    })

    if (error) {
      console.error("[v0] Error saving PPI score:", error)
      return { success: false, error: error.message }
    }

    // Also update the episode's ppi_score
    await supabase.from("episodes").update({ ppi_score: result.totalScore }).eq("id", stats.episodeId)

    return { success: true }
  } catch (error) {
    console.error("[v0] Exception saving PPI score:", error)
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    }
  }
}

/**
 * Get PPI score history for an agent
 */
export async function getAgentPPIHistory(agentId: string) {
  const supabase = await createClient()

  const { data, error } = await supabase
    .from("ppi_scores")
    .select("*")
    .eq("agent_id", agentId)
    .order("created_at", { ascending: false })

  if (error) {
    console.error("[v0] Error fetching PPI history:", error)
    return []
  }

  return data
}

/**
 * Get average PPI scores across all agents
 */
export async function getAveragePPIScores() {
  const supabase = await createClient()

  const { data, error } = await supabase
    .from("ppi_scores")
    .select("total_score, safety_score, belonging_score, esteem_score, self_actualization_score")

  if (error || !data || data.length === 0) {
    return null
  }

  const avg = {
    total: data.reduce((sum, s) => sum + s.total_score, 0) / data.length,
    safety: data.reduce((sum, s) => sum + s.safety_score, 0) / data.length,
    belonging: data.reduce((sum, s) => sum + s.belonging_score, 0) / data.length,
    esteem: data.reduce((sum, s) => sum + s.esteem_score, 0) / data.length,
    selfActualization: data.reduce((sum, s) => sum + s.self_actualization_score, 0) / data.length,
  }

  return avg
}
