<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      
      <div 
        v-motion
        :initial="{ opacity: 0, y: -20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="500"
        class="mb-8"
      >
        <h1 class="text-3xl font-bold text-gray-900 mb-2">
          {{ getUserDashboardTitle() }}
        </h1>
        <p class="text-gray-600">{{ getUserDashboardSubtitle() }}</p>
      </div>

      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div
          v-for="(stat, index) in stats"
          :key="stat.title"
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :delay="index * 100"
          :duration="500"
        >
          <v-card class="p-6 rounded-2xl hover:shadow-lg transition-all duration-300 border border-gray-100 cursor-pointer btn-hover !overflow-visible">
            <div class="flex items-start justify-between gap-3 mb-4">
              <div :class="stat.iconBg" class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0">
                <v-icon :icon="stat.icon" :color="stat.iconColor" size="24" />
              </div>
              <v-chip
                :color="stat.trend === 'up' ? 'success' : stat.trend === 'down' ? 'error' : 'gray'"
                variant="tonal"
                size="small"
              >
                {{ stat.change }}
              </v-chip>
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-1">{{ stat.value }}</h3>
            <p class="text-gray-600 text-sm">{{ stat.title }}</p>
          </v-card>
        </div>
      </div>

      
      <div v-if="authStore.user?.role === 'regulator' || authStore.user?.role === 'admin' || authStore.user?.user_type === 'government'">

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

          <v-card class="p-6 rounded-2xl">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">Critical Threats</h2>
              <v-chip color="error" variant="tonal" size="small">
                High Alert
              </v-chip>
            </div>
            <div class="space-y-4">
              <div class="flex items-center gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
                <v-icon icon="mdi-alert-octagon" color="error" size="20" />
                <div class="flex-1">
                  <p class="font-medium text-gray-900 text-sm">Hidden subscription spike</p>
                  <p class="text-gray-600 text-xs">Found across 3 fintech apps</p>
                </div>
                <span class="text-xs text-gray-500">2h ago</span>
              </div>
              <div class="flex items-center gap-3 p-4 bg-orange-50 rounded-lg border border-orange-200">
                <v-icon icon="mdi-alert-triangle" color="warning" size="20" />
                <div class="flex-1">
                  <p class="font-medium text-gray-900 text-sm">Visual interference surge</p>
                  <p class="text-gray-600 text-xs">Up 25% in mobile banking</p>
                </div>
                <span class="text-xs text-gray-500">4h ago</span>
              </div>
              <div class="flex items-center gap-3 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <v-icon icon="mdi-alert" color="warning" size="20" />
                <div class="flex-1">
                  <p class="font-medium text-gray-900 text-sm">Fresh urgency tricks</p>
                  <p class="text-gray-600 text-xs">New variant in crypto apps</p>
                </div>
                <span class="text-xs text-gray-500">6h ago</span>
              </div>
            </div>
          </v-card>


          <v-card class="p-6 rounded-2xl">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Violation Hotspots</h2>
            <div class="space-y-5">
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <span class="text-sm font-medium text-gray-700">Bangkok Metropolitan</span>
                <div class="flex items-center space-x-2">
                  <div class="w-20 h-3 bg-red-500 rounded-full"></div>
                  <span class="text-sm text-gray-600">High Risk</span>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <span class="text-sm font-medium text-gray-700">Chiang Mai</span>
                <div class="flex items-center space-x-2">
                  <div class="w-16 h-3 bg-orange-500 rounded-full"></div>
                  <span class="text-sm text-gray-600">Medium Risk</span>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <span class="text-sm font-medium text-gray-700">Phuket</span>
                <div class="flex items-center space-x-2">
                  <div class="w-12 h-3 bg-yellow-500 rounded-full"></div>
                  <span class="text-sm text-gray-600">Low Risk</span>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <span class="text-sm font-medium text-gray-700">Pattaya</span>
                <div class="flex items-center space-x-2">
                  <div class="w-14 h-3 bg-orange-500 rounded-full"></div>
                  <span class="text-sm text-gray-600">Medium Risk</span>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <span class="text-sm font-medium text-gray-700">Khon Kaen</span>
                <div class="flex items-center space-x-2">
                  <div class="w-8 h-3 bg-green-500 rounded-full"></div>
                  <span class="text-sm text-gray-600">Safe</span>
                </div>
              </div>
            </div>
          </v-card>
        </div>

        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          
          <v-card class="p-6 rounded-2xl">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Top Dark Patterns</h2>
            <div class="space-y-4">
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                    <span class="text-red-600 font-bold text-sm">1</span>
                  </div>
                  <span class="text-sm font-medium text-gray-900">Hidden Subscription</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-gray-900">40%</div>
                  <div class="text-xs text-gray-500">156 cases</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                    <span class="text-orange-600 font-bold text-sm">2</span>
                  </div>
                  <span class="text-sm font-medium text-gray-900">Visual Interference</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-gray-900">25%</div>
                  <div class="text-xs text-gray-500">98 cases</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <span class="text-yellow-600 font-bold text-sm">3</span>
                  </div>
                  <span class="text-sm font-medium text-gray-900">Forced Urgency</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-gray-900">18%</div>
                  <div class="text-xs text-gray-500">71 cases</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span class="text-blue-600 font-bold text-sm">4</span>
                  </div>
                  <span class="text-sm font-medium text-gray-900">Bait and Switch</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-gray-900">12%</div>
                  <div class="text-xs text-gray-500">47 cases</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span class="text-purple-600 font-bold text-sm">5</span>
                  </div>
                  <span class="text-sm font-medium text-gray-900">Confirm-shaming</span>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-gray-900">5%</div>
                  <div class="text-xs text-gray-500">19 cases</div>
                </div>
              </div>
            </div>
          </v-card>

          
          <v-card class="p-6 rounded-2xl">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">Red List Companies</h2>
              <v-chip color="error" variant="tonal" size="small">
                Action Needed
              </v-chip>
            </div>
            <div class="space-y-4">
              <div class="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-200">
                <div>
                  <div class="font-medium text-gray-900 text-sm">FinTech Solutions Ltd</div>
                  <div class="text-xs text-gray-600">Trust 24/100</div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-red-600">High Risk</div>
                  <div class="text-xs text-gray-500">47 violations</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-4 bg-orange-50 rounded-lg border border-orange-200">
                <div>
                  <div class="font-medium text-gray-900 text-sm">QuickLoan Express</div>
                  <div class="text-xs text-gray-600">Trust 31/100</div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-orange-600">Medium Risk</div>
                  <div class="text-xs text-gray-500">32 violations</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <div>
                  <div class="font-medium text-gray-900 text-sm">Digital Banking Co</div>
                  <div class="text-xs text-gray-600">Trust 45/100</div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-yellow-600">Watch List</div>
                  <div class="text-xs text-gray-500">18 violations</div>
                </div>
              </div>
              <div class="flex items-center justify-between p-4 bg-orange-50 rounded-lg border border-orange-200">
                <div>
                  <div class="font-medium text-gray-900 text-sm">CryptoTrade Platform</div>
                  <div class="text-xs text-gray-600">Trust 38/100</div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-bold text-orange-600">Medium Risk</div>
                  <div class="text-xs text-gray-500">25 violations</div>
                </div>
              </div>
            </div>
          </v-card>
        </div>
      </div>


      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

        <div
          v-motion
          :initial="{ opacity: 0, x: -20 }"
          :enter="{ opacity: 1, x: 0 }"
          :duration="600"
        >
          <v-card class="p-6 h-96 rounded-2xl">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Evaluation Status</h2>
            <div class="flex items-center justify-center h-64">
              <div class="text-center">
                <div class="w-32 h-32 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center mb-4">
                  <span class="text-white text-2xl font-bold">{{ darkPatternStore.totalEvaluations }}</span>
                </div>
                <p class="text-gray-600">Total Evaluations</p>
              </div>
            </div>
          </v-card>
        </div>

        
        <div
          v-motion
          :initial="{ opacity: 0, x: 20 }"
          :enter="{ opacity: 1, x: 0 }"
          :duration="600"
        >
          <v-card class="p-6 h-96 rounded-2xl">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">Recent Evaluations</h2>
              <router-link to="/evaluations" class="text-indigo-600 hover:text-indigo-700 font-medium">
                View all
              </router-link>
            </div>
            
            <div v-if="darkPatternStore.isLoading" class="flex justify-center items-center h-48">
              <v-progress-circular indeterminate color="primary" />
            </div>
            
            <div v-else class="space-y-3">
              <div
                v-for="evaluation in recentEvaluations"
                :key="evaluation.id"
                class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                @click="$router.push(`/evaluations/${evaluation.id}`)"
              >
                <div>
                  <h3 class="font-medium text-gray-900">{{ evaluation.name }}</h3>
                  <p class="text-sm text-gray-600">{{ formatDate(evaluation.created_at) }}</p>
                </div>
                <v-chip
                  :color="darkPatternStore.getEvaluationStatusColor(evaluation.evaluation_status)"
                  variant="tonal"
                  size="small"
                >
                  {{ getStatusLabel(evaluation.evaluation_status) }}
                </v-chip>
              </div>

              <div v-if="recentEvaluations.length === 0" class="text-center text-gray-500 py-8">
                No evaluations yet. Start with a quick website or document check.
              </div>
            </div>
          </v-card>
        </div>
      </div>


      <div
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="700"
      >
        <v-card class="p-6 rounded-2xl">
          <h2 class="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <v-btn
              @click="$router.push('/check-website')"
              size="large"
              variant="outlined"
              class="btn-hover h-20 flex-col"
              prepend-icon="mdi-plus"
            >
              <v-icon icon="mdi-web" size="24" class="mb-2" />
              Check Website
            </v-btn>
            
            <v-btn
              @click="$router.push('/check-document')"
              size="large"
              variant="outlined"
              class="btn-hover h-20 flex-col"
            >
              <v-icon icon="mdi-file-document" size="24" class="mb-2" />
              Check a Document
            </v-btn>

            <v-btn
              @click="$router.push('/evaluations')"
              size="large"
              variant="outlined"
              class="btn-hover h-20 flex-col"
            >
              <v-icon icon="mdi-shield-search" size="24" class="mb-2" />
              View Results
            </v-btn>
          </div>
        </v-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useDarkPatternStore } from '@/stores/projects'
