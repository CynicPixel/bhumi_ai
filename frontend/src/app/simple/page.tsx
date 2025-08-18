'use client'

import React from 'react'
import { SimpleChat } from '@/components/chat/SimpleChat'

export default function SimplePage() {
  return (
    <div className="h-screen bg-gray-100">
      <SimpleChat userId="farmer_simple" />
    </div>
  )
}
