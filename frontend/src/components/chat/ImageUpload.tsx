'use client'

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Upload, X, Image as ImageIcon, Camera } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn, isImageFile, isPDFFile, isDocumentFile, formatFileSize, blobToBase64, createPDFPreview } from '@/lib/utils'
import toast from 'react-hot-toast'

interface DocumentUploadProps {
  onDocumentSelect: (file: File, preview: string, base64: string) => void
  onDocumentRemove?: () => void
  className?: string
  maxSize?: number // in bytes
  acceptedTypes?: string[]
}

export function DocumentUpload({ 
  onDocumentSelect, 
  onDocumentRemove, 
  className,
  maxSize = 10 * 1024 * 1024, // 10MB default for PDFs
  acceptedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'application/pdf']
}: DocumentUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<{
    file: File
    preview: string
    base64: string
  } | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const processFile = useCallback(async (file: File) => {
    // Validate file type
    if (!isDocumentFile(file)) {
      toast.error('Please select a valid image or PDF file')
      return
    }

    if (!acceptedTypes.includes(file.type)) {
      toast.error(`File type ${file.type} is not supported`)
      return
    }

    // Validate file size
    if (file.size > maxSize) {
      toast.error(`File size must be less than ${formatFileSize(maxSize)}`)
      return
    }

    try {
      let preview: string
      
      if (isPDFFile(file)) {
        // Create PDF preview
        preview = await createPDFPreview(file)
        toast.success(`PDF selected: ${file.name}`)
      } else {
        // Create image preview
        preview = URL.createObjectURL(file)
        toast.success(`Image selected: ${file.name}`)
      }
      
      // Convert to base64
      const base64 = await blobToBase64(file)
      
      const documentData = { file, preview, base64 }
      setSelectedDocument(documentData)
      onDocumentSelect(file, preview, base64)
      
    } catch (error) {
      console.error('Error processing document:', error)
      toast.error('Error processing document')
    }
  }, [acceptedTypes, maxSize, onDocumentSelect])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      processFile(file)
    }
  }

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setDragOver(false)
    
    const files = event.dataTransfer.files
    if (files.length > 0) {
      processFile(files[0])
    }
  }, [processFile])

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setDragOver(false)
  }, [])

  const handleRemoveDocument = () => {
    if (selectedDocument) {
      // Only revoke URL if it's an image (not PDF preview)
      if (!isPDFFile(selectedDocument.file)) {
        URL.revokeObjectURL(selectedDocument.preview)
      }
      setSelectedDocument(null)
      onDocumentRemove?.()
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
      toast.success('Document removed')
    }
  }

  const openFileDialog = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className={cn('relative', className)}>
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes.join(',')}
        onChange={handleFileSelect}
        className="hidden"
        aria-label="Select image file"
      />

      {!selectedDocument ? (
        <div
          className={cn(
            'document-upload-zone border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer transition-all',
            dragOver && 'dragover',
            'hover:border-primary-400 hover:bg-primary-50'
          )}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={openFileDialog}
        >
          <div className="flex flex-col items-center space-y-3">
            <div className={cn(
              'w-12 h-12 rounded-full flex items-center justify-center',
              dragOver ? 'bg-primary-100' : 'bg-gray-100'
            )}>
              {dragOver ? (
                <Upload className="w-6 h-6 text-primary-600" />
              ) : (
                <ImageIcon className="w-6 h-6 text-gray-400" />
              )}
            </div>
            
            <div>
              <p className="text-sm font-medium text-gray-900">
                {dragOver ? 'Drop document here' : 'Upload an image or PDF'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Drag & drop or click to browse
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Images (PNG, JPG, WebP) or PDFs up to {formatFileSize(maxSize)}
              </p>
              <p className="text-xs text-blue-600 mt-1 font-medium">
                📄 PDFs will be analyzed for text content
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="relative">
            {isPDFFile(selectedDocument.file) ? (
              <div className="w-full h-40 bg-gray-50 flex items-center justify-center">
                <img
                  src={selectedDocument.preview}
                  alt={selectedDocument.file.name}
                  className="w-full h-full object-contain"
                />
              </div>
            ) : (
              <img
                src={selectedDocument.preview}
                alt={selectedDocument.file.name}
                className="w-full h-40 object-cover"
              />
            )}
            
            <Button
              size="icon"
              variant="destructive"
              onClick={handleRemoveDocument}
              className="absolute top-2 right-2 w-6 h-6"
              title="Remove document"
            >
              <X className="w-3 h-3" />
            </Button>
            
            {/* File type indicator */}
            <div className="absolute top-2 left-2">
              {isPDFFile(selectedDocument.file) ? (
                <span className="px-2 py-1 bg-red-500 text-white text-xs rounded-full font-medium">
                  PDF
                </span>
              ) : (
                <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded-full font-medium">
                  IMAGE
                </span>
              )}
            </div>
          </div>
          
          <div className="p-3">
            <p className="text-sm font-medium text-gray-900 truncate">
              {selectedDocument.file.name}
            </p>
            <p className="text-xs text-gray-500">
              {formatFileSize(selectedDocument.file.size)}
              {isPDFFile(selectedDocument.file) && (
                <span className="ml-2 text-red-600 font-medium">• PDF Document (Text will be extracted)</span>
              )}
            </p>
            {isPDFFile(selectedDocument.file) && (
              <p className="text-xs text-blue-600 mt-1">
                📄 This PDF will be analyzed for agricultural insights based on its text content
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Camera capture component (for mobile devices)
export function CameraCapture({ onImageCapture, className }: {
  onImageCapture: (file: File, preview: string, base64: string) => void
  className?: string
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isCapturing, setIsCapturing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isVideoReady, setIsVideoReady] = useState(false)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [cameraTimeout, setCameraTimeout] = useState<NodeJS.Timeout | null>(null)

  // Cleanup effect to stop camera stream when component unmounts
  useEffect(() => {
    return () => {
      if (stream) {
        console.log('🧹 Cleaning up camera stream on unmount')
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [stream])

  const startCamera = async () => {
    setIsLoading(true)
    try {
      console.log('🎥 Starting camera...')
      
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API not supported in this browser')
      }

      console.log('📱 Requesting camera access...')
      
      let mediaStream: MediaStream | null = null
      
      // Try back camera first, then fallback to any camera
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            facingMode: 'environment', // Use back camera if available
            width: { ideal: 1280 },
            height: { ideal: 720 }
          } 
        })
        console.log('✅ Got back camera')
      } catch (backCameraError) {
        console.log('⚠️ Back camera not available, trying any camera...')
        try {
          mediaStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
              width: { ideal: 1280 },
              height: { ideal: 720 }
            } 
          })
          console.log('✅ Got front/any camera')
        } catch (anyCameraError) {
          console.log('❌ No camera available')
          throw anyCameraError
        }
      }
      
      if (!mediaStream) {
        throw new Error('Could not get camera stream')
      }
      
      console.log('✅ Camera access granted, setting up stream...')
      setStream(mediaStream)
      setIsCapturing(true)
      setIsVideoReady(false)
      
      if (videoRef.current) {
        const video = videoRef.current
        
        console.log('🎬 Setting up video element...')
        
        // Remove any existing event listeners first
        video.removeEventListener('loadedmetadata', () => {})
        video.removeEventListener('canplay', () => {})
        video.removeEventListener('error', () => {})
        
        // Add event listeners for video
        const handleLoadedMetadata = () => {
          console.log('🎬 Video metadata loaded:', {
            videoWidth: video.videoWidth,
            videoHeight: video.videoHeight,
            readyState: video.readyState,
            currentSrc: video.currentSrc,
            srcObject: !!video.srcObject
          })
        }
        
        const handleCanPlay = () => {
          console.log('✅ Video can play - setting ready state')
          setIsVideoReady(true)
        }
        
        const handleError = (e: Event) => {
          console.error('❌ Video error:', e)
          const videoError = video.error
          if (videoError) {
            console.error('Video error details:', {
              code: videoError.code,
              message: videoError.message
            })
          }
          toast.error('Video playback error')
          setIsVideoReady(false)
        }
        
        const handleLoadStart = () => {
          console.log('🔄 Video load started')
        }
        
        const handleLoadedData = () => {
          console.log('📊 Video data loaded')
        }
        
        const handleCanPlayThrough = () => {
          console.log('🎯 Video can play through')
        }
        
        // Add all event listeners
        video.addEventListener('loadstart', handleLoadStart)
        video.addEventListener('loadedmetadata', handleLoadedMetadata)
        video.addEventListener('loadeddata', handleLoadedData)
        video.addEventListener('canplay', handleCanPlay)
        video.addEventListener('canplaythrough', handleCanPlayThrough)
        video.addEventListener('error', handleError)
        
        // Set the stream
        console.log('🎬 Setting video srcObject...')
        video.srcObject = mediaStream
        
        // Log stream details
        console.log('📡 Stream details:', {
          streamId: mediaStream.id,
          tracks: mediaStream.getTracks().map(track => ({
            kind: track.kind,
            enabled: track.enabled,
            readyState: track.readyState,
            muted: track.muted
          }))
        })
        
        // Force video element to load the stream
        video.load()
        
        // Log video element state after setting stream
        console.log('🎬 Video element state after setting stream:', {
          srcObject: !!video.srcObject,
          readyState: video.readyState,
          networkState: video.networkState,
          currentSrc: video.currentSrc
        })
        
        // Ensure video element is properly configured
        video.autoplay = true
        video.playsInline = true
        video.muted = true
        
        // Try to force the video to start
        const startVideo = async () => {
          try {
            console.log('🎬 Forcing video to start...')
            await video.play()
            console.log('✅ Video forced to start successfully')
          } catch (error) {
            console.error('❌ Could not force video to start:', error)
          }
        }
        
        // Try to start video after a short delay
        setTimeout(startVideo, 100)
        
        // Try to play immediately and also set up fallback checks
        const playVideo = async () => {
          try {
            console.log('🎬 Attempting to play video...')
            await video.play()
            console.log('✅ Video play() successful')
          } catch (error) {
            console.error('❌ Error playing video:', error)
            // Don't show error toast yet, try fallback
          }
        }
        
        // Try to play immediately
        playVideo()
        
        // Also try to manually trigger video events after a short delay
        setTimeout(() => {
          if (!isVideoReady && video.videoWidth > 0 && video.videoHeight > 0) {
            console.log('🚀 Manual trigger: Video has dimensions, forcing ready state')
            setIsVideoReady(true)
          }
        }, 300)
        
        // Set up multiple fallback checks
        const checkVideoReady = () => {
          console.log('🔍 Checking video readiness:', {
            videoWidth: video.videoWidth,
            videoHeight: video.videoHeight,
            readyState: video.readyState,
            paused: video.paused,
            ended: video.ended
          })
          
          if (video.videoWidth > 0 && video.videoHeight > 0 && video.readyState >= 2) {
            console.log('✅ Video appears ready, setting ready state')
            setIsVideoReady(true)
            return true
          }
          return false
        }
        
        // Check every 100ms for video readiness (very aggressive)
        const readyCheckInterval = setInterval(() => {
          if (checkVideoReady()) {
            clearInterval(readyCheckInterval)
          }
        }, 100)
        
        // Also check after 500ms as quick fallback
        setTimeout(() => {
          clearInterval(readyCheckInterval)
          if (!isVideoReady) {
            console.log('🔄 500ms fallback check')
            checkVideoReady()
          }
        }, 500)
        
        // Check after 1 second
        setTimeout(() => {
          if (!isVideoReady) {
            console.log('🔄 1-second fallback check')
            checkVideoReady()
          }
        }, 1000)
        
        // Final aggressive check after 1.5 seconds
        setTimeout(() => {
          if (!isVideoReady) {
            console.log('🔄 1.5-second aggressive check')
            // Force check and set ready if video has dimensions
            if (video.videoWidth > 0 && video.videoHeight > 0) {
              console.log('🚀 Force setting video ready (has dimensions)')
              setIsVideoReady(true)
            } else {
              // If still not ready, automatically try to recreate
              console.log('🔄 Auto-recreate: Video not ready after 1.5s, attempting recreate')
              forceRecreateVideo()
            }
          }
        }, 1500)
        
        // Ultra-aggressive check - monitor video element continuously
        const ultraAggressiveCheck = setInterval(() => {
          if (isVideoReady) {
            clearInterval(ultraAggressiveCheck)
            return
          }
          
          // Check if video is actually displaying content
          if (video.videoWidth > 0 && video.videoHeight > 0) {
            console.log('🚀 Ultra-aggressive: Video has dimensions, setting ready')
            setIsVideoReady(true)
            clearInterval(ultraAggressiveCheck)
          }
          
          // Also check if stream is actually connected
          if (video.srcObject && video.srcObject === mediaStream) {
            console.log('🔍 Ultra-aggressive: Stream is connected to video')
            // Force check dimensions again
            if (video.videoWidth > 0 && video.videoHeight > 0) {
              console.log('🚀 Ultra-aggressive: Stream connected and has dimensions')
              setIsVideoReady(true)
              clearInterval(ultraAggressiveCheck)
            }
          }
          
          // Check if video element is actually in DOM and visible
          if (video.offsetParent !== null && video.offsetWidth > 0 && video.offsetHeight > 0) {
            console.log('🔍 Ultra-aggressive: Video element is visible in DOM')
            // If video is visible but not ready, try to force it
            if (video.videoWidth === 0 && video.videoHeight === 0) {
              console.log('🔍 Ultra-aggressive: Video visible but no dimensions, trying to reconnect stream')
              // Try to reconnect the stream
              const currentStream = video.srcObject
              video.srcObject = null
              setTimeout(() => {
                video.srcObject = currentStream
                video.load()
              }, 50)
            }
          }
        }, 50) // Check every 50ms
        
        // Clean up ultra-aggressive check after 3 seconds
        setTimeout(() => {
          clearInterval(ultraAggressiveCheck)
          
          // Final fallback: if still not ready, try to completely recreate the video element
          if (!isVideoReady) {
            console.log('🔄 Final fallback: Attempting to recreate video element')
            try {
              // Remove current video element
              const currentVideo = videoRef.current
              if (currentVideo && currentVideo.parentNode) {
                currentVideo.parentNode.removeChild(currentVideo)
              }
              
              // Create new video element
              const newVideo = document.createElement('video')
              newVideo.autoplay = true
              newVideo.playsInline = true
              newVideo.muted = true
              newVideo.className = 'w-full rounded-lg mb-4 bg-gray-900'
              newVideo.style.aspectRatio = '4/3'
              
              // Add event listeners to new video
              newVideo.addEventListener('loadedmetadata', () => {
                console.log('✅ New video loaded metadata')
                if (newVideo.videoWidth > 0) {
                  setIsVideoReady(true)
                }
              })
              
              // Replace the video element
              if (videoRef.current && videoRef.current.parentNode) {
                const parentNode = videoRef.current.parentNode
                parentNode.insertBefore(newVideo, videoRef.current)
                parentNode.removeChild(videoRef.current)
                // Update the ref by creating a new ref object
                Object.defineProperty(videoRef, 'current', {
                  value: newVideo,
                  writable: true,
                  configurable: true
                })
                
                // Set the stream to new video
                newVideo.srcObject = mediaStream
                newVideo.load()
                newVideo.play().catch(console.error)
                
                console.log('🔄 Video element recreated and stream reconnected')
              }
            } catch (error) {
              console.error('❌ Error recreating video element:', error)
            }
          }
        }, 3000)
        
        // Auto-recreate after 2 seconds if still not ready
        setTimeout(() => {
          if (!isVideoReady) {
            console.log('🔄 Auto-recreate: Video not ready after 2s, attempting recreate')
            forceRecreateVideo()
          }
        }, 2000)
        
        // Set a timeout to prevent infinite loading
        const timeout = setTimeout(() => {
          if (!isVideoReady) {
            console.warn('⚠️ Camera timeout - video not ready after 5 seconds')
            toast.error('Camera took too long to start. Please try again.')
            stopCamera()
          }
        }, 5000) // 5 second timeout
        
        setCameraTimeout(timeout)
      }
    } catch (error: any) {
      console.error('❌ Error accessing camera:', error)
      
      let errorMessage = 'Could not access camera'
      
      if (error.name === 'NotAllowedError') {
        errorMessage = 'Camera access denied. Please allow camera permissions and try again.'
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'No camera found on this device.'
      } else if (error.name === 'NotSupportedError') {
        errorMessage = 'Camera not supported in this browser.'
      } else if (error.name === 'NotReadableError') {
        errorMessage = 'Camera is already in use by another application.'
      } else if (error.message) {
        errorMessage = error.message
      }
      
      toast.error(errorMessage)
      setIsCapturing(false)
    } finally {
      setIsLoading(false)
    }
  }
  
  // Add a function to force recreate the video element
  const forceRecreateVideo = () => {
    if (stream && videoRef.current) {
      console.log('🔄 Force recreate video requested')
      const video = videoRef.current
      
      // Remove and re-add the stream
      video.srcObject = null
      setTimeout(() => {
        video.srcObject = stream
        video.load()
        video.play().catch(console.error)
        
        // After recreating, check if video is ready
        setTimeout(() => {
          if (video.videoWidth > 0 && video.videoHeight > 0) {
            console.log('✅ Video recreated and ready')
            setIsVideoReady(true)
          }
        }, 500)
      }, 100)
      
      toast.success('Video element recreated')
    }
  }

  const stopCamera = () => {
    console.log('🛑 Stopping camera...')
    
    // Clear timeout
    if (cameraTimeout) {
      clearTimeout(cameraTimeout)
      setCameraTimeout(null)
    }
    
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    setIsCapturing(false)
    setIsVideoReady(false)
    
    // Clear video element
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  const capturePhoto = async () => {
    console.log('📸 Attempting to capture photo...', {
      videoReady: isVideoReady,
      hasVideo: !!videoRef.current,
      hasCanvas: !!canvasRef.current,
      hasStream: !!stream
    })
    
    if (!isVideoReady) {
      console.error('❌ Video not ready')
      toast.error('Please wait for the video to load before capturing.')
      return
    }
    
    if (!videoRef.current || !canvasRef.current) {
      console.error('❌ Video or canvas ref not available')
      toast.error('Camera not ready. Please try again.')
      return
    }

    const video = videoRef.current
    const canvas = canvasRef.current

    // Additional video checks
    if (video.readyState < 2) {
      console.error('❌ Video readyState insufficient:', video.readyState)
      toast.error('Video still loading. Please wait a moment.')
      return
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.error('❌ Video has no dimensions:', {
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        readyState: video.readyState
      })
      toast.error('Video not ready. Please wait and try again.')
      return
    }

    let context: CanvasRenderingContext2D | null = null
    try {
      context = canvas.getContext('2d')
      if (!context) {
        throw new Error('Could not get canvas 2D context')
      }
    } catch (error) {
      console.error('❌ Canvas context error:', error)
      toast.error('Canvas not supported. Please try a different browser.')
      return
    }

    try {
      console.log(`🎬 Capturing photo: ${video.videoWidth}x${video.videoHeight}`)
      
      // Set canvas dimensions
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      // Clear canvas first
      context.clearRect(0, 0, canvas.width, canvas.height)
      
      // Draw video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height)
      
      // Convert to blob
      canvas.toBlob(async (blob) => {
        try {
          if (!blob) {
            throw new Error('Failed to create blob from canvas')
          }
          
          console.log('✅ Photo captured successfully, blob size:', blob.size)
          
          const file = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' })
          const preview = URL.createObjectURL(blob)
          const base64 = await blobToBase64(blob)
          
          console.log('🎯 Calling onImageCapture with:', {
            fileName: file.name,
            fileSize: file.size,
            previewUrl: preview.substring(0, 50) + '...',
            base64Length: base64.length
          })
          
          onImageCapture(file, preview, base64)
          stopCamera()
          toast.success('Photo captured!')
        } catch (blobError) {
          console.error('❌ Error processing captured photo:', blobError)
          toast.error('Failed to process captured photo.')
        }
      }, 'image/jpeg', 0.9) // Higher quality
      
    } catch (error) {
      console.error('❌ Error during photo capture:', error)
      toast.error('Failed to capture photo. Please try again.')
    }
  }

  return (
    <div className={cn('relative', className)}>
      {!isCapturing ? (
        <Button
          size="icon"
          variant="outline"
          onClick={startCamera}
          disabled={isLoading}
          title={isLoading ? "Starting camera..." : "Take photo"}
        >
          {isLoading ? (
            <div className="w-4 h-4 animate-spin border-2 border-gray-300 border-t-gray-600 rounded-full" />
          ) : (
            <Camera className="w-4 h-4" />
          )}
        </Button>
      ) : (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-4 max-w-md w-full mx-4">
            <div className="text-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Camera</h3>
              <p className="text-sm text-gray-600">
                {isVideoReady 
                  ? "Position your image and click capture" 
                  : "Camera starting automatically... Please wait"
                }
              </p>
              {!isVideoReady && (
                <div className="mt-2 flex justify-center">
                  <div className="w-4 h-4 animate-spin border-2 border-blue-300 border-t-blue-600 rounded-full" />
                </div>
              )}
            </div>
            
            <div className="relative">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full rounded-lg mb-4 bg-gray-900"
                style={{ aspectRatio: '4/3' }}
                onLoadStart={() => console.log('🎬 Video onLoadStart')}
                onLoadedMetadata={() => {
                  console.log('🎬 Video onLoadedMetadata')
                  // Direct event handler - set ready immediately if we have dimensions
                  if (videoRef.current && videoRef.current.videoWidth > 0) {
                    console.log('✅ onLoadedMetadata: Video has dimensions, setting ready')
                    setIsVideoReady(true)
                  }
                }}
                onCanPlay={() => {
                  console.log('🎬 Video onCanPlay')
                  // Direct event handler - set ready immediately
                  console.log('✅ onCanPlay: Setting video ready')
                  setIsVideoReady(true)
                }}
                onCanPlayThrough={() => {
                  console.log('🎬 Video onCanPlayThrough')
                  // Direct event handler - set ready immediately
                  console.log('✅ onCanPlayThrough: Setting video ready')
                  setIsVideoReady(true)
                }}
                onLoadedData={() => {
                  console.log('🎬 Video onLoadedData')
                  // Direct event handler - set ready if we have dimensions
                  if (videoRef.current && videoRef.current.videoWidth > 0) {
                    console.log('✅ onLoadedData: Video has dimensions, setting ready')
                    setIsVideoReady(true)
                  }
                }}
                onPlaying={() => {
                  console.log('🎬 Video onPlaying')
                  // Direct event handler - set ready immediately
                  console.log('✅ onPlaying: Setting video ready')
                  setIsVideoReady(true)
                }}
                onError={(e) => console.error('🎬 Video onError:', e)}
              />
              
              {!isVideoReady && (
                <div className="absolute inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center rounded-lg">
                  <div className="text-white text-center">
                    <div className="w-8 h-8 animate-spin border-2 border-white border-t-transparent rounded-full mx-auto mb-2" />
                    <p className="text-sm">Loading camera...</p>
                    <p className="text-xs text-gray-300 mt-1">Camera light should be on</p>
                  </div>
                </div>
              )}
              
              {/* Simple status indicator */}
              <div className="absolute top-2 left-2 bg-black bg-opacity-50 text-white text-xs p-2 rounded">
                <div>Camera: {stream ? '✅ Active' : '❌ Inactive'}</div>
                <div>Status: {isVideoReady ? '✅ Ready' : '⏳ Loading...'}</div>
              </div>
            </div>
            
            <div className="flex justify-center space-x-4">
              <Button variant="outline" onClick={stopCamera}>
                Cancel
              </Button>
              
              {!isVideoReady && (
                <Button 
                  variant="outline"
                  onClick={() => {
                    console.log('🔄 Recreate video requested')
                    if (stream && videoRef.current) {
                      const video = videoRef.current
                      // Remove and re-add the stream
                      video.srcObject = null
                      setTimeout(() => {
                        video.srcObject = stream
                        video.play().catch(console.error)
                        
                        // After recreating, check if video is ready
                        setTimeout(() => {
                          if (video.videoWidth > 0 && video.videoHeight > 0) {
                            console.log('✅ Video recreated and ready')
                            setIsVideoReady(true)
                          }
                        }, 500)
                      }, 100)
                      toast.success('Video element recreated')
                    }
                  }}
                  className="text-purple-600 border-purple-600 hover:bg-purple-50"
                >
                  🔄 Recreate Camera
                </Button>
              )}
              
              <Button 
                onClick={capturePhoto}
                disabled={!isVideoReady}
                className={cn(
                  "text-white",
                  isVideoReady 
                    ? "bg-blue-600 hover:bg-blue-700" 
                    : "bg-gray-400 cursor-not-allowed"
                )}
              >
                📸 {isVideoReady ? 'Capture' : 'Wait...'}
              </Button>
            </div>
          </div>
        </div>
      )}
      
      <canvas ref={canvasRef} className="hidden" />
    </div>
  )
}
