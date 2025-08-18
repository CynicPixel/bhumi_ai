'use client'

import React, { useState } from 'react'
import { Message } from '@/types/chat'
import { formatTimestamp, cn } from '@/lib/utils'
import { User, Bot, Play, Pause, Image as ImageIcon, Volume2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface MessageBubbleProps {
  message: Message
  onImageClick?: (imageUrl: string) => void
  onPlayAudio?: (audioUrl: string) => void
}

export function MessageBubble({ message, onImageClick, onPlayAudio }: MessageBubbleProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null)

  const isUser = message.role === 'user'

  const handleAudioPlay = async () => {
    if (message.metadata?.audioUrl) {
      if (isPlayingAudio && currentAudio) {
        currentAudio.pause()
        setIsPlayingAudio(false)
        return
      }

      const audio = new Audio(message.metadata.audioUrl)
      setCurrentAudio(audio)
      
      audio.addEventListener('ended', () => {
        setIsPlayingAudio(false)
        setCurrentAudio(null)
      })

      audio.addEventListener('error', () => {
        setIsPlayingAudio(false)
        setCurrentAudio(null)
      })

      try {
        await audio.play()
        setIsPlayingAudio(true)
        onPlayAudio?.(message.metadata.audioUrl)
      } catch (error) {
        console.error('Error playing audio:', error)
        setIsPlayingAudio(false)
        setCurrentAudio(null)
      }
    }
  }

  const handleImageClick = () => {
    if (message.metadata?.imageUrl) {
      onImageClick?.(message.metadata.imageUrl)
    }
  }

  const speakText = () => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel()
      
      const utterance = new SpeechSynthesisUtterance(message.content)
      utterance.lang = 'en-IN' // Indian English
      utterance.rate = 0.9
      utterance.pitch = 1.0
      
      // Try to find an Indian English voice
      const voices = window.speechSynthesis.getVoices()
      const indianVoice = voices.find(voice => 
        voice.lang.includes('en-IN') || voice.name.includes('Indian')
      )
      
      if (indianVoice) {
        utterance.voice = indianVoice
      }
      
      window.speechSynthesis.speak(utterance)
    }
  }

  return (
    <div className={cn(
      'flex w-full mb-4 chat-message',
      isUser ? 'justify-end' : 'justify-start'
    )}>
      <div className={cn(
        'flex max-w-[80%] items-start space-x-3',
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
      )}>
        {/* Avatar */}
        <div className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary-600' : 'bg-emerald-600'
        )}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={cn(
          'flex flex-col space-y-2',
          isUser ? 'items-end' : 'items-start'
        )}>
          {/* Message Bubble */}
          <div className={cn(
            'px-4 py-3 rounded-2xl shadow-sm',
            isUser 
              ? 'bg-primary-600 text-white rounded-tr-md' 
              : 'bg-white text-gray-800 rounded-tl-md border border-gray-200'
          )}>
            {/* Image Content */}
            {message.type === 'image' && message.metadata?.imageUrl && (
              <div className="mb-3">
                <div 
                  className="relative cursor-pointer group rounded-lg overflow-hidden"
                  onClick={handleImageClick}
                >
                  <img 
                    src={message.metadata.imageUrl} 
                    alt={message.metadata.imageName || 'Uploaded image'}
                    className="max-w-full h-auto max-h-64 object-cover transition-transform group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all flex items-center justify-center">
                    <ImageIcon className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
                {message.metadata.imageName && (
                  <p className="text-sm mt-2 opacity-75">
                    📷 {message.metadata.imageName}
                  </p>
                )}
              </div>
            )}

            {/* Audio Content */}
            {message.type === 'audio' && message.metadata?.audioUrl && (
              <div className="mb-3 flex items-center space-x-3 p-3 bg-gray-100 rounded-lg">
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleAudioPlay}
                  className="w-10 h-10"
                >
                  {isPlayingAudio ? (
                    <Pause className="w-4 h-4" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                </Button>
                <div className="flex-1">
                  <div className="text-sm font-medium">Voice Message</div>
                  {message.metadata.audioLength && (
                    <div className="text-xs text-gray-500">
                      {Math.round(message.metadata.audioLength)}s
                    </div>
                  )}
                </div>
                <div className="flex space-x-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        'w-1 bg-primary-400 rounded-full audio-wave',
                        isPlayingAudio ? 'animate-wave' : 'h-2'
                      )}
                      style={{
                        animationDelay: `${i * 0.1}s`,
                        height: isPlayingAudio ? undefined : '8px'
                      }}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Text Content */}
            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap leading-relaxed">
                {message.content}
              </p>
            </div>

            {/* Agent Response Actions */}
            {!isUser && message.content && (
              <div className="flex items-center justify-end mt-3 pt-2 border-t border-gray-100">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={speakText}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  <Volume2 className="w-3 h-3 mr-1" />
                  Speak
                </Button>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className={cn(
            'text-xs text-gray-500 px-1',
            isUser ? 'text-right' : 'text-left'
          )}>
            {formatTimestamp(message.timestamp)}
          </div>
        </div>
      </div>
    </div>
  )
}
