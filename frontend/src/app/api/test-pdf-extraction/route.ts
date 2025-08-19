import { NextRequest, NextResponse } from 'next/server'
import { pdfTextExtractionService } from '@/services/pdfTextExtraction'

export async function POST(request: NextRequest) {
  try {
    const { pdfData, maxPages } = await request.json()

    if (!pdfData) {
      return NextResponse.json(
        { error: 'No PDF data provided' },
        { status: 400 }
      )
    }

    // Test the PDF text extraction service
    const result = await pdfTextExtractionService.extractText(pdfData, maxPages || 10)

    return NextResponse.json(result)
  } catch (error) {
    console.error('Error in test-pdf-extraction route:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function GET() {
  // Check if PDF extraction service is configured
  const status = pdfTextExtractionService.getStatus()
  
  return NextResponse.json({
    service: 'PDF Text Extraction',
    status,
    message: status.available 
      ? 'PDF extraction service is ready' 
      : 'PDF extraction service is not available'
  })
}
