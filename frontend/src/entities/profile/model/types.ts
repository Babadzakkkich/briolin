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
}

export interface ProfileResponse {
  basic: ProfileBasic;
  detailed: ProfileDetailed | null;
}
