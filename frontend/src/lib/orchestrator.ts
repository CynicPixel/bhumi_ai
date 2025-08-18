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

    // Prepare message parts
    const parts: OrchestratorRequest['params']['message']['parts'] = [
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

    const request: OrchestratorRequest = {
      jsonrpc: '2.0',
      id: generateUUID(),
      method: 'message/send',
      params: {
        message: {
          role: 'user',
          parts,
          messageId: generateUUID()
        }
      }
    }

    try {
      const response = await fetch(`${this.baseUrl}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(request),
        signal: this.abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: OrchestratorResponse = await response.json()
      
      if (!data.result) {
        throw new Error('Invalid response format from orchestrator')
      }

      return data
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
      const response = await fetch(`${this.baseUrl}/.well-known/agent.json`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        timeout: 5000,
      } as RequestInit)

      return response.ok
    } catch {
      return false
    }
  }

  getBaseUrl(): string {
    return this.baseUrl
  }
}

// Singleton instance
export const orchestratorClient = new OrchestratorClient()
