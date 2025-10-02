import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authService, type User } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!user.value)

  async function login(username: string, password: string) {
    try {
      isLoading.value = true
      error.value = null
      
      
      await authService.login({ username, password })
      await fetchCurrentUser()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await authService.logout()
      user.value = null
    } catch (err) {
      console.error('Logout error:', err)
    }
  }

  async function fetchCurrentUser() {
    try {
      if (!authService.isAuthenticated()) {
        user.value = null
        return
      }
      
      user.value = await authService.getCurrentUser()
    } catch (err) {
      console.error('Failed to fetch user:', err)
      await logout()
    }
  }

  
  async function initialize() {
    if (authService.isAuthenticated()) {
      await fetchCurrentUser()
    }
  }

  return {
    user,
    isLoading,
    error,
    isAuthenticated,
    login,
    logout,
    fetchCurrentUser,
    initialize
  }
})
