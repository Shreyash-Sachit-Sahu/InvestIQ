"use client"

import { motion } from "framer-motion"
import { TrendingUp, TrendingDown } from "lucide-react"

interface SummaryCardProps {
  title: string
  value: string
  delta: number
}

export default function SummaryCard({ title, value, delta }: SummaryCardProps) {
  const isPositive = delta >= 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="card"
    >
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
      <div className="flex items-center justify-between">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {delta !== 0 && (
          <div className={`flex items-center ${isPositive ? "text-green-500" : "text-red-500"}`}>
            {isPositive ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
            <span className="text-sm font-medium">{Math.abs(delta).toFixed(2)}%</span>
          </div>
        )}
      </div>
    </motion.div>
  )
}
