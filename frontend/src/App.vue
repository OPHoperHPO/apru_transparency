<template>
  <v-app>
    <v-navigation-drawer
      v-if="authStore.isAuthenticated"
      v-model="drawer"
      app
      permanent
      class="bg-white border-r border-gray-200"
      width="280"
    >
      <div class="p-6">
        <div class="flex items-center space-x-3 mb-8">
          <div class="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
            <span class="text-white font-bold text-lg">A</span>
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-900">APRU</h1>
            <p class="text-sm text-gray-500">Dark Pattern Detector</p>
          </div>
        </div>

        <nav class="space-y-2">
          <router-link
            v-for="item in navigationItems"
            :key="item.name"
            :to="item.path"
            class="flex items-center space-x-3 px-4 py-3 text-gray-700 rounded-xl hover:bg-gray-100 transition-all duration-200 group"
            active-class="bg-indigo-50 text-indigo-700 hover:bg-indigo-50"
          >
            <v-icon :icon="item.icon" size="20" />
            <span class="font-medium">{{ item.name }}</span>
          </router-link>
        </nav>
      </div>

      <template #append>
        <div class="p-6 border-t border-gray-200">
          <div class="flex items-center space-x-3 mb-4">
            <v-avatar size="40" color="indigo">
              <span class="text-white font-medium">
                {{ userInitials }}
              </span>
            </v-avatar>
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900">
                {{ authStore.user?.first_name || authStore.user?.username }}
              </p>
              <p class="text-xs text-gray-500">{{ authStore.user?.email }}</p>
              <p class="text-xs text-indigo-600 font-medium mt-1">
                {{ getUserTypeLabel(authStore.user?.user_type) }}
              </p>
            </div>
          </div>

          <v-btn
            @click="logout"
            block
            variant="outlined"
            color="gray-400"
            class="btn-hover"
            prepend-icon="mdi-logout"
          >
            Logout
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar
      v-if="authStore.isAuthenticated"
      app
      flat
      class="bg-white border-b border-gray-200"
    >
      <v-app-bar-nav-icon @click="drawer = !drawer" class="d-lg-none" />

      <v-spacer />

      <div class="flex items-center space-x-4">
        <v-btn
          icon="mdi-bell-outline"
          variant="text"
          class="btn-hover"
        />

        <v-menu>
          <template #activator="{ props }">
            <v-avatar
              v-bind="props"
              size="40"
              color="indigo"
              class="cursor-pointer"
            >
              <span class="text-white font-medium">
                {{ userInitials }}
              </span>
            </v-avatar>
          </template>

          <v-card min-width="200">
            <v-list>
              <v-list-item
                prepend-icon="mdi-account"
                title="Profile"
              />
              <v-list-item
                prepend-icon="mdi-cog"
                title="Settings"
              />
              <v-divider />
              <v-list-item
                prepend-icon="mdi-logout"
                title="Logout"
                @click="logout"
              />
            </v-list>
          </v-card>
        </v-menu>
      </div>
    </v-app-bar>

    <v-main>
      <div class="min-h-screen">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </v-main>


    <v-overlay v-model="authStore.isLoading" persistent>
      <v-progress-circular
        indeterminate
        size="64"
        color="primary"
      />
    </v-overlay>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const drawer = ref(true)

const navigationItems = computed(() => {
  const baseItems = [
    { name: 'Dashboard', path: '/dashboard', icon: 'mdi-view-dashboard' },
    { name: 'Evaluations', path: '/evaluations', icon: 'mdi-shield-search' },
    { name: 'Check Website', path: '/check-website', icon: 'mdi-web' },
    { name: 'Check Document', path: '/check-document', icon: 'mdi-file-document' },
  ]


  baseItems.push({ name: 'Complaints', path: '/complaints', icon: 'mdi-alert' })


  if (authStore.user?.role === 'regulator' || authStore.user?.role === 'admin') {
    baseItems.push({
      name: 'Regulator Dashboard',
      path: '/regulator',
      icon: 'mdi-shield-check'
    })
  }

  return baseItems
})

const userInitials = computed(() => {
  const user = authStore.user
  if (user?.first_name && user?.last_name) {
    return `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`
  }
  return user?.username?.substring(0, 2).toUpperCase() || 'U'
})

function getUserTypeLabel(userType?: string) {
  switch (userType) {
    case 'individual': return 'Individual User'
    case 'business': return 'Business Account'
    case 'government': return 'Government Official'
    default: return 'User'
  }
}

async function logout() {
  await authStore.logout()
  await router.push('/')
}

onMounted(async () => {
  await authStore.initialize()
})
</script>

<style>
.v-card {
  padding: 18px !important;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
