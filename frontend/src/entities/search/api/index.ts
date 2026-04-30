import { apiClient } from '@/shared/api/client';
import type {
  SearchRequest,
  TargetedSearchRequest,
  SearchResponse,
  SearchLockInfo,
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

export const searchApi = {
  classic: (params: SearchRequest) =>
    apiClient.get<SearchResponse>('/matching/search/classic', { params }),

  targeted: (params: TargetedSearchRequest) =>
    apiClient.get<SearchResponse>('/matching/search/targeted', {
      params,
      paramsSerializer: serializeParams,
    }),

  recommendations: (params?: { page?: number; limit?: number; city?: string }) =>
    apiClient.get<SearchResponse>('/matching/recommendations/targeted', { params }),

  lockStatus: () => apiClient.get<SearchLockInfo>('/matching/lock-status'),
};
