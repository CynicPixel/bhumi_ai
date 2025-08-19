'use client'

import React from 'react'
import { ChatInterface } from '@/components/chat/ChatInterface'

export default function FixedPage() {
  return (
    <div className="h-screen bg-gray-100">
      <div className="h-full max-w-4xl mx-auto">
        <ChatInterface userId="farmer_fixed" />
      </div>
    </div>
  )
}