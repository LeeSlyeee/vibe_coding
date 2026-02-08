<template>
  <div id="app">
    <!-- 데스크탑용 상단 네비게이션 -->
    <header class="navbar desktop-nav" v-if="showNavbar">
      <div class="navbar-content">
        <h1 class="logo" @click="goHome">haruON</h1>
        <div class="nav-actions">
          <button
            v-if="isAuthenticated"
            @click="$router.push('/guide')"
            class="stats-btn"
            title="사용 방법"
          >
            📘 가이드
          </button>
          <button v-if="isAuthenticated" @click="goToStats" class="stats-btn" title="통계 분석">
            📊 분석
          </button>
          <button
            v-if="isAuthenticated"
            @click="goToMedication"
            class="stats-btn"
            title="약물 관리"
          >
            💊 약물
          </button>
          <button
            v-if="isAuthenticated"
            @click="$router.push('/settings')"
            class="stats-btn"
            title="설정"
          >
            ⚙️ 설정
          </button>
        </div>
      </div>
    </header>

    <!-- 모바일용 상단 헤더 (앱 타이틀만) -->
    <header class="navbar mobile-header" v-if="showNavbar">
      <div class="mobile-navbar-content">
        <h1 class="logo" @click="goHome">haruON</h1>
        <div class="mobile-nav-actions" v-if="isAuthenticated">
          <button @click="$router.push('/guide')" class="mobile-icon-btn" title="가이드">📘</button>
          <button @click="goToStats" class="mobile-icon-btn" title="분석">📊</button>
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

      <button class="nav-item" :class="{ active: $route.path === '/stats' }" @click="goToStats">
        <span class="nav-icon">📊</span>
        <span class="nav-label">분석</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: $route.path === '/medication' }"
        @click="goToMedication"
      >
        <span class="nav-icon">💊</span>
        <span class="nav-label">약물</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: $route.path === '/guide' }"
        @click="$router.push('/guide')"
      >
        <span class="nav-icon">📘</span>
        <span class="nav-label">가이드</span>
      </button>

      <button
        class="nav-item"
        :class="{ active: $route.path === '/settings' }"
        @click="$router.push('/settings')"
      >
        <span class="nav-icon">⚙️</span>
        <span class="nav-label">설정</span>
      </button>
    </nav>
    <button
      v-if="isAuthenticated"
      class="safety-fab"
      @click="showSafetyModal = true"
      title="긴급 도움 요청"
    >
      🆘
    </button>
    <SafetyModal v-if="showSafetyModal" @close="showSafetyModal = false" />

    <!-- Logout Confirmation Modal -->
    <div v-if="showLogoutModal" class="modal-overlay">
      <div class="modal-content">
        <h3>로그아웃</h3>
        <p>정말 로그아웃 하시겠습니까?</p>
        <div class="modal-actions">
          <button @click="showLogoutModal = false" class="cancel-btn">취소</button>
          <button @click="confirmLogout" class="confirm-btn">로그아웃</button>
        </div>
      </div>
    </div>

    <!-- Restricted Access Modal -->
    <div v-if="showRestrictedModal" class="modal-overlay" @click.self="showRestrictedModal = false">
      <div class="modal-content">
        <h3 style="color: #ff3b30">⛔️ 접근 제한</h3>
        <p style="white-space: pre-line; line-height: 1.5">
          보건소 및 병원 사용자<br />또는 유료사용자 전용 기능입니다.
        </p>
        <div class="modal-actions">
          <button
            @click="showRestrictedModal = false"
            class="confirm-btn"
            style="background-color: #007aff; width: 100%"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Logout Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
  animation: fadeIn 0.2s ease-out;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 20px;
  width: 90%;
  max-width: 320px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-content h3 {
  margin: 0 0 12px 0;
  font-size: 1.2rem;
  color: #1d1d1f;
}

.modal-content p {
  color: #86868b;
  margin-bottom: 24px;
  font-size: 0.95rem;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.modal-actions button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s;
}
.modal-actions button:active {
  transform: scale(0.96);
}

