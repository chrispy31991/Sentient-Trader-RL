"use client"

import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Activity, TrendingUp } from "lucide-react"

interface NashMeterProps {
  isEquilibrium: boolean
  nashDeviation: number
  analysis: string
  equilibriumPercentage: number
}

export function NashMeter({ isEquilibrium, nashDeviation, analysis, equilibriumPercentage }: NashMeterProps) {
  const stabilityScore = Math.max(0, 100 - nashDeviation * 100)

  return (
    <Card className="p-6 bg-gradient-to-br from-background to-muted/20 border-2">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Nash Equilibrium Monitor</h3>
          </div>
          <Badge variant={isEquilibrium ? "default" : "secondary"} className="gap-1">
            {isEquilibrium ? "✓ Equilibrium" : "Seeking..."}
          </Badge>
        </div>

        {/* Stability Score */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Market Stability</span>
            <span className="font-mono font-semibold">{stabilityScore.toFixed(1)}%</span>
          </div>
          <Progress value={stabilityScore} className="h-2" />
        </div>

        {/* Nash Deviation */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Nash Deviation</span>
            <span className="font-mono">{(nashDeviation * 100).toFixed(1)}%</span>
          </div>
          <Progress value={Math.min(100, nashDeviation * 500)} className="h-1" />
        </div>

        {/* Equilibrium Percentage */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-primary/10 border border-primary/20">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">Equilibrium Time</span>
          </div>
          <span className="text-lg font-bold text-primary">{equilibriumPercentage.toFixed(0)}%</span>
        </div>

        {/* Analysis */}
        <div className="p-3 rounded-lg bg-muted/50 border border-border">
          <p className="text-sm text-muted-foreground">{analysis}</p>
        </div>

        {/* Green Flash Effect */}
        {isEquilibrium && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-green-500/20 animate-pulse rounded-lg" />
          </div>
        )}
      </div>
    </Card>
  )
}
