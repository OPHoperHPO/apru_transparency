<template>
  <div v-if="analysisResult" class="space-y-6">
    <!-- Overall Summary -->
    <div class="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
      <h4 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
        <v-icon icon="mdi-file-document-check" class="mr-2" color="purple" />
        Legal Compliance Summary
      </h4>
      <p class="text-gray-700 mb-4">{{ analysisResult.summary }}</p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div class="bg-white rounded-lg p-4 border border-gray-200">
          <p class="text-sm text-gray-600 mb-1">Compliance Score</p>
          <p class="text-2xl font-bold text-purple-600">
            {{ (analysisResult.overall_compliance_score * 100).toFixed(0) }}%
          </p>
        </div>
        <div class="bg-white rounded-lg p-4 border border-gray-200">
          <p class="text-sm text-gray-600 mb-1">Critical Issues</p>
          <p class="text-2xl font-bold text-red-600">
            {{ analysisResult.critical_issues?.length || 0 }}
          </p>
        </div>
        <div class="bg-white rounded-lg p-4 border border-gray-200">
          <p class="text-sm text-gray-600 mb-1">Analysis Date</p>
          <p class="text-sm font-medium text-gray-900">
            {{ formatDate(analysisResult.analysis_date) }}
          </p>
        </div>
      </div>
    </div>

    <!-- Critical Issues -->
    <div v-if="analysisResult.critical_issues && analysisResult.critical_issues.length > 0">
      <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <v-icon icon="mdi-alert-octagon" class="mr-2" color="error" />
        Critical Issues
      </h4>
      <div class="space-y-3">
        <div
          v-for="(issue, index) in analysisResult.critical_issues"
          :key="index"
          class="bg-red-50 border border-red-200 rounded-lg p-4"
        >
          <div class="flex items-start">
            <v-icon icon="mdi-alert-circle" color="error" class="mr-3 mt-1" />
            <p class="text-gray-800">{{ issue }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Criteria Analysis -->
    <div v-if="analysisResult.criteria">
      <h4 class="text-lg font-semibold text-gray-900 mb-4">Detailed Criteria Analysis</h4>
      <div class="space-y-4">
        <div
          v-for="(criterion, key) in analysisResult.criteria"
          :key="key"
          :class="[
            'border rounded-xl p-5',
            getCriterionBorderClass(criterion.status)
          ]"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-start flex-1">
              <v-icon
                :icon="getCriterionIcon(criterion.status)"
                :color="getCriterionColor(criterion.status)"
                class="mr-3 mt-1"
                size="24"
              />
              <div class="flex-1">
                <h5 class="font-semibold text-gray-900 mb-2">{{ formatCriterionName(key) }}</h5>
                <p class="text-gray-700 mb-3">{{ criterion.explanation }}</p>
                
                <div v-if="criterion.recommendations" class="bg-blue-50 rounded-lg p-3 mb-3">
                  <p class="text-sm font-medium text-blue-900 mb-1">Recommendations:</p>
                  <p class="text-sm text-blue-800">{{ criterion.recommendations }}</p>
                </div>

                <div class="flex items-center space-x-4">
                  <v-chip
                    :color="getCriterionColor(criterion.status)"
                    variant="tonal"
                    size="small"
                  >
                    {{ criterion.status.replace('_', ' ').toUpperCase() }}
                  </v-chip>
                  <div class="text-sm text-gray-600">
                    Confidence: {{ (criterion.confidence_score * 100).toFixed(0) }}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recommendations Summary -->
    <div v-if="analysisResult.recommendations && analysisResult.recommendations.length > 0">
      <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <v-icon icon="mdi-lightbulb-on" class="mr-2" color="amber" />
        Recommendations
      </h4>
      <div class="space-y-3">
        <div
          v-for="(recommendation, index) in analysisResult.recommendations"
          :key="index"
          class="bg-amber-50 border border-amber-200 rounded-lg p-4"
        >
          <div class="flex items-start">
            <v-icon icon="mdi-check-circle" color="success" class="mr-3 mt-1" />
            <p class="text-gray-800">{{ recommendation }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import type { DocumentAnalysisResult } from '@/services/agents'

defineProps<{
  analysisResult: DocumentAnalysisResult | null
}>()

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatCriterionName(key: string): string {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function getCriterionBorderClass(status: string): string {
  switch (status) {
    case 'compliant':
      return 'border-green-300 bg-green-50'
    case 'non_compliant':
      return 'border-red-300 bg-red-50'
    case 'partially_compliant':
      return 'border-yellow-300 bg-yellow-50'
    case 'unclear':
      return 'border-gray-300 bg-gray-50'
    default:
      return 'border-gray-300 bg-white'
  }
}

function getCriterionIcon(status: string): string {
  switch (status) {
    case 'compliant':
      return 'mdi-check-circle'
    case 'non_compliant':
      return 'mdi-close-circle'
    case 'partially_compliant':
      return 'mdi-alert-circle'
    case 'unclear':
      return 'mdi-help-circle'
    default:
      return 'mdi-information'
  }
}

function getCriterionColor(status: string): string {
  switch (status) {
    case 'compliant':
      return 'success'
    case 'non_compliant':
      return 'error'
    case 'partially_compliant':
      return 'warning'
    case 'unclear':
      return 'grey'
    default:
      return 'grey'
  }
}
</script>
