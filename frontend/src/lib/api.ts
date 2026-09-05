import type { StartLessonRequest, NextStepRequest, AnswerRequest, LessonResponse, DocumentUploadResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
  public status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `API Request failed with status ${response.status}`
    );
  }

  return response.json();
}

export const eduvaApi = {
  startLesson: (data: StartLessonRequest) => 
    fetchApi<LessonResponse>('/lessons/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  nextStep: (data: NextStepRequest) =>
    fetchApi<LessonResponse>('/lessons/next', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  submitAnswer: (data: AnswerRequest) =>
    fetchApi<LessonResponse>('/lessons/answer', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  recoverSession: (sessionId: number) =>
    fetchApi<LessonResponse>(`/lessons/session/${sessionId}`, {
      method: 'GET',
    }),

  getSessions: (studentId: number) =>
    fetchApi<import('./storage').LocalSession[]>(`/lessons/sessions/${studentId}`, {
      method: 'GET',
    }),

  changeLanguage: (sessionId: number, language: string) =>
    fetchApi<LessonResponse>(`/lessons/session/${sessionId}/language`, {
      method: 'POST',
      body: JSON.stringify({ language }),
    }),

  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // We can't use fetchApi because it sets Content-Type to application/json by default
    // For FormData, we must let the browser set the Content-Type with boundary automatically
    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.detail || `Upload failed with status ${response.status}`
      );
    }
    
    return response.json() as Promise<DocumentUploadResponse>;
  },
};
