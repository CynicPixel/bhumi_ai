'use client'

import React, { useState, useRef, useCallback } from 'react'
import { Upload, X, Image as ImageIcon, Camera } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn, isImageFile, formatFileSize, blobToBase64 } from '@/lib/utils'
import toast from 'react-hot-toast'

interface ImageUploadProps {
  onImageSelect: (file: File, preview: string, base64: string) => void
  onImageRemove?: () => void
  className?: string
  maxSize?: number // in bytes
  acceptedTypes?: string[]
}

export function ImageUpload({ 
  onImageSelect, 
  onImageRemove, 
  className,
  maxSize = 5 * 1024 * 1024, // 5MB default
  acceptedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
}: ImageUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [selectedImage, setSelectedImage] = useState<{
    file: File
    preview: string
    base64: string
  } | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const processFile = useCallback(async (file: File) => {
    // Validate file type
    if (!isImageFile(file)) {
      toast.error('Please select a valid image file')
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
      // Create preview URL
      const preview = URL.createObjectURL(file)
      
      // Convert to base64
      const base64 = await blobToBase64(file)
      
      const imageData = { file, preview, base64 }
      setSelectedImage(imageData)
      onImageSelect(file, preview, base64)
      
      toast.success(`Image selected: ${file.name}`)
    } catch (error) {
      console.error('Error processing image:', error)
      toast.error('Error processing image')
    }
  }, [acceptedTypes, maxSize, onImageSelect])

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

  const handleRemoveImage = () => {
    if (selectedImage) {
      URL.revokeObjectURL(selectedImage.preview)
      setSelectedImage(null)
      onImageRemove?.()
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
      toast.success('Image removed')
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

      {!selectedImage ? (
        <div
          className={cn(
            'image-upload-zone border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer transition-all',
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
                {dragOver ? 'Drop image here' : 'Upload an image'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Drag & drop or click to browse
              </p>
              <p className="text-xs text-gray-400 mt-1">
                PNG, JPG, WebP up to {formatFileSize(maxSize)}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="relative">
            <img
              src={selectedImage.preview}
              alt={selectedImage.file.name}
              className="w-full h-40 object-cover"
            />
            
            <Button
              size="icon"
              variant="destructive"
              onClick={handleRemoveImage}
              className="absolute top-2 right-2 w-6 h-6"
              title="Remove image"
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
          
          <div className="p-3">
            <p className="text-sm font-medium text-gray-900 truncate">
              {selectedImage.file.name}
            </p>
            <p className="text-xs text-gray-500">
              {formatFileSize(selectedImage.file.size)}
            </p>
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
  const [stream, setStream] = useState<MediaStream | null>(null)

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } // Use back camera if available
      })
      
      setStream(mediaStream)
      setIsCapturing(true)
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
    } catch (error) {
      console.error('Error accessing camera:', error)
      toast.error('Could not access camera')
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    setIsCapturing(false)
  }

  const capturePhoto = async () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')

    if (!context) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    context.drawImage(video, 0, 0)

    canvas.toBlob(async (blob) => {
      if (blob) {
        const file = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' })
        const preview = URL.createObjectURL(blob)
        const base64 = await blobToBase64(blob)
        
        onImageCapture(file, preview, base64)
        stopCamera()
        toast.success('Photo captured!')
      }
    }, 'image/jpeg', 0.8)
  }

  return (
    <div className={cn('relative', className)}>
      {!isCapturing ? (
        <Button
          size="icon"
          variant="outline"
          onClick={startCamera}
          title="Take photo"
        >
          <Camera className="w-4 h-4" />
        </Button>
      ) : (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-4 max-w-md w-full mx-4">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full rounded-lg mb-4"
            />
            
            <div className="flex justify-center space-x-4">
              <Button variant="outline" onClick={stopCamera}>
                Cancel
              </Button>
              <Button onClick={capturePhoto}>
                Capture
              </Button>
            </div>
          </div>
        </div>
      )}
      
      <canvas ref={canvasRef} className="hidden" />
    </div>
  )
}
