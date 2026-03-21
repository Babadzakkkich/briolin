import { apiClient } from '@/shared/api/client';

export interface AnswerOption {
  id: string;
  text: string;
  score: number;
}

export interface Question {
  id: string;
  text: string;
  question_type: 'multiple_choice' | 'likert_scale' | 'true_false';
  options: AnswerOption[];
  min_value?: number;
  max_value?: number;
  labels?: Record<string, string>;
}

export interface TestStartResponse {
  session_id: string;
  test_name: string;
  description: string;
  time_limit_minutes: number;
  questions: Question[];
}

export interface AnswerSubmitResponse {
  session_id: string;
  question_id: string;
  answer_saved: boolean;
  total_answered: number;
  total_questions: number;
}

export interface TestCompleteResponse {
  session_id: string;
  results: {
    total_score: number;
    max_possible_score: number;
    percentage: number;
    passed: boolean;
  };
}

export const testingApi = {
  start: () =>
    apiClient.post<TestStartResponse>('/api/v1/tests/start', {}),

  submitAnswer: (sessionId: string, questionId: string, answer: string | number | boolean) =>
    apiClient.post<AnswerSubmitResponse>(
      `/api/v1/tests/${sessionId}/answers/${questionId}`,
      { answer },
    ),

  complete: (sessionId: string) =>
    apiClient.post<TestCompleteResponse>(`/api/v1/tests/${sessionId}/complete`, {}),
};
