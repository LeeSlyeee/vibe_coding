import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/LoginView.vue')
  },
  {
    path: '/dashboard',
    name: 'Layout',
    component: () => import('../views/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'RegionHome',
        component: () => import('../views/RegionDashboard.vue')
      },
      {
        path: 'centers',
        name: 'Centers',
        component: () => import('../views/CenterList.vue')
      },
      {
        path: 'staff',
        name: 'Staff',
        component: () => import('../views/StaffList.vue')
      },
    ]
  }
]

const router = createRouter({
  history: createWebHistory('/region/'),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('region_token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
