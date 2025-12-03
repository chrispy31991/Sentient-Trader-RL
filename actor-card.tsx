"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

interface ActorCardProps {
  actor: {
    id: string
    name: string
    regret_score: number
    inventory_btc: number
    last_action: number
    nash_stable: boolean
    shull_fractal?: string
  }
  isActive?: boolean
}

const actorConfig: Record<string, { icon: string; color: string; prompt: string }> = {
  Retail: {
    icon: "👥",
    color: "#FF5555",
    prompt: "You are Retail. FOMO > 0.7 → buy. Regret > 0.8 → panic sell.",
  },
  Whale: {
    icon: "🐋",
    color: "#00AAFF",
    prompt: "You are Whale. Move 26k BTC. Predict short-cover cascade.",
  },
  "HFT-MM": {
    icon: "⚡",
    color: "#00FFAA",
    prompt: "You are HFT. Pin $115K gamma wall. Latency 5ms.",
  },
  Institution: {
    icon: "🏦",
    color: "#FFD700",
    prompt: "You are BlackRock. $1.2B daily inflow. Never sell the rip.",
  },
  "Arb Bot": {
    icon: "🤖",
    color: "#AA00FF",
    prompt: "You are Arb Bot. Exploit 0.3% Binance-Coinbase spread.",
  },
  "Sentient Trader": {
    icon: "易",
    color: "#FFFFFF",
    prompt: "You are Sentient Trader. Read 5 regrets → pick Nash move.",
  },
}

export function ActorCard({ actor, isActive }: ActorCardProps) {
  const config = actorConfig[actor.name] || actorConfig["Sentient Trader"]
  const isBlocked = actor.regret_score > 0.7

  return (
    <Card
      className={`relative overflow-hidden border-2 transition-all ${
        actor.nash_stable ? "border-green-500 shadow-lg shadow-green-500/20" : "border-red-500/50"
      } ${isActive ? "scale-105" : ""}`}
      style={{ borderColor: actor.nash_stable ? "#00ff00" : config.color }}
    >
      {/* Content */}
      <div className="relative p-4 space-y-3 bg-black/40 backdrop-blur-sm">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl" style={{ filter: `drop-shadow(0 0 8px ${config.color})` }}>
              {config.icon}
            </div>
            <div>
              <h3 className="font-bold text-lg" style={{ color: config.color }}>
                {actor.name}
              </h3>
              <Badge
                variant="outline"
                className="text-xs mt-1"
                style={{ borderColor: config.color, color: config.color }}
              >
                {actor.nash_stable ? "NASH STABLE" : "UNSTABLE"}
              </Badge>
            </div>
          </div>

          {/* Nash indicator */}
          {actor.nash_stable && (
            <div
              className="w-3 h-3 rounded-full bg-green-500 animate-pulse"
              style={{ boxShadow: "0 0 10px #00ff00" }}
            />
          )}
        </div>

        {/* Metrics */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Inventory</span>
            <span className="font-mono text-white">{actor.inventory_btc.toFixed(2)} BTC</span>
          </div>

          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Action</span>
            <span className="font-mono text-white">{getActionName(actor.last_action)}</span>
          </div>

          {/* Regret Score */}
          <div className="space-y-1">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Regret Score</span>
              <span className={`font-mono font-bold ${isBlocked ? "text-red-500" : "text-white"}`}>
                {actor.regret_score.toFixed(2)}
              </span>
            </div>
            <Progress
              value={actor.regret_score * 100}
              className="h-2"
              style={{
                backgroundColor: "rgba(255,255,255,0.1)",
              }}
            />
            {isBlocked && (
              <p className="text-xs text-red-500 font-bold animate-pulse">⚠️ TRADE BLOCKED - Regret &gt; 0.7</p>
            )}
          </div>

          {/* Shull Fractal */}
          {actor.shull_fractal && (
            <div className="pt-2 border-t border-white/10">
              <p className="text-xs text-muted-foreground italic">&quot;{actor.shull_fractal}&quot;</p>
            </div>
          )}
        </div>
      </div>

      {/* Active indicator */}
      {isActive && (
        <div className="absolute top-2 right-2">
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: config.color }} />
        </div>
      )}
    </Card>
  )
}

function getActionName(action: number): string {
  const actions = [
    "HOLD",
    "LONG 0.25%",
    "LONG 0.5%",
    "LONG 1.0%",
    "SHORT 0.25%",
    "SHORT 0.5%",
    "SHORT 1.0%",
    "RAMP EZ",
    "TRAC",
  ]
  return actions[action] || "HOLD"
}
