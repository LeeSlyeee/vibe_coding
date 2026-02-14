import { createRouter, createWebHistory } from 'vue-router'

// 정적 임포트
import LoginPage from '../views/LoginPage.vue'
import SignupPage from '../views/SignupPage.vue'
import CalendarPage from '../views/CalendarPage.vue'
import StatsPage from '../views/StatsPage.vue'
import GuidePage from '../views/GuidePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'intro',
      component: () => import('../views/IntroView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupPage
    },
    {
      path: '/assessment',
      name: 'assessment',
      component: () => import('../views/AssessmentPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/calendar',
      name: 'calendar',
      component: CalendarPage,
      meta: { requiresAuth: true }
    },
    {
      path: '/stats',
      name: 'stats',
      component: StatsPage,
      meta: { requiresAuth: true }
    },
    {
      path: '/guide',
      name: 'guide',
      component: GuidePage,
      meta: { requiresAuth: true }
    },
    {
      path: '/diary/chat/:date?',
      name: 'diary-chat',
      component: () => import('../views/ChatDiaryPage.vue'), // Lazy loading
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/medication',
      name: 'medication',
      component: () => import('../views/MedicationPage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/share',
      name: 'share',
      component: () => import('../views/SharePage.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/share/stats/:id',
      name: 'shared-stats',
      props: true,
      component: () => import('../views/SharedStatsPage.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 네비게이션 가드
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('authToken') || localStorage.getItem('token')
  const isAssessed = localStorage.getItem('assessment_completed') === 'true'
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if ((to.name === 'login' || to.name === 'signup') && isAuthenticated) {
    next('/calendar')
  } else {
    // [B2G Fix] Skip if center code exists (Linked user)
    const isLinked = localStorage.getItem('b2g_center_code') || localStorage.getItem('b2g_is_linked');
    
    // 이중 잠금 장치 활성화: 인증됨 + 진단 안 함 + 연동 안 됨 -> 진단 페이지로 납치
    if (isAuthenticated && !isAssessed && !isLinked && to.name !== 'assessment') {
        next({ name: 'assessment' })
    } else {
        next()
    }
  }
})

export default router
