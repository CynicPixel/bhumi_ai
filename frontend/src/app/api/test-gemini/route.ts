import { NextRequest, NextResponse } from 'next/server'
import { imageDescriptionService } from '@/services/imageDescription'

export async function POST(request: NextRequest) {
  try {
    const { imageData, prompt } = await request.json()

    if (!imageData) {
      return NextResponse.json(
        { error: 'No image data provided' },
        { status: 400 }
      )
    }

    // Test the image description service
    const result = await imageDescriptionService.describeImage(imageData, prompt)

    return NextResponse.json(result)
  } catch (error) {
    console.error('Error in test-gemini route:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function GET() {
  // Check if Gemini service is configured
  const isConfigured = imageDescriptionService.isConfigured()
  
  return NextResponse.json({
    configured: isConfigured,
    message: isConfigured 
      ? 'Gemini service is configured and ready' 
      : 'Gemini API key not found. Please set NEXT_PUBLIC_GEMINI_API_KEY in .env.local file.'
  })
}
