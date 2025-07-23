"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button" // Assuming shadcn/ui Button

interface PortfolioItem {
  symbol: string
  currentPrice: number
  predictedPrice: number
  change: number
}

interface PortfolioTableProps {
  data: PortfolioItem[]
  onImportClick?: () => void // New prop for import button click
}

export default function PortfolioTable({ data, onImportClick }: PortfolioTableProps) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No NSE portfolio data available.</p>
        <p className="text-sm mt-2">Connect your portfolio to see NSE holdings here.</p>
        <p className="text-sm mt-1">Data will be populated when backend is connected.</p>
        {onImportClick && (
          <Button onClick={onImportClick} className="mt-4 btn-primary">
            Import Portfolio
          </Button>
        )}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-medium text-gray-600">NSE Symbol</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Current Price (₹)</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Predicted Price (₹)</th>
            <th className="text-left py-3 px-4 font-medium text-gray-600">Change %</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <motion.tr
              key={item.symbol}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="py-3 px-4 font-medium">{item.symbol}</td>
              <td className="py-3 px-4">₹{item.currentPrice.toFixed(2)}</td>
              <td className="py-3 px-4">₹{item.predictedPrice.toFixed(2)}</td>
              <td className={`py-3 px-4 font-medium ${item.change >= 0 ? "text-green-500" : "text-red-500"}`}>
                {item.change >= 0 ? "+" : ""}
                {item.change.toFixed(2)}%
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
