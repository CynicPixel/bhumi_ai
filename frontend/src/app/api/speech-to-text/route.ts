import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { audio, config } = body

    console.log('📞 STT API called with config:', {
      hasAudio: !!audio,
      audioLength: audio?.length || 0,
      config: config
    })
    
    // For now, return empty transcript to let browser STT handle it
    // Later you can integrate Google Cloud Speech-to-Text here
    const response = {
      transcript: '',
      confidence: 0,
      note: 'Server-side STT not implemented yet. Using browser STT.',
      timestamp: new Date().toISOString()
    }
    
    console.log('📞 STT API returning response:', response)
    
    return NextResponse.json(response)
  } catch (error) {
    console.error('STT API Error:', error)
    return NextResponse.json({ 
      error: 'Failed to transcribe audio',
      details: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}
