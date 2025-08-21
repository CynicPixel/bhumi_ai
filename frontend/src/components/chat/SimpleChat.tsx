'use client'

import React, { useState } from 'react'
import { getOrchestratorUrl } from '../../lib/utils'

interface SimpleChatProps {
  userId?: string
}

export function SimpleChat({ userId = 'farmer_001' }: SimpleChatProps) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'bot'}>>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async () => {
    console.log('Send clicked!', message)
    
    if (!message.trim()) {
      alert('Please type a message')
      return
    }

    const userMessage = {
      id: Date.now().toString(),
      text: message,
      sender: 'user' as const
    }

    setMessages(prev => [...prev, userMessage])
    setMessage('')
    setIsLoading(true)

    try {
      // Test API call to orchestrator
  const response = await fetch(getOrchestratorUrl() + '/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 'test_' + Date.now(),
          method: 'message/send',
          params: {
            message: {
              role: 'user',
              parts: [
                {
                  type: 'text',
                  text: `user_id: ${userId}\n\n${message}`
                }
              ],
              messageId: 'msg_' + Date.now()
            }
          }
        })
      })

      if (response.ok) {
        const data = await response.json()
        const botResponse = data.result?.status?.message?.parts?.[0]?.text || 'No response received'
        
        const botMessage = {
          id: Date.now().toString() + '_bot',
          text: botResponse,
          sender: 'bot' as const
        }
        
        setMessages(prev => [...prev, botMessage])
      } else {
        throw new Error('Network response was not ok')
      }
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        id: Date.now().toString() + '_error',
        text: 'Sorry, there was an error connecting to the AI. Please try again.',
        sender: 'bot' as const
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto bg-white">
      {/* Header */}
      <div className="bg-green-600 text-white p-4">
        <h1 className="text-xl font-bold">🌾 Bhumi AI - Agricultural Assistant</h1>
        <p className="text-sm opacity-90">Ask about farming, weather, prices, or government schemes</p>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">👋 Welcome to Bhumi AI!</p>
            <p>Ask me anything about agriculture, weather, market prices, or government schemes.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`mb-4 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
              <div className={`inline-block p-3 rounded-lg max-w-xs lg:max-w-md ${
                msg.sender === 'user' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-white border border-gray-200'
              }`}>
                {msg.text}
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="text-left mb-4">
            <div className="inline-block p-3 rounded-lg bg-white border border-gray-200">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                <span className="text-sm text-gray-500 ml-2">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about farming, weather, market prices..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !message.trim()}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '...' : 'Send'}
          </button>
        </div>
        
        {/* Quick Actions */}
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={() => setMessage('What are onion prices in Mumbai?')}
            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
            disabled={isLoading}
          >
            Market Prices
          </button>
          <button
            onClick={() => setMessage('Weather forecast for farming in Punjab')}
            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
            disabled={isLoading}
          >
            Weather
          </button>
          <button
            onClick={() => setMessage('Government schemes for organic farming')}
            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
            disabled={isLoading}
          >
            Gov Schemes
          </button>
          <button
            onClick={() => setMessage('Best crops to plant this season')}
            className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full"
            disabled={isLoading}
          >
            Crop Planning
          </button>
        </div>
      </div>
    </div>
  )
}
