import { apiClient } from '@/shared/api/client';
import type {
  MatchingSearchResponse,
  RecommendationsResponse,
  LikeAnswers,
  LikeWithAnswersResponse,
  PendingLike,
  Match,
  MatchWithAnswers,
  LikeUsage,
  MatchingLockInfo,
} from '../model/types';

function serializeParams(params: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      v.forEach((item) => parts.push(`${k}=${encodeURIComponent(String(item))}`));
    } else {
      parts.push(`${k}=${encodeURIComponent(String(v))}`);
    }
  }
  return parts.join('&');
}

export const matchingApi = {
  searchClassic: (params: {
    gender?: string;
    min_age?: number;
    max_age?: number;
    city?: string;
    page?: number;
    limit?: number;
  }) => apiClient.get<MatchingSearchResponse>('/matching/search/classic', { params }),

  searchTargeted: (params: {
    gender?: string;
    min_age?: number;
    max_age?: number;
    city?: string;
    page?: number;
    limit?: number;
    education?: string;
    hobbies_keywords?: string[];
    online_only?: boolean;
  }) =>
    apiClient.get<MatchingSearchResponse>('/matching/search/targeted', {
      params,
      paramsSerializer: serializeParams,
    }),

  getRecommendations: (params?: { page?: number; limit?: number; city?: string }) =>
    apiClient.get<RecommendationsResponse>('/matching/recommendations/targeted', { params }),

  likeWithAnswers: (targetUserId: string, answers: LikeAnswers) =>
    apiClient.post<LikeWithAnswersResponse>('/matching/like-with-answers', {
      target_user_id: targetUserId,
      answers,
    }),

  reverseLike: (fromUserId: string, answers: LikeAnswers) =>
    apiClient.post<LikeWithAnswersResponse>('/matching/reverse-like', {
      from_user_id: fromUserId,
      answers,
    }),

  declineLike: (fromUserId: string) =>
    apiClient.post<{ declined: boolean }>('/matching/decline-like', {
      from_user_id: fromUserId,
    }),

  dislike: (targetUserId: string) =>
    apiClient.post<{ match: boolean }>('/matching/dislike', { target_user_id: targetUserId }),

  getPendingLikes: (params?: { page?: number; limit?: number }) =>
    apiClient.get<PendingLike[]>('/matching/pending-likes', { params }),

  getMatches: (params?: { page?: number; limit?: number }) =>
    apiClient.get<Match[]>('/matching/matches', { params }),

  getMatchAnswers: (matchId: number) =>
    apiClient.get<MatchWithAnswers>(`/matching/matches/${matchId}/answers`),

  getLikeUsage: () => apiClient.get<LikeUsage>('/matching/like-usage'),

  getLockStatus: () => apiClient.get<MatchingLockInfo>('/matching/lock-status'),
};
