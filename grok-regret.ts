import { generateObject } from "ai"
import { z } from "zod"

const regretSchema = z.object({
  regret: z.number().min(0).max(1).describe("Regret forecast from 0.00 to 1.00"),
  feeling_name: z.string().describe("Name of the primary emotion (e.g., FOMO, Fear, Greed)"),
  intensity: z.number().min(1).max(10).describe("Emotional intensity from 1-10"),
  fractal_link: z.string().describe("Connection to past emotional pattern"),
  prediction: z.string().describe("Predicted action in next 5 minutes"),
  recommendation: z.enum(["hold", "counter_bias", "ride_bias", "block_trade"]),
})

export type RegretForecast = z.infer<typeof regretSchema>

export async function forecastRegret(params: {
  actorName: string
  shullFractal: string
  price: number
  volatility: number
  lastAction: string
  inventory: number
}): Promise<RegretForecast> {
  const { actorName, shullFractal, price, volatility, lastAction, inventory } = params

  const prompt = `You are analyzing ${actorName}'s emotional state using Denise Shull's ReThink Method.

Actor: ${actorName}
Fractal Pattern: ${shullFractal}
Current BTC Price: $${price.toLocaleString()}
24h Volatility: ${(volatility * 100).toFixed(2)}%
Last Action: ${lastAction}
Current Inventory: ${inventory.toFixed(2)} BTC

Using the 7-step ReThink Method:
1. Name the feeling this actor is experiencing right now
2. Rate emotional intensity 1-10
3. Link to their fractal pattern (past emotional trauma)
4. Predict what they'll do in the next 5 minutes
5. Calculate regret forecast (0.00-1.00) if they hold for 5 more minutes
6. Recommend: hold, counter_bias, ride_bias, or block_trade (if regret > 0.7)

Return structured regret analysis.`

  try {
    const { object } = await generateObject({
      model: "xai/grok-beta",
      schema: regretSchema,
      prompt,
      temperature: 0.3,
    })

    return object
  } catch (error) {
    console.error("[v0] Grok regret forecast error:", error)
    // Fallback
    return {
      regret: 0.5,
      feeling_name: "Uncertainty",
      intensity: 5,
      fractal_link: "Unable to analyze fractal pattern",
      prediction: "Likely to hold position",
      recommendation: "hold",
    }
  }
}

// Block trade if regret > 0.7 (Denise Shull rule)
export function shouldBlockTrade(regret: number): boolean {
  return regret > 0.7
}
