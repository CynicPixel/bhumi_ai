import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTimestamp(date: Date): string {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date)
}

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c == 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

export async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export async function createPDFPreview(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      try {
        // Create a canvas to render PDF first page
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Could not get canvas context'))
          return
        }
        
        // Set canvas size for PDF preview
        canvas.width = 300
        canvas.height = 400
        
        // Create PDF preview (simple placeholder for now)
        ctx.fillStyle = '#f3f4f6'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        
        // Draw PDF icon
        ctx.fillStyle = '#ef4444'
        ctx.fillRect(20, 20, 260, 360)
        
        // Draw text
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 24px Arial'
        ctx.textAlign = 'center'
        ctx.fillText('PDF', canvas.width / 2, canvas.height / 2 - 20)
        
        ctx.font = '16px Arial'
        ctx.fillText(file.name, canvas.width / 2, canvas.height / 2 + 20)
        
        // Convert canvas to data URL
        resolve(canvas.toDataURL('image/png'))
      } catch (error) {
        reject(error)
      }
    }
    reader.onerror = reject
    reader.readAsArrayBuffer(file)
  })
}

export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

export function isAudioFile(file: File): boolean {
  return file.type.startsWith('audio/')
}

export function isPDFFile(file: File): boolean {
  return file.type === 'application/pdf'
}

export function isDocumentFile(file: File): boolean {
  return isImageFile(file) || isPDFFile(file)
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function truncateText(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export function extractUserIdFromMessage(message: string): string | null {
  const match = message.match(/user_id:\s*([^\s\n]+)/)
  return match ? match[1] : null
}

export function cleanMessageForDisplay(message: string): string {
  // Remove user_id prefix if present
  return message.replace(/^user_id:\s*[^\s\n]+\s*\n\s*/, '')
}

export function getOrchestratorUrl(): string {
  return process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || 'http://localhost:10007'
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return 'An unexpected error occurred'
}
