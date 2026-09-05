import { useState, useRef, useEffect } from 'react';
import { eduvaApi } from '../../lib/api';
import { storage } from '../../lib/storage';
import type { LocalMaterial } from '../../lib/storage';

interface MaterialListProps {
  onSelectMaterial: (documentId: number, filename: string) => void;
  disabled?: boolean;
}

export function MaterialList({ onSelectMaterial, disabled }: MaterialListProps) {
  const [materials, setMaterials] = useState<LocalMaterial[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMaterials(storage.getMaterials());
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Only PDF files are supported.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const response = await eduvaApi.uploadDocument(file);
      const newMaterial: LocalMaterial = {
        document_id: response.document_id,
        filename: response.filename,
        uploaded_at: new Date().toISOString()
      };
      storage.saveMaterial(newMaterial);
      setMaterials(storage.getMaterials());
      
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'PDF upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="sidebar-section">
      <h3 className="sidebar-title">My Materials</h3>
      
      <div style={{ marginBottom: '1rem' }}>
        <input 
          type="file" 
          accept=".pdf" 
          ref={fileInputRef}
          onChange={handleFileChange}
          style={{ display: 'none' }} 
          disabled={isUploading || disabled}
        />
        <button 
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading || disabled}
          style={{
            width: '100%',
            padding: '0.75rem',
            backgroundColor: '#f1f5f9',
            border: '1px dashed #cbd5e1',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            cursor: (isUploading || disabled) ? 'not-allowed' : 'pointer',
            opacity: (isUploading || disabled) ? 0.7 : 1
          }}
        >
          {isUploading ? 'Uploading PDF...' : 'Upload PDF'}
        </button>
        {error && <div style={{ marginTop: '0.5rem', color: 'var(--danger-color)', fontSize: '0.875rem' }}>{error}</div>}
      </div>

      {materials.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.5, padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', textAlign: 'center' }}>
          No materials yet. <br/>Upload a PDF to start learning from your own material.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {materials.map((mat) => (
            <div key={mat.document_id} style={{ padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {mat.filename}
              </div>
              <button 
                onClick={() => onSelectMaterial(mat.document_id, mat.filename)}
                disabled={isUploading || disabled}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: 'white',
                  border: '1px solid var(--primary-color)',
                  color: 'var(--primary-color)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                  cursor: (isUploading || disabled) ? 'not-allowed' : 'pointer',
                }}
              >
                Select Context
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
