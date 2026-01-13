<template>
  <div id="app">
    <!-- 네비게이션 바 -->
    <header class="navbar" v-if="showNavbar">
      <div class="navbar-content">
        <h1 class="logo">MOOD DIARY</h1>
        <button 
          v-if="isAuthenticated" 
          @click="handleLogout"
          class="logout-btn"
          title="로그아웃"
        >
          👤 로그아웃
        </button>
      </div>
    </header>

    <!-- 라우터 뷰 -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script>
import { RouterView } from 'vue-router'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export default {
  name: 'App',
  components: {
    RouterView
  },
  setup() {
    const route = useRoute()
    const router = useRouter()

    const showNavbar = computed(() => {
      return route.name !== 'login' && route.name !== 'signup'
    })

    const isAuthenticated = computed(() => {
      // 'token' 또는 'authToken' 둘 다 확인
      return localStorage.getItem('token') !== null || localStorage.getItem('authToken') !== null
    })

    const handleLogout = () => {
      localStorage.removeItem('token')
      localStorage.removeItem('authToken')
      router.push('/login')
    }

    return {
      showNavbar,
      isAuthenticated,
      handleLogout
    }
  }
}
</script>

<style scoped>
.navbar {
  background-color: var(--color-primary);
  color: white;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-md);
}

.navbar-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0;
}

.logout-btn {
  background-color: transparent;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.main-content {
  min-height: calc(100vh - 48px);
}
</style>
