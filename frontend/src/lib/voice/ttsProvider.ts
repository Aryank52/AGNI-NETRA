/**
 * AGNI-NETRA — Text-to-Speech (TTS) Provider Abstraction (WP7)
 * Interfaces with native speech synthesis with support for interruption (barge-in) and mute control.
 */

import { TTSProvider } from "./voiceTypes";

export class WebSpeechTTSProvider implements TTSProvider {
  private synth: SpeechSynthesis | null = null;
  private muted: boolean = false;
  private activeUtterance: SpeechSynthesisUtterance | null = null;

  constructor() {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      this.synth = window.speechSynthesis;
    }
  }

  isMuted(): boolean {
    return this.muted;
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
    if (muted) {
      this.stop();
    }
  }

  speak(
    text: string,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: (err: any) => void
  ): void {
    if (this.muted || !this.synth || typeof window === "undefined") {
      if (onEnd) onEnd();
      return;
    }

    // Stop active speech (Barge-in / clean boundary)
    this.stop();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    utterance.lang = "en-US";

    utterance.onstart = () => {
      this.activeUtterance = utterance;
      if (onStart) onStart();
    };

    utterance.onend = () => {
      this.activeUtterance = null;
      if (onEnd) onEnd();
    };

    utterance.onerror = (event: any) => {
      this.activeUtterance = null;
      if (onError) onError(event);
      if (onEnd) onEnd();
    };

    this.synth.speak(utterance);
  }

  stop(): void {
    if (this.synth) {
      try {
        this.synth.cancel();
      } catch {
        // ignore
      }
      this.activeUtterance = null;
    }
  }

  pause(): void {
    if (this.synth && this.synth.speaking) {
      try {
        this.synth.pause();
      } catch {
        // ignore
      }
    }
  }

  resume(): void {
    if (this.synth && this.synth.paused) {
      try {
        this.synth.resume();
      } catch {
        // ignore
      }
    }
  }
}

export const defaultTTSProvider = new WebSpeechTTSProvider();