import { useAuthStore } from '@/stores/auth'
import { dashboardService, type DashboardStats } from '@/services/dashboard'

const darkPatternStore = useDarkPatternStore()
const authStore = useAuthStore()
const dashboardStats = ref<DashboardStats>({})
const isLoading = ref(true)

const stats = computed(() => {
  const user = authStore.user
  
  
  if (user?.role === 'regulator' || user?.role === 'admin' || user?.user_type === 'government') {
    return [
      {
        title: 'Market Integrity Index',
        value: `${dashboardStats.value.market_integrity_index || 0}/100`,
        change: '-5 pts',
        trend: 'down',
        icon: 'mdi-shield-check',
        iconColor: 'warning',
        iconBg: 'bg-orange-50'
      },
      {
        title: 'Active Complaints',
        value: (dashboardStats.value.active_complaints || 0).toString(),
        change: '+8',
        trend: 'down',
        icon: 'mdi-alert-circle',
        iconColor: 'error',
        iconBg: 'bg-red-50'
      },
      {
        title: 'Avg Response Time',
        value: `${dashboardStats.value.avg_response_time_days || 0} days`,
        change: '-3.2 days',
        trend: 'up',
        icon: 'mdi-speedometer',
        iconColor: 'success',
        iconBg: 'bg-green-50'
      },
      {
        title: 'Enforcement Rate',
        value: `${dashboardStats.value.enforcement_rate || 0}%`,
        change: '+8%',
        trend: 'up',
        icon: 'mdi-gavel',
        iconColor: 'primary',
        iconBg: 'bg-indigo-50'
      }
    ]
  }
  
  
  if (user?.role === 'owner' || user?.user_type === 'business') {
    return [
      {
        title: 'Trust Score',
        value: `${dashboardStats.value.trust_score || 0}/100`,
        change: '+3 pts',
        trend: 'up',
        icon: 'mdi-shield-check',
        iconColor: 'success',
        iconBg: 'bg-green-50'
      },
      {
        title: 'Compliance Status',
        value: `${dashboardStats.value.compliance_rate || 0}%`,
        change: '+2%',
        trend: 'up',
        icon: 'mdi-check-circle',
        iconColor: 'success',
        iconBg: 'bg-green-50'
      },
      {
        title: 'Recent Evaluations',
        value: (dashboardStats.value.total_evaluations || 0).toString(),
        change: '+5',
        trend: 'up',
        icon: 'mdi-chart-line',
        iconColor: 'info',
        iconBg: 'bg-blue-50'
      },
      {
        title: 'Issues to Resolve',
        value: (dashboardStats.value.issues_to_resolve || 0).toString(),
        change: '-1',
        trend: 'up',
        icon: 'mdi-alert-circle',
        iconColor: 'warning',
        iconBg: 'bg-orange-50'
      }
    ]
  }
  
  
  return [
    {
      title: 'Total Evaluations',
      value: (dashboardStats.value.total_evaluations || darkPatternStore.totalEvaluations).toString(),
      change: '+12%',
      trend: 'up',
      icon: 'mdi-shield-search',
      iconColor: 'primary',
      iconBg: 'bg-indigo-50'
    },
    {
      title: 'Verified Evaluations',
      value: (dashboardStats.value.verified_evaluations || darkPatternStore.verifiedEvaluations).toString(),
      change: '+8%',
      trend: 'up',
      icon: 'mdi-shield-check',
      iconColor: 'success',
      iconBg: 'bg-green-50'
    },
    {
      title: 'Avg Transparency Score',
      value: `${dashboardStats.value.avg_transparency_score || darkPatternStore.averageTransparencyScore.toFixed(1)}%`,
      change: '+2.3%',
      trend: 'up',
      icon: 'mdi-chart-line',
      iconColor: 'info',
      iconBg: 'bg-blue-50'
    },
    {
      title: 'Dark Patterns Found',
      value: (dashboardStats.value.dark_patterns_found || 47).toString(),
      change: '-15%',
      trend: 'up',
      icon: 'mdi-alert-circle',
      iconColor: 'warning',
      iconBg: 'bg-orange-50'
    }
  ]
})

