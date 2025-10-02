<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-white">
    <div 
      v-motion
      :initial="{ opacity: 0, y: 20 }"
      :enter="{ opacity: 1, y: 0 }"
      :duration="500"
      class="w-full max-w-md"
    >
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl mx-auto flex items-center justify-center mb-4">
          <span class="text-white font-bold text-2xl">A</span>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Welcome to APRU</h1>
        <p class="text-gray-600">Sign in to your dark pattern detection platform</p>
      </div>

      <v-card class="glass-card p-8 border border-gray-200 shadow-xl">
        <v-form @submit.prevent="handleLogin" ref="form">
          <div class="space-y-6">
            <v-text-field
              v-model="username"
              :rules="usernameRules"
              label="Username"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              class="rounded-lg"
              required
            />

            <v-text-field
              v-model="password"
              :rules="passwordRules"
              label="Password"
              prepend-inner-icon="mdi-lock"
              :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
              :type="showPassword ? 'text' : 'password'"
              variant="outlined"
              class="rounded-lg"
              required
              @click:append-inner="showPassword = !showPassword"
            />

            <v-alert
              v-if="authStore.error"
              type="error"
              variant="tonal"
              class="rounded-lg"
            >
              {{ authStore.error }}
            </v-alert>

            <v-btn
              type="submit"
              :loading="authStore.isLoading"
              block
              size="large"
              variant="flat"
              class="btn-hover text-white rounded-xl font-medium"
              :style="signInGradient"
            >
              Sign In
            </v-btn>
          </div>
        </v-form>

        <div class="mt-6 text-center text-sm text-gray-600">
          <p>Demo credentials:</p>
          <div class="mt-2 space-y-1">
            <p><strong>Government:</strong> admin / admin123</p>
            <p><strong>Business:</strong> business / business123</p>
            <p><strong>Individual:</strong> user / user123</p>
          </div>
        </div>
      </v-card>

      <p class="text-center text-xs text-gray-500 mt-8">
        © 2025 APRU Tech Policy Hackathon. All rights reserved.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref()
const username = ref('')
const password = ref('')
const showPassword = ref(false)

const signInGradient = {
  background: 'linear-gradient(to right, #6366f1, #8b5cf6)'
}

const usernameRules = [
  (v: string) => !!v || 'Username is required',
  (v: string) => v.length >= 3 || 'Username must be at least 3 characters',
]

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 3 || 'Password must be at least 3 characters',
]

async function handleLogin() {
  const { valid } = await form.value.validate()
  
  if (valid) {
    try {
      await authStore.login(username.value, password.value)
      await router.push('/dashboard')
    } catch (error) {
      console.error('Login failed:', error)
    }
  }
}
</script>

<style scoped>
.glass-card {
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
</style>