import { apiClient } from '@/shared/api/client';
import type {
  TestStartResponse,
  CurrentTestResponse,
  AnswerSubmitResponse,
  TestCompleteResponse,
  TestHistory,
  UserTestStatistics,
} from '../model/types';

export const testSessionApi = {
  getHistory: () => apiClient.get<TestHistory>('/tests/history'),

  getStatistics: () => apiClient.get<UserTestStatistics>('/tests/statistics'),

  start: (signal?: AbortSignal) =>
    apiClient.post<TestStartResponse>('/tests/start', {}, { signal }),

  getCurrent: (signal?: AbortSignal) =>
    apiClient.get<CurrentTestResponse>('/tests/current', { signal }),

  submitAnswer: (sessionId: string, questionId: string, answer: string | number | boolean) =>
    apiClient.post<AnswerSubmitResponse>(`/tests/${sessionId}/answers/${questionId}`, { answer }),

  complete: (sessionId: string) =>
    apiClient.post<TestCompleteResponse>(`/tests/${sessionId}/complete`, {}),
};
