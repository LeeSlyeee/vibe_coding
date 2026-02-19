<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card card">
        <h1 class="auth-title">maumON</h1>
        
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

          <!-- 기관 코드 입력 (선택, 토글형) -->
          <div class="center-code-toggle" style="text-align: right; margin-bottom: 8px;">
              <span @click="showCenterInput = !showCenterInput" class="toggle-link" style="font-size: 13px; color: #5856d6; cursor: pointer;">
                  {{ showCenterInput ? '입력창 닫기' : '기관 코드가 있으신가요?' }}
              </span>
          </div>

          <div class="form-group" v-if="showCenterInput">
            <input
              v-model="centerCode"
              type="text"
              class="input"
              placeholder="기관 코드 (선택: 보건소/병원)"
              style="border-color: #5856d6; background-color: #f5f5ff;"
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
          <p>© 2026 maumON. All rights reserved.</p>
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
    const centerCode = ref('') // New
    const showCenterInput = ref(false) // Toggle
    const loading = ref(false)
    const errorMessage = ref('')

    const handleLogin = async () => {
      errorMessage.value = ''
      loading.value = true

      // 로그인 시도 전 기존 세션 데이터 정리
      localStorage.removeItem('authToken');
      localStorage.removeItem('token');
      localStorage.removeItem('risk_level');
      localStorage.removeItem('assessment_completed');


      try {
        const response = await authAPI.login(userId.value, password.value, centerCode.value)
        
        // 토큰 저장 (백엔드는 access_token으로 반환)
        localStorage.setItem('authToken', response.access_token || response.token || 'demo-token')
        localStorage.setItem('token', response.access_token || response.token || 'demo-token') // Duplicate for compatibility
        
        // assessment_completed 플래그 저장
        const isAssessed = response.assessment_completed;
        localStorage.setItem('assessment_completed', isAssessed);
        
        // [B2G] Center Info Persist from Login Response
        let finalCenterCode = response.linked_center_code || response.center_code;

        if (finalCenterCode) {
            localStorage.setItem('b2g_center_code', finalCenterCode);
            localStorage.setItem('b2g_is_linked', 'true');
            // If linked, force assessment true locally
            localStorage.setItem('assessment_completed', 'true');
            console.log("🏥 [Login] Linked Center (from Response): " + finalCenterCode);
        } else {
             // [Double Check] If response missed it, fetch user info immediately
             try {
                const userRes = await authAPI.getUserInfo();
                if (userRes) {
                    if (userRes.risk_level) localStorage.setItem('risk_level', userRes.risk_level);
                    
                    // [Fix] 프리미엄(is_premium) 유저도 진단 패스
                    if (userRes.is_premium) {
                        localStorage.setItem('assessment_completed', 'true');
                        console.log("💎 [Login] Premium User Detected. Bypassing Assessment.");
                    }

                    if (userRes.linked_center_code) {
                        finalCenterCode = userRes.linked_center_code;
                        localStorage.setItem('b2g_center_code', finalCenterCode);
                        localStorage.setItem('b2g_is_linked', 'true');
                        localStorage.setItem('assessment_completed', 'true'); // Force Pass
                        console.log("🏥 [Login] Linked Center (from UserInfo): " + finalCenterCode);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch user info on login", e);
            }
        }
        
        // Refresh Assessed Flag
        const finalAssessed = localStorage.getItem('assessment_completed') === 'true';
        
        // 캘린더 페이지로 이동
        // [Logic] 연동 코드(finalCenterCode)가 있거나, 진단이 완료되었으면 캘린더로 이동
        if (finalAssessed || finalCenterCode) {
             router.push('/calendar');
        } else {
             router.push('/assessment');
        }
      } catch (error) {
        console.error('Login failed:', error)
        const msg = error.response?.data?.message
        if (msg === 'Invalid credentials' || error.response?.status === 401) {
             errorMessage.value = '존재하지 않는 계정이거나 비밀번호가 올바르지 않습니다.'
        } else {
             errorMessage.value = msg || '로그인에 실패했습니다.'
        }
      } finally {
        loading.value = false
      }
    }

    return {
      userId,
      password,
      centerCode,
      showCenterInput,
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
.toggle-link:hover {
    text-decoration: underline;
}
</style>
