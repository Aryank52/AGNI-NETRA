/**
 * AGNI-NETRA — Voice Subsystem Type Definitions (WP7)
 * Defines strongly typed models for browser audio capture, STT/TTS providers,
 * visual voice states, and session telemetry.
 */

export type VoiceVisualState =
  | "MIC_OFF"
  | "REQUESTING_PERMISSION"
  | "LISTENING"
  | "TRANSCRIBING"
  | "THINKING"
  | "SPEAKING"
  | "ERROR";

export type STTProviderStatus = "AVAILABLE" | "DEGRADED" | "UNAVAILABLE" | "NOT_CONFIGURED";

export interface STTProvider {
  start(
    onInterim: (text: string) => void,
    onFinal: (text: string) => void,
    onError: (err: string) => void
  ): void;
  stop(): void;
  cancel(): void;
  getStatus(): STTProviderStatus;
}

export interface TTSProvider {
  speak(
    text: string,
    onStart?: () => void,
    onEnd?: () => void,
    onError?: (err: any) => void
  ): void;
  stop(): void;
  pause(): void;
  resume(): void;
  isMuted(): boolean;
  setMuted(muted: boolean): void;
}

export interface VoiceSessionMetrics {
  permissionLatencyMs: number;
  captureLatencyMs: number;
  sttLatencyMs: number;
  jarvisLatencyMs: number;
  ttsLatencyMs: number;
  totalRoundTripMs: number;
}
