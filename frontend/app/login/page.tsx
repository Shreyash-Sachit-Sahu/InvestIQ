"use client"

import type React from "react"
import { useState } from "react"
import { motion } from "framer-motion"
import Button from "@/components/Button"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);
  setErrorMessage("")

  try {
    const API_BASE_URL=process.env.NEXT_PUBLIC_API_BASE_URL || '';
    const response = await fetch('${API_BASE_URL}/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const message = data.error || `Login failed with status ${response.status}`;
      setErrorMessage(message); // or setError(message) for a more advanced UI
      setIsLoading(false);
      return;
    }

    const { access_token, refresh_token } = await response.json();

    // Store tokens (localStorage is common; adjust as needed)
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    // Redirect or update auth state in your app as needed
    router.push('/dashboard');
    alert('Login successful!');
  } catch (err: any) {
    console.error('Login error:', err);
    setErrorMessage(err.message || 'Login failed');
  } finally {
    setIsLoading(false);
  }
}

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-md w-full space-y-8"
      >
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Sign in to InvestIQ</h2>
          <p className="mt-2 text-gray-600">Access your investment dashboard</p>
        </div>

        <form className="card space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email address
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
            />
          </div>

          <Button
            text={isLoading ? "Signing in..." : "Sign in"}
            onClick={() => {}}
            className="w-full btn-primary"
            disabled={isLoading}
          />

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{" "}
              <Link href="/signup" className="text-blue-500 hover:text-blue-600 font-medium">
                Sign up
              </Link>
            </p>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
