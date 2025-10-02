<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-4xl mx-auto">
      <div 
        v-motion
        :initial="{ opacity: 0, y: -20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="500"
        class="mb-8"
      >
        <router-link 
          to="/projects"
          class="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <v-icon icon="mdi-arrow-left" size="20" class="mr-2" />
          Back to Projects
        </router-link>
        
        <div v-if="projectStore.currentProject">
          <h1 class="text-3xl font-bold text-gray-900 mb-2">
            {{ projectStore.currentProject.name }}
          </h1>
          <p class="text-gray-600">{{ projectStore.currentProject.site_url }}</p>
        </div>
      </div>

      <div v-if="projectStore.isLoading" class="flex justify-center items-center h-64">
        <v-progress-circular indeterminate size="64" color="primary" />
      </div>

      <div v-else-if="!projectStore.currentProject" class="text-center py-12">
        <v-icon icon="mdi-alert-circle-outline" size="64" color="gray" class="mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Project Not Found</h3>
        <p class="text-gray-600">The requested project could not be found.</p>
      </div>

      <div v-else class="space-y-6">
        
        <v-card 
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :duration="500"
          class="p-6"
        >
          <h2 class="text-xl font-semibold text-gray-900 mb-6">Project Details</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 class="text-sm font-medium text-gray-500 mb-2">Status</h3>
              <v-chip
                :color="getStatusColor(projectStore.currentProject.status)"
                variant="tonal"
                size="large"
              >
                {{ projectStore.currentProject.status.replace('_', ' ').toUpperCase() }}
              </v-chip>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-gray-500 mb-2">Trust Score</h3>
              <div class="flex items-center">
                <span class="text-2xl font-bold text-indigo-600">
                  {{ projectStore.currentProject.trust_score.toFixed(1) }}
                </span>
                <span class="text-gray-500 ml-2">/ 100</span>
              </div>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-gray-500 mb-2">Created</h3>
              <p class="text-gray-900">{{ formatDate(projectStore.currentProject.created_at) }}</p>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-gray-500 mb-2">Last Updated</h3>
              <p class="text-gray-900">{{ formatDate(projectStore.currentProject.updated_at) }}</p>
            </div>
          </div>
        </v-card>

        
        <v-card 
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :delay="200"
          :duration="500"
          class="p-6"
        >
          <h2 class="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <v-btn
              size="large"
              variant="outlined"
              class="btn-hover h-20 flex-col"
              @click="submitTask"
            >
              <v-icon icon="mdi-rocket-launch" size="24" class="mb-2" />
              Submit Task
            </v-btn>
            
            <v-btn
              size="large"
              variant="outlined"
              class="btn-hover h-20 flex-col"
              @click="viewAnalytics"
            >
              <v-icon icon="mdi-chart-line" size="24" class="mb-2" />
              View Analytics
            </v-btn>
            
            <v-btn
              size="large"
              variant="outlined"
              class="btn-hover h-20 flex-col"
              @click="exportData"
            >
              <v-icon icon="mdi-download" size="24" class="mb-2" />
              Export Data
            </v-btn>
          </div>
        </v-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projects'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

function getStatusColor(status: string) {
  switch (status) {
    case 'approved': return 'success'
    case 'rejected': return 'error'
    case 'under_review': return 'warning'
    case 'submitted': return 'info'
    default: return 'gray'
  }
}

function submitTask() {
  router.push('/tasks')
}

function viewAnalytics() {
  router.push('/regulator')
}

function exportData() {
  
  console.log('Export data for project:', projectStore.currentProject?.id)
}

onMounted(async () => {
  const projectId = route.params.id as string
  if (projectId) {
    await projectStore.fetchProject(projectId)
  }
})
</script>