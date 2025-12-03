"use client"

import { useEffect, useState } from "react"
import { ArrowDown, ArrowUp, Minus } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Action {
  step: number
  type: "buy" | "sell" | "hold"
  size: number
  price: number
  timestamp: string
}

export function ActionLog({ step, realtimeActions }: { step: number; realtimeActions?: any[] }) {
  const [actions, setActions] = useState<Action[]>([
    { step: 0, type: "hold", size: 0, price: 67234.56, timestamp: "00:00:00" },
  ])

  useEffect(() => {
    if (realtimeActions && realtimeActions.length > 0) {
      const newActions = realtimeActions.map((action) => ({
        step: action.step,
        type: action.action_type as "buy" | "sell" | "hold",
        size: action.size,
        price: action.price,
        timestamp: new Date(action.timestamp).toLocaleTimeString(),
      }))
      setActions((prev) => {
        const merged = [...newActions, ...prev]
        const unique = merged.filter((action, index, self) => index === self.findIndex((a) => a.step === action.step))
        return unique.slice(0, 20)
      })
    }
  }, [realtimeActions])

  useEffect(() => {
    const interval = setInterval(() => {
      const types: ("buy" | "sell" | "hold")[] = ["buy", "sell", "hold"]
      const type = types[Math.floor(Math.random() * types.length)]
      const newAction: Action = {
        step: actions.length,
        type,
        size: type === "hold" ? 0 : Math.random() * 0.5,
        price: 67000 + Math.random() * 2000,
        timestamp: new Date().toLocaleTimeString(),
      }
      setActions((prev) => [newAction, ...prev].slice(0, 20))
    }, 3000)

    return () => clearInterval(interval)
  }, [actions.length])

  return (
    <ScrollArea className="h-[calc(100%-2rem)]">
      <div className="space-y-2">
        {actions.map((action, i) => (
          <div
            key={i}
            className="flex items-center justify-between p-2 rounded-lg glass border border-purple-500/10 hover:border-purple-500/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  action.type === "buy"
                    ? "bg-green-500/20 text-green-400"
                    : action.type === "sell"
                      ? "bg-red-500/20 text-red-400"
                      : "bg-gray-500/20 text-gray-400"
                }`}
              >
                {action.type === "buy" ? (
                  <ArrowUp className="w-4 h-4" />
                ) : action.type === "sell" ? (
                  <ArrowDown className="w-4 h-4" />
                ) : (
                  <Minus className="w-4 h-4" />
                )}
              </div>
              <div>
                <div className="text-sm font-semibold capitalize">{action.type}</div>
                <div className="text-xs text-muted-foreground">Step {action.step}</div>
              </div>
            </div>
            <div className="text-right">
              {action.size > 0 && <div className="text-sm font-mono">{action.size.toFixed(3)} BTC</div>}
              <div className="text-xs text-muted-foreground">${action.price.toFixed(2)}</div>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
