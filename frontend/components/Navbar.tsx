"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Menu, X, TrendingUp, LogOut, AlertCircle } from "lucide-react"
import { motion } from "framer-motion"

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authError, setAuthError] = useState("")

  // Check authentication status on component mount
  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token")
      if (!token) {
        throw new Error("Not authenticated. Please log in.")
      }
      setIsAuthenticated(true)
      setAuthError("")
    } catch (error) {
      console.error("Authentication error:", error)
      setIsAuthenticated(false)
      // Only show error if user was previously authenticated or trying to access protected content
      const currentPath = window.location.pathname
      const protectedPaths = ["/dashboard", "/ai-advisor"]
      if (protectedPaths.includes(currentPath)) {
        setAuthError("Not authenticated. Please log in.")
      }
    }
  }, [])

  const handleSignOut = () => {
    try {
      // Clear authentication data
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      localStorage.removeItem("user_email")
      setIsAuthenticated(false)
      setAuthError("")
      setIsOpen(false)
      // Redirect to home page
      window.location.href = "/"
    } catch (error) {
      console.error("Sign out error:", error)
      setAuthError("Error signing out. Please try again.")
    }
  }

  const dismissError = () => {
    setAuthError("")
  }

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/ai-advisor", label: "AI Advisor" },
    { href: "/about", label: "About" },
  ]

  return (
    <>
      {/* Error Banner */}
      {authError && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          className="bg-red-50 border-b border-red-200 px-4 py-3"
        >
          <div className="container mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-800 text-sm font-medium">{authError}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Link href="/login" className="text-red-600 hover:text-red-800 text-sm font-medium underline">
                Login
              </Link>
              <button onClick={dismissError} className="text-red-500 hover:text-red-700 p-1" aria-label="Dismiss error">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}

      <nav className="bg-white shadow-sm border-b border-gray-100">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-2">
              <TrendingUp className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-bold text-gray-900">InvestIQ</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-gray-600 hover:text-blue-500 font-medium transition-colors duration-200"
                >
                  {link.label}
                </Link>
              ))}

              {/* Authentication Section */}
              <div className="flex items-center space-x-4">
                {isAuthenticated ? (
                  <button
                    onClick={handleSignOut}
                    className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                ) : (
                  <>
                    <Link
                      href="/login"
                      className="text-gray-600 hover:text-blue-500 font-medium transition-colors duration-200"
                    >
                      Login
                    </Link>
                    <Link
                      href="/signup"
                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
                    >
                      Sign Up
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Mobile menu button */}
            <button onClick={() => setIsOpen(!isOpen)} className="md:hidden p-2 rounded-lg hover:bg-gray-100">
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="md:hidden py-4 border-t border-gray-100"
            >
              <div className="flex flex-col space-y-4">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="text-gray-600 hover:text-blue-500 font-medium transition-colors duration-200"
                    onClick={() => setIsOpen(false)}
                  >
                    {link.label}
                  </Link>
                ))}

                {/* Mobile Authentication Section */}
                <div className="flex flex-col space-y-2 pt-4 border-t border-gray-100">
                  {isAuthenticated ? (
                    <button
                      onClick={handleSignOut}
                      className="flex items-center space-x-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 text-left"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  ) : (
                    <>
                      <Link
                        href="/login"
                        className="text-gray-600 hover:text-blue-500 font-medium transition-colors duration-200"
                        onClick={() => setIsOpen(false)}
                      >
                        Login
                      </Link>
                      <Link
                        href="/signup"
                        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 text-center"
                        onClick={() => setIsOpen(false)}
                      >
                        Sign Up
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </nav>
    </>
  )
}
