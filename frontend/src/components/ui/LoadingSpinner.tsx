import React from 'react'
import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6', 
    lg: 'w-8 h-8'
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-gray-300 border-t-primary-600',
        sizeClasses[size],
        className
      )}
    />
  )
}

export function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1 p-3">
      <div className="text-sm text-gray-500 mr-2">AI is thinking</div>
      <div className="typing-indicator">
        <div className="typing-dot" style={{ '--delay': '0ms' } as React.CSSProperties} />
        <div className="typing-dot" style={{ '--delay': '150ms' } as React.CSSProperties} />
        <div className="typing-dot" style={{ '--delay': '300ms' } as React.CSSProperties} />
      </div>
    </div>
  )
}
