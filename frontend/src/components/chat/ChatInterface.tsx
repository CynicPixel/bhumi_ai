'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Message, ChatState } from '@/types/chat'
import { MessageBubble } from './MessageBubble'
import { ChatInput } from './ChatInput'
import { TypingIndicator } from '@/components/ui/LoadingSpinner'
import { orchestratorClient } from '@/lib/orchestrator'
import { generateId, generateUUID, extractUserIdFromMessage, cleanMessageForDisplay, getErrorMessage } from '@/lib/utils'
import { AlertCircle, Wifi, WifiOff, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import toast from 'react-hot-toast'

interface ChatInterfaceProps {
  userId?: string
  className?: string
}

export function ChatInterface({ userId = 'farmer_001', className }: ChatInterfaceProps) {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    isRecording: false,
    contextId: undefined,
    currentTaskId: undefined,
  })
  
  const [isConnected, setIsConnected] = useState(true)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatState.messages])

  // Check connection health on mount
  useEffect(() => {
    checkConnection()
  }, [])

  const checkConnection = async () => {
    try {
      console.log('🔍 ChatInterface: Checking connection to orchestrator...')
      const isHealthy = await orchestratorClient.checkHealth()
      console.log('🔍 ChatInterface: Health check result:', isHealthy)
      setIsConnected(isHealthy)
      setConnectionError(isHealthy ? null : 'Unable to connect to agricultural intelligence backend')
      
      if (isHealthy) {
        console.log('✅ ChatInterface: Connected to orchestrator successfully')
      } else {
        console.log('❌ ChatInterface: Failed to connect to orchestrator')
      }
    } catch (error) {
      console.error('❌ ChatInterface: Connection check error:', error)
      setIsConnected(false)
      setConnectionError(getErrorMessage(error))
    }
  }

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: generateId(),
      timestamp: new Date(),
    }

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }))

    return newMessage
  }

  const updateLastMessage = (updates: Partial<Message>) => {
    setChatState(prev => {
      const messages = [...prev.messages]
      const lastIndex = messages.length - 1
      if (lastIndex >= 0) {
        messages[lastIndex] = { ...messages[lastIndex], ...updates }
      }
      return { ...prev, messages }
    })
  }

  const handleSendMessage = async (
    content: string,
    options: {
      imageData?: string
      audioBlob?: Blob
      audioUrl?: string
      audioDuration?: number
    } = {}
  ) => {
    console.log('ChatInterface handleSendMessage called:', { content, options })
    if (!content.trim() && !options.imageData && !options.audioBlob) {
      console.log('No content to send')
      return
    }

    // Check connection before sending
    if (!isConnected) {
      toast.error('Not connected to backend. Please check connection.')
      return
    }

    // Add user message
    const messageType = options.audioBlob ? 'audio' : options.imageData ? 'image' : 'text'
    
    const userMessage = addMessage({
      role: 'user',
      content: cleanMessageForDisplay(content),
      type: messageType,
      metadata: {
        imageUrl: options.imageData ? options.imageData : undefined,
        audioUrl: options.audioUrl,
        audioLength: options.audioDuration,
        contextId: chatState.contextId,
      }
    })

    // Set loading state
    setChatState(prev => ({ ...prev, isLoading: true }))

    // Add typing indicator
    const typingMessage = addMessage({
      role: 'agent',
      content: '',
      type: 'text',
    })

    try {
      // Send message to orchestrator
      console.log('📤 Sending message to orchestrator:', content)
      const response = await orchestratorClient.sendMessage(content, {
        userId,
        imageData: options.imageData,
        contextId: chatState.contextId,
      })

      console.log('📥 Received response:', response)

      // Update context ID from response
      const newContextId = response.result.contextId
      if (newContextId !== chatState.contextId) {
        setChatState(prev => ({ ...prev, contextId: newContextId }))
      }

      // Extract the final response from the correct location
      const finalMessage = response.result.status?.message
      let responseContent = 'No response received from agricultural intelligence system.'
      
      if (finalMessage?.parts && finalMessage.parts.length > 0) {
        // Handle the new response format with parts array
        const textPart = finalMessage.parts.find((part: any) => part.kind === 'text' || part.type === 'text')
        if (textPart) {
          responseContent = textPart.text || responseContent
        }
      } else if (finalMessage?.parts?.[0]?.text) {
        // Fallback for older format
        responseContent = finalMessage.parts[0].text
      }

      console.log('📝 Final response content:', responseContent)

      // Update the typing message with actual response
      updateLastMessage({
        content: responseContent,
        metadata: {
          contextId: newContextId,
          taskId: response.result.id,
          messageId: finalMessage?.messageId,
        }
      })

      // Update task ID
      setChatState(prev => ({ 
        ...prev, 
        currentTaskId: response.result.id,
        contextId: newContextId 
      }))

      setConnectionError(null)
      setIsConnected(true)

    } catch (error) {
      console.error('Error sending message:', error)
      
      const errorMessage = getErrorMessage(error)
      
      // Update the typing message with error
      updateLastMessage({
        content: `❌ Sorry, I encountered an error: ${errorMessage}. Please try again or check your connection to the agricultural intelligence backend.`,
      })

      // Update connection state
      if (errorMessage.includes('fetch') || errorMessage.includes('network') || errorMessage.includes('connection')) {
        setIsConnected(false)
        setConnectionError(errorMessage)
      }

      toast.error('Failed to send message')
    } finally {
      setChatState(prev => ({ ...prev, isLoading: false }))
    }
  }

  const handleRetry = () => {
    checkConnection()
  }

  const clearChat = () => {
    setChatState({
      messages: [],
      isLoading: false,
      isRecording: false,
      contextId: undefined,
      currentTaskId: undefined,
    })
    toast.success('Chat cleared')
  }

  const handleImageClick = (imageUrl: string) => {
    // Open image in new tab/window
    window.open(imageUrl, '_blank')
  }

  const renderWelcomeMessage = () => (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
        <span className="text-2xl">🌾</span>
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Welcome to Bhumi AI
      </h2>
      <p className="text-gray-600 mb-6 max-w-md">
        Your intelligent agricultural assistant powered by specialized AI agents. 
        Get real-time insights on weather, market prices, and government schemes.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
        <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors">
          <div className="text-lg mb-2">📊 Market Intelligence</div>
          <p className="text-sm text-gray-600">
            Get current commodity prices, market trends, and trading insights across India
          </p>
        </div>
        
        <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors">
          <div className="text-lg mb-2">🌤️ Weather Insights</div>
          <p className="text-sm text-gray-600">
            Access detailed weather forecasts, farming conditions, and agricultural planning
          </p>
        </div>
        
        <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors">
          <div className="text-lg mb-2">📋 Government Schemes</div>
          <p className="text-sm text-gray-600">
            Discover agricultural subsidies, schemes, and support programs available to you
          </p>
        </div>
        
        <div className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors">
          <div className="text-lg mb-2">🎤 Multimodal Support</div>
          <p className="text-sm text-gray-600">
            Communicate via text, voice messages, or upload images for analysis
          </p>
        </div>
      </div>
    </div>
  )

  return (
    <div className={`flex flex-col h-full bg-gray-50 ${className}`}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg">🌾</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                Bhumi AI Assistant
              </h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-gray-500">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {!isConnected && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleRetry}
                title="Retry connection"
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Retry
              </Button>
            )}
            
            <Button
              size="sm"
              variant="ghost"
              onClick={clearChat}
              title="Clear chat"
            >
              Clear
            </Button>
          </div>
        </div>
        
        {connectionError && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
            <span className="text-sm text-red-700">{connectionError}</span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto custom-scrollbar px-4 py-4"
      >
        {chatState.messages.length === 0 ? (
          renderWelcomeMessage()
        ) : (
          <>
            {chatState.messages.map((message, index) => (
              <MessageBubble
                key={message.id}
                message={message}
                onImageClick={handleImageClick}
              />
            ))}
            
            {chatState.isLoading && (
              <div className="flex justify-start mb-4">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm"> </span>
                  </div>
                  <TypingIndicator />
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={chatState.isLoading || !isConnected}
        placeholder={
          !isConnected 
            ? 'Please check connection to continue...'
            : 'Ask about farming, weather, market prices, or government schemes...'
        }
      />
    </div>
  )
}
