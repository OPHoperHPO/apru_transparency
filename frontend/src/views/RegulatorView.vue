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
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Regulator Dashboard</h1>
        <p class="text-gray-600">Monitor system performance and regulatory compliance metrics.</p>
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
          <v-card class="p-6 hover:shadow-lg transition-all duration-300 border border-gray-100">
            <div class="flex items-center justify-between mb-4">
              <div :class="stat.iconBg" class="w-12 h-12 rounded-xl flex items-center justify-center">
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

      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        
        <div
          v-motion
          :initial="{ opacity: 0, x: -20 }"
          :enter="{ opacity: 1, x: 0 }"
          :duration="600"
        >
          <v-card class="p-6 h-96">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">System Performance</h2>
              <v-chip variant="tonal" color="success" size="small">
                <v-icon icon="mdi-check" size="16" class="mr-1" />
                Healthy
              </v-chip>
            </div>
            
            <div class="flex items-center justify-center h-64">
              <div class="text-center">
                <div class="w-32 h-32 rounded-full bg-gradient-to-r from-green-400 to-blue-500 flex items-center justify-center mb-4 relative">
                  <div class="w-24 h-24 bg-white rounded-full flex items-center justify-center">
                    <span class="text-2xl font-bold text-gray-900">98.5%</span>
                  </div>
                  <div class="absolute top-0 right-0 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <v-icon icon="mdi-check" color="white" size="12" />
                  </div>
                </div>
                <p class="text-gray-600">System Uptime</p>
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
          <v-card class="p-6 h-96">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Compliance Status</h2>
            
            <div class="space-y-4">
              <div
                v-for="compliance in complianceMetrics"
                :key="compliance.name"
                class="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div class="flex items-center space-x-3">
                  <div :class="compliance.statusColor" class="w-3 h-3 rounded-full"></div>
                  <span class="font-medium text-gray-900">{{ compliance.name }}</span>
                </div>
                <div class="text-right">
                  <span class="text-sm font-bold text-gray-900">{{ compliance.score }}%</span>
                </div>
              </div>
            </div>

            <div class="mt-6 pt-6 border-t border-gray-200">
              <div class="flex items-center justify-between">
                <span class="font-medium text-gray-900">Overall Compliance</span>
                <div class="flex items-center space-x-2">
                  <v-progress-linear
                    model-value="95"
                    height="8"
                    rounded
                    color="success"
                    class="w-20"
                  />
                  <span class="text-sm font-bold text-green-600">95%</span>
                </div>
              </div>
            </div>
          </v-card>
        </div>
      </div>

      
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        <div
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :delay="200"
          :duration="500"
        >
          <v-card class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">Recent Activities</h2>
              <v-btn variant="outlined" size="small" icon="mdi-refresh" />
            </div>

            <div class="space-y-3">
              <div
                v-for="activity in recentActivities"
                :key="activity.id"
                class="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div :class="activity.iconBg" class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0">
                  <v-icon :icon="activity.icon" :color="activity.iconColor" size="16" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">{{ activity.message }}</p>
                  <p class="text-xs text-gray-500">{{ activity.time }}</p>
                </div>
                <v-chip
                  :color="activity.status === 'success' ? 'success' : activity.status === 'error' ? 'error' : 'warning'"
                  variant="tonal"
                  size="small"
                />
              </div>
            </div>
          </v-card>
        </div>

        
        <div
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :delay="300"
          :duration="500"
        >
          <v-card class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-semibold text-gray-900">System Alerts</h2>
              <v-chip variant="tonal" color="success" size="small">
                All Clear
              </v-chip>
            </div>

            <div v-if="systemAlerts.length === 0" class="text-center py-8">
              <div class="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <v-icon icon="mdi-shield-check" color="success" size="32" />
              </div>
              <h3 class="text-lg font-semibold text-gray-900 mb-2">All Systems Normal</h3>
              <p class="text-gray-600 text-sm">No active alerts or warnings detected.</p>
            </div>

            <div v-else class="space-y-3">
              <v-alert
                v-for="alert in systemAlerts"
                :key="alert.id"
                :type="alert.severity"
                variant="tonal"
                class="text-sm"
              >
                <div class="flex items-center justify-between">
                  <span>{{ alert.message }}</span>
                  <v-btn variant="text" size="x-small" icon="mdi-close" />
                </div>
              </v-alert>
            </div>
          </v-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const stats = ref([
  {
    title: 'Active Projects',
    value: '127',
    change: '+8%',
    trend: 'up',
    icon: 'mdi-briefcase',
    iconColor: 'primary',
    iconBg: 'bg-indigo-50'
  },
  {
    title: 'Processing Tasks',
    value: '43',
    change: '+12%',
    trend: 'up',
    icon: 'mdi-cogs',
    iconColor: 'warning',
    iconBg: 'bg-orange-50'
  },
  {
    title: 'Avg Response Time',
    value: '1.2s',
    change: '-5%',
    trend: 'up',
    icon: 'mdi-speedometer',
    iconColor: 'success',
    iconBg: 'bg-green-50'
  },
  {
    title: 'Error Rate',
    value: '0.03%',
    change: '-12%',
    trend: 'up',
    icon: 'mdi-alert-circle',
    iconColor: 'error',
    iconBg: 'bg-red-50'
  }
])

const complianceMetrics = ref([
  { name: 'Data Privacy', score: 98, statusColor: 'bg-green-500' },
  { name: 'Security Standards', score: 95, statusColor: 'bg-green-500' },
  { name: 'Financial Regulations', score: 92, statusColor: 'bg-yellow-500' },
  { name: 'Audit Requirements', score: 97, statusColor: 'bg-green-500' }
])

const recentActivities = ref([
  {
    id: 1,
    message: 'Project "FinanceApp" status changed to approved',
    time: '2 minutes ago',
    status: 'success',
    icon: 'mdi-check-circle',
    iconColor: 'success',
    iconBg: 'bg-green-50'
  },
  {
    id: 2,
    message: 'New task submitted for processing',
    time: '5 minutes ago',
    status: 'info',
    icon: 'mdi-rocket-launch',
    iconColor: 'info',
    iconBg: 'bg-blue-50'
  },
  {
    id: 3,
    message: 'System backup completed successfully',
    time: '1 hour ago',
    status: 'success',
    icon: 'mdi-backup-restore',
    iconColor: 'success',
    iconBg: 'bg-green-50'
  },
  {
    id: 4,
    message: 'Warning: High CPU usage detected',
    time: '2 hours ago',
    status: 'warning',
    icon: 'mdi-alert',
    iconColor: 'warning',
    iconBg: 'bg-orange-50'
  }
])

interface SystemAlert {
  id: number
  message: string
  severity: 'error' | 'warning' | 'info' | 'success'
}

const systemAlerts = ref<SystemAlert[]>([
  
])
</script>