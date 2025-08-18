'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Square, Play, Pause, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn, formatDuration } from '@/lib/utils'
import toast from 'react-hot-toast'

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob, audioUrl: string, duration: number) => void
  onRecordingCancel?: () => void
  className?: string
}

export function AudioRecorder({ onRecordingComplete, onRecordingCancel, className }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [hasRecording, setHasRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' })
        const audioUrl = URL.createObjectURL(audioBlob)
        
        setAudioBlob(audioBlob)
        setAudioUrl(audioUrl)
        setHasRecording(true)
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
      toast.success('Recording started')
    } catch (error) {
      console.error('Error accessing microphone:', error)
      toast.error('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      
      toast.success('Recording stopped')
    }
  }

  const playRecording = () => {
    if (audioUrl) {
      if (isPlaying && audioRef.current) {
        audioRef.current.pause()
        setIsPlaying(false)
        return
      }
      
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      
      audio.addEventListener('ended', () => {
        setIsPlaying(false)
        audioRef.current = null
      })
      
      audio.addEventListener('error', () => {
        setIsPlaying(false)
        audioRef.current = null
        toast.error('Error playing audio')
      })
      
      audio.play()
      setIsPlaying(true)
    }
  }

  const discardRecording = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
    }
    
    setAudioUrl(null)
    setAudioBlob(null)
    setHasRecording(false)
    setIsPlaying(false)
    setRecordingTime(0)
    
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    
    onRecordingCancel?.()
    toast.success('Recording discarded')
  }

  const sendRecording = () => {
    if (audioBlob && audioUrl) {
      onRecordingComplete(audioBlob, audioUrl, recordingTime)
      
      // Reset state
      setHasRecording(false)
      setAudioBlob(null)
      setRecordingTime(0)
      // Keep audioUrl for playback in chat
    }
  }

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      {!hasRecording ? (
        <>
          {!isRecording ? (
            <Button
              size="icon"
              onClick={startRecording}
              className="bg-red-500 hover:bg-red-600 text-white"
              title="Start recording"
            >
              <Mic className="w-4 h-4" />
            </Button>
          ) : (
            <>
              <div className="flex items-center space-x-2">
                <Button
                  size="icon"
                  onClick={stopRecording}
                  className="bg-red-500 hover:bg-red-600 text-white recording-animation"
                  title="Stop recording"
                >
                  <Square className="w-4 h-4" />
                </Button>
                
                <div className="flex items-center space-x-2 text-red-600">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  <span className="text-sm font-mono">
                    {formatDuration(recordingTime)}
                  </span>
                </div>
              </div>
            </>
          )}
        </>
      ) : (
        <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
          <Button
            size="icon"
            variant="ghost"
            onClick={playRecording}
            title={isPlaying ? 'Pause' : 'Play recording'}
          >
            {isPlaying ? (
              <Pause className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </Button>
          
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    'w-1 bg-primary-400 rounded-full',
                    isPlaying ? 'audio-wave' : 'h-2'
                  )}
                  style={{
                    animationDelay: `${i * 0.1}s`,
                    height: isPlaying ? undefined : '8px'
                  }}
                />
              ))}
            </div>
            
            <span className="text-sm text-gray-600">
              {formatDuration(recordingTime)}
            </span>
          </div>
          
          <div className="flex space-x-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={discardRecording}
              title="Discard recording"
              className="text-red-500 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="w-3 h-3" />
            </Button>
            
            <Button
              size="sm"
              onClick={sendRecording}
              title="Send recording"
              className="bg-primary-600 hover:bg-primary-700"
            >
              Send
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
