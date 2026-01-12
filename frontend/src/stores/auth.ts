import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'));
  const user = ref<string | null>(localStorage.getItem('user'));

  const isAuthenticated = computed(() => !!token.value);

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/login', { username, password });
      token.value = response.data.access_token;
      user.value = response.data.username;
      
      if (token.value) {
        localStorage.setItem('token', token.value);
        localStorage.setItem('user', user.value || '');
      }
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const register = async (username: string, password: string) => {
    try {
      await api.post('/register', { username, password });
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
  };

  const logout = () => {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return { token, user, isAuthenticated, login, register, logout };
});
