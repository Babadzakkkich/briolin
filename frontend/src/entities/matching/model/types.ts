export interface MatchingProfilePreview {
  keycloak_id: string;
  display_name: string;
  age: number;
  city: string;
  avatar_url?: string | null;
  education?: string | null;
  hobbies?: string | null;
  about_me?: string | null;
  partner_preferences?: string | null;
  red_flags?: string[] | null;
  similarity?: number;
  combined_score?: number;
}

export interface MatchingPagination {
  current_page: number;
  total_pages: number;
  total_results: number;
  page_size: number;
}

export interface MatchingLockInfo {
  is_locked: boolean;
  profiles_viewed: number;
  daily_limit: number;
  locked_until: string | null;
  time_until_unlock: number | null;
}

export interface MatchingSearchResponse {
  profiles: MatchingProfilePreview[];
  pagination: MatchingPagination;
}

export interface RecommendationsResponse {
  profiles: MatchingProfilePreview[];
  pagination: MatchingPagination;
  lock_info: MatchingLockInfo;
  applied_filters: Record<string, unknown>;
  sentiment_boost_applied: boolean;
}

export interface LikeAnswers {
  question_1: string;
  question_2: string;
  question_3: string;
  question_4: string;
  question_5: string;
}

export interface LikeWithAnswersResponse {
  status: 'liked' | 'matched';
  message: string;
  match_id: number | null;
  regular_match_id?: number;
  show_answers: boolean;
  answers?: {
    my_answers: LikeAnswers;
    my_questions: LikeAnswers;
    partner_answers: LikeAnswers;
    partner_questions: LikeAnswers;
  };
}

export interface PendingLike {
  from_user_id: string;
  from_user_display_name: string;
  from_user_age: number;
  from_user_city: string;
  from_user_avatar: string | null;
  from_user_about_me: string | null;
  from_user_hobbies: string | null;
  from_user_red_flags: string[] | null;
  from_user_partner_preferences: string | null;
  answers: LikeAnswers;
  questions: LikeAnswers;
  created_at: string;
}

export interface MatchPartner {
  keycloak_id: string;
  display_name: string;
  avatar_url: string | null;
}

export interface Match {
  match_id: number;
  partner: MatchPartner;
  matched_at: string;
}

export interface MatchWithAnswers {
  match_id: number;
  partner: MatchPartner;
  matched_at: string;
  my_answers: LikeAnswers;
  my_questions: LikeAnswers;
  partner_answers: LikeAnswers;
  partner_questions: LikeAnswers;
}

export interface LikeUsage {
  likes_used_today: number;
  daily_like_limit: number;
  likes_remaining: number;
}
