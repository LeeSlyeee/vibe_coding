import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/LoginView.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'National',
        component: () => import('../views/NationalDashboard.vue')
      },
      {
        path: 'region/:id',
        name: 'RegionDashboard',
        component: () => import('../views/RegionDashboard.vue'),
        props: true
      },
      {
        path: 'regions',
        name: 'RegionManagement',
        component: () => import('../views/RegionManagement.vue')
      },
      {
        path: 'map',
        name: 'RiskMap',
        component: () => import('../views/NationalRiskMap.vue')
      },
      {
        path: 'broadcasts',
        name: 'PolicyBroadcast',
        component: () => import('../views/PolicyBroadcast.vue')
      },
      {
        path: 'centers',
        name: 'CenterManagement',
        component: () => import('../views/CenterManagement.vue')
      },
      {
        path: 'staff',
        name: 'StaffManagement',
        component: () => import('../views/StaffManagement.vue')
      },
      {
        path: 'audit',
        name: 'AuditLog',
        component: () => import('../views/AuditLog.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
