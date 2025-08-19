// src/pages/api/speech-to-text.ts
import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { audio, config } = req.body

    console.log('📞 STT API called, returning fallback response')
    
    // For now, return empty transcript to let browser STT handle it
    // Later you can integrate Google Cloud Speech-to-Text here
    res.status(200).json({ 
      transcript: '',
      confidence: 0,
      note: 'Server-side STT not implemented yet. Using browser STT.'
    })
  } catch (error) {
    console.error('STT API Error:', error)
    res.status(500).json({ error: 'Failed to transcribe audio' })
  }
}
