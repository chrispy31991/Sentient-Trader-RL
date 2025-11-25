"use client"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { ArrowLeft, Save, Key } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { createClient } from "@/lib/supabase/client"

export default function SettingsPage() {
  const [xaiKey, setXaiKey] = useState("")
  const [alpacaKey, setAlpacaKey] = useState("")
  const [isSaving, setIsSaving] = useState(false)

  // PPI weight sliders (Maslow tiers)
  const [weights, setWeights] = useState({
    physiological: 20,
    safety: 20,
    belonging: 20,
    esteem: 20,
    selfActualization: 20,
  })

  const handleWeightChange = (tier: keyof typeof weights, value: number) => {
    setWeights((prev) => ({ ...prev, [tier]: value }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    const supabase = createClient()

    try {
      // Save settings to Supabase
      const { error } = await supabase.from("settings").upsert({
        xai_api_key: xaiKey,
        alpaca_api_key: alpacaKey,
        ppi_weights: {
          physiological: weights.physiological / 100,
          safety: weights.safety / 100,
          belonging: weights.belonging / 100,
          esteem: weights.esteem / 100,
          self_actualization: weights.selfActualization / 100,
        },
        updated_at: new Date().toISOString(),
      })

      if (error) throw error

      alert("Settings saved successfully!")
    } catch (error) {
      console.error("[v0] Error saving settings:", error)
      alert("Failed to save settings. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="glass-strong border-b border-purple-500/20 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <Button variant="ghost" size="sm" className="gap-2">
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
              </Link>
              <div className="h-6 w-px bg-border" />
              <h1 className="text-xl font-bold neon-text">Settings</h1>
            </div>
            <Button size="sm" onClick={handleSave} disabled={isSaving} className="gradient-cyber gap-2">
              <Save className="w-4 h-4" />
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        <div className="space-y-6">
          {/* API Keys Section */}
          <Card className="glass-strong border-purple-500/20 p-6">
            <div className="flex items-center gap-2 mb-6">
              <Key className="w-5 h-5 text-purple-400" />
              <h2 className="text-lg font-semibold">API Keys</h2>
            </div>

            <div className="space-y-4">
              {/* xAI Grok API Key */}
              <div className="space-y-2">
                <Label htmlFor="xai-key" className="text-sm text-muted-foreground">
                  xAI Grok API Key
                </Label>
                <Input
                  id="xai-key"
                  type="password"
                  placeholder="xai-..."
                  value={xaiKey}
                  onChange={(e) => setXaiKey(e.target.value)}
                  className="glass border-purple-500/30 focus:border-purple-500/50 bg-transparent"
                />
                <p className="text-xs text-muted-foreground">
                  Required for Grok AI confidence scoring. Get your key from{" "}
                  <a
                    href="https://x.ai"
                    className="text-purple-400 hover:underline"
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    x.ai
                  </a>
                </p>
              </div>

              {/* Alpaca API Key */}
              <div className="space-y-2">
                <Label htmlFor="alpaca-key" className="text-sm text-muted-foreground">
                  Alpaca API Key
                </Label>
                <Input
                  id="alpaca-key"
                  type="password"
                  placeholder="PK..."
                  value={alpacaKey}
                  onChange={(e) => setAlpacaKey(e.target.value)}
                  className="glass border-purple-500/30 focus:border-purple-500/50 bg-transparent"
                />
                <p className="text-xs text-muted-foreground">
                  Required for live market data. Get your key from{" "}
                  <a
                    href="https://alpaca.markets"
                    className="text-purple-400 hover:underline"
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    alpaca.markets
                  </a>
                </p>
              </div>

              {/* Supabase Info (Read-only) */}
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Supabase Connection</Label>
                <div className="glass border-purple-500/30 rounded-lg p-3 flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Connected via environment variables</span>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span className="text-xs text-green-400">Active</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* PPI Weight Sliders Section */}
          <Card className="glass-strong border-purple-500/20 p-6">
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-2">PPI Trust Score Weights</h2>
              <p className="text-sm text-muted-foreground">
                Adjust the importance of each Maslow tier in the PPI calculation. Total should equal 100%.
              </p>
            </div>

            <div className="space-y-6">
              {/* Physiological */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Physiological Needs</Label>
                  <span className="text-sm font-mono text-purple-400">{weights.physiological}%</span>
                </div>
                <Slider
                  value={[weights.physiological]}
                  onValueChange={(value) => handleWeightChange("physiological", value[0])}
                  min={0}
                  max={100}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">Basic survival and resource management</p>
              </div>

              {/* Safety */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Safety & Security</Label>
                  <span className="text-sm font-mono text-purple-400">{weights.safety}%</span>
                </div>
                <Slider
                  value={[weights.safety]}
                  onValueChange={(value) => handleWeightChange("safety", value[0])}
                  min={0}
                  max={100}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">Risk management and stability</p>
              </div>

              {/* Belonging */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Belonging & Social</Label>
                  <span className="text-sm font-mono text-purple-400">{weights.belonging}%</span>
                </div>
                <Slider
                  value={[weights.belonging]}
                  onValueChange={(value) => handleWeightChange("belonging", value[0])}
                  min={0}
                  max={100}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">Cooperation and network effects</p>
              </div>

              {/* Esteem */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Esteem & Recognition</Label>
                  <span className="text-sm font-mono text-purple-400">{weights.esteem}%</span>
                </div>
                <Slider
                  value={[weights.esteem]}
                  onValueChange={(value) => handleWeightChange("esteem", value[0])}
                  min={0}
                  max={100}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">Performance and achievement</p>
              </div>

              {/* Self-Actualization */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Self-Actualization</Label>
                  <span className="text-sm font-mono text-purple-400">{weights.selfActualization}%</span>
                </div>
                <Slider
                  value={[weights.selfActualization]}
                  onValueChange={(value) => handleWeightChange("selfActualization", value[0])}
                  min={0}
                  max={100}
                  step={1}
                />
                <p className="text-xs text-muted-foreground">Innovation and optimal strategy</p>
              </div>

              {/* Total Weight Indicator */}
              <div className="pt-4 border-t border-purple-500/20">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">Total Weight</span>
                  <span
                    className={`text-lg font-mono font-bold ${totalWeight === 100 ? "text-green-400" : "text-red-400"}`}
                  >
                    {totalWeight}%
                  </span>
                </div>
                {totalWeight !== 100 && (
                  <p className="text-xs text-red-400 mt-1">Warning: Total should equal 100% for accurate scoring</p>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