const recentEvaluations = computed(() => {
  return darkPatternStore.evaluations
    .slice()
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)
})

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

function getUserDashboardTitle() {
  const user = authStore.user
  
  if (user?.role === 'regulator' || user?.role === 'admin' || user?.user_type === 'government') {
    return 'Regulatory Dashboard'
  } else if (user?.role === 'owner' || user?.user_type === 'business') {
    return 'Business Dashboard'
  }
  
  return 'Dashboard'
}

function getUserDashboardSubtitle() {
  const user = authStore.user

  if (user?.role === 'regulator' || user?.role === 'admin' || user?.user_type === 'government') {
    return 'Track market health, complaints, and enforcement at a glance.'
  } else if (user?.role === 'owner' || user?.user_type === 'business') {
    return 'Stay on top of compliance, trust score, and fresh evaluations.'
  }

  return 'Welcome back! Review evaluations and transparency metrics in seconds.'
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'not_evaluated': return 'NOT EVALUATED'
    case 'ai_only': return 'AI EVALUATED'
    case 'human_verified': return 'VERIFIED'
    default: return status.toUpperCase()
  }
}

onMounted(async () => {
  try {
    isLoading.value = true
    
    dashboardStats.value = await dashboardService.getStats()
    
    await darkPatternStore.fetchEvaluations()
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    isLoading.value = false
  }
})
</script>