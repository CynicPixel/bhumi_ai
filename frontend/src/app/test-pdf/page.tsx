'use client'

import React, { useState } from 'react'
import { DocumentUpload } from '@/components/chat/ImageUpload'
import { pdfTextExtractionService } from '@/services/pdfTextExtraction'
import toast from 'react-hot-toast'

export default function TestPDFPage() {
  const [extractedText, setExtractedText] = useState<string>('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [pdfInfo, setPdfInfo] = useState<{
    pageCount?: number
    extractedPages?: number
  } | null>(null)

  const handleDocumentSelect = async (file: File, preview: string, base64: string) => {
    if (file.type === 'application/pdf') {
      setIsProcessing(true)
      setExtractedText('')
      setPdfInfo(null)
      
      try {
        console.log('📄 Processing PDF:', file.name)
        const result = await pdfTextExtractionService.extractText(base64)
        
        if (result.success && result.text) {
          setExtractedText(result.text)
          setPdfInfo({
            pageCount: result.pageCount,
            extractedPages: result.extractedPages
          })
          toast.success(`PDF processed successfully! Extracted ${result.extractedPages}/${result.pageCount} pages`)
        } else {
          toast.error(`PDF processing failed: ${result.error}`)
        }
      } catch (error) {
        console.error('❌ PDF processing error:', error)
        toast.error('Failed to process PDF')
      } finally {
        setIsProcessing(false)
      }
    } else {
      toast.info('Please select a PDF file to test text extraction')
    }
  }

  const handleDocumentRemove = () => {
    setExtractedText('')
    setPdfInfo(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            📄 PDF Text Extraction Test
          </h1>
          <p className="text-gray-600">
            Test the PDF text extraction service by uploading a PDF document
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* PDF Upload Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Upload PDF Document
            </h2>
            <DocumentUpload
              onDocumentSelect={handleDocumentSelect}
              onDocumentRemove={handleDocumentRemove}
              acceptedTypes={['application/pdf']}
              maxSize={20 * 1024 * 1024} // 20MB
            />
            
            {isProcessing && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 animate-spin border-2 border-blue-300 border-t-blue-600 rounded-full" />
                  <span className="text-blue-700">Processing PDF...</span>
                </div>
              </div>
            )}
          </div>

          {/* Extracted Text Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Extracted Text
            </h2>
            
            {pdfInfo && (
              <div className="mb-4 p-3 bg-green-50 rounded-lg">
                <p className="text-sm text-green-700">
                  <span className="font-medium">✅ Successfully processed:</span> {pdfInfo.extractedPages} of {pdfInfo.pageCount} pages
                </p>
              </div>
            )}
            
            {extractedText ? (
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
                  {extractedText}
                </pre>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <p className="text-gray-500">
                  {isProcessing 
                    ? 'Processing PDF...' 
                    : 'Upload a PDF to see extracted text here'
                  }
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Service Status */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Service Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h3 className="font-medium text-blue-900">PDF.js Library</h3>
              <p className="text-sm text-blue-700">
                {typeof window !== 'undefined' ? '✅ Available' : '❌ Not available'}
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <h3 className="font-medium text-green-900">Text Extraction</h3>
              <p className="text-sm text-green-700">
                {pdfTextExtractionService.isConfigured() ? '✅ Ready' : '⏳ Initializing...'}
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h3 className="font-medium text-purple-900">Worker Support</h3>
              <p className="text-sm text-purple-700">
                {typeof window !== 'undefined' ? '✅ Supported' : '❌ Not supported'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
