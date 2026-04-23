import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import pinia from '@/stores'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { publicOnly: true }
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/SignupView.vue'),
      meta: { publicOnly: true }
    },
    {
      path: '/connect',
      name: 'connect',
      component: () => import('../views/ConnectCenterView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/patients',
      name: 'patient-list',
      component: () => import('../views/PatientListView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/patients/:id',
      name: 'patient-detail',
      component: () => import('../views/PatientDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/staff',
      name: 'staff-manage',
      component: () => import('../views/StaffManageView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore(pinia)
  authStore.initialize()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath }
    }
  }

  if (to.meta.publicOnly && authStore.isAuthenticated) {
    const redirectPath = typeof to.query.redirect === 'string' ? to.query.redirect : '/admin/dashboard'
    return redirectPath
  }
})

export default router
