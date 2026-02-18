import type {
  LoginPayload,
  RegisterPayload,
  RegisterResponse,
  TokenResponse,
} from "@/types/auth";
import { client } from "./client";

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  try {
    const res = await client.post<TokenResponse>("/auth/login", payload);
    return res.data;
  } catch (err: any) {
    if (err.response && err.response.data) {
      throw err.response.data;
    }
    throw err;
  }
}

export async function register(
  payload: RegisterPayload,
): Promise<RegisterResponse> {
  try {
    const res = await client.post<RegisterResponse>("/auth/register", payload);
    return res.data;
  } catch (err: any) {
    if (err.response && err.response.data) {
      throw err.response.data;
    }
    throw err;
  }
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  try {
    const res = await client.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return res.data;
  } catch (err: any) {
    if (err.response && err.response.data) {
      throw err.response.data;
    }
    throw err;
  }
}
