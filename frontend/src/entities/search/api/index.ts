import { apiClient } from '@/shared/api/client';
import type { SearchRequest, TargetedSearchRequest, SearchResponse, SearchLockInfo } from '../model/types';

export const searchApi = {
  classic: (data: SearchRequest) =>
    apiClient.post<SearchResponse>('/api/v1/search/classic', data),

  targeted: (data: TargetedSearchRequest) =>
    apiClient.post<SearchResponse>('/api/v1/search/targeted', data),

  lockStatus: () =>
    apiClient.get<SearchLockInfo>('/api/v1/search/lock-status'),
};
