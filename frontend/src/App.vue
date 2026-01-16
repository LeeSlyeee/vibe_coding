<template>
  <div id="app">
    <!-- 네비게이션 바 -->
    <header class="navbar" v-if="showNavbar">
      <div class="navbar-content">
        <h1 class="logo" @click="goHome">MOOD DIARY</h1>
        <div class="nav-actions">
          <button
            v-if="isAuthenticated"
            @click="$router.push('/guide')"
            class="stats-btn"
            title="사용 방법"
          >
            📘 가이드
          </button>
          <button
            v-if="isAuthenticated"
            @click="$router.push('/stats')"
            class="stats-btn"
            title="통계 분석"
          >
            📊 분석
          </button>
          <button v-if="isAuthenticated" @click="handleLogout" class="logout-btn" title="로그아웃">
            👤 로그아웃
          </button>
        </div>
      </div>
    </header>

    <!-- 라우터 뷰 -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script>
import { RouterView } from "vue-router";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

export default {
  name: "App",
  components: {
    RouterView,
  },
  setup() {
    const route = useRoute();
    const router = useRouter();

    const showNavbar = computed(() => {
      return route.name !== "login" && route.name !== "signup";
    });

    const isAuthenticated = ref(false);

    const checkAuth = () => {
      isAuthenticated.value =
        localStorage.getItem("token") !== null || localStorage.getItem("authToken") !== null;
    };

    watch(
      route,
      () => {
        checkAuth();
      },
      { immediate: true }
    );

    const handleLogout = () => {
      localStorage.removeItem("token");
      localStorage.removeItem("authToken");
      router.push("/login");
    };

    const goHome = () => {
      if (isAuthenticated.value) {
        router.push("/calendar");
      } else {
        router.push("/login");
      }
    };

    return {
      showNavbar,
      isAuthenticated,
      handleLogout,
      goHome,
    };
  },
};
</script>

<style scoped>
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.navbar {
  background-color: var(--color-primary);
  color: white;
  padding: 0;
  flex-shrink: 0;
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

.nav-actions {
  display: flex;
  align-items: center;
}

.logo {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0;
  cursor: pointer;
}

.stats-btn {
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
  margin-right: 8px;
}

.stats-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
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
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
