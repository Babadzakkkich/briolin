import { apiClient } from '@/shared/api/client';

export interface BasicProfileData {
  first_name: string;
  last_name: string;
  gender: string;
  date_of_birth: Date;
  city: string;
}

export interface ProfileResponse {
  basic: {
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
  };
  detailed: {
    id: number;
    about_me: string;
    education: string;
    hobbies: string;
    partner_preferences: string;
  } | null;
}

export const profileApi = {
  createBasicProfile: (data: BasicProfileData) => apiClient.post('/api/v1/profiles/basic', data),
  getMe: () => apiClient.get<ProfileResponse>('/api/v1/profiles/me'),
};
