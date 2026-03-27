export interface JwtPayload {
  sub?: string;
  preferred_username?: string;
  email?: string;
  given_name?: string;
  family_name?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterResponse {
  status: string;
  saga_id: string;
  check_status_url: string;
}
