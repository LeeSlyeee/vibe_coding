import { defineStore } from 'pinia';
import api from '@/api';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const AUTH_USER_KEY = 'auth_user';

function parseJson(value) {
    if (!value) {
        return null;
    }

    try {
        return JSON.parse(value);
    } catch {
        return null;
    }
}

function decodeJwtPayload(token) {
    if (!token) {
        return null;
    }

    const parts = token.split('.');
    if (parts.length < 2) {
        return null;
    }

    try {
        const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
        return JSON.parse(atob(padded));
    } catch {
        return null;
    }
}

function normalizeUser(payload, fallbackUsername = null) {
    if (!payload && !fallbackUsername) {
        return null;
    }

    const username =
        payload?.username ||
        payload?.user_name ||
        payload?.preferred_username ||
        fallbackUsername;

    return {
        id: payload?.user_id || payload?.id || null,
        username: username || null,
        first_name: payload?.first_name || null,
        email: payload?.email || null,
    };
}

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem(ACCESS_TOKEN_KEY) || null,
        user: parseJson(localStorage.getItem(AUTH_USER_KEY)),
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
    },
    actions: {
        initialize() {
            this.token = localStorage.getItem(ACCESS_TOKEN_KEY) || null;

            if (!this.token) {
                this.user = null;
                localStorage.removeItem(AUTH_USER_KEY);
                return;
            }

            const decodedUser = normalizeUser(decodeJwtPayload(this.token));
            const savedUser = parseJson(localStorage.getItem(AUTH_USER_KEY));
            this.user = decodedUser?.username ? decodedUser : savedUser;

            if (this.user) {
                localStorage.setItem(AUTH_USER_KEY, JSON.stringify(this.user));
            }
        },
        async login(username, password) {
            try {
                const response = await api.post('auth/login/', { username, password });
                const { access, refresh } = response.data;
                const user =
                    normalizeUser(response.data?.user, username) ||
                    normalizeUser(decodeJwtPayload(access), username) ||
                    { username };
                
                this.token = access;
                this.user = user;
                localStorage.setItem(ACCESS_TOKEN_KEY, access);
                localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));

                if (refresh) {
                    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
                } else {
                    localStorage.removeItem(REFRESH_TOKEN_KEY);
                }

                return true;
            } catch (error) {
                console.error('Login failed:', error);
                throw error;
            }
        },
        async register(userData) {
            try {
                await api.post('auth/register/', userData);
                return true;
            } catch (error) {
                throw error;
            }
        },
        async resetPassword(data) {
            try {
                await api.post('auth/reset-password/', data);
                return true;
            } catch (error) {
                throw error;
            }
        },
        async fetchCenters() {
            try {
                const response = await api.get('centers/list/');
                return response.data;
            } catch (error) {
                console.error('Failed to fetch centers:', error);
                return [];
            }
        },
        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem(ACCESS_TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            localStorage.removeItem(AUTH_USER_KEY);
        },
    },
});
