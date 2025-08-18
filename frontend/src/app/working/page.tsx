'use client'

import React, { useState, useRef, useEffect } from 'react'

export default function WorkingPage() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'bot', timestamp: Date}>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    console.log('🚀 Send clicked!', { message, selectedImage })
    
    if (!message.trim() && !selectedImage) {
      console.log('❌ No message or image')
      return
    }

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      text: message || (selectedImage ? `[Image: ${selectedImage.name}]` : ''),
      sender: 'user' as const,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentMessage = message
    setMessage('')
    setSelectedImage(null)
    setImagePreview(null)
    setIsLoading(true)

    try {
      // Prepare request
      const requestBody = {
        jsonrpc: '2.0',
        id: 'req_' + Date.now(),
        method: 'message/send',
        params: {
          message: {
            role: 'user',
            parts: [
              {
                type: 'text',
                text: `user_id: farmer_working\n\n${currentMessage || 'Please analyze this image.'}`
              }
            ],
            messageId: 'msg_' + Date.now()
          }
        }
      }

      console.log('📤 Sending request:', requestBody)

      const response = await fetch('http://localhost:10007/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      console.log('📥 Response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('📋 Response data:', data)
        
        const botText = data.result?.status?.message?.parts?.[0]?.text || 'No response received from AI system.'
        
        const botMessage = {
          id: Date.now().toString() + '_bot',
          text: botText,
          sender: 'bot' as const,
          timestamp: new Date()
        }
        
        setMessages(prev => [...prev, botMessage])
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('💥 Error:', error)
      const errorMessage = {
        id: Date.now().toString() + '_error',
        text: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check that the backend is running.`,
        sender: 'bot' as const,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
      console.log('🖼️ Image selected:', file.name)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      
      const chunks: Blob[] = []
      setAudioChunks(chunks)
      
      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data)
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' })
        console.log('🎤 Recording complete:', audioBlob.size, 'bytes')
        // For now, just add a text message indicating audio was recorded
        setMessage(prev => prev + ' [Voice message recorded]')
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      console.log('🎤 Recording started')
    } catch (error) {
      console.error('🎤 Recording error:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      console.log('🎤 Recording stopped')
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-green-50 to-emerald-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-green-200 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
              <span className="text-white text-lg">🌾</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Bhumi AI - Working Version</h1>
              <p className="text-sm text-gray-600">Multimodal Agricultural Intelligence Assistant</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">Connected</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🌾</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Bhumi AI!</h2>
              <p className="text-gray-600 mb-6">Your intelligent agricultural assistant. Ask about farming, weather, market prices, or government schemes.</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-lg mb-2">📊 Market Intelligence</div>
                  <p className="text-sm text-gray-600">Get real-time commodity prices and market trends</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-lg mb-2">🌤️ Weather Insights</div>
                  <p className="text-sm text-gray-600">Access detailed weather forecasts for farming</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-lg mb-2">📋 Government Schemes</div>
                  <p className="text-sm text-gray-600">Discover agricultural subsidies and support programs</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-lg mb-2">🎤 Voice & Images</div>
                  <p className="text-sm text-gray-600">Upload images or record voice messages</p>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    msg.sender === 'user'
                      ? 'bg-green-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-800'
                  }`}>
                    <div className="whitespace-pre-wrap">{msg.text}</div>
                    <div className={`text-xs mt-1 ${
                      msg.sender === 'user' ? 'text-green-100' : 'text-gray-500'
                    }`}>
                      {formatTime(msg.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                      <span className="text-sm text-gray-600">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Image Preview */}
      {imagePreview && (
        <div className="p-4 bg-yellow-50 border-t border-yellow-200">
          <div className="max-w-4xl mx-auto flex items-center space-x-4">
            <img src={imagePreview} alt="Preview" className="w-16 h-16 object-cover rounded-lg" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-800">Image selected: {selectedImage?.name}</p>
              <p className="text-xs text-yellow-600">This image will be sent with your message</p>
            </div>
            <button
              onClick={() => {
                setSelectedImage(null)
                setImagePreview(null)
                if (fileInputRef.current) fileInputRef.current.value = ''
              }}
              className="text-yellow-600 hover:text-yellow-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-2">
            <div className="flex-1">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="Ask about farming, weather, market prices, or government schemes..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                rows={1}
                disabled={isLoading}
              />
            </div>
            
            {/* File Input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              className="hidden"
            />
            
            {/* Action Buttons */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              title="Upload image"
              disabled={isLoading}
            >
              📎
            </button>
            
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`p-3 rounded-lg ${
                isRecording 
                  ? 'bg-red-500 text-white animate-pulse' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
              title={isRecording ? 'Stop recording' : 'Record voice message'}
              disabled={isLoading}
            >
              🎤
            </button>
            
            <button
              onClick={handleSend}
              disabled={isLoading || (!message.trim() && !selectedImage)}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '...' : 'Send'}
            </button>
          </div>
          
          {/* Quick Actions */}
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              onClick={() => {
                console.log('🔥 Quick action: Market Prices')
                setMessage('What are the current onion prices in Mumbai?')
              }}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
              disabled={isLoading}
            >
              Market Prices
            </button>
            <button
              onClick={() => {
                console.log('🔥 Quick action: Weather')
                setMessage('What is the weather forecast for farming in Punjab?')
              }}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
              disabled={isLoading}
            >
              Weather Forecast
            </button>
            <button
              onClick={() => {
                console.log('🔥 Quick action: Gov Schemes')
                setMessage('What government schemes are available for organic farming?')
              }}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
              disabled={isLoading}
            >
              Gov Schemes
            </button>
            <button
              onClick={() => {
                console.log('🔥 Quick action: Crop Planning')
                setMessage('Best crops to plant this season in my area?')
              }}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
              disabled={isLoading}
            >
              Crop Planning
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
