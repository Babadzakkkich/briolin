import { create } from 'zustand';

interface JwtPayload {
    sub?: string;
    preferred_username?: string;
    email?: string;
    given_name?: string;
    family_name?: string;
}

const decodeJwt = (token: string): JwtPayload | null => {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch {
        return null;
    }
};

interface AuthState {
    accessToken: string | null;
    username: string | null;
    isAuthenticated: boolean;
    setAccessToken: (token: string | null) => void;
    clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    accessToken: null,
    username: null,
    isAuthenticated: false,
    setAccessToken: (token) => {
        const payload = token ? decodeJwt(token) : null;
        set({
            accessToken: token,
            isAuthenticated: !!token,
            username: payload?.preferred_username ?? null,
        });
    },
    clear: () => set({ accessToken: null, isAuthenticated: false, username: null }),
}));
