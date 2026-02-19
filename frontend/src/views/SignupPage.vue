<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card card">
        <div class="signup-header">
          <h2 class="signup-title">새로운 여정을 위해</h2>
          <h2 class="signup-subtitle">함께 기록을 해주세요!</h2>
        </div>
        
        <form @submit.prevent="handleSignup" class="auth-form">
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

          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>
          
          <button 
            type="submit" 
            class="btn btn-primary btn-large"
            :disabled="loading"
          >
            {{ loading ? '처리 중...' : '회원가입하기' }}
          </button>
          
          <div class="auth-link">
            이미 계정이 있으신가요? 
            <router-link to="/login">로그인하기</router-link>
          </div>
        </form>

        <div class="auth-footer">
          <p>© 2026 maumON. All rights reserved.</p>
          <p class="footer-credit">Design by Youngjae</p>
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
  name: 'SignupPage',
  setup() {
    const router = useRouter()
    const userId = ref('')
    const password = ref('')
    const loading = ref(false)
    const errorMessage = ref('')
    const successMessage = ref('')

    const handleSignup = async () => {
      errorMessage.value = ''
      successMessage.value = ''
      loading.value = true

      try {
        await authAPI.signup(userId.value, password.value)
        
        successMessage.value = '회원가입이 완료되었습니다! 로그인 페이지로 이동합니다...'
        
        // 2초 후 로그인 페이지로 이동
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      } catch (error) {
        console.error('Signup failed:', error)
        errorMessage.value = error.response?.data?.message || '회원가입에 실패했습니다.'
        loading.value = false
      }
    }

    return {
      userId,
      password,
      loading,
      errorMessage,
      successMessage,
      handleSignup
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

.signup-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.signup-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--color-text);
}

.signup-subtitle {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}

.signup-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin-top: 8px;
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

.success-message {
  color: #4CAF50;
  font-size: 13px;
  text-align: center;
  padding: var(--spacing-sm);
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: var(--radius-sm);
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
  color: var(--color-text-light);
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
