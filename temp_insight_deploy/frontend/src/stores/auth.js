import { defineStore } from 'pinia';
import api from '@/api';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('access_token') || null,
        user: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
    },
    actions: {
        async login(username, password) {
            try {
                const response = await api.post('auth/login/', { username, password });
                const { access, refresh } = response.data;
                
                this.token = access;
                localStorage.setItem('access_token', access);
                localStorage.setItem('refresh_token', refresh);
                
                // TODO: 사용자 정보 가져오기 API 호출 필요
                this.user = { username }; 
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
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        },
    },
});
