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
  partner_preferences?: string;
  online_only?: boolean;
}

export interface ProfilePreview {
  keycloak_id: string;
  first_name: string;
  last_name: string;
  gender: string;
  age: number;
  city: string;
  online: boolean;
  education?: string | null;
  hobbies?: string | null;
  about_me?: string | null;
  partner_preferences?: string | null;
}

export interface SearchResponse {
  search_session_id: number;
  profiles: ProfilePreview[];
  filters: Record<string, unknown>;
  created_at: string;
  current_page: number;
  total_pages: number;
  total_results: number;
  has_next: boolean;
  has_previous: boolean;
  locked_until?: string | null;
  time_until_unlock?: number | null;
  profiles_viewed: number;
}

export interface SearchLockInfo {
  search_type: string;
  is_locked: boolean;
  profiles_viewed: number;
  locked_until?: string | null;
  time_until_unlock?: number | null;
}
