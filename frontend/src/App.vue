<template>
  <div id="app">
    <!-- 데스크탑용 상단 네비게이션 -->
    <header class="navbar desktop-nav" v-if="showNavbar">
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

    <!-- 모바일용 상단 헤더 (앱 타이틀만) -->
    <header class="navbar mobile-header" v-if="showNavbar">
      <div class="mobile-navbar-content">
        <h1 class="logo" @click="goHome">MOOD DIARY</h1>
        <div class="mobile-nav-actions" v-if="isAuthenticated">
          <button @click="$router.push('/guide')" class="mobile-icon-btn" title="가이드">📘</button>
          <button @click="$router.push('/stats')" class="mobile-icon-btn" title="분석">📊</button>
        </div>
      </div>
    </header>

    <!-- 라우터 뷰 -->
    <main class="main-content">
      <RouterView />
    </main>

    <!-- 모바일용 하단 네비게이션 -->
    <nav class="bottom-nav" v-if="showNavbar && isAuthenticated">
      <button
        class="nav-item"
        :class="{ active: $route.path === '/calendar' || $route.path === '/' }"
        @click="$router.push('/calendar')"
      >
        <span class="nav-icon">📅</span>
        <span class="nav-label">일기</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: $route.path === '/stats' }"
        @click="$router.push('/stats')"
      >
        <span class="nav-icon">📊</span>
        <span class="nav-label">분석</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: $route.path === '/guide' }"
        @click="$router.push('/guide')"
      >
        <span class="nav-icon">📘</span>
        <span class="nav-label">가이드</span>
      </button>

      <button class="nav-item" @click="handleLogout">
        <span class="nav-icon">👤</span>
        <span class="nav-label">MY</span>
      </button>
    </nav>
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
      { immediate: true },
    );

    const handleLogout = () => {
      if (confirm("로그아웃 하시겠습니까?")) {
        localStorage.removeItem("token");
        localStorage.removeItem("authToken");
        router.push("/login");
      }
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
  background-color: var(--bg-primary);
}

/* === Desktop Navigation === */
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
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin: 0;
  cursor: pointer;
}

.stats-btn,
.logout-btn {
  background-color: transparent;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 4px;
}

.stats-btn:hover,
.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.15);
}

.main-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  width: 100%;
}

/* === Mobile & Responsive Styles === */
.mobile-header {
  display: none;
  background-color: white;
  z-index: 1000;
  border-bottom: 1px solid #f2f2f7;
}

.mobile-navbar-content {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  padding-top: max(12px, env(safe-area-inset-top));
}

.mobile-nav-actions {
  display: flex;
  gap: 12px;
}

.mobile-icon-btn {
  background: #f5f5f7;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s;
}

.mobile-icon-btn:active {
  background: #e8e8ed;
}

.bottom-nav {
  display: none;
  background: white;
  border-top: 1px solid #eee;
  padding: 8px 0;
  justify-content: space-around;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.03);
  z-index: 100;
  padding-bottom: max(8px, env(safe-area-inset-bottom)); /* Handle Home Indicator */
  flex-shrink: 0; /* Prevent shrinking */
}

.nav-item {
  background: none;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 12px;
  color: #999;
  font-size: 10px;
  gap: 4px;
  cursor: pointer;
}

.nav-item.active {
  color: var(--color-primary);
}

.nav-icon {
  font-size: 20px;
}

@media (max-width: 768px) {
  /* Hide Desktop Nav */
  .desktop-nav {
    display: none;
  }

  /* Show Mobile Header & Bottom Nav */
  .mobile-header {
    display: flex;
  }

  .bottom-nav {
    display: flex;
  }

  .navbar {
    background: white; /* Mobile header white background */
    color: #1d1d1f;
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.05); /* Subtle separator */
  }

  .logo {
    font-size: 18px;
    color: #1d1d1f;
  }

  /* Adjust main content for bottom nav */
  .main-content {
    /* No extra padding needed as bottom nav is flex item, not fixed overlay */
  }
}
</style>

<!-- 전역 스타일: 가로 모드 스크롤 강제 허용 -->
<style>
@media (max-height: 800px) and (orientation: landscape) {
  html,
  body {
    overflow-y: auto !important;
    height: auto !important;
    min-height: 100vh !important;
    -webkit-overflow-scrolling: touch !important; /* iOS 부드러운 스크롤 */
  }
}
</style>

<style scoped>
/* Mobile Landscape Optimization - App Layout */
@media (max-height: 800px) and (orientation: landscape) {
  #app {
    height: auto !important;
    min-height: 100vh;
    overflow: visible !important;
  }

  .main-content {
    overflow: visible !important;
    height: auto !important;
    flex: none !important;
  }

  .bottom-nav {
    position: relative;
    z-index: 10;
  }
}
</style>
