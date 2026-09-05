import { useState } from 'react';
import { MainLayout } from './layouts/MainLayout'
import { MaterialList } from './features/materials/MaterialList'
import { LessonHistory } from './features/lessons/LessonHistory'
import { ConceptTracker } from './features/concepts/ConceptTracker'
import { StudentStateHeader } from './features/student/StudentStateHeader'
import { AiTeacherWorkspace } from './features/teacher/AiTeacherWorkspace'
import { QuestionAnswerArea } from './features/interaction/QuestionAnswerArea'
import type { LessonResponse, TeacherState } from './types/api'
import { eduvaApi } from './lib/api'
import { storage } from './lib/storage'

export default function App() {
  const [currentView, setCurrentView] = useState<'home' | 'learning_studio'>('home');
  const [sessionData, setSessionData] = useState<LessonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Global settings
  const [language, setLanguage] = useState<'English' | 'Tamil' | 'Hindi'>('English');
  const [audioEnabled, setAudioEnabled] = useState(true);

  // Home screen state
  const [topic, setTopic] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<{id: number, filename: string} | null>(null);

  // Fallback to 2 if not set in environment
  const studentId = parseInt(import.meta.env.VITE_DEV_STUDENT_ID || '2', 10);

  const handleStartLesson = async () => {
    const finalTopic = topic.trim();
    if (!finalTopic) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await eduvaApi.startLesson({
        student_id: studentId,
        topic: finalTopic,
        document_id: selectedDocument?.id,
        language: language
      });
      setSessionData(response);
      
      // Save minimal metadata to local storage
      storage.saveSession({
        session_id: response.session_id,
        topic: response.topic || finalTopic || 'Lesson',
        concept: response.concept,
        last_updated: new Date().toISOString()
      });
      
      setCurrentView('learning_studio');
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'Failed to start lesson');
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinueSession = async (sessionId: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await eduvaApi.recoverSession(sessionId);
      setSessionData(response);
      setCurrentView('learning_studio');
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'Failed to restore lesson. It may have expired or been deleted.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerSubmit = async (answer: string) => {
    if (!sessionData) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await eduvaApi.submitAnswer({
        session_id: sessionData.session_id,
        state: { ...sessionData.state, language: language },
        answer: answer
      });
      setSessionData(response);
      
      // Update local storage concept state
      storage.saveSession({
        session_id: response.session_id,
        topic: response.topic || sessionData.topic || 'Lesson',
        concept: response.concept,
        last_updated: new Date().toISOString()
      });
      
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'Failed to submit answer');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLanguageChange = async (newLang: 'English' | 'Tamil' | 'Hindi') => {
    setLanguage(newLang);
    if (!sessionData) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await eduvaApi.changeLanguage(sessionData.session_id, newLang);
      setSessionData(response);
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'Failed to change language');
    } finally {
      setIsLoading(false);
    }
  };

  const activeState: Partial<TeacherState> = sessionData?.state || {};

  const sidebarContent = (
    <>
      <MaterialList 
        onSelectMaterial={(docId, filename) => setSelectedDocument({ id: docId, filename })} 
        disabled={isLoading} 
      />
      <LessonHistory onContinueSession={handleContinueSession} disabled={isLoading} />
      <ConceptTracker state={activeState} />
    </>
  );

  if (currentView === 'home') {
    return (
      <MainLayout
        sidebarContent={sidebarContent}
        headerContent={<div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>EDUVA</div>}
        interactionContent={null}
      >
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          padding: '2rem',
          position: 'relative'
        }}>
          {isLoading && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, margin: '1rem', color: 'var(--primary-color)', backgroundColor: '#eff6ff', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid #bfdbfe', textAlign: 'center' }}>
              Loading lesson...
            </div>
          )}
          
          {selectedDocument && (
            <div style={{
              marginBottom: '1.5rem',
              padding: '0.75rem 1rem',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              width: '100%',
              maxWidth: '500px'
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                  Supporting Material
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--primary-color)' }}>
                  {selectedDocument.filename}
                </div>
              </div>
              <button
                onClick={() => setSelectedDocument(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  fontSize: '1.25rem',
                  lineHeight: 1
                }}
                title="Remove"
              >
                ×
              </button>
            </div>
          )}
          
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1.5rem' }}>
            What do you want to learn?
          </h2>
          
          <div style={{ display: 'flex', gap: '0.5rem', width: '100%', maxWidth: '500px' }}>
            <input 
              type="text" 
              placeholder="e.g. Binary Search" 
              value={topic} 
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleStartLesson()}
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                fontSize: '1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                outline: 'none',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
              }}
            />
            <button 
              onClick={() => handleStartLesson()}
              disabled={isLoading || !topic.trim()}
              style={{
                padding: '0.75rem 1.5rem',
                fontSize: '1rem',
                fontWeight: 600,
                backgroundColor: 'var(--primary-color)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: isLoading || !topic.trim() ? 'not-allowed' : 'pointer',
                opacity: isLoading || !topic.trim() ? 0.7 : 1
              }}
            >
              Start Learning
            </button>
          </div>
          
          {error && (
            <div style={{ marginTop: '1rem', color: 'var(--danger-color)', backgroundColor: '#fef2f2', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid #fecaca', width: '100%', maxWidth: '500px' }}>
              {error}
            </div>
          )}
        </div>
      </MainLayout>
    );
  }

  // Learning Studio View
  return (
    <MainLayout
      sidebarContent={sidebarContent}
      headerContent={
        <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <button 
            onClick={() => {
              setCurrentView('home');
              setSessionData(null);
            }}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginRight: 'auto'
            }}
          >
            ← Back to Learning
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginRight: '1rem' }}>
            <button
              onClick={() => setAudioEnabled(!audioEnabled)}
              style={{
                padding: '0.5rem 0.75rem',
                backgroundColor: audioEnabled ? '#e0f2fe' : '#f1f5f9',
                border: '1px solid',
                borderColor: audioEnabled ? '#bae6fd' : '#cbd5e1',
                borderRadius: 'var(--radius-md)',
                color: audioEnabled ? '#0284c7' : '#64748b',
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.875rem'
              }}
            >
              {audioEnabled ? '🔊 Audio On' : '🔇 Audio Off'}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Language:</span>
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value as 'English' | 'Tamil' | 'Hindi')}
                style={{
                  padding: '0.4rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'white',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <option value="English">English</option>
                <option value="Tamil">தமிழ்</option>
                <option value="Hindi">हिन्दी</option>
              </select>
            </div>
          </div>
          <StudentStateHeader state={activeState} />
        </div>
      }
      interactionContent={
        <QuestionAnswerArea 
          question={sessionData?.question || null}
          onSubmit={handleAnswerSubmit}
          disabled={isLoading || !sessionData?.question}
        />
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
        {error && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, margin: '1rem', color: 'var(--danger-color)', backgroundColor: '#fef2f2', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid #fecaca' }}>
            {error}
          </div>
        )}
        
        {sessionData && (
          <AiTeacherWorkspace 
            teachingText={sessionData.teaching || ''}
            visual={sessionData.visual || null}
            audioUrl={sessionData.audio_url || null}
            audioEnabled={audioEnabled}
          />
        )}
        
        {isLoading && (
          <div style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ padding: '0.5rem 1rem', backgroundColor: 'white', borderRadius: 'var(--radius-md)', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', color: 'var(--primary-color)', fontWeight: 500 }}>
              Thinking...
            </span>
          </div>
        )}
      </div>
    </MainLayout>
  )
}
