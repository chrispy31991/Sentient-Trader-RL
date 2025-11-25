import { NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/server"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { agentId, episode, step } = body

    // Mock simulation step data
    const actions = ["buy", "sell", "hold"]
    const action = actions[Math.floor(Math.random() * actions.length)]
    const price = 67000 + Math.random() * 2000
    const size = action === "hold" ? 0 : Math.random() * 0.5
    const reward = (Math.random() - 0.3) * 10

    // Calculate PPI score components (Maslow tiers)
    const ppiComponents = {
      physiological: 85 + Math.random() * 10,
      safety: 80 + Math.random() * 15,
      belonging: 75 + Math.random() * 20,
      esteem: 82 + Math.random() * 12,
      selfActualization: 78 + Math.random() * 15,
    }

    const ppiScore =
      (ppiComponents.physiological +
        ppiComponents.safety +
        ppiComponents.belonging +
        ppiComponents.esteem +
        ppiComponents.selfActualization) /
      5

    const grokConfidence = 0.7 + Math.random() * 0.25

    // Mock market data
    const marketData = {
      btcPrice: price,
      volume: Math.random() * 1000000,
      volatility: Math.random() * 0.05,
    }

    // Save action to database
    const supabase = await createClient()

    // First, ensure episode exists
    const { data: episodeData, error: episodeError } = await supabase
      .from("episodes")
      .select("id")
      .eq("agent_id", agentId)
      .eq("episode_number", episode)
      .single()

    let episodeId = episodeData?.id

    if (!episodeId) {
      // Create new episode
      const { data: newEpisode, error: createError } = await supabase
        .from("episodes")
        .insert({
          agent_id: agentId,
          episode_number: episode,
          total_reward: reward,
          steps: step,
          ppi_score: ppiScore,
        })
        .select()
        .single()

      if (createError) {
        console.error("[v0] Error creating episode:", createError)
      } else {
        episodeId = newEpisode.id
      }
    } else {
      // Update existing episode
      await supabase
        .from("episodes")
        .update({
          total_reward: reward,
          steps: step,
          ppi_score: ppiScore,
        })
        .eq("id", episodeId)
    }

    // Insert action
    if (episodeId) {
      const { error: actionError } = await supabase.from("actions").insert({
        episode_id: episodeId,
        step: step,
        action_type: action,
        size: size,
        price: price,
        reward: reward,
        grok_confidence: grokConfidence,
      })

      if (actionError) {
        console.error("[v0] Error inserting action:", actionError)
      }
    }

    // Return simulation step data
    return NextResponse.json({
      success: true,
      step: {
        episode,
        step,
        action,
        size,
        price,
        reward,
        ppiScore,
        ppiComponents,
        grokConfidence,
        marketData,
        timestamp: new Date().toISOString(),
      },
    })
  } catch (error) {
    console.error("[v0] Simulation error:", error)
    return NextResponse.json({ success: false, error: "Simulation failed" }, { status: 500 })
  }
}

export async function GET() {
  return NextResponse.json({
    message: "Simulation API - Use POST to run a simulation step",
    endpoints: {
      POST: "/api/simulate",
      body: {
        agentId: "uuid",
        episode: "number",
        step: "number",
      },
    },
  })
}
