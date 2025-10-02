import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/evaluations',
      name: 'evaluations',
      component: () => import('../views/EvaluationsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/evaluations/:id',
      name: 'evaluation-detail',
      component: () => import('../views/EvaluationDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/check-website',
      name: 'check-website',
      component: () => import('../views/CheckWebsiteView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/check-document',
      name: 'check-document',
      component: () => import('../views/CheckDocumentView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/complaints',
      name: 'complaints',
      component: () => import('../views/ComplaintsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/regulator',
      name: 'regulator',
      component: () => import('../views/RegulatorView.vue'),
      meta: { requiresAuth: true, requiresRole: 'government' }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ],
})


router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  
  if (!authStore.user && authStore.isAuthenticated) {
    await authStore.initialize()
  }
  
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresRole = to.meta.requiresRole
  const isAuthenticated = authStore.isAuthenticated
  
  if (requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next('/dashboard')
  } else if (to.path === '/' && isAuthenticated) {
    
    next('/dashboard')
  } else if (requiresRole && authStore.user?.role !== requiresRole) {
    
    next('/dashboard')
  } else {
    next()
  }
})

export default router
