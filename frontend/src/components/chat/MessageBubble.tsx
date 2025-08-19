'use client'

import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Message } from '@/types/chat'
import { formatTimestamp, cn } from '@/lib/utils'
import { User, Bot, Play, Pause, Image as ImageIcon, Volume2, VolumeX } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface MessageBubbleProps {
  message: Message
  onImageClick?: (imageUrl: string) => void
  onPlayAudio?: (audioUrl: string) => void
}

export function MessageBubble({ message, onImageClick, onPlayAudio }: MessageBubbleProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null)
  const [isSpeaking, setIsSpeaking] = useState(false)

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
      if (isSpeaking) {
        // Stop speaking if already speaking
        window.speechSynthesis.cancel()
        setIsSpeaking(false)
        return
      }

      // Clean the text for speech - remove markdown formatting
      const cleanText = message.content
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
        .replace(/#{1,6}\s+/g, '') // Remove heading markers
        .replace(/```[\s\S]*?```/g, 'code block') // Replace code blocks
        .replace(/`([^`]+)`/g, '$1') // Remove inline code backticks
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links, keep text
        .replace(/\n\s*\n/g, '. ') // Replace double line breaks with periods
        .replace(/\n/g, ' ') // Replace single line breaks with spaces
        .replace(/[•·]/g, 'bullet point:') // Replace bullet points
        .replace(/^\s*[\-\*\+]\s+/gm, 'bullet point: ') // Replace list markers
        .replace(/^\s*\d+\.\s+/gm, 'number: ') // Replace numbered list markers
        .trim()
      
      const utterance = new SpeechSynthesisUtterance(cleanText)
      utterance.lang = 'en-IN' // Indian English
      utterance.rate = 0.85 // Slightly slower for clarity
      utterance.pitch = 1.0
      utterance.volume = 0.9
      
      // Try to find a good voice
      const voices = window.speechSynthesis.getVoices()
      let selectedVoice = null
      
      // Prefer female Indian English voices
      selectedVoice = voices.find(voice => 
        voice.lang.includes('en-IN') && voice.name.toLowerCase().includes('female')
      ) || voices.find(voice => 
        voice.lang.includes('en-IN')
      ) || voices.find(voice => 
        voice.lang.includes('en-GB') && voice.name.toLowerCase().includes('female')
      ) || voices.find(voice => 
        voice.lang.includes('en-US') && voice.name.toLowerCase().includes('female')
      )
      
      if (selectedVoice) {
        utterance.voice = selectedVoice
      }

      utterance.onstart = () => {
        setIsSpeaking(true)
      }
      
      utterance.onend = () => {
        setIsSpeaking(false)
      }
      
      utterance.onerror = () => {
        setIsSpeaking(false)
      }
      
      window.speechSynthesis.speak(utterance)
    }
  }

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
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
              {isUser ? (
                <p className="whitespace-pre-wrap leading-relaxed">
                  {message.content}
                </p>
              ) : (
                <ReactMarkdown 
                  className="markdown-content"
                  components={{
                    // Customize markdown rendering
                    h1: ({node, ...props}) => <h1 className="text-lg font-bold mb-2" {...props} />,
                    h2: ({node, ...props}) => <h2 className="text-base font-semibold mb-2" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-sm font-medium mb-1" {...props} />,
                    p: ({node, ...props}) => <p className="mb-2 leading-relaxed" {...props} />,
                    ul: ({node, ...props}) => <ul className="list-disc ml-4 mb-2" {...props} />,
                    ol: ({node, ...props}) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                    li: ({node, ...props}) => <li className="mb-1" {...props} />,
                    strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
                    em: ({node, ...props}) => <em className="italic" {...props} />,
                    code: ({node, ...props}) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs" {...props} />,
                    blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-green-500 pl-3 italic text-gray-700" {...props} />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
            </div>

            {/* Agent Response Actions */}
            {!isUser && message.content && (
              <div className="flex items-center justify-end mt-3 pt-2 border-t border-gray-100">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={isSpeaking ? stopSpeaking : speakText}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  {isSpeaking ? <VolumeX className="w-3 h-3 mr-1" /> : <Volume2 className="w-3 h-3 mr-1" />}
                  {isSpeaking ? "Stop" : "Speak"}
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
