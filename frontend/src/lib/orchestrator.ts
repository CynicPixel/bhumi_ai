import { OrchestratorRequest, OrchestratorResponse } from '@/types/chat'
import { getOrchestratorUrl, generateUUID } from './utils'

export class OrchestratorClient {
  private baseUrl: string
  private abortController: AbortController | null = null

  constructor() {
    this.baseUrl = getOrchestratorUrl()
  }

  async sendMessage(
    message: string,
    options: {
      userId?: string
      imageData?: string
      contextId?: string
    } = {}
  ): Promise<OrchestratorResponse> {
    // Cancel any previous request
    if (this.abortController) {
      this.abortController.abort()
    }
    
    this.abortController = new AbortController()

    // Prepare message content with user_id if provided
    let messageContent = message
    if (options.userId) {
      messageContent = `user_id: ${options.userId}\n\n${message}`
    }

    // Define a type for message parts to allow both text and image parts
    type MessagePart =
      | { type: 'text'; text: string }
      | { type: 'image_url'; image_url: { url: string; detail: string } }

    // Prepare message parts in the correct format for the orchestrator
    const parts: MessagePart[] = [
      {
        type: 'text',
        text: messageContent
      }
    ]

    // Add image if provided
    if (options.imageData) {
      parts.push({
        type: 'image_url',
        image_url: {
          url: options.imageData,
          detail: 'high'
        }
      })
    }

    const request = {
      jsonrpc: '2.0',
      id: generateUUID(),
      method: 'message/stream',
      params: {
        message: {
          role: 'user',
          parts,
          messageId: generateUUID()
        }
      }
    }

    try {
      console.log('🚀 Sending request to orchestrator:', request)
      const response = await fetch(`${this.baseUrl}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal: this.abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Handle Server-Sent Events response
      const responseText = await response.text()
      console.log('📥 Raw SSE response:', responseText)
      
      // Parse SSE format: extract JSON from "data: {...}" lines
      const lines = responseText.split('\n')
      let finalData: OrchestratorResponse | null = null
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonData = line.substring(6) // Remove "data: " prefix
            const parsedData = JSON.parse(jsonData)
            console.log('📦 Parsed SSE data:', parsedData)
            
            // Keep the final response (usually the last one with final: true)
            if (parsedData.result) {
              finalData = parsedData
            }
          } catch (parseError) {
            console.warn('⚠️ Failed to parse SSE line:', line, parseError)
          }
        }
      }
      
      if (!finalData || !finalData.result) {
        throw new Error('No valid response data found in SSE stream')
      }

      console.log('✅ Final parsed response:', finalData)
      return finalData
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request was cancelled')
        }
        throw error
      }
      throw new Error('Unknown error occurred')
    }
  }

  async sendMessageStream(
    message: string,
    options: {
      userId?: string
      imageData?: string
      contextId?: string
      onUpdate?: (content: string, isComplete: boolean) => void
    } = {}
  ): Promise<OrchestratorResponse> {
    // For now, we'll use the regular sendMessage method
    // In a real implementation, you might want to implement Server-Sent Events
    // or WebSocket streaming for real-time updates
    
    const response = await this.sendMessage(message, options)
    
    // Simulate streaming by calling onUpdate with the final result
    if (options.onUpdate && response.result.status.message.parts[0]) {
      options.onUpdate(response.result.status.message.parts[0].text, true)
    }
    
    return response
  }

  cancelRequest() {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
  }

  async checkHealth(): Promise<boolean> {
    try {
      console.log('🔍 Checking orchestrator health at:', `${this.baseUrl}/.well-known/agent.json`)
      const response = await fetch(`${this.baseUrl}/.well-known/agent.json`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        timeout: 5000,
      } as RequestInit)

      console.log('✅ Health check response:', response.status, response.ok)
      return response.ok
    } catch (error) {
      console.error('❌ Health check failed:', error)
      return false
    }
  }

  getBaseUrl(): string {
    return this.baseUrl
  }
}

// Singleton instance
export const orchestratorClient = new OrchestratorClient()
