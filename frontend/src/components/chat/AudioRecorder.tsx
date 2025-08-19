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
  const [finalTranscript, setFinalTranscript] = useState('') // New state for final transcript
  const [selectedLanguage, setSelectedLanguage] = useState<string>('bn-IN') // Language selection
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const sttServiceRef = useRef<SpeechToTextService | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const transcriptRef = useRef<string>('') // Add ref to preserve transcript
  const finalTranscriptRef = useRef<string>('') // Add ref to preserve final transcript
  const persistentTranscriptRef = useRef<string>('') // Persistent transcript storage
  const persistentFinalTranscriptRef = useRef<string>('') // Persistent final transcript storage

  // Helper function to get language name from code
  const getLanguageName = (code: string): string => {
    const languageMap: { [key: string]: string } = {
      'bn-IN': 'Bengali',
      'hi-IN': 'Hindi',
      'en-IN': 'English',
      'pa-IN': 'Punjabi',
      'te-IN': 'Telugu',
      'ta-IN': 'Tamil',
      'ml-IN': 'Malayalam',
      'gu-IN': 'Gujarati',
      'kn-IN': 'Kannada',
      'or-IN': 'Odia',
      'as-IN': 'Assamese'
    }
    return languageMap[code] || code
  }

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
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [audioUrl])

  // Preserve transcript state when component updates
  useEffect(() => {
    if (hasRecording && transcript && !finalTranscript) {
      setFinalTranscript(transcript)
      finalTranscriptRef.current = transcript
      console.log('🔄 Preserving transcript state:', transcript)
    }
  }, [hasRecording, transcript, finalTranscript])

  // Sync refs with state changes
  useEffect(() => {
    if (transcript) {
      transcriptRef.current = transcript
      console.log('📝 Syncing transcript ref:', transcript)
    }
  }, [transcript])

  useEffect(() => {
    if (finalTranscript) {
      finalTranscriptRef.current = finalTranscript
      console.log('💾 Syncing final transcript ref:', finalTranscript)
    }
  }, [finalTranscript])

  // Monitor transcript state changes
  useEffect(() => {
    console.log('👁️ Transcript state changed:', {
      transcript,
      finalTranscript,
      hasRecording,
      transcriptRef: transcriptRef.current,
      finalTranscriptRef: finalTranscriptRef.current
    })
  }, [transcript, finalTranscript, hasRecording])

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

      streamRef.current = stream
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
        
        console.log('🔴 MediaRecorder stopped, current transcript state:', {
          transcript: transcript.trim(),
          realtimeTranscript,
          detectedLanguage,
          transcriptRef: transcriptRef.current,
          finalTranscriptRef: finalTranscriptRef.current
        })
        
        // Stop realtime transcription
        if (sttServiceRef.current) {
          sttServiceRef.current.stopListening()
        }

        // Wait a bit for real-time transcription to finalize
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Get the final transcript from real-time results
        const finalRealtimeTranscript = transcript.trim()
        console.log('⏳ After waiting, final realtime transcript:', finalRealtimeTranscript)
        
        if (finalRealtimeTranscript) {
          setFinalTranscript(finalRealtimeTranscript)
          finalTranscriptRef.current = finalRealtimeTranscript
          persistentFinalTranscriptRef.current = finalRealtimeTranscript
          console.log('✅ Set final transcript from realtime:', finalRealtimeTranscript)
        }
        
        // If no real-time transcript, try cloud transcription
        if (!finalRealtimeTranscript) {
          console.log('⚠️ No realtime transcript, trying cloud transcription')
          await transcribeAudio(audioBlob)
        }
        
        // Stop all tracks to release microphone
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop())
          streamRef.current = null
        }
        
        console.log('🎯 Final transcript state after processing:', {
          transcript: transcript.trim(),
          finalTranscript: finalTranscript,
          transcriptRef: transcriptRef.current,
          finalTranscriptRef: finalTranscriptRef.current,
          hasRecording: true
        })
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      // Only clear transcript states after we confirm recording has started
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

      toast.success(`🎤 Recording started in ${getLanguageName(selectedLanguage)}`)
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
        selectedLanguage, // Pass the selected language
        (result: STTResult) => {
          console.log('Realtime STT result:', {
            transcript: result.transcript,
            isFinal: result.isFinal,
            language: result.language,
            confidence: result.confidence
          })
          
          if (result.language && result.language !== 'unknown') {
            setDetectedLanguage(result.language)
          }
          
          if (result.isFinal) {
            // Accumulate final transcripts
            setTranscript(prev => {
              const newTranscript = prev + (prev ? ' ' : '') + result.transcript
              transcriptRef.current = newTranscript // Store in ref
              persistentTranscriptRef.current = newTranscript // Store in persistent ref
              console.log('📝 Accumulating transcript:', { prev, new: result.transcript, combined: newTranscript })
              return newTranscript
            })
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
      // Use the accumulated real-time transcript if available
      let finalTranscriptResult = transcript.trim()
      let language = detectedLanguage
      
      if (!finalTranscriptResult) {
        // Use cloud transcription for better accuracy
        const result = await sttServiceRef.current.transcribeAudio(audioBlob)
        finalTranscriptResult = result.transcript
        language = result.language
      }
      
      // Update both transcript states
      setTranscript(finalTranscriptResult)
      setFinalTranscript(finalTranscriptResult)
      setDetectedLanguage(language)
      
      if (finalTranscriptResult) {
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
    setFinalTranscript('')
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
      // Use the final transcript if available, otherwise use the accumulated transcript
      let transcriptToSend = finalTranscript || transcript || persistentFinalTranscriptRef.current || persistentTranscriptRef.current
      
      // If we still don't have a transcript, try to get it from the STT service
      if (!transcriptToSend && sttServiceRef.current) {
        const serviceTranscript = sttServiceRef.current.getAccumulatedTranscript()
        if (serviceTranscript) {
          transcriptToSend = serviceTranscript
          console.log('📡 Using transcript from STT service:', transcriptToSend)
        }
      }
      
      // Final safeguard - if we still don't have a transcript, use a placeholder
      if (!transcriptToSend) {
        transcriptToSend = 'Voice message (transcription unavailable)'
        console.log('⚠️ No transcript available, using placeholder')
      }
      
      console.log('🚀 AudioRecorder - sendRecording called:', {
        hasFinalTranscript: !!finalTranscript,
        finalTranscriptLength: finalTranscript?.length || 0,
        hasTranscript: !!transcript,
        transcriptLength: transcript?.length || 0,
        transcriptToSend,
        transcriptToSendLength: transcriptToSend?.length || 0,
        audioBlobSize: audioBlob.size,
        recordingTime,
        refTranscript: transcriptRef.current,
        refFinalTranscript: finalTranscriptRef.current,
        persistentTranscript: persistentTranscriptRef.current,
        persistentFinalTranscript: persistentFinalTranscriptRef.current
      })
      
      onRecordingComplete(audioBlob, audioUrl, recordingTime, transcriptToSend)
      
      // Reset state
      setHasRecording(false)
      setAudioBlob(null)
      setRecordingTime(0)
      setTranscript('')
      setRealtimeTranscript('')
      setFinalTranscript('')
      setDetectedLanguage('')
      
      // Reset refs
      transcriptRef.current = ''
      finalTranscriptRef.current = ''
      persistentTranscriptRef.current = ''
      persistentFinalTranscriptRef.current = ''
    }
  }

  const currentTranscript = transcript + (realtimeTranscript ? ' ' + realtimeTranscript : '')

  return (
    <div className={cn('flex flex-col gap-3 p-4 bg-white rounded-lg border', className)}>
      {!hasRecording ? (
        <>
          {!isRecording ? (
            <>
              {/* Language Selection */}
              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Language:
                </label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isRecording}
                >
                  <option value="bn-IN">বাংলা (Bengali)</option>
                  <option value="hi-IN">हिंदी (Hindi)</option>
                  <option value="en-IN">English</option>
                  <option value="pa-IN">ਪੰਜਾਬੀ (Punjabi)</option>
                  <option value="te-IN">తెలుగు (Telugu)</option>
                  <option value="ta-IN">தமிழ் (Tamil)</option>
                  <option value="ml-IN">മലയാളം (Malayalam)</option>
                  <option value="gu-IN">ગુજરાતી (Gujarati)</option>
                  <option value="kn-IN">ಕನ್ನಡ (Kannada)</option>
                  <option value="or-IN">ଓଡ଼ିଆ (Odia)</option>
                  <option value="as-IN">অসমীয়া (Assamese)</option>
                </select>
              </div>
              
              <Button
                onClick={startRecording}
                className="flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white"
                disabled={isTranscribing}
              >
                <Mic className="h-4 w-4" />
                Start Recording
              </Button>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                  <span className="text-sm font-medium">
                    Recording...
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                      {getLanguageName(selectedLanguage)}
                    </span>
                    {detectedLanguage && detectedLanguage !== getLanguageName(selectedLanguage) && !detectedLanguage.includes('Unknown') && (
                      <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                        Detected: {detectedLanguage}
                      </span>
                    )}
                  </span>
                  <span className="text-sm text-gray-500">
                    {formatDuration(recordingTime)}
                  </span>
                </div>
                <div className="ml-6">
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
          {(transcript || finalTranscript || persistentTranscriptRef.current || persistentFinalTranscriptRef.current) && (
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
                {finalTranscript && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                    Final
                  </span>
                )}
                {(persistentTranscriptRef.current || persistentFinalTranscriptRef.current) && !finalTranscript && !transcript && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                    Restored
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
                value={finalTranscript || transcript || persistentFinalTranscriptRef.current || persistentTranscriptRef.current}
                onChange={(e) => {
                  const newValue = e.target.value
                  setTranscript(newValue)
                  setFinalTranscript(newValue)
                  transcriptRef.current = newValue
                  finalTranscriptRef.current = newValue
                  persistentTranscriptRef.current = newValue
                  persistentFinalTranscriptRef.current = newValue
                }}
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
            
            {/* Debug button - remove in production */}
            <Button 
              onClick={() => {
                console.log('Current transcript state:', {
                  transcript: transcript || 'None',
                  finalTranscript: finalTranscript || 'None',
                  realtimeTranscript: realtimeTranscript || 'None',
                  detectedLanguage: detectedLanguage || 'None',
                  hasRecording,
                  isTranscribing
                })
              }} 
              variant="outline" 
              size="sm"
              className="text-xs"
            >
              Debug
            </Button>
            
            <Button 
              onClick={sendRecording} 
              className="flex-1 bg-green-500 hover:bg-green-600 text-white"
              disabled={isTranscribing}
            >
              <Send className="h-4 w-4 mr-1" />
              Send {(finalTranscript || transcript) ? 'with Transcript' : 'Voice Message'}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
