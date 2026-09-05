export interface TeacherState {
  student_id: number;
  topic: string;
  language: string;
  current_concept: string | null;
  mastery_score: number;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  teaching_strategy: 'direct_explanation' | 'guided_discovery' | 'socratic_questioning' | 'worked_example';
  current_phase: 'introduction' | 'explanation' | 'questioning' | 'feedback' | 'reteaching' | 'transition';
  last_question: string | null;
  last_answer: string | null;
  last_evaluation: {
    correctness: string;
    score: number;
    feedback: string;
    misconception: string | null;
  } | null;
  concepts_completed: string[];
  concepts_struggling: string[];
  needs_reteaching: boolean;
  attempt_count: number;
}

export interface VisualEvent {
  type: string; // e.g. "blackboard", "concept_map"
  content: string;
  title: string;
  url?: string | null;
}

export interface StartLessonRequest {
  student_id: number;
  topic: string;
  document_id?: number | null;
  language?: string | null;
}

export interface NextStepRequest {
  session_id: number;
  state: TeacherState;
}

export interface AnswerRequest {
  session_id: number;
  state: TeacherState;
  answer: string;
}

export interface LessonResponse {
  session_id: number;
  lesson_id?: number; // Present on start
  student_id?: number; // Present on start
  topic?: string; // Present on start
  action?: 'teaching' | 'completed' | string; 
  concept: string | null;
  teaching: string;
  question: string | null;
  visual: VisualEvent | null;
  audio_url: string | null;
  state: TeacherState;
  evaluation?: {
    correctness: string;
    score: number;
    feedback: string;
    misconception: string | null;
  }; // Present on answer
}

export interface DocumentUploadResponse {
  message: string;
  document_id: number;
  filename: string;
  status: string;
  chunks_created: number;
}
