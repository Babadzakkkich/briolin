export type UserRole = 'admin' | 'psychologist' | 'user';

export interface AccountResponse {
  id: number;
  keycloak_id: string;
  username: string;
  email: string;
  roles: UserRole[];
  is_active: boolean;
  is_test_passed: boolean;
  created_at: string;
}

export interface AccountUpdateData {
  username?: string;
  email?: string;
}
