"use client"

import { motion } from "framer-motion"
import { TrendingUp, Users, Award, Shield } from "lucide-react"

export default function About() {
  return (
    <div className="container mx-auto px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-4xl mx-auto"
      >
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">About InvestIQ</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Empowering Indian investors with AI-driven insights and intelligent NSE portfolio recommendations.
          </p>
        </div>

        <div className="card mb-8">
          <h2 className="text-2xl font-semibold mb-4">Our Mission</h2>
          <p className="text-gray-600 leading-relaxed">
            InvestIQ democratizes sophisticated investment strategies for Indian investors by leveraging artificial
            intelligence to provide retail investors with institutional-grade portfolio recommendations and NSE market
            analysis. Our platform combines advanced machine learning algorithms with real-time NSE data to deliver
            personalized investment recommendations that adapt to your risk tolerance and financial goals in the Indian
            stock market.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="card">
            <div className="flex items-center mb-4">
              <TrendingUp className="w-8 h-8 text-blue-500 mr-3" />
              <h3 className="text-xl font-semibold">NSE Market Analytics</h3>
            </div>
            <p className="text-gray-600">
              Our AI models analyze thousands of NSE market indicators, Indian economic data points, and historical
              patterns to identify optimal investment opportunities in Indian stocks and predict market movements.
            </p>
          </div>

          <div className="card">
            <div className="flex items-center mb-4">
              <Shield className="w-8 h-8 text-green-500 mr-3" />
              <h3 className="text-xl font-semibold">Risk Management</h3>
            </div>
            <p className="text-gray-600">
              Built-in risk assessment tools continuously monitor your NSE portfolio's exposure and provide real-time
              alerts to help you make informed decisions about your Indian stock investments.
            </p>
          </div>

          <div className="card">
            <div className="flex items-center mb-4">
              <Users className="w-8 h-8 text-purple-500 mr-3" />
              <h3 className="text-xl font-semibold">India-Focused Approach</h3>
            </div>
            <p className="text-gray-600">
              Every recommendation is tailored to Indian market conditions, your unique financial situation, investment
              timeline, and risk preferences, ensuring strategies that align with your personal goals and Indian market
              dynamics.
            </p>
          </div>

          <div className="card">
            <div className="flex items-center mb-4">
              <Award className="w-8 h-8 text-orange-500 mr-3" />
              <h3 className="text-xl font-semibold">NSE-Proven Results</h3>
            </div>
            <p className="text-gray-600">
              Our AI algorithms are trained on historical NSE market data and continuously refined to deliver
              consistent, risk-adjusted returns for Indian investors.
            </p>
          </div>
        </div>

        <div className="card text-center">
          <h2 className="text-2xl font-semibold mb-4">Ready to Invest in NSE?</h2>
          <p className="text-gray-600 mb-6">
            Join thousands of Indian investors who are already using InvestIQ to get AI-powered NSE portfolio
            recommendations and achieve their financial goals in the Indian stock market.
          </p>
          <div className="flex justify-center gap-4">
            <a href="/signup" className="btn-primary">
              Start Free Trial
            </a>
            <a href="/ai-advisor" className="btn-secondary">
              Get AI Recommendations
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
