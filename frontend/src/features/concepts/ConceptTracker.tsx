import type { TeacherState } from '../../types/api'

interface ConceptTrackerProps {
  state: Partial<TeacherState>;
}

export function ConceptTracker({ state }: ConceptTrackerProps) {
  const hasConcepts = (state.concepts_completed && state.concepts_completed.length > 0) ||
                      state.current_concept ||
                      (state.concepts_struggling && state.concepts_struggling.length > 0);

  return (
    <div className="sidebar-section" style={{ flex: 1 }}>
      <h3 className="sidebar-title">Concepts</h3>
      
      {!hasConcepts ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.5, padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', textAlign: 'center' }}>
          No concepts tracked yet.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {state.concepts_completed?.map((concept, i) => (
            <div key={`completed-${i}`} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--success-color)' }}></div>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{concept}</span>
            </div>
          ))}

          {state.current_concept && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem', backgroundColor: '#eff6ff', borderRadius: 'var(--radius-md)', border: '1px solid #bfdbfe' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--primary-color)' }}></div>
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>{state.current_concept}</span>
            </div>
          )}

          {state.concepts_struggling?.map((concept, i) => (
            <div key={`struggling-${i}`} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--warning-color)' }}></div>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{concept}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
