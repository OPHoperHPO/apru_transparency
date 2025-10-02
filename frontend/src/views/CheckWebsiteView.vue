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
        <div class="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl mx-auto flex items-center justify-center mb-4">
          <v-icon icon="mdi-web" color="white" size="32" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Check Website for Dark Patterns</h1>
        <p class="text-gray-600">Enter a fintech website URL to evaluate its transparency and detect dark patterns.</p>
      </div>


      <v-card
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="600"
        class="p-10 mb-8 border border-gray-200 shadow-xl"
      >
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-gray-900 mb-4">Website Transparency Analysis</h2>
          <p class="text-lg text-gray-600">Enter a website URL to check for dark patterns and transparency issues</p>
          <p class="text-sm text-gray-500 mt-2">Our AI will analyze visual elements, legal terms, and user behavior patterns</p>
        </div>

        <v-form @submit.prevent="handleSubmit" ref="form">
          <div class="space-y-8">
            <v-text-field
              v-model="evaluationForm.name"
              :rules="nameRules"
              label="Analysis Name"
              placeholder="e.g., CryptoTrade Pro Transparency Check"
              prepend-inner-icon="mdi-tag"
              variant="outlined"
              required
              class="rounded-xl text-lg"
              style="font-size: 1.1rem;"
            />

            <v-text-field
              v-model="evaluationForm.site_url"
              :rules="urlRules"
              label="Website URL"
              placeholder="https://example.com"
              prepend-inner-icon="mdi-web"
              variant="outlined"
              required
              class="rounded-xl text-lg"
              style="font-size: 1.1rem;"
            />

            <div class="bg-blue-50 p-6 rounded-xl border border-blue-200">
              <div class="flex items-start space-x-3">
                <v-icon icon="mdi-information" color="blue" size="24" />
                <div>
                  <h3 class="font-semibold text-blue-900 mb-2">AI-Powered Analysis with 12 Dark Pattern Detectors:</h3>
                  <ul class="text-blue-800 space-y-1 text-sm">
                    <li>• <strong>Roach Motel</strong> - Easy subscribe, hard to cancel detection</li>
                    <li>• <strong>Fake Urgency & Scarcity</strong> - False countdown timers and stock claims</li>
                    <li>• <strong>Drip Pricing</strong> - Hidden fees at checkout detection</li>
                    <li>• <strong>Hidden Subscriptions</strong> - Concealed recurring charges</li>
                    <li>• <strong>Sneak into Basket</strong> - Unconsented cart additions</li>
                    <li>• <strong>Confirmshaming</strong> - Guilt-inducing decline options</li>
                    <li>• <strong>...and 6 more specialized detectors</strong></li>
                  </ul>
                </div>
              </div>
            </div>

            <v-alert
              v-if="darkPatternStore.error"
              type="error"
              variant="tonal"
              class="rounded-lg"
            >
              {{ darkPatternStore.error }}
            </v-alert>

            <div class="flex justify-center">
              <v-btn
                type="submit"
                :loading="darkPatternStore.isLoading"
                size="x-large"
                class="btn-hover bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl font-bold px-16 py-4 shadow-lg"
                style="font-size: 1.2rem; height: 64px;"
              >
                <v-icon icon="mdi-shield-search" class="mr-3" size="28" />
                Analyze Website
              </v-btn>
            </div>
          </div>
        </v-form>
      </v-card>


      <v-dialog
        v-model="showAnalysisDialog"
        persistent
        max-width="600px"
        class="analysis-dialog"
      >
        <v-card class="rounded-2xl">
          <v-card-title class="text-center py-8">
            <div class="w-20 h-20 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full mx-auto flex items-center justify-center mb-4">
              <v-icon icon="mdi-shield-search" color="white" size="40" />
            </div>
            <h2 class="text-2xl font-bold text-gray-900">Analyzing Website</h2>
            <p class="text-gray-600 mt-2">{{ evaluationForm.site_url }}</p>
          </v-card-title>

          <v-card-text class="px-8 pb-8">
            <div class="mb-6">
              <div class="flex items-center justify-between mb-2">
                <span class="text-lg font-semibold text-gray-900">{{ analysisStage }}</span>
                <span class="text-lg font-bold text-indigo-600">{{ Math.round(analysisProgress) }}%</span>
              </div>
              <v-progress-linear
                v-model="analysisProgress"
                height="12"
                rounded
                color="indigo"
                bg-color="gray-100"
              />
            </div>

            <div class="bg-blue-50 p-4 rounded-xl border border-blue-200">
              <div class="flex items-start space-x-3">
                <div class="animate-pulse">
                  <v-icon icon="mdi-cog" color="blue" size="24" />
                </div>
                <p class="text-blue-900 font-medium">{{ analysisDescription }}</p>
              </div>
            </div>


            <div class="mt-6 space-y-3">
              <div class="flex items-center space-x-3 text-sm">
                <div class="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                  <v-icon icon="mdi-eye" color="green" size="14" />
                </div>
                <span class="text-gray-700">Visual Analysis: Detecting misleading UI elements</span>
              </div>
              <div class="flex items-center space-x-3 text-sm">
                <div class="w-6 h-6 rounded-full bg-yellow-100 flex items-center justify-center">
                  <v-icon icon="mdi-gavel" color="yellow-600" size="14" />
                </div>
                <span class="text-gray-700">Legal Analysis: Checking terms and conditions</span>
              </div>
              <div class="flex items-center space-x-3 text-sm">
                <div class="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center">
                  <v-icon icon="mdi-account-group" color="purple" size="14" />
                </div>
                <span class="text-gray-700">Behavioral Analysis: Testing user journey flows</span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-dialog>


      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <v-card
          v-for="tier in evaluationTiers"
          :key="tier.type"
          :class="[
            'p-6 border-2 transition-all duration-300',
            authStore.user?.user_type === tier.type ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'
          ]"
        >
          <div class="text-center">
            <div :class="tier.iconBg" class="w-12 h-12 rounded-xl mx-auto flex items-center justify-center mb-4">
              <v-icon :icon="tier.icon" :color="tier.iconColor" size="24" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ tier.title }}</h3>
            <p class="text-sm text-gray-600 mb-4">{{ tier.description }}</p>

            <div class="space-y-2">
              <div v-for="feature in tier.features" :key="feature" class="flex items-center text-sm">
                <v-icon icon="mdi-check-circle" color="success" size="16" class="mr-2" />
                <span>{{ feature }}</span>
              </div>
            </div>

            <div v-if="tier.resultColor" class="mt-4 p-3 rounded-lg" :class="tier.resultBg">
              <p class="text-sm font-medium" :class="tier.resultColor">
                Results: {{ tier.resultLabel }}
              </p>
            </div>
          </div>
        </v-card>
      </div>


      <v-card
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0 }"
        :delay="200"
        :duration="600"
        class="p-8"
      >
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">How Our Analysis Works</h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <v-icon icon="mdi-spider" color="blue" size="32" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">1. Website Crawling</h3>
            <p class="text-gray-600">Our AI scans your website structure, content, and user interface elements.</p>
          </div>

          <div class="text-center">
            <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <v-icon icon="mdi-brain" color="purple" size="32" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">2. AI Analysis</h3>
            <p class="text-gray-600">Advanced algorithms detect common dark patterns and manipulative design elements.</p>
          </div>

          <div class="text-center">
            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <v-icon icon="mdi-file-chart" color="green" size="32" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">3. Detailed Report</h3>
            <p class="text-gray-600">Receive a comprehensive transparency score with specific recommendations.</p>
          </div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDarkPatternStore } from '@/stores/projects'
