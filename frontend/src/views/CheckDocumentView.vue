<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-4xl mx-auto">
      <div 
        v-motion
        :initial="{ opacity: 0, y: -20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="500"
        class="text-center mb-8"
      >
        <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-teal-600 rounded-2xl mx-auto flex items-center justify-center mb-4">
          <v-icon icon="mdi-file-document" color="white" size="32" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Check Document for Dark Patterns</h1>
        <p class="text-gray-600">Upload a fintech document to analyze its transparency and detect manipulative language.</p>
      </div>

      <v-card class="p-8 mb-8">
        <v-form @submit.prevent="handleSubmit" ref="form">
          <div class="space-y-6">
            <v-text-field
              v-model="evaluationForm.name"
              :rules="nameRules"
              label="Evaluation Name"
              placeholder="e.g., Terms of Service Analysis"
              prepend-inner-icon="mdi-tag"
              variant="outlined"
              required
            />

            <v-file-input
              v-model="evaluationForm.file"
              :rules="fileRules"
              label="Upload Document"
              accept=".pdf,.doc,.docx,.txt"
              prepend-inner-icon="mdi-file-upload"
              variant="outlined"
              show-size
              required
              clearable
            />

            <div class="flex justify-center space-x-4">
              <v-btn
                type="submit"
                :loading="darkPatternStore.isLoading || isAnalyzing"
                size="large"
                variant="flat"
                class="btn-hover text-white rounded-xl font-medium px-12"
                :style="gradientStyle"
              >
                Analyze Document
              </v-btn>
            </div>

            <!-- Analysis Progress -->
            <v-progress-linear
              v-if="isAnalyzing"
              :model-value="analysisProgress"
              color="green"
              class="mt-4"
              height="6"
              rounded
            />
            <p v-if="isAnalyzing" class="text-center text-sm text-gray-600 mt-2">
              Analyzing document with AI agent... {{ analysisProgress.toFixed(0) }}%
            </p>
          </div>
        </v-form>
      </v-card>

      
      <v-card class="p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Supported Document Types</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <v-icon icon="mdi-file-pdf-box" color="red" size="32" class="mb-2" />
            <p class="text-sm font-medium">PDF</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <v-icon icon="mdi-file-word-box" color="blue" size="32" class="mb-2" />
            <p class="text-sm font-medium">Word</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <v-icon icon="mdi-file-document-outline" color="gray" size="32" class="mb-2" />
            <p class="text-sm font-medium">Text</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <v-icon icon="mdi-file-document-multiple" color="green" size="32" class="mb-2" />
            <p class="text-sm font-medium">More</p>
          </div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useDarkPatternStore } from '@/stores/projects'
import { agentService } from '@/services/agents'

const router = useRouter()
const darkPatternStore = useDarkPatternStore()
const form = ref()
const isAnalyzing = ref(false)
const analysisProgress = ref(0)

const evaluationForm = reactive({
  name: '',
  file: null as File[] | File | null
})

const gradientStyle = {
  background: 'linear-gradient(to right, #22c55e, #0d9488)'
}

const nameRules = [
  (v: string) => !!v || 'Evaluation name is required'
]

const fileRules = [
  (v: File[] | File | null) => {
    if (!v) return 'Document is required'
    return Array.isArray(v) ? !!v.length || 'Document is required' : true
  },
  (v: File[] | File | null) => {
    if (!v) return true
    const file = Array.isArray(v) ? v[0] : v
    if (!file) return true
    return file.size < 10 * 1024 * 1024 || 'File size should be less than 10MB'
  }
]

async function handleSubmit() {
  const { valid } = await form.value.validate()
  
  const file = Array.isArray(evaluationForm.file) ? evaluationForm.file[0] : evaluationForm.file

  if (valid && file) {
    try {
      isAnalyzing.value = true
      analysisProgress.value = 0
      

      const file = evaluationForm.file[0]
      

      const projectData = {
        name: evaluationForm.name,
        site_url: `document:${file.name}`,
      }
      
      const projectResponse = await darkPatternStore.createEvaluation({
        name: evaluationForm.name,
        evaluation_method: 'document',
        site_url: projectData.site_url
      })
      

      const analysisTask = await agentService.analyzeDocument(
        file,
        projectResponse.id
      )
      

      const result = await agentService.pollTaskUntilComplete(
        analysisTask.id,
        (progress) => {
          analysisProgress.value = progress || 0
        }
      )
      

      if (result.result_json) {
        await darkPatternStore.updateEvaluation(projectResponse.id, {
          evaluation_status: 'ai_only'
        })
      }
      
      isAnalyzing.value = false
      router.push(`/evaluations/${projectResponse.id}`)
    } catch (error) {
      console.error('Failed to create evaluation:', error)
      isAnalyzing.value = false
    }
  }
}
</script>