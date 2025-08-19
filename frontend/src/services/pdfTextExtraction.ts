export interface PDFTextExtractionResponse {
  success: boolean;
  text?: string;
  error?: string;
  pageCount?: number;
  extractedPages?: number;
}

export class PDFTextExtractionService {
  private isInitialized: boolean = false;
  private pdfjsLib: any = null;

  constructor() {
    // Only initialize on client side
    if (typeof window !== 'undefined') {
      this.initializePDFJS();
    }
  }

  private async initializePDFJS() {
    try {
      // Dynamically import pdfjs-dist to avoid SSR issues
      if (typeof window !== 'undefined') {
        // Use the main build with proper error handling
        this.pdfjsLib = await import('pdfjs-dist');
        
        // Set worker source for PDF.js v3
        if (this.pdfjsLib.GlobalWorkerOptions) {
          this.pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`;
        }
        
        this.isInitialized = true;
        console.log('✅ PDF.js initialized successfully');
      }
    } catch (error) {
      console.error('❌ Failed to initialize PDF.js:', error);
      this.isInitialized = false;
    }
  }

  /**
   * Extract text from a PDF file
   * @param base64PDF - Base64 encoded PDF string (with data: prefix)
   * @param maxPages - Maximum number of pages to extract (default: 10)
   * @returns Promise with extracted text
   */
  async extractText(
    base64PDF: string, 
    maxPages: number = 10
  ): Promise<PDFTextExtractionResponse> {
    // Ensure we're on the client side
    if (typeof window === 'undefined') {
      return {
        success: false,
        error: 'PDF text extraction is only available in the browser.'
      };
    }

    if (!this.isInitialized || !this.pdfjsLib) {
      await this.initializePDFJS();
      if (!this.isInitialized || !this.pdfjsLib) {
        return {
          success: false,
          error: 'PDF.js not initialized. Please try again.'
        };
      }
    }

    try {
      // Extract the base64 data without the data:application/pdf;base64, prefix
      const base64Data = base64PDF.includes(',') 
        ? base64PDF.split(',')[1] 
        : base64PDF;

      // Convert base64 to Uint8Array
      const pdfBytes = this.base64ToUint8Array(base64Data);

      // Use the initialized PDF.js library
      if (!this.pdfjsLib) {
        throw new Error('PDF.js not initialized');
      }
      
      // Load the PDF document
      const loadingTask = this.pdfjsLib.getDocument({ data: pdfBytes });
      const pdf = await loadingTask.promise;
      
      console.log(`📄 PDF loaded successfully. Pages: ${pdf.numPages}`);
      
      const pageCount = pdf.numPages;
      const pagesToExtract = Math.min(pageCount, maxPages);
      let extractedText = '';
      let extractedPages = 0;

      // Extract text from each page
      for (let pageNum = 1; pageNum <= pagesToExtract; pageNum++) {
        try {
          const page = await pdf.getPage(pageNum);
          const textContent = await page.getTextContent();
          
          // Combine text items
          const pageText = textContent.items
            .map((item: any) => item.str)
            .join(' ')
            .replace(/\s+/g, ' ')
            .trim();
          
          if (pageText) {
            extractedText += `\n\n--- Page ${pageNum} ---\n${pageText}`;
            extractedPages++;
          }
          
          console.log(`📄 Extracted page ${pageNum}/${pagesToExtract}`);
        } catch (pageError) {
          console.warn(`⚠️ Failed to extract page ${pageNum}:`, pageError);
          // Continue with other pages
        }
      }

      if (!extractedText.trim()) {
        return {
          success: false,
          error: 'No text could be extracted from the PDF. The document might be image-based or scanned.',
          pageCount,
          extractedPages: 0
        };
      }

      // Clean up the extracted text
      const cleanedText = this.cleanExtractedText(extractedText);

      console.log(`✅ PDF text extraction completed. Pages: ${extractedPages}/${pageCount}`);
      
      return {
        success: true,
        text: cleanedText,
        pageCount,
        extractedPages
      };

    } catch (error) {
      console.error('❌ PDF text extraction failed:', error);
      
      let errorMessage = 'Failed to extract text from PDF';
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      return {
        success: false,
        error: errorMessage
      };
    }
  }

  /**
   * Convert base64 string to Uint8Array
   */
  private base64ToUint8Array(base64: string): Uint8Array {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
  }

  /**
   * Clean and format extracted text
   */
  private cleanExtractedText(text: string): string {
    return text
      // Remove excessive whitespace
      .replace(/\s+/g, ' ')
      // Remove page separators
      .replace(/--- Page \d+ ---/g, '\n\n')
      // Clean up line breaks
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      // Trim whitespace
      .trim();
  }

  /**
   * Check if the service is properly configured
   */
  isConfigured(): boolean {
    return this.isInitialized;
  }

  /**
   * Get service status
   */
  getStatus(): { initialized: boolean; available: boolean } {
    return {
      initialized: this.isInitialized,
      available: typeof window !== 'undefined' && this.isInitialized
    };
  }
}

// Export singleton instance
export const pdfTextExtractionService = new PDFTextExtractionService();
