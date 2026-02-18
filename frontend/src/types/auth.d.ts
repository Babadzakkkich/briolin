export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  role: string[];
}

export interface RegisterResponse {
  id: number;
  keycloak_id: string;
  email: string;
  is_active: boolean;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
}
