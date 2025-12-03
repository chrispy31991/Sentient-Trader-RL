"use client"

import { useEffect, useState } from "react"
import { Line } from "react-chartjs-2"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js"

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

export function MarketChart() {
  const [data, setData] = useState<number[]>([])

  useEffect(() => {
    // Generate initial candlestick data
    const initialData = Array.from({ length: 24 }, (_, i) => 67000 + Math.random() * 2000)
    setData(initialData)

    // Simulate real-time updates
    const interval = setInterval(() => {
      setData((prev) => {
        const newData = [...prev.slice(1), prev[prev.length - 1] + (Math.random() - 0.5) * 500]
        return newData
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const chartData = {
    labels: Array.from({ length: data.length }, (_, i) => `${i}h`),
    datasets: [
      {
        label: "BTC/USD",
        data: data,
        borderColor: "rgb(168, 85, 247)",
        backgroundColor: "rgba(168, 85, 247, 0.1)",
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 2,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: "index" as const,
        intersect: false,
        backgroundColor: "rgba(15, 15, 30, 0.9)",
        titleColor: "rgb(168, 85, 247)",
        bodyColor: "rgb(240, 240, 255)",
        borderColor: "rgb(168, 85, 247)",
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        grid: {
          color: "rgba(168, 85, 247, 0.1)",
        },
        ticks: {
          color: "rgb(160, 160, 180)",
          font: {
            size: 10,
          },
        },
      },
      y: {
        grid: {
          color: "rgba(168, 85, 247, 0.1)",
        },
        ticks: {
          color: "rgb(160, 160, 180)",
          font: {
            size: 10,
          },
          callback: (value: number | string) => `$${Number(value).toLocaleString()}`,
        },
      },
    },
  }

  return (
    <div className="h-[calc(100%-2rem)]">
      <Line data={chartData} options={options} />
    </div>
  )
}
