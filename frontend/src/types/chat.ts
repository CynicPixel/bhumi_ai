export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
  type: 'text' | 'audio' | 'image'
  metadata?: {
    audioUrl?: string
    imageUrl?: string
    imageName?: string
    audioLength?: number
    contextId?: string
    taskId?: string
    messageId?: string
    language?: string    // ADD THIS LINE
    transcript?: string  // ADD THIS LINE
  }
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  isRecording: boolean
  contextId?: string
  currentTaskId?: string
}

export interface OrchestratorRequest {
  jsonrpc: '2.0'
  id: string
  method: 'message/stream'
  params: {
    message: {
      role: 'user'
      parts: Array<{
        type: 'text' | 'image_url'
        text?: string
        image_url?: {
          url: string
          detail?: 'low' | 'high' | 'auto'
        }
      }>
      messageId: string
    }
  }
}

export interface OrchestratorResponse {
  id: string
  jsonrpc: '2.0'
  result: {
    contextId: string
    history: Array<{
      contextId: string
      kind: 'message'
      messageId: string
      parts: Array<{
        kind: 'text'
        text: string
      }>
      role: 'user' | 'agent'
      taskId: string
    }>
    id: string
    kind: 'task'
    status: {
      message: {
        contextId: string
        kind: 'message'
        messageId: string
        parts: Array<{
          kind: 'text'
          text: string
        }>
        role: 'agent'
        taskId: string
      }
      state: 'completed' | 'working' | 'failed'
      timestamp: string
    }
  }
}

export interface AudioRecordingState {
  isRecording: boolean
  mediaRecorder: MediaRecorder | null
  audioChunks: Blob[]
  audioUrl: string | null
  duration: number
}

export interface ImageUploadState {
  file: File | null
  preview: string | null
  isUploading: boolean
}
