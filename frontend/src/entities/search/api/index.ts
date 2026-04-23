import { apiClient } from '@/shared/api/client';
import type {
  SearchRequest,
  TargetedSearchRequest,
  SearchResponse,
  SearchLockInfo,
} from '../model/types';

export const searchApi = {
  classic: (data: SearchRequest) => apiClient.post<SearchResponse>('/search/classic', data),

  targeted: (data: TargetedSearchRequest) =>
    apiClient.post<SearchResponse>('/search/targeted', data),

  lockStatus: () => apiClient.get<SearchLockInfo>('/search/lock-status'),
};
