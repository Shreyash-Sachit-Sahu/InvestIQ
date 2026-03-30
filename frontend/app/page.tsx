"use client"

import { motion } from "framer-motion"
import Button from "@/components/Button"
import { ArrowRight, TrendingUp, Shield, Zap } from "lucide-react"
import Link from "next/link"

export default function Home() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl mx-auto"
        >
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Invest Smarter with <span className="text-blue-500">InvestIQ</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Smarter investments powered by AI. Get data-driven insights and personalized NSE portfolio recommendations
            to maximize your returns in the Indian stock market.
          </p>
          <Link href="/ai-advisor">
            <Button
              text="Get AI Recommendations"
              onClick={() => {}}
              className="btn-primary text-lg px-8 py-4 inline-flex items-center gap-2"
            >
              Get AI Recommendations <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* How It Works Section */}
      <section className="container mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Our AI-powered platform analyzes NSE market data to provide you with intelligent investment recommendations
            tailored for Indian investors.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="card text-center"
          >
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="w-6 h-6 text-blue-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Analyze</h3>
            <p className="text-gray-600">
              Our AI analyzes thousands of NSE data points to identify market trends and opportunities in Indian stocks.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="card text-center"
          >
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Zap className="w-6 h-6 text-green-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Recommend</h3>
            <p className="text-gray-600">
              Get personalized NSE portfolio recommendations based on your risk tolerance and investment goals.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="card text-center"
          >
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Shield className="w-6 h-6 text-purple-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Monitor</h3>
            <p className="text-gray-600">
              Track your NSE investments with real-time risk assessment and performance monitoring.
            </p>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
