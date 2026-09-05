import { useState, useEffect } from 'react';
import { eduvaApi } from '../../lib/api';
import type { LocalSession } from '../../lib/storage';

interface LessonHistoryProps {
  onContinueSession: (sessionId: number) => void;
  disabled?: boolean;
}

export function LessonHistory({ onContinueSession, disabled }: LessonHistoryProps) {
  const [sessions, setSessions] = useState<LocalSession[]>([]);

  useEffect(() => {
    // Fetch from backend API using default student ID (e.g. 2 for development)
    eduvaApi.getSessions(2).then(data => {
      setSessions(data);
    }).catch(err => console.error("Failed to fetch sessions", err));
  }, []);

  return (
    <div className="sidebar-section">
      <h3 className="sidebar-title">Continue Learning</h3>
      
      {sessions.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.5, padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', textAlign: 'center' }}>
          No lessons yet. <br/>Choose a topic to start learning.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {sessions.map(sess => (
            <div key={sess.session_id} style={{ padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                {sess.topic}
              </div>
              {sess.concept && (
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Current: {sess.concept}
                </div>
              )}
              <button 
                onClick={() => onContinueSession(sess.session_id)}
                disabled={disabled}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: 'white',
                  border: '1px solid var(--primary-color)',
                  color: 'var(--primary-color)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  opacity: disabled ? 0.7 : 1
                }}
              >
                Continue →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
