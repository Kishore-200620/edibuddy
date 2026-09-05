import type { VisualEvent } from '../../types/api'
import { LiveAiTeacher } from './LiveAiTeacher'
import { useState, useRef, useEffect } from 'react';

interface AiTeacherWorkspaceProps {
  teachingText: string;
  visual: VisualEvent | null;
  audioUrl: string | null;
  audioEnabled: boolean;
}

export function AiTeacherWorkspace({ teachingText, visual, audioUrl, audioEnabled }: AiTeacherWorkspaceProps) {
  const [audioOwner, setAudioOwner] = useState<'simli' | 'fallback' | 'none'>('none');
  const fallbackAudioRef = useRef<HTMLAudioElement>(null);

  // Handle native fallback audio when audioOwner is 'fallback'
  useEffect(() => {
    if (audioOwner === 'fallback' && audioUrl && fallbackAudioRef.current && audioEnabled) {
      const fullAudioUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${audioUrl}`;
      if (fallbackAudioRef.current.src !== fullAudioUrl) {
        fallbackAudioRef.current.src = fullAudioUrl;
        fallbackAudioRef.current.play().catch(e => console.error("Fallback audio play failed", e));
      } else {
        fallbackAudioRef.current.play().catch(e => console.error("Fallback audio play failed", e));
      }
    } else if (fallbackAudioRef.current) {
      fallbackAudioRef.current.pause();
    }
  }, [audioOwner, audioUrl, audioEnabled]);
  // Parse Humanized Text safely
  let humanizedText = teachingText;
  
  if (humanizedText) {
    humanizedText = humanizedText.replace(/EXPLANATION:/g, "Alright, let's make this simple.");
    humanizedText = humanizedText.replace(/EXAMPLE:/g, "Here's an example.");
    humanizedText = humanizedText.replace(/QUESTION:/g, ""); // Usually pushed to Question area, but just hide the label if it leaks here
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1.5rem',
      padding: '2rem',
      flex: 1,
      overflowY: 'auto',
      backgroundColor: '#f8fafc'
    }}>
      {/* AI Teacher Avatar Area */}
      <LiveAiTeacher 
        audioUrl={audioUrl}
        onAudioOwnerChange={setAudioOwner}
        audioEnabled={audioEnabled}
      />
      <audio ref={fallbackAudioRef} style={{ display: 'none' }} />

      {/* Teaching Explanation */}
      {humanizedText && (
        <div style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
          lineHeight: 1.6,
          color: 'var(--text-primary)',
          fontSize: '1.05rem',
          whiteSpace: 'pre-wrap'
        }}>
          {humanizedText}
        </div>
      )}

      {/* Visual Event Rendering */}
      {visual && (
        <div style={{
          backgroundColor: '#1e293b',
          padding: '1.5rem',
          borderRadius: 'var(--radius-lg)',
          color: 'white',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          marginTop: '0.5rem'
        }}>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#94a3b8', marginBottom: '0.75rem' }}>
            {visual.type.replace('_', ' ')}
          </div>
          <h4 style={{ margin: '0 0 1rem 0', color: '#f8fafc', fontSize: '1.125rem' }}>{visual.title}</h4>
          
          <div style={{
            padding: '1rem',
            backgroundColor: '#0f172a',
            borderRadius: 'var(--radius-md)',
            fontFamily: visual.type === 'code' ? 'monospace' : 'inherit',
            whiteSpace: 'pre-wrap',
            lineHeight: 1.5,
            border: '1px solid #334155'
          }}>
            {visual.type === 'diagram' && visual.url ? (
              <img 
                src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${visual.url}`} 
                alt={visual.title || "Diagram"}
                style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }}
              />
            ) : visual.type === 'diagram' && visual.content.startsWith('/static/') ? (
              <img 
                src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${visual.content}`} 
                alt={visual.title}
                style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }}
              />
            ) : (
              visual.content
            )}
          </div>
        </div>
      )}
    </div>
  )
}
