<template>
  <div class="login-page">
    <div class="login-card glass-card fade-in">
      <div class="brand">
        <div class="brand-icon">🏢</div>
        <h1>마음온 광역 관제</h1>
        <p>시·도 정신건강 관리 시스템</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <label>아이디</label>
          <input v-model="username" type="text" placeholder="관리자 아이디" required autofocus />
        </div>
        <div class="input-group">
          <label>비밀번호</label>
          <input v-model="password" type="password" placeholder="비밀번호" required />
        </div>
        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
        <div v-if="error" class="error-msg">{{ error }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.login(username.value, password.value)
    const { access, refresh } = res.data
    localStorage.setItem('region_token', access)
    localStorage.setItem('region_refresh', refresh)

    // 권한 확인: region_admin 이상만 허용
    const me = await api.getMe()
    if (!['region_admin', 'central_admin'].includes(me.data.admin_level)) {
      localStorage.removeItem('region_token')
      error.value = '광역 관리자 권한이 필요합니다'
      return
    }
    localStorage.setItem('region_user', JSON.stringify(me.data))
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '로그인 실패'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0c1222 0%, #111a2e 50%, #0f1b2d 100%);
}
.login-card { width: 420px; padding: 48px 40px; }
.brand { text-align: center; margin-bottom: 36px; }
.brand-icon { font-size: 48px; margin-bottom: 12px; }
.brand h1 { font-size: 24px; font-weight: 900; letter-spacing: -0.5px; background: linear-gradient(135deg, #14b8a6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.brand p { font-size: 13px; color: var(--text-muted); margin-top: 6px; }
.login-form { display: flex; flex-direction: column; gap: 16px; }
.input-group { display: flex; flex-direction: column; gap: 6px; }
.input-group label { font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.input-group input { background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border); color: var(--text-primary); padding: 14px 16px; border-radius: 12px; font-size: 14px; transition: border-color 0.2s; }
.input-group input:focus { outline: none; border-color: var(--accent-teal); }
.login-btn { width: 100%; justify-content: center; padding: 14px; font-size: 15px; margin-top: 8px; }
.error-msg { text-align: center; color: var(--accent-rose); font-size: 13px; font-weight: 600; }
</style>
