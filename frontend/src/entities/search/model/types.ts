export interface ProfilePreview {
  keycloak_id: string;
  display_name: string;
  age: number;
  city: string;
  avatar_url?: string | null;
  online?: boolean;
  education?: string | null;
  hobbies?: string | null;
  about_me?: string | null;
  partner_preferences?: string | null;
  red_flags?: string[] | null;
  similarity?: number;
  combined_score?: number;
}

export interface SearchPagination {
  current_page: number;
  total_pages: number;
  total_results: number;
  page_size: number;
}

export interface SearchRequest {
  gender?: string;
  min_age?: number;
  max_age?: number;
  city?: string;
  page?: number;
  limit?: number;
}

export interface TargetedSearchRequest extends SearchRequest {
  education?: string;
  hobbies_keywords?: string[];
  online_only?: boolean;
}

export interface SearchResponse {
  profiles: ProfilePreview[];
  pagination: SearchPagination;
  lock_info?: SearchLockInfo;
  applied_filters?: Record<string, unknown>;
  sentiment_boost_applied?: boolean;
}

export interface SearchLockInfo {
  is_locked: boolean;
  profiles_viewed: number;
  daily_limit?: number;
  locked_until?: string | null;
  time_until_unlock?: number | null;
}
