<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      
      <div 
        v-motion
        :initial="{ opacity: 0, y: -20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="500"
        class="flex flex-col sm:flex-row sm:items-center justify-between mb-8"
      >
        <div>
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Dark Pattern Evaluations</h1>
          <p class="text-gray-600">Manage and review your transparency assessments.</p>
        </div>
        
        <div class="flex space-x-4 mt-4 sm:mt-0">
          <v-btn
            @click="$router.push('/check-website')"
            color="primary"
            size="large"
            class="btn-hover"
            prepend-icon="mdi-web"
          >
            Check Website
          </v-btn>
          <v-btn
            @click="$router.push('/check-document')"
            color="secondary"
            size="large"
            class="btn-hover"
            prepend-icon="mdi-file-document"
          >
            Check Document
          </v-btn>
        </div>
      </div>

      
      <div class="mb-6">
        <v-tabs v-model="activeTab" color="primary">
          <v-tab value="all">All Evaluations</v-tab>
          <v-tab value="not_evaluated">Pending</v-tab>
          <v-tab value="ai_only">AI Evaluated</v-tab>
          <v-tab value="human_verified">Human Verified</v-tab>
        </v-tabs>
      </div>

      
      <div v-if="darkPatternStore.isLoading" class="flex justify-center items-center h-64">
        <v-progress-circular indeterminate size="64" color="primary" />
      </div>

      <div v-else-if="filteredEvaluations.length === 0" class="text-center py-12">
        <div 
          v-motion
          :initial="{ opacity: 0, scale: 0.9 }"
          :enter="{ opacity: 1, scale: 1 }"
          :duration="500"
          class="max-w-md mx-auto"
        >
          <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <v-icon icon="mdi-shield-search-outline" size="48" color="gray" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">No evaluations yet</h3>
          <p class="text-gray-600 mb-6">Start by checking a website or document for dark patterns.</p>
          <div class="flex justify-center space-x-4">
            <v-btn
              @click="$router.push('/check-website')"
              color="primary"
              size="large"
              class="btn-hover"
              prepend-icon="mdi-web"
            >
              Check Website
            </v-btn>
            <v-btn
              @click="$router.push('/check-document')"
              variant="outlined"
              size="large"
              class="btn-hover"
              prepend-icon="mdi-file-document"
            >
              Check Document
            </v-btn>
          </div>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="(evaluation, index) in filteredEvaluations"
          :key="evaluation.id"
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :delay="index * 100"
          :duration="500"
        >
          <v-card 
            :class="[
              'h-full hover:shadow-xl transition-all duration-300 cursor-pointer btn-hover border-2',
              darkPatternStore.getEvaluationBorderColor(evaluation)
            ]"
            @click="$router.push(`/evaluations/${evaluation.id}`)"
          >
            <v-card-text class="p-6">
              <div class="flex items-center justify-between mb-4">
                <v-chip
                  :color="darkPatternStore.getEvaluationStatusColor(evaluation.evaluation_status)"
                  variant="tonal"
                  size="small"
                >
                  {{ getStatusLabel(evaluation.evaluation_status) }}
                </v-chip>
                
                <v-menu>
                  <template #activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon="mdi-dots-vertical"
                      variant="text"
                      size="small"
                      @click.stop
                    />
                  </template>
                  
                  <v-list>
                    <v-list-item
                      prepend-icon="mdi-eye"
                      title="View Details"
                      @click.stop="$router.push(`/evaluations/${evaluation.id}`)"
                    />
                    <v-list-item
                      v-if="evaluation.evaluation_status === 'ai_only' && authStore.user?.user_type === 'business'"
                      prepend-icon="mdi-account-check"
                      title="Request Human Review"
                      @click.stop="requestHumanReview(evaluation)"
                    />
                    <v-list-item
                      prepend-icon="mdi-delete"
                      title="Delete"
                      @click.stop="confirmDelete(evaluation)"
                    />
                  </v-list>
                </v-menu>
              </div>

              <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ evaluation.name }}</h3>
              
              <div class="flex items-center text-sm text-gray-600 mb-4">
                <v-icon :icon="evaluation.evaluation_method === 'website' ? 'mdi-web' : 'mdi-file-document'" size="16" class="mr-1" />
                <span class="truncate">
                  {{ evaluation.evaluation_method === 'website' ? evaluation.site_url : 'Document' }}
                </span>
              </div>

              <div class="flex items-center justify-between mb-4">
                <div class="text-center">
                  <p class="text-2xl font-bold" :class="getScoreColor(evaluation.transparency_score)">
                    {{ evaluation.transparency_score.toFixed(1) }}%
                  </p>
                  <p class="text-xs text-gray-500">Transparency</p>
                </div>
                
                <div class="text-center">
                  <p class="text-xl font-bold text-orange-600">{{ evaluation.dark_patterns_found.length }}</p>
                  <p class="text-xs text-gray-500">Dark Patterns</p>
                </div>
              </div>

              <div class="flex items-center justify-between">
                <div class="text-right">
                  <p class="text-sm font-medium text-gray-900">{{ formatDate(evaluation.created_at) }}</p>
                  <p class="text-xs text-gray-500">Created</p>
                </div>
                
                <div v-if="evaluation.evaluated_by" class="text-left">
                  <p class="text-sm font-medium text-green-600">{{ evaluation.evaluated_by }}</p>
                  <p class="text-xs text-gray-500">Evaluated by</p>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div>

    
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-card-title class="text-lg font-semibold px-6 pt-6 pb-2">Confirm Delete</v-card-title>
        <v-card-text class="px-6 pb-6">
          Are you sure you want to delete "{{ evaluationToDelete?.name }}"? This action cannot be undone.
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn @click="showDeleteDialog = false" variant="text">Cancel</v-btn>
          <v-btn
            @click="handleDelete"
            :loading="darkPatternStore.isLoading"
            color="error"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useDarkPatternStore } from '@/stores/projects'
import { useAuthStore } from '@/stores/auth'
import type { DarkPatternEvaluation } from '@/services/projects'

const darkPatternStore = useDarkPatternStore()
const authStore = useAuthStore()

const activeTab = ref('all')
const showDeleteDialog = ref(false)
const evaluationToDelete = ref<DarkPatternEvaluation | null>(null)

const filteredEvaluations = computed(() => {
  if (activeTab.value === 'all') {
    return darkPatternStore.evaluations
  }
  return darkPatternStore.evaluations.filter(e => e.evaluation_status === activeTab.value)
})

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'not_evaluated': return 'PENDING'
    case 'ai_only': return 'AI EVALUATED'
    case 'human_verified': return 'VERIFIED'
    default: return status.toUpperCase()
  }
}

function getScoreColor(score: number) {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

function confirmDelete(evaluation: DarkPatternEvaluation) {
  evaluationToDelete.value = evaluation
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (evaluationToDelete.value) {
    try {
      await darkPatternStore.deleteEvaluation(evaluationToDelete.value.id)
      showDeleteDialog.value = false
      evaluationToDelete.value = null
    } catch (error) {
      console.error('Failed to delete evaluation:', error)
    }
  }
}

async function requestHumanReview(evaluation: DarkPatternEvaluation) {
  
  console.log('Requesting human review for:', evaluation.id)
  
}

onMounted(async () => {
  await darkPatternStore.fetchEvaluations()
})
</script>