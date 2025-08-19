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
    
  // Set primary language to Hindi but allow auto-detection
  this.recognition.lang = 'hi-IN';
  // Do not set grammars to null; leave as default or set to SpeechGrammarList if needed
  }

  async transcribeRealtime(
    options: STTOptions,
    onResult: (result: STTResult) => void,
    onError: (error: string) => void
  ): Promise<void> {
    if (!this.recognition) {
      throw new Error('Speech Recognition not supported');
    }

    // Use browser's automatic language detection
    // Start with Hindi as primary, but browser will auto-switch
    this.recognition.lang = 'hi-IN';
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
        detectedLanguage = this.detectLanguage(result.transcript);
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

    this.recognition.start();
    this.isListening = true;
  }

  // Simple language detection based on script/characters
  private detectLanguage(text: string): string {
    if (!text) return 'unknown';
    
    // Bengali detection (Bengali script)
    if (/[\u0980-\u09FF]/.test(text)) {
      return 'Bengali';
    }
    
    // Hindi detection (Devanagari script)
    if (/[\u0900-\u097F]/.test(text)) {
      return 'Hindi';
    }
    
    // English detection (Latin script + common English words)
    if (/^[a-zA-Z0-9\s.,!?'"()-]+$/.test(text)) {
      return 'English';
    }
    
    // Mixed content
    if (/[\u0900-\u097F]/.test(text) && /[a-zA-Z]/.test(text)) {
      return 'Hindi + English';
    }
    
    if (/[\u0980-\u09FF]/.test(text) && /[a-zA-Z]/.test(text)) {
      return 'Bengali + English';
    }
    
    return 'Mixed';
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
          languageCode: 'hi-IN',
          alternativeLanguageCodes: ['bn-IN', 'en-IN'],
          enableAutomaticPunctuation: true,
          model: 'latest_short',
          useEnhanced: true,
          enableLanguageDetection: true
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
}
