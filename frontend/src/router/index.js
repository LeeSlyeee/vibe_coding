
import { createRouter, createWebHistory } from 'vue-router'

// 정적 임포트로 변경하여 빌드 오류 해결 시도
import LoginPage from '../views/LoginPage.vue'
import SignupPage from '../views/SignupPage.vue'
import CalendarPage from '../views/CalendarPage.vue'
import StatsPage from '../views/StatsPage.vue'
import GuidePage from '../views/GuidePage.vue'
import DiaryWritePage from '../views/DiaryWritePage.vue'
import DiaryDetailPage from '../views/DiaryDetailPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/calendar'
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
      path: '/diary/write/:date?',
      name: 'diary-write',
      component: DiaryWritePage,
      meta: { requiresAuth: true }
    },
    {
      path: '/diary/:id',
      name: 'diary-detail',
      component: DiaryDetailPage,
      meta: { requiresAuth: true }
    }
  ]
})

// 네비게이션 가드
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('authToken')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if ((to.name === 'login' || to.name === 'signup') && isAuthenticated) {
    next('/calendar')
  } else {
    next()
  }
})

export default router
