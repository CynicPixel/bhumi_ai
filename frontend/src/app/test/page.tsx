'use client'

import React, { useState } from 'react'

export default function TestPage() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState('')

  const handleClick = () => {
    console.log('Button clicked!')
    setCount(prev => prev + 1)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('Input changed:', e.target.value)
    setMessage(e.target.value)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Form submitted:', message)
    alert(`You typed: ${message}`)
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-4">🧪 Interactive Test Page</h1>
        
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-2">Button Click Test:</p>
            <button 
              onClick={handleClick}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            >
              Click me! Count: {count}
            </button>
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-2">Input Test:</p>
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                value={message}
                onChange={handleInputChange}
                placeholder="Type something..."
                className="w-full border border-gray-300 rounded px-3 py-2 mb-2"
              />
              <button 
                type="submit"
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
              >
                Submit
              </button>
            </form>
          </div>

          <div>
            <p className="text-sm text-gray-600">Current message: {message}</p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded">
          <p className="text-xs text-gray-500">
            Open browser console (F12) to see event logs.
            If buttons don't work, there's a hydration issue.
          </p>
        </div>
      </div>
    </div>
  )
}
