"use client"

import { Pie } from "react-chartjs-2"
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js"

ChartJS.register(ArcElement, Tooltip, Legend)

interface PieChartProps {
  data: Array<{ label: string; value: number; color?: string }>
}

export default function PieChart({ data }: PieChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
        <div className="text-center">
          <p>No allocation data available</p>
          <p className="text-sm mt-1">NSE portfolio allocation will appear here</p>
        </div>
      </div>
    )
  }

  const chartData = {
    labels: data.map((item) => item.label),
    datasets: [
      {
        data: data.map((item) => item.value),
        backgroundColor: data.map((item, index) => item.color || `hsl(${(index * 137.5) % 360}, 70%, 60%)`),
        borderWidth: 2,
        borderColor: "#ffffff",
      },
    ],
  }

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "bottom" as const,
      },
    },
  }

  return (
    <div className="h-64">
      <Pie data={chartData} options={options} />
    </div>
  )
}
