import { apiClient } from '@/shared/api/client';
import type {
  TestStartResponse,
  AnswerSubmitResponse,
  TestCompleteResponse,
  TestHistory,
} from '../model/types';

export const testSessionApi = {
  getHistory: () => apiClient.get<TestHistory>('/api/v1/tests/history'),

  start: () => apiClient.post<TestStartResponse>('/api/v1/tests/start', {}),

  submitAnswer: (sessionId: string, questionId: string, answer: string | number | boolean) =>
    apiClient.post<AnswerSubmitResponse>(
      `/api/v1/tests/${sessionId}/answers/${questionId}`,
      { answer },
    ),

  complete: (sessionId: string) =>
    apiClient.post<TestCompleteResponse>(`/api/v1/tests/${sessionId}/complete`, {}),
};
