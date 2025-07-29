"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import AIAdvisorForm from "@/components/AIAdvisorForm"
import AIRecommendations from "@/components/AIRecommendations"
import { Brain, Sparkles } from "lucide-react"

interface Preferences {
  investment_goal: string
  risk_tolerance: string
}

export default function AIAdvisor() {
  const [recommendations, setRecommendations] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [userPreferences, setUserPreferences] = useState<Preferences | null>(null)
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || ""
  const [authError, setAuthError] = useState("")

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token")
      if (!token) throw new Error("Not authenticated. Please log in.")
      setAuthError("")
    } catch (error) {
      console.error(error)
      setAuthError("Not authenticated. Please log in.")
      setTimeout(() => window.location.href = "/login", 2000)
    }
  }, [])

  const handleGetRecommendations = async (preferences: Preferences) => {
    setIsLoading(true)
    setUserPreferences(preferences)

    try {
      const token = localStorage.getItem("access_token")
      if (!token) throw new Error("Not authenticated. Please log in.")

      const response = await fetch(`${API_BASE_URL}/ai/recommend-nse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(preferences),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const message = errorData?.error || `Request failed with status ${response.status}`
        throw new Error(message)
      }

      const aiRecommendations = await response.json()
      setRecommendations(aiRecommendations)
    } catch (err: any) {
      console.error("AI Recommendation error:", err)
      setRecommendations(null)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        {authError && <div className="text-red-600 mb-4 text-center font-semibold">{authError}</div>}

        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <Brain className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">AI Investment Advisor</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Let our AI analyze your preferences and recommend the perfect NSE portfolio tailored to your goals, risk
            tolerance, and investment timeline for the Indian stock market.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="card">
            <div className="flex items-center mb-6">
              <Sparkles className="w-6 h-6 text-blue-500 mr-2" />
              <h2 className="text-2xl font-semibold">Tell Us About Your Goals</h2>
            </div>
            <AIAdvisorForm onSubmit={handleGetRecommendations} isLoading={isLoading} />
          </div>

          <div className="card">
            <h2 className="text-2xl font-semibold mb-6">AI Recommendations</h2>
            <AIRecommendations
              recommendations={recommendations}
              isLoading={isLoading}
              userPreferences={userPreferences}
            />
          </div>
        </div>

        {!recommendations && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-12"
          >
            <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-100">
              <h3 className="text-xl font-semibold mb-4 text-center">How Our AI Works with NSE Data</h3>
              <div className="grid md:grid-cols-3 gap-6">
                {/* ... Info Boxes ... */}
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
