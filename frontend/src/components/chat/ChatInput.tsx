'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Mic, Camera, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { AudioRecorder } from './AudioRecorder'
import { DocumentUpload, CameraCapture } from './ImageUpload'
import { cn, cleanMessageForDisplay } from '@/lib/utils'
import toast from 'react-hot-toast'

interface ChatInputProps {
  onSendMessage: (message: string, options?: {
    imageData?: string
    audioBlob?: Blob
    audioUrl?: string
    audioDuration?: number
  }) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

type InputMode = 'text' | 'audio' | 'image'

export function ChatInput({ 
  onSendMessage, 
  disabled = false, 
  placeholder = 'Ask about farming, weather, market prices, or government schemes...',
  className 
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [inputMode, setInputMode] = useState<InputMode>('text')
  const [selectedImage, setSelectedImage] = useState<{
    file: File
    preview: string
    base64: string
  } | null>(null)
  const [isMounted, setIsMounted] = useState(false)
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Handle client-side mounting to prevent hydration issues
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [message])

  // Focus textarea when switching to text mode
  useEffect(() => {
    if (inputMode === 'text' && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [inputMode])

  const handleSendText = () => {
    console.log('Send button clicked!', { message, selectedImage })
    const trimmedMessage = message.trim()
    if (!trimmedMessage && !selectedImage) {
      console.log('No message or image to send')
      return
    }

    // Create appropriate default message based on document type
    let defaultMessage = 'Please analyze this document.'
    if (selectedImage?.file.type === 'application/pdf') {
      defaultMessage = 'Please analyze this PDF document and provide insights based on its content.'
    } else if (selectedImage?.file.type.startsWith('image/')) {
      defaultMessage = 'Please analyze this image and provide agricultural insights.'
    }

    const finalMessage = trimmedMessage || defaultMessage
    console.log('Sending message:', finalMessage)
    console.log('Document type:', selectedImage?.file.type)
    
    onSendMessage(finalMessage, {
      imageData: selectedImage?.base64
    })

    // Reset state
    setMessage('')
    setSelectedImage(null)
    setInputMode('text')
  }

  const handleSendAudio = (audioBlob: Blob, audioUrl: string, duration: number, transcript?: string) => {
    // Send the transcript as the main message, with audio as metadata
    const messageContent = transcript && transcript.trim() 
      ? transcript.trim() 
      : 'Voice message (transcription unavailable)'

    console.log('Sending audio message:', { 
      messageContent, 
      hasTranscript: !!transcript, 
      hasImage: !!selectedImage,
      selectedImage: selectedImage?.file?.name 
    })

    // Include document data if a document is selected (image or PDF)
    onSendMessage(messageContent, {
      audioBlob,
      audioUrl,
      audioDuration: duration,
      imageData: selectedImage?.base64 // Include document data if available
    })

    // Reset state after sending
    setSelectedImage(null)
    setInputMode('text')
  }
  const handleImageSelect = (file: File, preview: string, base64: string) => {
    setSelectedImage({ file, preview, base64 })
    setInputMode('text') // Switch back to text mode to allow adding a message
  }
  
  const handleDocumentSelect = (file: File, preview: string, base64: string) => {
    setSelectedImage({ file, preview, base64 })
    setInputMode('text') // Switch back to text mode to allow adding a message
  }

  const handleImageRemove = () => {
    if (selectedImage) {
      URL.revokeObjectURL(selectedImage.preview)
      setSelectedImage(null)
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!disabled) {
        handleSendText()
      }
    }
  }

  const switchToMode = (mode: InputMode) => {
    if (disabled) return
    setInputMode(mode)
  }

  const canSend = (message.trim() || selectedImage) && !disabled

  return (
    <div className={cn('bg-white border-t border-gray-200 p-4', className)}>
      {/* Image Preview */}
      {selectedImage && (
        <div className="mb-3 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-start space-x-3">
            <img
              src={selectedImage.preview}
              alt={selectedImage.file.name}
              className="w-16 h-16 object-cover rounded-lg"
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {selectedImage.file.name}
              </p>
              <p className="text-xs text-gray-500">
                Image selected - add a message or send as is
              </p>
            </div>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleImageRemove}
              className="w-6 h-6 text-gray-400 hover:text-gray-600"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-end space-x-2">
        {/* Input Area */}
        <div className="flex-1">
          {inputMode === 'text' ? (
            <div className="relative">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                disabled={disabled}
                rows={1}
                className="w-full resize-none rounded-lg border border-gray-300 px-4 py-3 pr-12 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-gray-50 disabled:text-gray-500 min-h-[50px] max-h-32"
              />
            </div>
          ) : inputMode === 'audio' ? (
            <div className="space-y-3">
              {/* Show image preview if one is selected */}
              {selectedImage && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <img
                      src={selectedImage.preview}
                      alt={selectedImage.file.name}
                      className="w-12 h-12 object-cover rounded-lg"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-900">
                        Image selected for multimodal message
                      </p>
                      <p className="text-xs text-blue-700">
                        Your voice transcript will be sent with this image
                      </p>
                    </div>
                  </div>
                </div>
              )}
              <div className="flex items-center justify-center py-4 bg-gray-50 rounded-lg">
               <AudioRecorder
                  onRecordingComplete={handleSendAudio}
                  onRecordingCancel={() => setInputMode('text')}
                />
              </div>
            </div>
          ) : (
                          <div className="py-2">
                <DocumentUpload
                  onDocumentSelect={handleDocumentSelect}
                  onDocumentRemove={handleImageRemove}
                />
              </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-1">
          {inputMode === 'text' && (
            <>
              {/* Attachment Menu */}
              <div className="flex space-x-1">
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => switchToMode('image')}
                  disabled={disabled}
                  title="Upload image"
                  className="text-gray-500 hover:text-gray-700"
                >
                  <Paperclip className="w-4 h-4" />
                </Button>
                
                {/* Camera (mobile) - only render on client side */}
                {isMounted && typeof window !== 'undefined' && 'mediaDevices' in navigator && (
                  <CameraCapture 
                    onImageCapture={handleImageSelect}
                    className="inline-block"
                  />
                )}
                
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => switchToMode('audio')}
                  disabled={disabled}
                  title="Record voice message"
                  className="text-gray-500 hover:text-gray-700"
                >
                  <Mic className="w-4 h-4" />
                </Button>
              </div>

              {/* Send Button */}
              <Button
                onClick={handleSendText}
                disabled={!canSend}
                size="icon"
                className={cn(
                  'ml-2 transition-all',
                  canSend
                    ? 'bg-primary-600 hover:bg-primary-700 text-white'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                )}
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </Button>
            </>
          )}

          {inputMode !== 'text' && (
            <Button
              variant="outline"
              onClick={() => setInputMode('text')}
              disabled={disabled}
              title="Cancel"
            >
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Input Mode Indicator */}
      {inputMode !== 'text' && (
        <div className="mt-2 text-center">
          <span className="text-xs text-gray-500">
            {inputMode === 'audio' 
              ? selectedImage 
                ? '🎤📷 Multimodal input mode (Voice + Image)' 
                : '🎤 Voice input mode'
              : '📷 Image input mode'
            }
          </span>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            console.log('Market Prices clicked')
            setMessage('What are the current onion prices in Mumbai?')
          }}
          disabled={disabled}
          className="text-xs"
        >
          Market Prices
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            console.log('Weather Forecast clicked')
            setMessage('What is the weather forecast for farming in Punjab?')
          }}
          disabled={disabled}
          className="text-xs"
        >
          Weather Forecast
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            console.log('Gov Schemes clicked')
            setMessage('What government schemes are available for organic farming?')
          }}
          disabled={disabled}
          className="text-xs"
        >
          Gov Schemes
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            console.log('Crop Planning clicked')
            setMessage('Best crops to plant this season in my area?')
          }}
          disabled={disabled}
          className="text-xs"
        >
          Crop Planning
        </Button>
      </div>
    </div>
  )
}
