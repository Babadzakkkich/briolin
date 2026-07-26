import type { UserRole } from '@/entities/account';

export interface AdminUser {
  id: number;
  keycloak_id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_test_passed: boolean;
  roles: UserRole[];
  created_at: string;
}

export interface AdminUserList {
  users: AdminUser[];
  total: number;
  page: number;
  size: number;
}

export interface AdminProfileBasic {
  first_name: string;
  last_name: string;
  city: string;
  date_of_birth: string;
}

export interface AdminProfileResponse {
  basic: AdminProfileBasic;
}

export interface MatchingResetResponse {
  message: string;
  swipes_deleted: number;
}
