import { apiClient } from '@/shared/api/client';

export interface BasicProfileData {
  first_name: string;
  last_name: string;
  gender: string;
  date_of_birth: Date;
  city: string;
}

export const profileApi = {
  createBasicProfile: (data: BasicProfileData) => apiClient.post('/api/v1/profiles/basic', data),
  getMe: () => apiClient.get('/api/v1/profiles/me'),
};
