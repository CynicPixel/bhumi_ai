import { OrchestratorRequest, OrchestratorResponse } from '@/types/chat'
import { getOrchestratorUrl, generateUUID } from './utils'
import { imageDescriptionService } from '@/services/imageDescription'
import { pdfTextExtractionService } from '@/services/pdfTextExtraction'

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

    // Handle document processing (images vs PDFs)
    let enhancedMessage = message
    if (options.imageData) {
      // Check if it's a PDF or image
      if (options.imageData.startsWith('data:application/pdf')) {
        console.log('📄 PDF detected, extracting text...')
        
        try {
          const pdfResult = await pdfTextExtractionService.extractText(options.imageData)
          
          if (pdfResult.success && pdfResult.text) {
            // Append PDF text to the original message
            enhancedMessage = message 
              ? `${message}\n\n[PDF Content: ${pdfResult.text}]`
              : `[PDF Content: ${pdfResult.text}]`
            
            console.log('✅ PDF text extracted successfully')
            console.log(`📄 Extracted ${pdfResult.extractedPages}/${pdfResult.pageCount} pages`)
            console.log('📝 Enhanced message length:', enhancedMessage.length)
          } else {
            console.warn('⚠️ Failed to extract PDF text:', pdfResult.error)
            
            enhancedMessage = message 
              ? `${message}\n\n[Note: PDF text extraction failed: ${pdfResult.error}. Please provide more details about the document content.]`
              : `[Note: PDF text extraction failed: ${pdfResult.error}. Please describe the document content or provide more context about your agricultural question.]`
          }
        } catch (error) {
          console.error('❌ Error extracting PDF text:', error)
          enhancedMessage = message || 'Please analyze the uploaded PDF document.'
        }
      } else {
        // Handle image with Gemini
        console.log('🖼️ Image detected, getting description from Gemini...')
        
        try {
          const descriptionResult = await imageDescriptionService.describeImage(options.imageData)
          
          if (descriptionResult.success && descriptionResult.description) {
            // Append image description to the original message
            enhancedMessage = message 
              ? `${message}\n\n[Image Description: ${descriptionResult.description}]`
              : `[Image Description: ${descriptionResult.description}]`
            
            console.log('✅ Image description added to message')
            console.log('📝 Enhanced message:', enhancedMessage)
          } else {
            console.warn('⚠️ Failed to get image description:', descriptionResult.error)
            
            // Provide specific error message based on the failure reason
            if (descriptionResult.error?.includes('API key not configured')) {
              enhancedMessage = message 
                ? `${message}\n\n[Note: Image analysis is currently unavailable - Gemini API key not configured. Please provide more details about what you see in the image.]`
                : `[Note: Image analysis is currently unavailable - Gemini API key not configured. Please describe what you see in the image or provide more context about your agricultural question.]`
          } else {
              enhancedMessage = message 
                ? `${message}\n\n[Note: Image analysis is currently unavailable. Please provide more details about what you see in the image.]`
                : `[Note: Image analysis is currently unavailable. Please describe what you see in the image or provide more context about your agricultural question.]`
            }
          }
        } catch (error) {
          console.error('❌ Error getting image description:', error)
          // Fallback to original message if description fails
          enhancedMessage = message || 'Please analyze the uploaded image.'
        }
      }
    }

    // Prepare message content with user_id if provided
    let messageContent = enhancedMessage
    if (options.userId) {
      messageContent = `user_id: ${options.userId}\n\n${enhancedMessage}`
      console.log('🔍 Orchestrator client: Added user_id prefix:', options.userId)
      console.log('🔍 Orchestrator client: Final message content:', messageContent)
    } else {
      console.log('⚠️ Orchestrator client: No userId provided in options')
    }

    // Prepare message parts - only text now since we converted image to description
    const parts = [
      {
        type: 'text',
        text: messageContent
      }
    ]

    // Note: We no longer add image_url parts since we're converting images to text descriptions

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
      console.log('📝 Request body (JSON):', JSON.stringify(request, null, 2))
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
