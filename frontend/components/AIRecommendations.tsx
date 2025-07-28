"use client"

import { motion } from "framer-motion"
import { Brain, Target, CheckCircle, AlertCircle } from "lucide-react"
import Button from "./Button"
import PieChart from "./PieChart"

interface Stock {
  symbol: string
  name: string
  weight: number
  confidence: number
  reasoning: string
  sector: string
  expectedReturn: number
  riskScore: number
}

interface Recommendations {
  portfolio: Stock[]
  summary: {
    totalExpectedReturn: number
    portfolioRiskScore: number
    diversificationScore: number
    alignmentScore: number
  }
  insights: string[]
}

interface AIRecommendationsProps {
  recommendations: Recommendations | null
  isLoading: boolean
  userPreferences: any
}

export default function AIRecommendations({ recommendations, isLoading, userPreferences }: AIRecommendationsProps) {
  if (isLoading) {
    return (
      <div className="text-center py-12">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
          className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <Brain className="w-8 h-8 text-white" />
        </motion.div>
        <h3 className="text-lg font-semibold mb-2">AI is analyzing your preferences...</h3>
        <p className="text-gray-600 text-sm">Processing NSE market data and optimizing your portfolio</p>
        <div className="mt-4 space-y-2">
          <div className="text-xs text-gray-500">✓ Analyzing risk tolerance</div>
          <div className="text-xs text-gray-500">✓ Evaluating NSE market conditions</div>
          <div className="text-xs text-gray-500">✓ Optimizing asset allocation</div>
          <div className="text-xs text-gray-500">⏳ Generating recommendations...</div>
        </div>
      </div>
    )
  }

  if (!recommendations || !Array.isArray(recommendations.portfolio) || recommendations.portfolio.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p className="text-lg mb-2">Ready to analyze your preferences</p>
        <p className="text-sm">Fill out the form to get personalized AI recommendations</p>
        {userPreferences && !isLoading && (
          <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-800">
              AI analysis complete, but no recommendations received. Please check your backend connection.
            </p>
          </div>
        )}
      </div>
    )
  }

  // Prepare data for pie chart with HSL colors uniquely assigned
  const pieChartData = recommendations.portfolio.map((stock, index) => ({
    label: stock.symbol,
    value: stock.weight,
    color: `hsl(${(index * 137.5) % 360}, 70%, 60%)`,
  }))

  const handleAcceptRecommendations = () => {
    // TODO: Implement saving/accept flow
    console.log("Accepting AI recommendations:", recommendations)
  }

  const handleModifyRecommendations = () => {
    // TODO: Implement modify recommendations flow
    console.log("Modifying recommendations")
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      {/* Summary Section */}
      <div className="bg-gradient-to-br from-green-50 to-blue-50 p-4 rounded-lg border border-green-200">
        <div className="flex items-center mb-3">
          <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
          <h3 className="font-semibold text-green-800">AI Analysis Complete</h3>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Expected Return:</span>
            <span className="font-semibold text-green-600 ml-1">{recommendations.summary.totalExpectedReturn}%</span>
          </div>
          <div>
            <span className="text-gray-600">Risk Score:</span>
            <span className="font-semibold ml-1">{recommendations.summary.portfolioRiskScore}/10</span>
          </div>
          <div>
            <span className="text-gray-600">Diversification:</span>
            <span className="font-semibold text-blue-600 ml-1">{recommendations.summary.diversificationScore}/10</span>
          </div>
          <div>
            <span className="text-gray-600">Goal Alignment:</span>
            <span className="font-semibold text-purple-600 ml-1">{recommendations.summary.alignmentScore}%</span>
          </div>
        </div>
      </div>

      {/* Allocation Pie Chart */}
      <div>
        <h4 className="font-semibold mb-3">Recommended Allocation</h4>
        <PieChart data={pieChartData} />
      </div>

      {/* Stock List */}
      <div>
        <h4 className="font-semibold mb-3">AI-Selected NSE Stocks</h4>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {recommendations.portfolio.map((stock, index) => (
            <motion.div
              key={stock.symbol}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
              className="border border-gray-200 rounded-lg p-3"
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h5 className="font-semibold text-sm">{stock.symbol}</h5>
                  <p className="text-xs text-gray-600">{stock.name}</p>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-blue-600">{stock.weight}%</div>
                  <div className="flex items-center text-xs">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
                    {stock.confidence}% confidence
                  </div>
                </div>
              </div>
              <p className="text-xs text-gray-700 mb-2">{stock.reasoning}</p>
              <div className="flex justify-between text-xs text-gray-500">
                <span>{stock.sector}</span>
                <span>Expected: {stock.expectedReturn}%</span>
                <span>Risk: {stock.riskScore}/10</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* AI Insights */}
      <div>
        <h4 className="font-semibold mb-3 flex items-center">
          <Target className="w-4 h-4 mr-1" />
          AI Insights
        </h4>
        <div className="space-y-2">
          {recommendations.insights.map((insight, index) => (
            <div key={index} className="flex items-start text-sm">
              <AlertCircle className="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
              <span className="text-gray-700">{insight}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-3 pt-4 border-t border-gray-200">
        <Button text="Accept AI Recommendations" onClick={handleAcceptRecommendations} className="w-full btn-primary" />
        <Button text="Modify Recommendations" onClick={handleModifyRecommendations} className="w-full btn-secondary" />
        <p className="text-xs text-gray-500 text-center">
          Accepting will add these NSE stocks to your portfolio for tracking and management
        </p>
      </div>
    </motion.div>
  )
}
