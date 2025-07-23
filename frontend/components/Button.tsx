"use client"

import type { ReactNode } from "react"

interface ButtonProps {
  text?: string
  onClick: () => void
  className?: string
  disabled?: boolean
  children?: ReactNode
}

export default function Button({ text, onClick, className = "", disabled = false, children }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {children || text}
    </button>
  )
}