import { useAuthStore } from '@/stores/auth'
import { agentService } from '@/services/agents'

const router = useRouter()
const darkPatternStore = useDarkPatternStore()
const authStore = useAuthStore()

const form = ref()
const showAnalysisDialog = ref(false)
const analysisProgress = ref(0)
const analysisStage = ref('')
const analysisDescription = ref('')

const evaluationForm = reactive({
  name: '',
  site_url: ''
})

const nameRules = [
  (v: string) => !!v || 'Evaluation name is required',
  (v: string) => v.length >= 3 || 'Name must be at least 3 characters'
]

const urlRules = [
  (v: string) => !!v || 'Website URL is required',
  (v: string) => {
    try {
      new URL(v)
      return true
    } catch {
      return 'Please enter a valid URL'
    }
  }
]

const evaluationTiers = computed(() => [

])

async function handleSubmit() {
  const { valid } = await form.value.validate()

  if (valid) {
    try {

      showAnalysisDialog.value = true
      analysisProgress.value = 0


      const newEvaluation = await darkPatternStore.createEvaluation({
        name: evaluationForm.name,
        site_url: evaluationForm.site_url,
        evaluation_method: 'website'
      })


      const stages = [
        { progress: 10, stage: 'Initializing Browser Agent', description: 'Starting MCP browser automation agent...' },
        { progress: 20, stage: 'Loading Website', description: 'Navigating to target URL and analyzing structure...' },
        { progress: 35, stage: 'Running 12 Pattern Detectors', description: 'Roach Motel, Fake Urgency, Drip Pricing, Hidden Subscriptions...' },
        { progress: 50, stage: 'Analyzing User Flows', description: 'Testing subscription and cancellation processes...' },
        { progress: 65, stage: 'Scanning Legal Documents', description: 'Checking terms of service and privacy policy transparency...' },
        { progress: 80, stage: 'Calculating Metrics', description: 'SAR ratios, price deltas, timer resets, navigation complexity...' },
        { progress: 95, stage: 'Generating Report', description: 'Compiling transparency score and pattern findings...' },
      ]


      analysisStage.value = 'Starting Analysis'
      analysisDescription.value = 'Initializing browser agent...'

      const analysisTask = await agentService.analyzeWebsite(
        evaluationForm.site_url,
        newEvaluation.id
      )


      let stageIndex = 0
      const pollResult = agentService.pollTaskUntilComplete(
        analysisTask.id,
        (progress) => {
          analysisProgress.value = progress

          while (stageIndex < stages.length && progress >= stages[stageIndex].progress) {
            analysisStage.value = stages[stageIndex].stage
            analysisDescription.value = stages[stageIndex].description
            stageIndex++
          }
        }
      )


      const progressAnimation = (async () => {
        for (const stage of stages) {
          analysisStage.value = stage.stage
          analysisDescription.value = stage.description

          const startProgress = analysisProgress.value
          const targetProgress = stage.progress
          const duration = 3000
          const steps = 30
          const stepDuration = duration / steps
          const progressStep = (targetProgress - startProgress) / steps

          for (let i = 0; i < steps; i++) {
            await new Promise(resolve => setTimeout(resolve, stepDuration))
            if (analysisProgress.value < stage.progress) {
              analysisProgress.value = Math.min(startProgress + (progressStep * (i + 1)), stage.progress)
            }
          }
        }
      })()


      const result = await pollResult


      analysisProgress.value = 100
      analysisStage.value = 'Report Generation'
      analysisDescription.value = 'Compiling comprehensive analysis...'

      await new Promise(resolve => setTimeout(resolve, 1000))


      if (result.result_json) {
        await darkPatternStore.updateEvaluation(newEvaluation.id, {
          evaluation_status: 'ai_only'
        })
      }


      showAnalysisDialog.value = false
      router.push(`/evaluations/${newEvaluation.id}`)

    } catch (error) {
      console.error('Failed to create evaluation:', error)
      showAnalysisDialog.value = false
    }
  }
}

</script>
