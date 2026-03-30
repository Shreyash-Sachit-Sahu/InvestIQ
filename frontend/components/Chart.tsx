"use client"

import { Line, Bar } from "react-chartjs-2"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js"

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend)

interface ChartProps {
  labels: string[]
  data: any[]
  type?: "line" | "bar"
}

export default function Chart({ labels, data, type = "line" }: ChartProps) {
  // Ensure labels and data are arrays before proceeding
  if (!Array.isArray(labels) || !Array.isArray(data) || labels.length === 0 || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
        <div className="text-center">
          <p>No chart data available</p>
          <p className="text-sm mt-1">NSE data will appear here when connected to API</p>
          {/* TODO: Connect to Flask backend for NSE chart data */}
        </div>
      </div>
    )
  }

  const chartData = {
    labels,
    datasets: data,
  }

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top" as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  }

  return (
    <div className="h-64">
      {type === "line" ? <Line data={chartData} options={options} /> : <Bar data={chartData} options={options} />}
    </div>
  )
}
