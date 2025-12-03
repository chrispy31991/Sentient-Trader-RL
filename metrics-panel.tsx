"use client"

import { useEffect, useState } from "react"
import { Progress } from "@/components/ui/progress"

interface MetricsPanelProps {
  episode: number
  step: number
  isPlaying: boolean
}

export function MetricsPanel({ episode, step, isPlaying }: MetricsPanelProps) {
  const [reward, setReward] = useState(0)
  const [ppiScore, setPpiScore] = useState(85.5)
  const [grokConfidence, setGrokConfidence] = useState(0.78)

  useEffect(() => {
    if (!isPlaying) return

    const interval = setInterval(() => {
      setReward((prev) => prev + (Math.random() - 0.3) * 10)
      setPpiScore((prev) => Math.max(0, Math.min(100, prev + (Math.random() - 0.5) * 2)))
      setGrokConfidence(Math.random() * 0.3 + 0.7)
    }, 2000)

    return () => clearInterval(interval)
  }, [isPlaying])

  return (
    <div className="space-y-4">
      {/* Episode & Step */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-muted-foreground mb-1">Episode</div>
          <div className="text-2xl font-bold font-mono text-purple-400">#{episode}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground mb-1">Step</div>
          <div className="text-2xl font-bold font-mono text-blue-400">{step}</div>
        </div>
      </div>

      {/* Reward */}
      <div>
        <div className="text-xs text-muted-foreground mb-1">Total Reward</div>
        <div className={`text-xl font-bold font-mono ${reward >= 0 ? "text-green-400" : "text-red-400"}`}>
          {reward >= 0 ? "+" : ""}
          {reward.toFixed(2)}
        </div>
      </div>

      {/* PPI Trust Score */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs text-muted-foreground">PPI Trust Score</div>
          <div className="text-sm font-mono text-purple-400">{ppiScore.toFixed(1)}/100</div>
        </div>
        <Progress value={ppiScore} className="h-2" />
      </div>

      {/* Grok Confidence */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="text-xs text-muted-foreground">Grok Confidence</div>
          <div className="text-sm font-mono text-blue-400">{(grokConfidence * 100).toFixed(1)}%</div>
        </div>
        <Progress value={grokConfidence * 100} className="h-2" />
      </div>

      {/* Maslow Tiers Breakdown */}
      <div className="pt-2 border-t border-purple-500/20">
        <div className="text-xs text-muted-foreground mb-3">Maslow Tier Breakdown</div>
        <div className="space-y-2">
          {[
            { name: "Physiological", value: 92 },
            { name: "Safety", value: 88 },
            { name: "Belonging", value: 81 },
            { name: "Esteem", value: 85 },
            { name: "Self-Actualization", value: 79 },
          ].map((tier) => (
            <div key={tier.name} className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{tier.name}</span>
              <span className="font-mono text-purple-300">{tier.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