.cancel-btn {
  background: #f5f5f7;
  color: #1d1d1f;
}

.confirm-btn {
  background: #ff3b30;
  color: white;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Rest of Styles */
</style>

<script>
import { RouterView } from "vue-router";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import SafetyModal from "./components/SafetyModal.vue";
import { authAPI } from "./services/api"; // Import authAPI

export default {
  name: "App",
  components: {
    RouterView,
    SafetyModal,
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const showSafetyModal = ref(false);
    const showLogoutModal = ref(false);
    const showRestrictedModal = ref(false);

    // Risk Level Logic
    const userRiskLevel = ref(1);
    const isSevere = computed(() => userRiskLevel.value >= 3);

    const showNavbar = computed(() => {
      // Assessment page doesn't need navbar
      if (route.name === "assessment") return false;
      return route.name !== "login" && route.name !== "signup" && route.name !== "intro";
    });

    const isAuthenticated = ref(false);

    const isLinked = ref(localStorage.getItem('b2g_is_linked') === 'true');
    const isPremium = ref(false);

    const checkAuth = async () => {
      isAuthenticated.value =
        localStorage.getItem("token") !== null || localStorage.getItem("authToken") !== null;

      if (isAuthenticated.value) {
        // [Fast-Load] Local Storage Priority
        if (localStorage.getItem('b2g_is_linked') === 'true') isLinked.value = true;

        try {
          const userData = await authAPI.getUserInfo();
          
          if (userData) {
              if (userData.risk_level) userRiskLevel.value = userData.risk_level;
              if (userData.is_premium) isPremium.value = true;
          }
          
          // [B2G Sync] Check Linkage Status
          if (userData && userData.linked_center_code) {
             isLinked.value = true;
             localStorage.setItem('b2g_center_code', userData.linked_center_code);
             localStorage.setItem('b2g_is_linked', 'true');
             
             // Force Assessment Flag if Linked
             if (!userData.assessment_completed) {
                 localStorage.setItem('assessment_completed', 'true');
             }
          } else {
             // If not linked in DB, clear local state (unless premium)
             if (!userData?.linked_center_code) {
                 isLinked.value = false;
                 localStorage.removeItem('b2g_is_linked');
             }
          }

          if (userData && userData.assessment_completed) {
              localStorage.setItem('assessment_completed', 'true');
          }
        } catch (e) {
          console.error("User Info Fetch Failed", e);
        }
      }
    };

    watch(
      route,
      () => {
        checkAuth();
      },
      { immediate: true },
    );

    const handleRestrictedAccess = (featureName) => {
      showRestrictedModal.value = true;
    };

    const goToStats = () => {
      // 분석 탭: 고위험군(3단계 이상) 또는 기관 연동 사용자만 접근 허용
      if (isSevere.value || isLinked.value) router.push("/stats");
      else handleRestrictedAccess("분석");
    };

    const goToMedication = () => {
      // 약물 탭: 모든 사용자 접근 허용
      router.push("/medication");
    };

    // Event Listerner for Safety Modal
    window.addEventListener("open-safety-modal", () => {
      showSafetyModal.value = true;
    });

    const handleLogout = () => {
      showLogoutModal.value = true;
    };

    const confirmLogout = () => {
      showLogoutModal.value = false;
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
      confirmLogout,
      showLogoutModal,
      goHome,
      showSafetyModal,
      isSevere,
      goToStats,
      goToMedication,
      showRestrictedModal,
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
  overflow-y: auto; /* Key fix: Allow pages to scroll */
  -webkit-overflow-scrolling: touch;
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

/* Safety Floating Button */
.safety-fab {
  position: fixed;
  bottom: 100px;
  left: 20px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #ff6b6b;
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  z-index: 9999;
  transition: transform 0.2s;
}

.safety-fab:hover {
  transform: scale(1.1);
  background: #fa5252;
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
