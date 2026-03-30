"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import AIAdvisorForm from "@/components/AIAdvisorForm"
import AIRecommendations from "@/components/AIRecommendations"
import { Brain, Sparkles, X, LogIn } from "lucide-react"
import Link from "next/link"
import { API_BASE_URL } from "@/lib/api"

export default function AIAdvisor() {
  const [recommendations, setRecommendations] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [userPreferences, setUserPreferences] = useState(null)
  const [showLoginModal, setShowLoginModal] = useState(false)

  const handleGetRecommendations = async (preferences: any) => {
    const token = localStorage.getItem("access_token")
    if (!token) {
      setShowLoginModal(true)
      return
    }

    setIsLoading(true)
    setUserPreferences(preferences)

    try {
      const response = await fetch(`${API_BASE_URL}/api/ai/recommend-nse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(preferences),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData?.error || `Request failed with status ${response.status}`)
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
    <>
    <div className="container mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        {/* Header */}
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
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <span className="text-blue-600 font-bold">1</span>
                  </div>
                  <h4 className="font-semibold mb-2">Analyze Preferences</h4>
                  <p className="text-sm text-gray-600">
                    Our AI processes your risk tolerance, timeline, and financial goals for Indian markets
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <span className="text-blue-600 font-bold">2</span>
                  </div>
                  <h4 className="font-semibold mb-2">NSE Market Analysis</h4>
                  <p className="text-sm text-gray-600">
                    Advanced algorithms analyze NSE stocks, sectoral trends, and Indian economic indicators
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <span className="text-blue-600 font-bold">3</span>
                  </div>
                  <h4 className="font-semibold mb-2">Indian Portfolio</h4>
                  <p className="text-sm text-gray-600">
                    Get a custom NSE portfolio with detailed reasoning for each Indian stock recommendation
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>

      {/* Login Modal */}
      <AnimatePresence>
        {showLoginModal && (
          <>
            {/* Backdrop + centering container */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center px-4"
              onClick={() => setShowLoginModal(false)}
            >
            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="w-full max-w-md z-50"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="bg-white rounded-2xl shadow-xl p-8 relative">
                {/* Close button */}
                <button
                  onClick={() => setShowLoginModal(false)}
                  className="absolute top-4 right-4 p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>

                {/* Icon */}
                <div className="flex items-center justify-center mb-4">
                  <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center">
                    <LogIn className="w-7 h-7 text-blue-500" />
                  </div>
                </div>

                {/* Content */}
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Sign in to continue</h3>
                  <p className="text-gray-500 text-sm">
                    You need to be logged in to get AI-powered portfolio recommendations. Create a free account or sign
                    in to get started.
                  </p>
                </div>

                {/* Buttons */}
                <div className="flex flex-col gap-3">
                  <Link
                    href="/login"
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 text-center"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/signup"
                    className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors duration-200 text-center"
                  >
                    Create an account
                  </Link>
                </div>
              </div>
            </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}