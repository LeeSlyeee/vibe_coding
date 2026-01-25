<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card card">
        <h1 class="auth-title">MOOD DIARY</h1>
        
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="test-account-info">
             <p>Test Account: <strong>test</strong> / <strong>12qw</strong></p>
          </div>

          <div class="form-group">
            <input
              v-model="userId"
              type="text"
              class="input"
              placeholder="아이디 입력"
              required
            />
          </div>
          
          <div class="form-group">
            <input
              v-model="password"
              type="password"
              class="input"
              placeholder="비밀번호 입력"
              required
            />
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
          
          <button 
            type="submit" 
            class="btn btn-primary btn-large"
            :disabled="loading"
          >
            {{ loading ? '로그인 중...' : '로그인' }}
          </button>
          
          <div class="auth-link">
            <router-link to="/signup">회원가입하기</router-link>
          </div>
        </form>

        <div class="auth-footer">
          <p>© 2026 Slyeee. All rights reserved.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../services/api'

export default {
  name: 'LoginPage',
  setup() {
    const router = useRouter()
    const userId = ref('')
    const password = ref('')
    const loading = ref(false)
    const errorMessage = ref('')

    const handleLogin = async () => {
      errorMessage.value = ''
      loading.value = true

      try {
        const response = await authAPI.login(userId.value, password.value)
        
        // 토큰 저장 (백엔드는 access_token으로 반환)
        localStorage.setItem('authToken', response.access_token || response.token || 'demo-token')
        
        // 캘린더 페이지로 이동
        router.push('/calendar')
      } catch (error) {
        console.error('Login failed:', error)
        errorMessage.value = error.response?.data?.message || '로그인에 실패했습니다.'
      } finally {
        loading.value = false
      }
    }

    return {
      userId,
      password,
      loading,
      errorMessage,
      handleLogin
    }
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background-color: var(--bg-primary);
}

.auth-container {
  width: 100%;
  max-width: 400px;
}

.auth-card {
  padding: var(--spacing-xl);
}

.auth-title {
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  margin-bottom: var(--spacing-xl);
  letter-spacing: 0.5px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  width: 100%;
}

.error-message {
  color: #FF6B6B;
  font-size: 13px;
  text-align: center;
  padding: var(--spacing-sm);
  background-color: rgba(255, 107, 107, 0.1);
  border-radius: var(--radius-sm);
}

.test-account-info {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 12px;
  border-radius: var(--radius-sm);
  text-align: center;
  font-size: 13px;
  margin-bottom: 8px;
}

.btn-large {
  width: 100%;
  margin-top: var(--spacing-sm);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-link {
  text-align: center;
  margin-top: var(--spacing-md);
  font-size: 14px;
}

.auth-footer {
  margin-top: var(--spacing-xl);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.auth-footer p {
  font-size: 12px;
  color: var(--color-text-light);
  margin: 4px 0;
}

.footer-credit {
  font-style: italic;
}
</style>
