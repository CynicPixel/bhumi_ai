# 📄 PDF Text Extraction Functionality

## Overview

The Bhumi AI frontend now supports PDF document analysis through intelligent text extraction. When a PDF is uploaded, the system extracts the text content and sends it directly to the orchestrator for agricultural intelligence analysis, bypassing the Gemini image analysis route.

## Architecture

```
PDF Upload → Text Extraction (PDF.js) → Orchestrator → Agricultural Agents
    ↓
Image Upload → Gemini Analysis → Orchestrator → Agricultural Agents
```

## Key Features

### 1. **Smart Document Routing**
- **PDFs**: Text extraction → Direct orchestrator routing
- **Images**: Gemini analysis → Orchestrator routing
- **Automatic detection** of document type

### 2. **PDF Text Extraction**
- Uses **PDF.js** library for client-side text extraction
- Supports up to 10 pages by default (configurable)
- Handles text-based PDFs efficiently
- Graceful fallback for image-based/scanned PDFs

### 3. **Enhanced User Experience**
- Clear visual indicators for PDF vs Image uploads
- Real-time processing feedback
- Informative error messages
- Document type-specific default prompts

## Implementation Details

### Services

#### `PDFTextExtractionService` (`/src/services/pdfTextExtraction.ts`)
- **Client-side PDF processing** using PDF.js
- **Dynamic library loading** to avoid SSR issues
- **Text extraction** with page-by-page processing
- **Error handling** and fallback mechanisms

#### `OrchestratorClient` (`/src/lib/orchestrator.ts`)
- **Smart routing logic** for different document types
- **PDF text integration** into message content
- **Image analysis fallback** for failed PDF extraction

### Components

#### `DocumentUpload` (`/src/components/chat/ImageUpload.tsx`)
- **Unified interface** for both images and PDFs
- **Type-specific previews** and indicators
- **Enhanced user feedback** for PDF processing

#### `ChatInput` (`/src/components/chat/ChatInput.tsx`)
- **Document-aware messaging** with appropriate defaults
- **Type-specific prompts** for better user guidance

## Usage

### 1. **Upload PDF Document**
```
1. Click "Upload an image or PDF" button
2. Select PDF file (up to 20MB)
3. System automatically detects PDF type
4. Text extraction begins automatically
5. Extracted text is sent to orchestrator
```

### 2. **Test PDF Functionality**
```
Visit /test-pdf for dedicated testing interface
- Upload PDFs and see extracted text
- Monitor processing status
- Check service health
```

### 3. **API Endpoints**
```
POST /api/test-pdf-extraction
- Test PDF text extraction service
- Accepts: { pdfData: string, maxPages?: number }
- Returns: { success, text, error, pageCount, extractedPages }

GET /api/test-pdf-extraction
- Check service status and configuration
```

## Configuration

### Dependencies
```json
{
  "dependencies": {
    "pdfjs-dist": "^4.0.0"
  },
  "devDependencies": {
    "@types/pdfjs-dist": "^3.0.0"
  }
}
```

### Environment Variables
- No additional environment variables required
- PDF.js worker loaded from CDN automatically

## Error Handling

### Common Scenarios

#### 1. **PDF.js Not Initialized**
- Automatic retry mechanism
- User-friendly error messages
- Fallback to manual text input

#### 2. **Text Extraction Failure**
- Detailed error reporting
- Graceful degradation
- User guidance for alternative approaches

#### 3. **Large PDF Files**
- Configurable page limits
- Memory-efficient processing
- Progress indicators

## Performance Considerations

### 1. **Client-Side Processing**
- No server upload required for text extraction
- Reduced bandwidth usage
- Faster processing for text-based PDFs

### 2. **Memory Management**
- Page-by-page processing
- Configurable page limits
- Automatic cleanup of extracted data

### 3. **User Experience**
- Real-time feedback during processing
- Non-blocking UI updates
- Responsive interface during extraction

## Testing

### 1. **Unit Tests**
- Service initialization
- Text extraction logic
- Error handling scenarios

### 2. **Integration Tests**
- End-to-end PDF processing
- Orchestrator integration
- User interface workflows

### 3. **Manual Testing**
- Various PDF formats and sizes
- Different content types
- Edge cases and error conditions

## Future Enhancements

### 1. **Advanced PDF Features**
- OCR support for scanned documents
- Table and form extraction
- Multi-language support

### 2. **Performance Improvements**
- Web Workers for background processing
- Streaming text extraction
- Caching mechanisms

### 3. **User Experience**
- Drag-and-drop improvements
- Batch PDF processing
- Progress tracking for large files

## Troubleshooting

### Common Issues

#### 1. **PDF.js Not Loading**
```
Check browser console for errors
Verify internet connection for CDN
Clear browser cache and reload
```

#### 2. **Text Extraction Fails**
```
Verify PDF is text-based (not scanned)
Check file size and page count
Review console for specific error messages
```

#### 3. **Memory Issues**
```
Reduce maxPages configuration
Process smaller PDFs
Check browser memory usage
```

## Support

For issues or questions related to PDF functionality:
1. Check browser console for error messages
2. Verify PDF file format and content
3. Test with `/test-pdf` endpoint
4. Review service status indicators

---

**Note**: This functionality is designed to work seamlessly with the existing agricultural intelligence system, providing farmers with comprehensive document analysis capabilities for agricultural queries.
