/**
 * AGNI-NETRA — Speech-to-Text (STT) Provider Abstraction (WP7)
 * Interfaces with the native Web Speech API with safe degradation and error categorization.
 */

import { STTProvider, STTProviderStatus } from "./voiceTypes";

export class WebSpeechSTTProvider implements STTProvider {
  private recognition: any = null;
  private isRunning: boolean = false;

  constructor() {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          this.recognition = new SpeechRecognition();
          this.recognition.continuous = false;
          this.recognition.interimResults = true;
          this.recognition.lang = "en-US";
        } catch {
          this.recognition = null;
        }
      }
    }
  }

  getStatus(): STTProviderStatus {
    if (typeof window === "undefined") return "NOT_CONFIGURED";
    return this.recognition ? "AVAILABLE" : "UNAVAILABLE";
  }

  start(
    onInterim: (text: string) => void,
    onFinal: (text: string) => void,
    onError: (err: string) => void
  ): void {
    if (!this.recognition) {
      onError("Speech recognition hardware or browser API unavailable. Operating in text mode.");
      return;
    }

    if (this.isRunning) {
      this.stop();
    }

    this.recognition.onresult = (event: any) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (interim) {
        onInterim(interim);
      }
      if (final) {
        onFinal(final);
      }
    };

    this.recognition.onerror = (event: any) => {
      this.isRunning = false;
      const err = event.error || "unknown";
      if (err === "not-allowed" || err === "permission-denied") {
        onError("Microphone permission denied. Voice input is unavailable. Please type your query in the prompt bar.");
      } else if (err === "no-speech") {
        onError("No speech detected. Please speak clearly into your microphone.");
      } else if (err === "audio-capture") {
        onError("No microphone hardware detected on this device.");
      } else if (err === "network") {
        onError("Network error during speech processing. Falling back to visual text mode.");
      } else {
        onError(`Speech recognition issue (${err}). Gracefully falling back to text interface.`);
      }
    };

    this.recognition.onend = () => {
      this.isRunning = false;
    };

    try {
      this.recognition.start();
      this.isRunning = true;
    } catch (err: any) {
      this.isRunning = false;
      onError(`Failed to start microphone: ${err.message}`);
    }
  }

  stop(): void {
    if (this.recognition && this.isRunning) {
      try {
        this.recognition.stop();
      } catch {
        // ignore
      }
      this.isRunning = false;
    }
  }

  cancel(): void {
    if (this.recognition && this.isRunning) {
      try {
        this.recognition.abort();
      } catch {
        // ignore
      }
      this.isRunning = false;
    }
  }
}

export const defaultSTTProvider = new WebSpeechSTTProvider();
