'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Mic, Square, Play, Pause, Trash2, MessageSquare, Send } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn, formatDuration } from '@/lib/utils'
import { SpeechToTextService, STTResult } from '@/services/speechToText'
import toast from 'react-hot-toast'

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob, audioUrl: string, duration: number, transcript?: string) => void
  onRecordingCancel?: () => void
  className?: string
}

export function AudioRecorder({ 
  onRecordingComplete, 
  onRecordingCancel, 
  className
}: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [hasRecording, setHasRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [transcript, setTranscript] = useState('')
  const [realtimeTranscript, setRealtimeTranscript] = useState('')
  const [detectedLanguage, setDetectedLanguage] = useState<string>('')
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const sttServiceRef = useRef<SpeechToTextService | null>(null)

  useEffect(() => {
    sttServiceRef.current = new SpeechToTextService()
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
      if (sttServiceRef.current) {
        sttServiceRef.current.stopListening()
      }
    }
  }, [audioUrl])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 48000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      })

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

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' })
        const audioUrl = URL.createObjectURL(audioBlob)
        
        setAudioBlob(audioBlob)
        setAudioUrl(audioUrl)
        setHasRecording(true)
        
        // Stop realtime transcription
        if (sttServiceRef.current) {
          sttServiceRef.current.stopListening()
        }

        // Auto-transcribe with better accuracy
        await transcribeAudio(audioBlob)
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      setTranscript('')
      setRealtimeTranscript('')
      setDetectedLanguage('')

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

      // Start real-time transcription with auto-detection
      if (sttServiceRef.current?.isSupported()) {
        startRealtimeTranscription()
      }

      toast.success('🎤 Recording started (Auto-detecting language)')
    } catch (error) {
      console.error('Error accessing microphone:', error)
      toast.error('Could not access microphone. Please check permissions.')
    }
  }

  const startRealtimeTranscription = async () => {
    if (!sttServiceRef.current) return

    try {
      await sttServiceRef.current.transcribeRealtime(
        {
          continuous: true,
          interimResults: true
        },
        (result: STTResult) => {
          if (result.language && result.language !== 'unknown') {
            setDetectedLanguage(result.language)
          }
          
          if (result.isFinal) {
            setTranscript(prev => prev + ' ' + result.transcript)
            setRealtimeTranscript('')
          } else {
            setRealtimeTranscript(result.transcript)
          }
        },
        (error: string) => {
          console.warn('Realtime STT error:', error)
        }
      )
    } catch (error) {
      console.warn('Realtime transcription not available:', error)
    }
  }

  const transcribeAudio = async (audioBlob: Blob) => {
    if (!sttServiceRef.current) return

    setIsTranscribing(true)
    try {
      let finalTranscript = transcript.trim()
      let language = detectedLanguage
      
      if (!finalTranscript) {
        // Use cloud transcription for better accuracy
        const result = await sttServiceRef.current.transcribeAudio(audioBlob)
        finalTranscript = result.transcript
        language = result.language
      }
      
      setTranscript(finalTranscript)
      setDetectedLanguage(language)
      
      if (finalTranscript) {
        toast.success(`✅ Transcribed in ${language || 'auto-detected language'}`)
      }
    } catch (error) {
      console.error('Transcription error:', error)
      toast.error('Failed to transcribe audio. You can still send the voice message.')
    } finally {
      setIsTranscribing(false)
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

      if (sttServiceRef.current) {
        sttServiceRef.current.stopListening()
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
    setTranscript('')
    setRealtimeTranscript('')
    setDetectedLanguage('')
    
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    onRecordingCancel?.()
    toast.success('Recording discarded')
  }

  const sendRecording = () => {
    if (audioBlob && audioUrl) {
      onRecordingComplete(audioBlob, audioUrl, recordingTime, transcript)
      // Reset state
      setHasRecording(false)
      setAudioBlob(null)
      setRecordingTime(0)
      setTranscript('')
      setRealtimeTranscript('')
      setDetectedLanguage('')
    }
  }

  const currentTranscript = transcript + (realtimeTranscript ? ' ' + realtimeTranscript : '')

  return (
    <div className={cn('flex flex-col gap-3 p-4 bg-white rounded-lg border', className)}>
      {!hasRecording ? (
        <>
          {!isRecording ? (
            <Button
              onClick={startRecording}
              className="flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white"
              disabled={isTranscribing}
            >
              <Mic className="h-4 w-4" />
              Start Recording
            </Button>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                  <span className="text-sm font-medium">
                    Recording...
                    {detectedLanguage && (
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                        {detectedLanguage}
                      </span>
                    )}
                  </span>
                  <span className="text-sm text-gray-500">
                    {formatDuration(recordingTime)}
                  </span>
                </div>
                <div className="ml-6">{/* Add margin-left for spacing */}
                  <Button
                    onClick={stopRecording}
                    size="sm"
                    className="bg-green-500 hover:bg-green-600 text-white"
                  >
                    <Square className="h-4 w-4" />
                    Stop
                  </Button>
                </div>
              </div>

              {/* Real-time transcript display */}
              {currentTranscript && (
                <div className="p-3 bg-gray-50 rounded-md border-l-4 border-blue-400">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium text-blue-700">Live Transcript:</span>
                    {detectedLanguage && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                        {detectedLanguage}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700">
                    {transcript}
                    {realtimeTranscript && (
                      <span className="text-gray-400 italic"> {realtimeTranscript}</span>
                    )}
                  </p>
                </div>
              )}
            </>
          )}
        </>
      ) : (
        <div className="space-y-3">
          {/* Playback controls */}
          <div className="flex items-center gap-2">
            <Button onClick={playRecording} size="sm" variant="outline">
              {isPlaying ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>
            
            {/* Audio visualization */}
            <div className="flex items-center gap-1 flex-1">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    'w-1 bg-gray-300 rounded-full transition-all',
                    isPlaying ? 'h-6 bg-blue-500 animate-pulse' : 'h-2'
                  )}
                />
              ))}
            </div>
            
            <span className="text-sm text-gray-500 min-w-fit">
              {formatDuration(recordingTime)}
            </span>

            {/* Language indicator */}
            {detectedLanguage && (
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                {detectedLanguage}
              </span>
            )}
          </div>

          {/* Transcript display and editing */}
          {(transcript || isTranscribing) && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium text-green-700">
                  Transcript:
                </span>
                {detectedLanguage && (
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                    {detectedLanguage}
                  </span>
                )}
                {isTranscribing && (
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" />
                    <span className="text-xs text-gray-500">Transcribing...</span>
                  </div>
                )}
              </div>
              
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Transcript will appear here... You can edit it if needed."
                className="w-full p-3 border rounded-md text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                disabled={isTranscribing}
              />
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2">
            <Button onClick={discardRecording} variant="outline" size="sm">
              <Trash2 className="h-4 w-4 mr-1" />
              Discard
            </Button>
            
            <Button 
              onClick={sendRecording} 
              className="flex-1 bg-green-500 hover:bg-green-600 text-white"
              disabled={isTranscribing}
            >
              <Send className="h-4 w-4 mr-1" />
              Send {transcript ? 'with Transcript' : 'Voice Message'}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
