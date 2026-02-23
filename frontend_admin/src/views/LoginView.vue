<template>
  <div class="login-container">
    <div class="glass-card login-box fade-in">
      <div style="text-align:center;margin-bottom:8px;font-size:36px;">🏛️</div>
      <h1 style="text-align:center;">마음온 관리 시스템</h1>
      <p class="subtitle" style="text-align:center;">Maum-On National Administration</p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>아이디</label>
          <input v-model="username" type="text" class="form-input" placeholder="관리자 아이디" autofocus />
        </div>
        <div class="form-group">
          <label>비밀번호</label>
          <input v-model="password" type="password" class="form-input" placeholder="비밀번호" />
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;" :disabled="loading">
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
        <p v-if="error" class="error-msg" style="text-align:center;">{{ error }}</p>
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
    const token = res.data.access
    if (!token) throw new Error('토큰 없음')
    localStorage.setItem('admin_token', token)
    if (res.data.refresh) localStorage.setItem('admin_refresh', res.data.refresh)

    // 관리자 레벨 확인
    const me = await api.getMe()
    const level = me.data.admin_level
    if (!['central_admin', 'region_admin', 'center_admin'].includes(level) && !me.data.is_superuser) {
      localStorage.removeItem('admin_token')
      error.value = '관리자 권한이 없는 계정입니다.'
      return
    }
    localStorage.setItem('admin_user', JSON.stringify(me.data))
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '로그인에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>
