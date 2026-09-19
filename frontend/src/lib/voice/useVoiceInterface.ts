"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { VoiceVisualState, VoiceSessionMetrics } from "./voiceTypes";
import { WebSpeechSTTProvider } from "./sttProvider";
import { WebSpeechTTSProvider } from "./ttsProvider";

interface UseVoiceInterfaceOptions {
  onTranscriptComplete?: (finalTranscript: string) => void;
  onError?: (errorMsg: string) => void;
  autoSpeak?: boolean;
}

export function useVoiceInterface(options: UseVoiceInterfaceOptions = {}) {
  const { onTranscriptComplete, onError } = options;

  const [visualState, setVisualState] = useState<VoiceVisualState>("MIC_OFF");
  const [transcript, setTranscript] = useState<string>("");
  const [interimTranscript, setInterimTranscript] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isMuted, setIsMutedState] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<VoiceSessionMetrics>({
    permissionLatencyMs: 0,
    captureLatencyMs: 0,
    sttLatencyMs: 0,
    jarvisLatencyMs: 0,
    ttsLatencyMs: 0,
    totalRoundTripMs: 0,
  });

  const sttProviderRef = useRef<WebSpeechSTTProvider | null>(null);
  const ttsProviderRef = useRef<WebSpeechTTSProvider | null>(null);
  const startTimeRef = useRef<number>(0);
  const activeStreamRef = useRef<MediaStream | null>(null);

  // Initialize providers
  useEffect(() => {
    sttProviderRef.current = new WebSpeechSTTProvider();
    ttsProviderRef.current = new WebSpeechTTSProvider();

    return () => {
      // Clean up on unmount
      if (sttProviderRef.current) {
        sttProviderRef.current.cancel();
      }
      if (ttsProviderRef.current) {
        ttsProviderRef.current.stop();
      }
      if (activeStreamRef.current) {
        activeStreamRef.current.getTracks().forEach((t) => t.stop());
        activeStreamRef.current = null;
      }
    };
  }, []);

  // Barge-in: User interaction stops ongoing speech synthesis
  const interruptSpeaking = useCallback(() => {
    if (ttsProviderRef.current) {
      ttsProviderRef.current.stop();
    }
    if (visualState === "SPEAKING") {
      setVisualState("MIC_OFF");
    }
  }, [visualState]);

  // Start microphone capture & STT
  const startListening = useCallback(async () => {
    // 1. Interruption: cancel any active TTS immediately
    interruptSpeaking();
    setErrorMessage(null);
    setTranscript("");
    setInterimTranscript("");
    setVisualState("REQUESTING_PERMISSION");

    const t0 = performance.now();

    // 2. Explicit Browser Permission and Device Validation
    if (typeof navigator === "undefined" || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const err = "Microphone hardware capture API unsupported in this browser environment.";
      setErrorMessage(err);
      setVisualState("ERROR");
      if (onError) onError(err);
      return;
    }

    try {
      // Request permission with clean release to prevent resource leak
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const tPerm = performance.now() - t0;

      // Immediately stop temporary permission stream tracks
      stream.getTracks().forEach((track) => track.stop());

      setMetrics((m) => ({ ...m, permissionLatencyMs: Math.round(tPerm) }));
    } catch (err: any) {
      const permErr =
        err.name === "NotAllowedError" || err.name === "PermissionDeniedError"
          ? "Microphone access denied. Voice interface degraded; please use the text console."
          : `Microphone device error (${err.name || "Unknown"}). Defaulting to typed commands.`;

      setErrorMessage(permErr);
      setVisualState("ERROR");
      if (onError) onError(permErr);
      return;
    }

    // 3. Start STT recognition
    if (!sttProviderRef.current) {
      sttProviderRef.current = new WebSpeechSTTProvider();
    }

    startTimeRef.current = performance.now();
    setVisualState("LISTENING");

    sttProviderRef.current.start(
      (interim: string) => {
        setInterimTranscript(interim);
        setVisualState("TRANSCRIBING");
      },
      (final: string) => {
        const tEnd = performance.now();
        const duration = Math.round(tEnd - startTimeRef.current);
        setTranscript(final);
        setInterimTranscript("");
        setMetrics((m) => ({ ...m, sttLatencyMs: duration }));
        setVisualState("THINKING");

        if (onTranscriptComplete && final.trim()) {
          onTranscriptComplete(final.trim());
        }
      },
      (err: string) => {
        setErrorMessage(err);
        setVisualState("ERROR");
        if (onError) onError(err);
      }
    );
  }, [interruptSpeaking, onError, onTranscriptComplete]);

  // Stop STT listening explicitly
  const stopListening = useCallback(() => {
    if (sttProviderRef.current) {
      sttProviderRef.current.stop();
    }
    if (visualState === "LISTENING" || visualState === "TRANSCRIBING") {
      setVisualState("MIC_OFF");
    }
  }, [visualState]);

  // Speak response text via TTS
  const speak = useCallback(
    (
      text: string,
      onStartCallback?: () => void,
      onEndCallback?: () => void,
      onErrorCallback?: (err: any) => void
    ) => {
      if (isMuted) return;

      if (!ttsProviderRef.current) {
        ttsProviderRef.current = new WebSpeechTTSProvider();
      }

      const t0 = performance.now();

      ttsProviderRef.current.speak(
        text,
        () => {
          const tStart = performance.now() - t0;
          setMetrics((m) => ({ ...m, ttsLatencyMs: Math.round(tStart) }));
          setVisualState("SPEAKING");
          if (onStartCallback) onStartCallback();
        },
        () => {
          setVisualState("MIC_OFF");
          if (onEndCallback) onEndCallback();
        },
        (err: any) => {
          setVisualState("MIC_OFF");
          if (onErrorCallback) onErrorCallback(err);
        }
      );
    },
    [isMuted]
  );

  // Stop speaking explicitly
  const stopSpeaking = useCallback(() => {
    if (ttsProviderRef.current) {
      ttsProviderRef.current.stop();
    }
    setVisualState("MIC_OFF");
  }, []);

  // Mute control
  const setMuted = useCallback((muted: boolean) => {
    setIsMutedState(muted);
    if (ttsProviderRef.current) {
      ttsProviderRef.current.setMuted(muted);
    }
    if (muted && ttsProviderRef.current) {
      ttsProviderRef.current.stop();
    }
  }, []);

  return {
    visualState,
    setVisualState,
    transcript,
    interimTranscript,
    errorMessage,
    setErrorMessage,
    isMuted,
    setMuted,
    metrics,
    setMetrics,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    interruptSpeaking,
    isAvailable: typeof window !== "undefined" && "speechSynthesis" in window,
  };
}
