"use client"

import type React from "react"
import { useState } from "react"
import Button from "./Button"
import { DollarSign, Calendar, Target, TrendingUp } from "lucide-react"

interface AIAdvisorFormProps {
  onSubmit: (preferences: any) => void
  isLoading: boolean
}

export default function AIAdvisorForm({ onSubmit, isLoading }: AIAdvisorFormProps) {
  const [preferences, setPreferences] = useState({
    investmentAmount: "",
    riskTolerance: "moderate",
    investmentHorizon: "5-10",
    primaryGoal: "growth",
    age: "",
    currentIncome: "",
    hasEmergencyFund: "yes",
    investmentExperience: "intermediate",
    sectors: [] as string[],
    esgPreference: "neutral",
    rebalanceFrequency: "quarterly",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(preferences)
  }

  const handleSectorChange = (sector: string) => {
    setPreferences((prev) => ({
      ...prev,
      sectors: prev.sectors.includes(sector) ? prev.sectors.filter((s) => s !== sector) : [...prev.sectors, sector],
    }))
  }

  // NSE/Indian market sectors
  const availableSectors = [
    "Banking",
    "Information Technology",
    "Oil & Gas",
    "FMCG",
    "Pharmaceuticals",
    "Automobiles",
    "Metals & Mining",
    "Telecommunications",
    "Power",
    "Real Estate",
    "Textiles",
    "Chemicals",
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Investment Amount in INR */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          <DollarSign className="w-4 h-4 mr-1" />
          Investment Amount (INR)
        </label>
        <select
          value={preferences.investmentAmount}
          onChange={(e) => setPreferences((prev) => ({ ...prev, investmentAmount: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="">Select amount range</option>
          <option value="50000-100000">₹50,000 - ₹1,00,000</option>
          <option value="100000-250000">₹1,00,000 - ₹2,50,000</option>
          <option value="250000-500000">₹2,50,000 - ₹5,00,000</option>
          <option value="500000-1000000">₹5,00,000 - ₹10,00,000</option>
          <option value="1000000-2500000">₹10,00,000 - ₹25,00,000</option>
          <option value="2500000+">₹25,00,000+</option>
        </select>
      </div>

      {/* Risk Tolerance */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          <TrendingUp className="w-4 h-4 mr-1" />
          Risk Tolerance
        </label>
        <div className="grid grid-cols-3 gap-2">
          {["conservative", "moderate", "aggressive"].map((risk) => (
            <button
              key={risk}
              type="button"
              onClick={() => setPreferences((prev) => ({ ...prev, riskTolerance: risk }))}
              className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                preferences.riskTolerance === risk
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
              }`}
            >
              {risk.charAt(0).toUpperCase() + risk.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Investment Horizon */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          <Calendar className="w-4 h-4 mr-1" />
          Investment Timeline
        </label>
        <select
          value={preferences.investmentHorizon}
          onChange={(e) => setPreferences((prev) => ({ ...prev, investmentHorizon: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="1-2">1-2 years</option>
          <option value="3-5">3-5 years</option>
          <option value="5-10">5-10 years</option>
          <option value="10-20">10-20 years</option>
          <option value="20+">20+ years</option>
        </select>
      </div>

      {/* Primary Goal */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          <Target className="w-4 h-4 mr-1" />
          Primary Investment Goal
        </label>
        <select
          value={preferences.primaryGoal}
          onChange={(e) => setPreferences((prev) => ({ ...prev, primaryGoal: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="growth">Capital Growth</option>
          <option value="income">Regular Income/Dividends</option>
          <option value="balanced">Balanced Growth & Income</option>
          <option value="preservation">Capital Preservation</option>
          <option value="retirement">Retirement Planning</option>
          <option value="tax-saving">Tax Saving (ELSS)</option>
        </select>
      </div>

      {/* Age */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
        <select
          value={preferences.age}
          onChange={(e) => setPreferences((prev) => ({ ...prev, age: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="">Select age range</option>
          <option value="18-25">18-25</option>
          <option value="26-35">26-35</option>
          <option value="36-45">36-45</option>
          <option value="46-55">46-55</option>
          <option value="56-65">56-65</option>
          <option value="65+">65+</option>
        </select>
      </div>

      {/* Annual Income */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Annual Income (INR)</label>
        <select
          value={preferences.currentIncome}
          onChange={(e) => setPreferences((prev) => ({ ...prev, currentIncome: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select income range</option>
          <option value="300000-500000">₹3,00,000 - ₹5,00,000</option>
          <option value="500000-1000000">₹5,00,000 - ₹10,00,000</option>
          <option value="1000000-1500000">₹10,00,000 - ₹15,00,000</option>
          <option value="1500000-2500000">₹15,00,000 - ₹25,00,000</option>
          <option value="2500000+">₹25,00,000+</option>
        </select>
      </div>

      {/* Investment Experience */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Investment Experience</label>
        <select
          value={preferences.investmentExperience}
          onChange={(e) => setPreferences((prev) => ({ ...prev, investmentExperience: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="beginner">Beginner (0-2 years)</option>
          <option value="intermediate">Intermediate (2-5 years)</option>
          <option value="advanced">Advanced (5+ years)</option>
          <option value="expert">Expert (10+ years)</option>
        </select>
      </div>

      {/* NSE Sector Preferences */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Preferred NSE Sectors (Optional)</label>
        <div className="grid grid-cols-2 gap-2">
          {availableSectors.map((sector) => (
            <button
              key={sector}
              type="button"
              onClick={() => handleSectorChange(sector)}
              className={`p-2 rounded-lg border text-xs font-medium transition-colors ${
                preferences.sectors.includes(sector)
                  ? "bg-blue-100 text-blue-700 border-blue-300"
                  : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
              }`}
            >
              {sector}
            </button>
          ))}
        </div>
      </div>

      {/* ESG Preference */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          ESG (Environmental, Social, Governance) Preference
        </label>
        <select
          value={preferences.esgPreference}
          onChange={(e) => setPreferences((prev) => ({ ...prev, esgPreference: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="neutral">No preference</option>
          <option value="prefer">Prefer ESG-focused companies</option>
          <option value="require">Only ESG-compliant companies</option>
          <option value="avoid">Focus on returns over ESG</option>
        </select>
      </div>

      <Button
        text={isLoading ? "AI is analyzing NSE data..." : "Get AI Recommendations"}
        onClick={() => {}}
        className="w-full btn-primary py-4 text-lg"
        disabled={isLoading || !preferences.investmentAmount || !preferences.age}
      />

      <p className="text-xs text-gray-500 text-center">
        {/* TODO: This will call your Flask backend AI endpoint: /api/ai/recommend-nse */}
        Our AI will analyze your preferences and NSE market data to create a personalized Indian stock portfolio
      </p>
    </form>
  )
}
