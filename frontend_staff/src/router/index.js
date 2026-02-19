import { createRouter, createWebHistory } from 'vue-router'
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
      component: LoginView
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('../views/SignupView.vue')
    },
    {
      path: '/connect',
      name: 'connect',
      component: () => import('../views/ConnectCenterView.vue')
    },
    {
      path: '/admin/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue')
    },
    {
      path: '/admin/patients',
      name: 'patient-list',
      component: () => import('../views/PatientListView.vue')
    },
    {
      path: '/admin/patients/:id',
      name: 'patient-detail',
      component: () => import('../views/PatientDetailView.vue')
    }
  ]
})

export default router
