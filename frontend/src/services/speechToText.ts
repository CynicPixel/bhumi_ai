'use client'

export interface STTResult {
  transcript: string;
  confidence: number;
  language?: string;
  isFinal: boolean;
}

export interface STTOptions {
  continuous: boolean;
  interimResults: boolean;
}

export class SpeechToTextService {
  private recognition: any = null;
  private isListening = false;
  private accumulatedTranscript = '';

  constructor() {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.setupRecognition();
      }
    }
  }

  private setupRecognition() {
    if (!this.recognition) return;

    // Configure for automatic multi-language detection
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.maxAlternatives = 3;
    
    // Set default language to Bengali
    this.recognition.lang = 'bn-IN';
    
    // Enable multiple language support
    if (this.recognition.grammars) {
      // Some browsers support multiple language grammars
      console.log('Speech recognition grammars supported');
    }
  }

  async transcribeRealtime(
    options: STTOptions,
    language: string = 'bn-IN',
    onResult: (result: STTResult) => void,
    onError: (error: string) => void
  ): Promise<void> {
    if (!this.recognition) {
      throw new Error('Speech Recognition not supported');
    }

    // Reset accumulated transcript for new session
    this.accumulatedTranscript = '';

    // Use the selected language, but browser will auto-detect
    this.recognition.lang = language;
    this.recognition.continuous = options.continuous;
    this.recognition.interimResults = options.interimResults;

    this.recognition.onresult = (event: any) => {
      let transcript = '';
      let confidence = 0;
      let isFinal = false;
      let detectedLanguage = 'unknown';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        transcript += result[0].transcript;
        confidence = result.confidence || 0.8;
        isFinal = result.isFinal;
        
        // Try to detect language from transcript
        detectedLanguage = this.detectLanguage(result[0].transcript);
      }

      if (isFinal) {
        // Accumulate final transcripts
        this.accumulatedTranscript += (this.accumulatedTranscript ? ' ' : '') + transcript;
        transcript = this.accumulatedTranscript;
      }

      onResult({
        transcript: transcript.trim(),
        confidence,
        isFinal,
        language: detectedLanguage
      });
    };

    this.recognition.onerror = (event: any) => {
      onError(`Speech recognition error: ${event.error}`);
    };

    this.recognition.onend = () => {
      this.isListening = false;
    };

    this.recognition.start();
    this.isListening = true;
  }

  // Enhanced language detection based on script/characters and common words
  private detectLanguage(text: string): string {
    if (!text) return '';
    
    // Bengali detection (Bengali script)
    if (/[\u0980-\u09FF]/.test(text)) {
      // Check for common Bengali words to confirm
      const bengaliWords = ['কৃষি', 'চাষ', 'ধান', 'গম', 'আলু', 'টমেটো', 'বেগুন', 'পেঁয়াজ', 'রসুন', 'মরিচ', 'হলুদ', 'ধনিয়া', 'জিরা', 'মেথি'];
      const hasBengaliWords = bengaliWords.some(word => text.includes(word));
      return hasBengaliWords ? 'Bengali' : 'Bengali';
    }
    
    // Hindi detection (Devanagari script)
    if (/[\u0900-\u097F]/.test(text)) {
      // Check for common Hindi words to confirm
      const hindiWords = ['कृषि', 'खेती', 'धान', 'गेहूं', 'आलू', 'टमाटर', 'बैंगन', 'प्याज', 'लहसुन', 'मिर्च', 'हल्दी', 'धनिया', 'जीरा', 'मेथी'];
      const hasHindiWords = hindiWords.some(word => text.includes(word));
      return hasHindiWords ? 'Hindi' : 'Hindi';
    }
    
    // English detection (Latin script + common English words)
    if (/^[a-zA-Z0-9\s.,!?'"()-]+$/.test(text)) {
      const englishWords = ['farming', 'agriculture', 'crop', 'weather', 'market', 'price', 'scheme', 'government', 'organic', 'fertilizer', 'pesticide'];
      const hasEnglishWords = englishWords.some(word => text.toLowerCase().includes(word));
      return hasEnglishWords ? 'English' : 'English';
    }
    
    // Mixed content detection
    if (/[\u0900-\u097F]/.test(text) && /[a-zA-Z]/.test(text)) {
      return 'Hindi + English';
    }
    
    if (/[\u0980-\u09FF]/.test(text) && /[a-zA-Z]/.test(text)) {
      return 'Bengali + English';
    }
    
    // Check for transliterated Indian languages (Roman script)
    const transliteratedBengali = /[aeiouAEIOU][aeiouAEIOU]|[aeiouAEIOU][bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ][aeiouAEIOU]/;
    const transliteratedHindi = /[aeiouAEIOU][aeiouAEIOU]|[aeiouAEIOU][bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ][aeiouAEIOU]/;
    
    if (transliteratedBengali.test(text) && text.length > 10) {
      return 'Bengali';
    }
    
    if (transliteratedHindi.test(text) && text.length > 10) {
      return 'Hindi';
    }
    
    return '';
  }

  // Cloud API with automatic language detection
  async transcribeAudio(audioBlob: Blob): Promise<{transcript: string, language: string}> {
    try {
      const base64Audio = await this.blobToBase64(audioBlob);
      
      const response = await fetch('/api/speech-to-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio: base64Audio,
          config: {
            encoding: 'WEBM_OPUS',
            sampleRateHertz: 48000,
            languageCode: 'bn-IN', // Primary: Bengali
            alternativeLanguageCodes: ['hi-IN', 'en-IN', 'pa-IN', 'te-IN', 'ta-IN', 'ml-IN', 'gu-IN', 'kn-IN', 'or-IN', 'as-IN'],
            enableAutomaticPunctuation: true,
            model: 'latest_short',
            useEnhanced: true,
            enableLanguageDetection: true,
            enableWordTimeOffsets: true
          }
        }),
      });

      if (!response.ok) {
        console.warn('Cloud STT API not available, using browser STT only');
        return {
          transcript: '', // Let browser STT handle it
          language: 'auto-detected'
        };
      }

      const result = await response.json();
      const transcript = result.transcript || '';
      const detectedLang = this.detectLanguage(transcript);
      
      return {
        transcript,
        language: detectedLang
      };
    } catch (error) {
      console.warn('Cloud STT error, using browser STT only:', error);
      // Return empty transcript to rely on browser STT
      return {
        transcript: '',
        language: 'auto-detected'
      };
    }
  }

  private blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result.split(',')[1]);
        } else {
          reject('Failed to convert blob to base64');
        }
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  isSupported(): boolean {
    return !!this.recognition;
  }

  // Get the accumulated transcript
  getAccumulatedTranscript(): string {
    return this.accumulatedTranscript;
  }
}
