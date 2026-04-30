export interface BasicProfileData {
  first_name: string;
  last_name: string;
  gender: string;
  date_of_birth: Date;
  city: string;
}

export interface DetailedProfileData {
  about_me: string;
  education: string;
  hobbies: string;
  partner_preferences: string;
  red_flags?: string[] | null;
}

export interface ProfileUpdateData {
  basic?: {
    first_name?: string;
    last_name?: string;
    gender?: string;
    date_of_birth?: string;
    city?: string;
  };
  detailed?: {
    about_me?: string;
    education?: string;
    hobbies?: string;
    partner_preferences?: string;
    red_flags?: string[] | null;
  };
}

export interface ProfileBasic {
  id: number;
  keycloak_id: string;
  first_name: string;
  last_name: string;
  gender: string;
  date_of_birth: string;
  city: string;
  online: boolean;
  avatar_url?: string | null;
  thumbnail_url?: string | null;
  created_at: string;
  updated_at: string;
  last_login_at: string;
}

export interface ProfileDetailed {
  id: number;
  about_me: string;
  education: string;
  hobbies: string;
  partner_preferences: string;
  red_flags?: string[] | null;
}

export interface ProfileQuestions {
  question_1: string;
  question_2: string;
  question_3: string;
  question_4: string;
  question_5: string;
  created_at?: string;
  updated_at?: string;
}

export interface QuestionsStatus {
  has_questions: boolean;
  questions_count: number;
  total_required: number;
  can_receive_likes: boolean;
}

export interface ProfileResponse {
  basic: ProfileBasic;
  detailed: ProfileDetailed | null;
  questions?: ProfileQuestions | null;
}
