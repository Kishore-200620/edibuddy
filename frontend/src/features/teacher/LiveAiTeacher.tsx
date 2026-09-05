import { useState, useEffect, useRef } from 'react';
import { SimliClient } from 'simli-client';

interface LiveAiTeacherProps {
  audioUrl: string | null;
  onAudioOwnerChange: (owner: 'simli' | 'fallback') => void;
  audioEnabled: boolean;
}

export function LiveAiTeacher({ audioUrl, onAudioOwnerChange, audioEnabled }: LiveAiTeacherProps) {
  const [simliClient, setSimliClient] = useState<SimliClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Connecting to AI Teacher...');
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const loopRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Initialize Simli Client exactly once
  useEffect(() => {
    let activeClient: SimliClient | null = null;

    const initSimli = async () => {
      try {
        console.log("[EDUVA][Simli] session requested");
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/avatar/session`, {
          method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to create avatar session');
        
        const sessionData = await response.json();
        console.log("[EDUVA][Simli] session received");
        
        if (!videoRef.current || !audioRef.current) return;

        const client = new SimliClient(
          sessionData.session_token,
          videoRef.current,
          audioRef.current,
          sessionData.ice_servers
        );
        activeClient = client;

        console.log("[EDUVA][Simli] initializing");

        // @ts-expect-error SimliClientEvents may not be fully typed here
        client.on('connected', () => {
          console.log("[EDUVA][Simli] connected");
          setIsConnected(true);
          setStatus(''); // connected, hide status text
          onAudioOwnerChange('simli');
          
          // Attach media stream explicitly
          // @ts-expect-error accessing private connection property as per their SDK example
          if (client.connection?.signalingConnection?.mediaStream) {
            // @ts-expect-error
            const stream = client.connection.signalingConnection.mediaStream;
            console.log("[EDUVA][Simli] video stream received");
            
            // Explicit assignment for video track safety
            if (videoRef.current && videoRef.current.srcObject !== stream) {
              videoRef.current.srcObject = stream;
            }
            if (audioRef.current && audioRef.current.srcObject !== stream) {
              audioRef.current.srcObject = stream;
            }
            audioRef.current?.play().catch(e => console.error("[EDUVA][Simli] Audio playback failed:", e));
          }
        });

        // @ts-expect-error
        client.on('disconnected', () => {
          console.log("[EDUVA][Simli] disconnected");
          setIsConnected(false);
          setStatus('AI Teacher Disconnected. Voice continuing.');
          onAudioOwnerChange('fallback');
        });

        // @ts-expect-error
        client.on('failed', () => {
          console.log("[EDUVA][Simli] failed");
          setIsConnected(false);
          setStatus('AI Teacher Connection Failed. Voice continuing.');
          onAudioOwnerChange('fallback');
        });

        setStatus('Starting WebRTC stream...');
        await client.start();
        console.log("[EDUVA][Simli] initialized");
        setSimliClient(client);

      } catch (err: any) {
        console.error("[EDUVA][Simli] Initialization Error", err.message || err);
        setStatus('AI Teacher Video Unavailable. Voice continuing.');
        onAudioOwnerChange('fallback');
      }
    };

    initSimli();

    return () => {
      if (activeClient) {
        activeClient.stop();
      }
      if (loopRef.current) {
        clearInterval(loopRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, [onAudioOwnerChange]);

  // Handle PCM Conversion and Audio Chunking when audioUrl changes
  useEffect(() => {
    if (!audioUrl) return;
    
    // Stop previous loop
    if (loopRef.current) {
      clearInterval(loopRef.current);
      loopRef.current = null;
    }

    if (!audioEnabled) {
      return;
    }

    if (!isConnected || !simliClient) {
      // Fallback is already handled by parent/audioOwner logic
      return;
    }

    const processAndSendAudio = async () => {
      try {
        const fullAudioUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${audioUrl}`;
        const response = await fetch(fullAudioUrl);
        if (!response.ok) throw new Error('Audio fetch failed');
        const arrayBuffer = await response.arrayBuffer();

        if (!audioContextRef.current) {
          // @ts-expect-error
          audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        const audioBuffer = await audioContextRef.current!.decodeAudioData(arrayBuffer);
        
        // Resample to 16kHz Mono
        const targetSampleRate = 16000;
        const offlineCtx = new OfflineAudioContext(1, Math.ceil(audioBuffer.duration * targetSampleRate), targetSampleRate);
        const source = offlineCtx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(offlineCtx.destination);
        source.start(0);
        
        const renderedBuffer = await offlineCtx.startRendering();
        const float32Data = renderedBuffer.getChannelData(0);
        
        // Convert to PCM16
        const pcm16Data = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          const s = Math.max(-1, Math.min(1, float32Data[i]));
          pcm16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        const uint8Data = new Uint8Array(pcm16Data.buffer);
        
        const chunkSize = 6000; 
        const intervalMs = 187.5;
        let offset = 0;

        console.log("[EDUVA][Simli] audio sending started");

        loopRef.current = setInterval(() => {
          if (!isConnected || !simliClient || !audioEnabled) {
            if (loopRef.current) clearInterval(loopRef.current);
            loopRef.current = null;
            return;
          }
          
          if (offset >= uint8Data.length) {
            if (loopRef.current) clearInterval(loopRef.current);
            loopRef.current = null;
            return;
          }
          
          const chunk = uint8Data.slice(offset, offset + chunkSize);
          simliClient.sendAudioData(chunk);
          offset += chunkSize;
        }, intervalMs);

      } catch (err: any) {
        console.error("[EDUVA][Simli] Audio processing failed for Simli", err.message || err);
        // Inform parent to fallback to native audio element
        onAudioOwnerChange('fallback');
      }
    };

    processAndSendAudio();

    return () => {
      if (loopRef.current) {
        clearInterval(loopRef.current);
      }
    };
  }, [audioUrl, isConnected, simliClient, onAudioOwnerChange, audioEnabled]);

  return (
    <div style={{
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      marginBottom: '1rem',
      position: 'relative'
    }}>
      <div style={{
        width: '300px',
        height: '300px',
        backgroundColor: '#e2e8f0',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        {/* We keep audio/video tags regardless, they are needed for WebRTC track attachment */}
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline
          style={{ width: '100%', height: '100%', objectFit: 'cover', position: 'absolute', opacity: isConnected ? 1 : 0 }}
        />
        <audio ref={audioRef} autoPlay style={{ display: 'none' }} />

        {!isConnected && (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>
            <div style={{ marginBottom: '0.5rem', fontWeight: 500 }}>Live AI Teacher</div>
            <div style={{ fontSize: '0.875rem' }}>{status}</div>
          </div>
        )}
      </div>
    </div>
  );
}
