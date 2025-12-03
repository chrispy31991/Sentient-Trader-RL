import { generateText } from "ai"

export interface MarketState {
  price: number
  volatility: number
  ppiTier: string
  capital: number
}

export interface TradeDecision {
  action: "buy" | "sell" | "hold"
  size: number
  reasoning: string
}

interface CachedResponse {
  timestamp: number
  state: MarketState
  decision: TradeDecision
}

// Cache last 5 responses
const responseCache: CachedResponse[] = []
const MAX_CACHE_SIZE = 5

function addToCache(state: MarketState, decision: TradeDecision) {
  responseCache.push({
    timestamp: Date.now(),
    state,
    decision,
  })

  if (responseCache.length > MAX_CACHE_SIZE) {
    responseCache.shift()
  }
}

function getCacheContext(): string {
  if (responseCache.length === 0) return ""

  return `\n\nPrevious decisions (for context):\n${responseCache
    .map(
      (r, i) =>
        `${i + 1}. Price: $${r.state.price}, Action: ${r.decision.action} (${r.decision.size}x) - ${r.decision.reasoning}`,
    )
    .join("\n")}`
}

export async function getGrokTradeDecision(state: MarketState, maxRetries = 3): Promise<TradeDecision> {
  const cacheContext = getCacheContext()

  const prompt = `You are a sovereign AI trader in a regenerative trust node.

Current BTC price: $${state.price.toFixed(2)}
24h volatility: ${(state.volatility * 100).toFixed(2)}%
Sentiment (PPI Maslow tier): ${state.ppiTier}
Your capital: ${state.capital.toFixed(4)} BTC

Goal: Maximize risk-adjusted return while maintaining PPI trust > 80.
${cacheContext}

Return ONLY valid JSON with this exact structure:
{
  "action": "buy" or "sell" or "hold",
  "size": number between 0.1 and 1.0,
  "reasoning": "brief explanation"
}`

  let lastError: Error | null = null

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const { text } = await generateText({
        model: "xai/grok-4-fast",
        prompt,
        maxOutputTokens: 500,
        temperature: 0.7,
      })

      // Parse JSON from response (handle markdown code blocks)
      let jsonText = text.trim()
      if (jsonText.startsWith("```json")) {
        jsonText = jsonText.replace(/```json\n?/g, "").replace(/```\n?/g, "")
      } else if (jsonText.startsWith("```")) {
        jsonText = jsonText.replace(/```\n?/g, "")
      }

      const decision = JSON.parse(jsonText) as TradeDecision

      // Validate response
      if (!["buy", "sell", "hold"].includes(decision.action)) {
        throw new Error(`Invalid action: ${decision.action}`)
      }
      if (decision.size < 0.1 || decision.size > 1.0) {
        throw new Error(`Invalid size: ${decision.size}`)
      }
      if (!decision.reasoning || decision.reasoning.length < 10) {
        throw new Error("Reasoning too short")
      }

      // Add to cache
      addToCache(state, decision)

      return decision
    } catch (error) {
      lastError = error as Error
      console.error(`[v0] Grok API attempt ${attempt + 1} failed:`, error)

      // Wait before retry (exponential backoff)
      if (attempt < maxRetries - 1) {
        await new Promise((resolve) => setTimeout(resolve, Math.pow(2, attempt) * 1000))
      }
    }
  }

  // Fallback to conservative decision if all retries fail
  console.error("[v0] All Grok API retries failed, using fallback decision")
  return {
    action: "hold",
    size: 0.1,
    reasoning: `API error after ${maxRetries} retries: ${lastError?.message || "Unknown error"}. Defaulting to conservative hold.`,
  }
}

export function getCachedResponses(): CachedResponse[] {
  return [...responseCache]
}

export function clearCache() {
  responseCache.length = 0
}
