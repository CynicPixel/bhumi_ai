'use client'

import React, { useState, useEffect } from 'react'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { Button } from '@/components/ui/Button'
import { Settings, Info, Github, ExternalLink } from 'lucide-react'

export default function HomePage() {
  const [userId, setUserId] = useState('farmer_001')
  const [showSettings, setShowSettings] = useState(false)
  const [showInfo, setShowInfo] = useState(false)

  // Generate unique user ID on first load
  useEffect(() => {
    const savedUserId = localStorage.getItem('bhumi-ai-user-id')
    if (savedUserId) {
      setUserId(savedUserId)
    } else {
      const newUserId = `farmer_${Math.random().toString(36).substring(2, 8)}`
      setUserId(newUserId)
      localStorage.setItem('bhumi-ai-user-id', newUserId)
    }
  }, [])

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
      {/* Top Navigation */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-green-200/50 px-4 py-2">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">🌾</span>
            </div>
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Bhumi AI
              </h1>
              <p className="text-xs text-gray-500">Agricultural Intelligence Assistant</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowInfo(true)}
              title="About"
            >
              <Info className="w-4 h-4" />
            </Button>
            
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowSettings(true)}
              title="Settings"
            >
              <Settings className="w-4 h-4" />
            </Button>

            <a
              href="https://github.com/your-repo/bhumi-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
              title="View on GitHub"
            >
              <Github className="w-4 h-4" />
            </a>
          </div>
        </div>
      </nav>

      {/* Main Chat Interface */}
      <div className="flex-1 max-w-4xl mx-auto w-full">
        <div className="h-full bg-white/50 backdrop-blur-sm border-l border-r border-green-200/50">
          <ChatInterface userId={userId} />
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-lg font-semibold mb-4">Settings</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User ID
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => {
                    setUserId(e.target.value)
                    localStorage.setItem('bhumi-ai-user-id', e.target.value)
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Enter your farmer ID"
                />
                <p className="text-xs text-gray-500 mt-1">
                  This helps maintain conversation context across sessions
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Backend Status</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>Orchestrator:</span>
                    <span className="text-green-600">http://localhost:10007</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Market Agent:</span>
                    <span className="text-green-600">http://localhost:10006</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Weather Agent:</span>
                    <span className="text-green-600">http://localhost:10005</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Schemes Agent:</span>
                    <span className="text-green-600">http://localhost:10004</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <Button onClick={() => setShowSettings(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Info Modal */}
      {showInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <span className="mr-2">🌾</span>
              About Bhumi AI
            </h2>
            
            <div className="space-y-4 text-sm">
              <p>
                <strong>Bhumi AI</strong> is an advanced agricultural intelligence assistant 
                designed specifically for Indian farmers. It provides comprehensive support 
                through specialized AI agents.
              </p>

              <div>
                <h3 className="font-medium mb-2">🎯 Key Features</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li><strong>Market Intelligence:</strong> Real-time commodity prices and market trends</li>
                  <li><strong>Weather Insights:</strong> Agricultural weather forecasts and farming conditions</li>
                  <li><strong>Government Schemes:</strong> Agricultural subsidies and support programs</li>
                  <li><strong>Multimodal Input:</strong> Text, voice, and image-based queries</li>
                </ul>
              </div>

              <div>
                <h3 className="font-medium mb-2">🤖 AI Agents</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li><strong>Orchestrator:</strong> Intelligent routing and coordination</li>
                  <li><strong>Market Agent:</strong> CEDA API integration for price data</li>
                  <li><strong>Weather Agent:</strong> Open-Meteo API for weather insights</li>
                  <li><strong>Schemes Agent:</strong> RAG-powered government schemes database</li>
                </ul>
              </div>

              <div>
                <h3 className="font-medium mb-2">📱 How to Use</h3>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Type your questions about farming, weather, or markets</li>
                  <li>Use voice messages for hands-free interaction</li>
                  <li>Upload images of crops or fields for analysis</li>
                  <li>Try the quick action buttons for common queries</li>
                </ul>
              </div>

              <div className="bg-green-50 p-3 rounded-lg">
                <p className="text-green-800 text-xs">
                  <strong>Note:</strong> This is an MVP frontend for the Bhumi AI agricultural 
                  intelligence system. Ensure all backend agents are running for full functionality.
                </p>
              </div>
            </div>

            <div className="flex justify-between items-center mt-6">
              <a
                href="https://github.com/your-repo/bhumi-ai"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-green-600 hover:text-green-700 flex items-center"
              >
                <Github className="w-4 h-4 mr-1" />
                View on GitHub
                <ExternalLink className="w-3 h-3 ml-1" />
              </a>
              
              <Button onClick={() => setShowInfo(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm border-t border-green-200/50 px-4 py-2">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <div>
            Built for Indian farmers with ❤️ using AI agents
          </div>
          <div>
            User: {userId}
          </div>
        </div>
      </footer>
    </div>
  )
}
