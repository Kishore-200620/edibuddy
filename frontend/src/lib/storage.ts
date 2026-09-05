export interface LocalSession {
  session_id: number;
  topic: string;
  concept?: string | null;
  last_updated: string;
}

export interface LocalMaterial {
  document_id: number;
  filename: string;
  uploaded_at: string;
}

const STORAGE_KEYS = {
  SESSIONS: 'eduva_recent_sessions',
  MATERIALS: 'eduva_recent_materials'
};

export const storage = {
  getSessions: (): LocalSession[] => {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SESSIONS);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  saveSession: (session: LocalSession) => {
    try {
      const sessions = storage.getSessions();
      // Remove if it exists
      const filtered = sessions.filter(s => s.session_id !== session.session_id);
      // Add to front
      filtered.unshift({ ...session, last_updated: new Date().toISOString() });
      localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(filtered.slice(0, 10))); // Keep last 10
    } catch {
      // Ignore
    }
  },

  getMaterials: (): LocalMaterial[] => {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.MATERIALS);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  saveMaterial: (material: LocalMaterial) => {
    try {
      const materials = storage.getMaterials();
      // Remove if it exists
      const filtered = materials.filter(m => m.document_id !== material.document_id);
      // Add to front
      filtered.unshift({ ...material, uploaded_at: new Date().toISOString() });
      localStorage.setItem(STORAGE_KEYS.MATERIALS, JSON.stringify(filtered));
    } catch {
      // Ignore
    }
  }
};
