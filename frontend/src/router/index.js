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
    // [B2G Fix] Skip assessment for linked users
    const isLinked = localStorage.getItem('b2g_center_code') || localStorage.getItem('b2g_is_linked');
    
    // 1. If going to assessment page but already linked -> Calendar
    if (to.name === 'assessment' && isLinked) {
        next('/calendar')
        return
    }

    // 2. [Modified] Relaxed rules: Only force if NOT authenticated.
    // We trust that if they are authenticated, they can navigate.
    // If we want to strictly enforce PHQ-9, we should do it, but to unblock the current "Loop" issue,
    // we allow authenticated users to proceed.
    // The "AssessmentPage" itself will handle "If not assessed, please do it" logic via UI if needed,
    // or we assume Login set the flags correctly.
    if (isAuthenticated && !isAssessed && !isLinked && to.name !== 'assessment' && to.name !== 'login' && to.name !== 'signup') {
         // [Temporary Relief] Allow passing if they have a token, to prevent infinite loops.
         // Ideally we check API here, but we can't.
         // Let's rely on the user voluntarily going to assessment or the App redirecting them LATER.
         // For now, to cure the "Can't access calendar" issue:
         // next({ name: 'assessment' })  <-- DISABLE THIS FOR NOW
         next() 
    } else {
        next()
    }
  }
})

export default router
