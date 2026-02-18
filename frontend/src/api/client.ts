import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
} from "@/utils/tokenStorage";
import axios, { type InternalAxiosRequestConfig } from "axios";
import { refresh } from "./auth";

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const client = axios.create({
  baseURL: BASE_URL,
});

axios.interceptors.request.use(
  function (config): InternalAxiosRequestConfig<any> {
    const accessToken = getAccessToken();
    if (!accessToken) return config;

    config.headers.Authorization = `Bearer ${accessToken}`;

    return config;
  },
);

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      let accessToken;
      let refreshToken = getRefreshToken();

      try {
        if (!refreshToken) throw "Unauthorized";
        const res = await refresh(refreshToken);

        accessToken = res.access_token;

        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return client(originalRequest);
      } catch (refreshError) {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
