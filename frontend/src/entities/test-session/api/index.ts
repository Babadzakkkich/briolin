import { apiClient } from '@/shared/api/client';
import type {
  TestStartResponse,
  AnswerSubmitResponse,
  TestCompleteResponse,
  TestHistory,
} from '../model/types';

export const testSessionApi = {
  getHistory: () => apiClient.get<TestHistory>('/tests/history'),

  start: () => apiClient.post<TestStartResponse>('/tests/start', {}),

  submitAnswer: (sessionId: string, questionId: string, answer: string | number | boolean) =>
    apiClient.post<AnswerSubmitResponse>(`/tests/${sessionId}/answers/${questionId}`, { answer }),

  complete: (sessionId: string) =>
    apiClient.post<TestCompleteResponse>(`/tests/${sessionId}/complete`, {}),
};
