<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto">
      
      <div class="mb-8">
        <div class="flex items-center space-x-4 mb-4">
          <v-btn
            @click="$router.push('/evaluations')"
            icon="mdi-arrow-left"
            variant="text"
            class="btn-hover"
          />
          <div>
            <h1 class="text-3xl font-bold text-gray-900">Analysis Report</h1>
            <p class="text-gray-600">Detailed dark pattern detection results</p>
          </div>
        </div>
      </div>
      
      <div v-if="darkPatternStore.isLoading" class="flex justify-center items-center h-64">
        <v-progress-circular indeterminate size="64" color="primary" />
      </div>

      <div v-else-if="!darkPatternStore.currentEvaluation" class="text-center py-12">
        <v-icon icon="mdi-alert-circle-outline" size="64" color="gray" class="mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">Evaluation Not Found</h3>
      </div>

      <div v-else>
        
        <v-card 
          :class="[
            'p-8 mb-8 border-4 shadow-lg rounded-2xl',
            getTrustScoreBorderClass(darkPatternStore.currentEvaluation)
          ]"
          v-motion
          :initial="{ opacity: 0, y: -20 }"
          :enter="{ opacity: 1, y: 0 }"
          :duration="600"
        >
          <div class="text-center">
            
            <div class="mb-8">
              <h1 class="text-3xl font-bold text-gray-900 mb-2">
                Analysis Report
              </h1>
              <h2 class="text-xl text-gray-700 mb-1">{{ darkPatternStore.currentEvaluation.name }}</h2>
              <p class="text-gray-600">
                {{ darkPatternStore.currentEvaluation.site_url || formatFileName(darkPatternStore.currentEvaluation.file_path) }}
              </p>
            </div>

            
            <div 
              :class="[
                'inline-block p-8 rounded-2xl border-2 mb-6',
                getTrustScoreBackgroundClass(darkPatternStore.currentEvaluation)
              ]"
            >
              <div class="flex flex-col md:flex-row justify-center items-center space-y-6 md:space-y-0 md:space-x-12">
                
                <div class="text-center">
                  <div class="relative inline-block">
                    <v-progress-circular
                      :model-value="darkPatternStore.currentEvaluation.transparency_score"
                      :size="140"
                      :width="12"
                      :color="getTrustScoreColor(darkPatternStore.currentEvaluation.transparency_score)"
                    >
                      <div class="text-center">
                        <div class="text-4xl font-bold text-gray-900">
                          {{ darkPatternStore.currentEvaluation.transparency_score.toFixed(0) }}
                        </div>
                        <div class="text-lg text-gray-600 font-medium">/ 100</div>
                      </div>
                    </v-progress-circular>
                  </div>
                  <div class="mt-4">
                    <p class="text-xl font-bold text-gray-900">Trust Score</p>
                  </div>
                </div>

                
                <div class="text-center space-y-4">
                  <div>
                    <div 
                      :class="[
                        'text-xl font-bold px-6 py-2 rounded-full',
                        getTrustScoreTextClass(darkPatternStore.currentEvaluation)
                      ]"
                    >
                      {{ getTrustScoreVerificationStatus(darkPatternStore.currentEvaluation) }}
                    </div>
                    <p class="text-gray-700 mt-2 font-medium">
                      {{ getStatusDescription(darkPatternStore.currentEvaluation.evaluation_status) }}
                    </p>
                  </div>
                  
                  <div class="text-sm text-gray-600">
                    <div class="mb-1">
                      <strong>Analyzed:</strong> {{ formatDate(darkPatternStore.currentEvaluation.created_at) }}
                    </div>
                    <div v-if="darkPatternStore.currentEvaluation.evaluated_by">
                      <strong>Verified by:</strong> {{ darkPatternStore.currentEvaluation.evaluated_by }}
                    </div>
                  </div>
                </div>

                
                <div class="text-center">
                  <div 
                    :class="[
                      'text-4xl font-bold mb-2',
                      darkPatternStore.currentEvaluation.dark_patterns_found.length > 0 ? 'text-red-600' : 'text-green-600'
                    ]"
                  >
                    {{ darkPatternStore.currentEvaluation.dark_patterns_found.length }}
                  </div>
                  <p class="text-lg font-semibold text-gray-900">Dark Patterns</p>
                  <p class="text-sm text-gray-600">detected</p>
                </div>
              </div>
            </div>

            
            <div class="bg-gray-50 rounded-xl p-6">
              <h3 class="text-lg font-semibold text-gray-900 mb-3">Analysis Summary</h3>
              <p class="text-gray-700">
                {{ getAnalysisSummary(darkPatternStore.currentEvaluation) }}
              </p>
            </div>
          </div>
        </v-card>

        
        <v-tabs v-model="activeTab" class="mb-6" color="indigo" align-tabs="center">
          <v-tab value="visual">
            <v-icon icon="mdi-eye" class="mr-2" />
            Visual Analysis (Level 1)
          </v-tab>
          <v-tab value="legal">
            <v-icon icon="mdi-gavel" class="mr-2" />
            Legal Analysis (Level 2)
          </v-tab>
          <v-tab value="behavioral">
            <v-icon icon="mdi-account-arrow-right" class="mr-2" />
            Behavioral Analysis (Level 3)
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          
          <v-tabs-window-item value="visual">
            <v-card class="p-6">
              <div class="flex items-center space-x-3 mb-6">
                <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <v-icon icon="mdi-eye" color="blue" size="24" />
                </div>
                <div>
                  <h3 class="text-xl font-bold text-gray-900">Static Visual Element Analysis</h3>
                  <p class="text-gray-600">Accessibility, readability, and visual manipulation check</p>
                </div>
              </div>

              <div class="space-y-6">
                
                <div v-if="getVisualIssues(darkPatternStore.currentEvaluation).length > 0">
                  <h4 class="text-lg font-semibold text-gray-900 mb-4">Issues Found</h4>
                  <div class="space-y-4">
                    <div
                      v-for="issue in getVisualIssues(darkPatternStore.currentEvaluation)"
                      :key="issue.id"
                      class="border border-red-200 rounded-xl p-6 bg-red-50"
                    >
                      <div class="flex items-start space-x-4">
                        <div class="w-16 h-16 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <v-icon icon="mdi-alert-circle" color="error" size="24" />
                        </div>
                        <div class="flex-1">
                          <div class="flex items-center justify-between mb-3">
                            <h5 class="font-semibold text-gray-900">{{ formatPatternType(issue.pattern_type) }}</h5>
                            <v-chip :color="getSeverityColor(issue.severity)" variant="tonal" size="small">
                              {{ issue.severity.toUpperCase() }}
                            </v-chip>
                          </div>
                          <p class="text-gray-700 mb-3">{{ issue.description }}</p>
                          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <p class="text-sm font-medium text-gray-900 mb-1">Location:</p>
                              <p class="text-sm text-gray-600">{{ issue.location }}</p>
                            </div>
                            <div v-if="issue.recommendation">
                              <p class="text-sm font-medium text-gray-900 mb-1">Recommendation:</p>
                              <p class="text-sm text-gray-600">{{ issue.recommendation }}</p>
                            </div>
                          </div>
                          
                          <div class="mt-4 bg-gray-200 rounded-lg h-32 flex items-center justify-center">
                            <div class="text-center text-gray-500">
                              <v-icon icon="mdi-image" size="32" class="mb-2" />
                              <p class="text-sm">Problem area screenshot</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                
                <div class="border border-gray-200 rounded-xl p-6">
                  <h4 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <v-icon icon="mdi-universal-access" class="mr-2" />
                    WCAG 2.1 Standards Compliance
                  </h4>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="text-center p-4 bg-green-50 rounded-lg">
                      <v-icon icon="mdi-check-circle" color="success" size="32" class="mb-2" />
                      <p class="font-medium text-green-900">Contrast</p>
                      <p class="text-sm text-green-700">Meets AA Standard</p>
                    </div>
                    <div class="text-center p-4 bg-yellow-50 rounded-lg">
                      <v-icon icon="mdi-alert-circle" color="warning" size="32" class="mb-2" />
                      <p class="font-medium text-yellow-900">Navigation</p>
                      <p class="text-sm text-yellow-700">Needs Improvement</p>
                    </div>
                    <div class="text-center p-4 bg-green-50 rounded-lg">
                      <v-icon icon="mdi-check-circle" color="success" size="32" class="mb-2" />
                      <p class="font-medium text-green-900">Text Size</p>
                      <p class="text-sm text-green-700">Readable</p>
                    </div>
                  </div>
                </div>
              </div>
            </v-card>
          </v-tabs-window-item>

          <!-- Legal Analysis Tab -->
          <v-tabs-window-item value="legal">
            <v-card class="p-6">
              <div class="flex items-center space-x-3 mb-6">
                <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <v-icon icon="mdi-gavel" color="purple" size="24" />
                </div>
                <div>
                  <h3 class="text-xl font-bold text-gray-900">Legal Document Analysis</h3>
                  <p class="text-gray-600">Checking user agreements and legal formulations</p>
                </div>
              </div>

              <!-- Loading State -->
              <div v-if="isLoadingAgentResults" class="text-center py-12">
                <v-progress-circular indeterminate color="purple" size="64" />
                <p class="text-gray-600 mt-4">Loading legal analysis results...</p>
              </div>

              <!-- Agent Analysis Results -->
              <div v-else-if="legalAnalysisResult">
                <LegalAnalysisDisplay :analysis-result="legalAnalysisResult" />
              </div>

              <!-- Fallback to Mock Data -->
              <div v-else class="space-y-6">
                
                <div v-if="getLegalIssues(darkPatternStore.currentEvaluation).length > 0">
                  <h4 class="text-lg font-semibold text-gray-900 mb-4">Legal Issues</h4>
                  <div class="space-y-4">
                    <div
                      v-for="issue in getLegalIssues(darkPatternStore.currentEvaluation)"
                      :key="issue.id"
                      class="border border-orange-200 rounded-xl p-6 bg-orange-50"
                    >
                      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        
                        <div>
                          <div class="flex items-center justify-between mb-3">
                            <h5 class="font-semibold text-gray-900">{{ formatPatternType(issue.pattern_type) }}</h5>
                            <v-chip :color="getSeverityColor(issue.severity)" variant="tonal" size="small">
                              {{ issue.severity.toUpperCase() }}
                            </v-chip>
                          </div>
                          <p class="text-gray-700 mb-3">{{ issue.description }}</p>
                          <div class="bg-white rounded-lg p-4 border-l-4 border-red-500">
                            <p class="text-sm font-medium text-red-900 mb-1">Law Violation:</p>
                            <p class="text-sm text-red-700">Consumer Protection Act, Section 22</p>
                          </div>
                        </div>

                        
                        <div>
                          <p class="text-sm font-medium text-gray-900 mb-2">Document Quote:</p>
                          <div class="bg-gray-100 rounded-lg p-4 border-l-4 border-gray-400">
                            <p class="text-sm text-gray-700 italic">
                              "Service fees may be changed unilaterally 
                              without prior notice to the customer..."
                            </p>
                          </div>
                          <div class="mt-3 bg-blue-50 rounded-lg p-4 border-l-4 border-blue-400">
                            <p class="text-sm font-medium text-blue-900 mb-1">Plain Language Explanation:</p>
                            <p class="text-sm text-blue-700">
                              This means the bank can raise fees without your consent, 
                              which is an unfair contract term.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="border border-gray-200 rounded-xl p-6">
                  <h4 class="text-lg font-semibold text-gray-900 mb-4">Legal Compliance</h4>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-4">
                      <div class="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                        <span class="text-green-900 font-medium">Consumer Protection Act</span>
                        <v-icon icon="mdi-check-circle" color="success" />
                      </div>
                      <div class="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                        <span class="text-red-900 font-medium">Unfair Contract Terms Act</span>
                        <v-icon icon="mdi-close-circle" color="error" />
                      </div>
                    </div>
                    <div class="space-y-4">
                      <div class="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                        <span class="text-green-900 font-medium">Data Protection Act</span>
                        <v-icon icon="mdi-check-circle" color="success" />
                      </div>
                      <div class="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                        <span class="text-yellow-900 font-medium">Financial Services Act</span>
                        <v-icon icon="mdi-alert-circle" color="warning" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <!-- End fallback -->
            </v-card>
          </v-tabs-window-item>

          
          <v-tabs-window-item value="behavioral">
            <v-card class="p-6">
              <div class="flex items-center space-x-3 mb-6">
                <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <v-icon icon="mdi-account-arrow-right" color="green" size="24" />
                </div>
                <div>
                  <h3 class="text-xl font-bold text-gray-900">Dynamic User Journey Analysis</h3>
                  <p class="text-gray-600">User behavior modeling and UX flow analysis</p>
                </div>
              </div>

              <div class="space-y-6">
                
                <div>
                  <h4 class="text-lg font-semibold text-gray-900 mb-4">User Scenario Analysis</h4>
                  
                  
                    <div class="border border-gray-200 rounded-xl p-6 md:px-8 mb-6">
                    <h5 class="font-semibold text-gray-900 mb-4 flex items-center">
                      <v-icon icon="mdi-cancel" class="mr-2" color="orange" />
                      Scenario: Service Unsubscription
                    </h5>
                    
                    <div class="relative">
                      
                      <div class="space-y-4">
                        <div
                          v-for="(step, index) in cancellationSteps"
                          :key="index"
                          class="grid grid-cols-[2.75rem,1fr] gap-4 md:gap-6"
                        >
                          <div class="flex flex-col items-center">
                            <div :class="[
                              'w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-sm',
                              step.problematic ? 'bg-red-500' : 'bg-blue-500'
                            ]">
                              {{ index + 1 }}
                            </div>
                            <div
                              v-if="index < cancellationSteps.length - 1"
                              class="w-px flex-1 bg-gray-300 mt-2"
                            ></div>
                          </div>
                          <div class="flex-1 pb-6 pl-2 md:pl-4">
                            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-2">
                              <h6 class="font-medium text-gray-900">{{ step.action }}</h6>
                              <span class="text-sm text-gray-500 md:text-right">{{ step.time }}</span>
                            </div>
                            <p class="text-gray-600 text-sm mb-2">{{ step.description }}</p>
                            <div v-if="step.problematic" class="bg-red-50 border border-red-200 rounded-lg p-3">
                              <p class="text-red-800 text-sm font-medium mb-1">🚨 Dark Pattern:</p>
                              <p class="text-red-700 text-sm">{{ step.issue }}</p>
                            </div>
                            
                            <div class="mt-3 bg-gray-200 rounded-lg h-24 flex items-center justify-center">
                              <span class="text-gray-500 text-sm">Step {{ index + 1 }} Screenshot</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    
                    <div class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div class="flex items-start space-x-3">
                        <v-icon icon="mdi-alert-triangle" color="warning" />
                        <div>
                          <h6 class="font-medium text-yellow-900 mb-1">Unsubscription Path Analysis</h6>
                          <p class="text-yellow-800 text-sm">
                            <strong>"Roach Motel" Pattern Detected:</strong> Unsubscription process took 7 steps and 5 minutes, 
                            while optimal path should be maximum 3 steps. 
                            This creates artificial barriers to service cancellation.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                
                <div class="border border-gray-200 rounded-xl p-6">
                  <h4 class="text-lg font-semibold text-gray-900 mb-4">User Experience Metrics</h4>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="text-center p-4 bg-red-50 rounded-lg">
                      <div class="text-2xl font-bold text-red-600 mb-2">7 steps</div>
                      <p class="text-red-900 font-medium">Service Unsubscription</p>
                      <p class="text-sm text-red-700">Norm: ≤ 3 steps</p>
                    </div>
                    <div class="text-center p-4 bg-green-50 rounded-lg">
                      <div class="text-2xl font-bold text-green-600 mb-2">2 steps</div>
                      <p class="text-green-900 font-medium">Subscription Signup</p>
                      <p class="text-sm text-green-700">Good</p>
                    </div>
                    <div class="text-center p-4 bg-yellow-50 rounded-lg">
                      <div class="text-2xl font-bold text-yellow-600 mb-2">4.2 sec</div>
                      <p class="text-yellow-900 font-medium">Loading Time</p>
                      <p class="text-sm text-yellow-700">Acceptable</p>
                    </div>
                  </div>
                </div>
              </div>
            </v-card>
          </v-tabs-window-item>
        </v-tabs-window>

        
        <div class="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <v-btn
            v-if="darkPatternStore.currentEvaluation.transparency_score < 75"
            @click="showComplaintDialog = true"
            color="red"
            size="large"
            class="rounded-xl px-8"
            prepend-icon="mdi-alert"
          >
            Submit Complaint
          </v-btn>
          
          <v-btn
            variant="outlined"
            size="large"
            class="rounded-xl px-8"
            prepend-icon="mdi-download"
          >
            Download PDF Report
          </v-btn>
          
          <v-btn
            variant="outlined"
            size="large"
            class="rounded-xl px-8"
            prepend-icon="mdi-share"
          >
            Share Results
          </v-btn>
        </div>

        
        <div v-if="darkPatternStore.currentEvaluation.evaluation_type === 'free'" 
             class="mt-12 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-8 text-white text-center">
          <h3 class="text-2xl font-bold mb-4">Are you the owner of this service?</h3>
          <p class="text-indigo-100 mb-6 max-w-2xl mx-auto">
            Get professional assessment with expert confirmation. 
            Turn transparency into your competitive advantage with Trust Score!
          </p>
          <v-btn
            @click="$router.push('/login')"
            size="large"
            class="bg-white text-indigo-600 hover:bg-gray-50 rounded-xl px-8"
          >
            Get Trust Score
          </v-btn>
        </div>
      </div>
    </div>

    
    <v-dialog v-model="showComplaintDialog" max-width="600">
      <v-card class="rounded-xl">
        <v-card-title class="text-xl font-bold text-gray-900 px-6 py-4">
          Submit Violation Complaint
        </v-card-title>
        <v-divider />
        <v-card-text class="px-6 py-6">
          <div class="space-y-4">
            <v-select
              v-model="complaintForm.type"
              :items="complaintTypes"
              item-title="label"
              item-value="value"
              label="Violation Type"
              variant="outlined"
            />
            <v-textarea
              v-model="complaintForm.description"
              label="Problem Description"
              placeholder="Describe in detail what violations you discovered..."
              variant="outlined"
              rows="4"
            />
          </div>
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn @click="showComplaintDialog = false" variant="text">Cancel</v-btn>
          <v-btn @click="submitComplaint" color="red" :loading="isSubmittingComplaint">
            Submit Complaint
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDarkPatternStore } from '@/stores/projects'
import { agentService, type DocumentAnalysisResult } from '@/services/agents'
import LegalAnalysisDisplay from '@/components/LegalAnalysisDisplay.vue'

const route = useRoute()
const router = useRouter()
const darkPatternStore = useDarkPatternStore()

const activeTab = ref('visual')
const showComplaintDialog = ref(false)
const isSubmittingComplaint = ref(false)
const legalAnalysisResult = ref<DocumentAnalysisResult | null>(null)
const isLoadingAgentResults = ref(false)

const complaintForm = ref<{
  type: 'false_positive' | 'missing_pattern' | 'incorrect_severity' | 'other' | '',
  description: string
}>({
  type: '',
  description: ''
})

const complaintTypes = [
  { label: 'False Positive', value: 'false_positive' },
  { label: 'Missed Pattern', value: 'missing_pattern' },
  { label: 'Incorrect Severity', value: 'incorrect_severity' },
  { label: 'Other Issue', value: 'other' }
]

const cancellationSteps = [
  {
    action: 'Login to Account',
    description: 'User authenticates in the system',
    time: '10 sec',
    problematic: false
  },
  {
    action: 'Search for "Subscriptions" Section',
    description: 'Section is hidden in "Settings" → "Advanced" menu',
    time: '45 sec',
    problematic: true,
    issue: 'Navigation hiding - subscriptions section is intentionally buried deep in menus'
  },
  {
    action: 'Click "Manage Subscription"',
    description: 'Navigate to active services list page',
    time: '5 sec',
    problematic: false
  },
  {
    action: 'Attempt to Cancel Subscription',
    description: 'Instead of cancel button, only "Change Plan" button is shown',
    time: '30 sec',
    problematic: true,
    issue: 'Missing clear cancel button - user is forced to change plan instead'
  },
  {
    action: 'Contact Support Chat',
    description: 'User is forced to contact support for cancellation',
    time: '120 sec',
    problematic: true,
    issue: 'Forced operator contact - artificial process complication'
  },
  {
    action: 'Wait for Operator Response',
    description: 'Average wait time in chat',
    time: '180 sec',
    problematic: true,
    issue: 'Creating time barriers for service cancellation'
  },
  {
    action: 'Confirm Cancellation',
    description: 'Operator processes cancellation request',
    time: '60 sec',
    problematic: false
  }
]

function getTrustScoreBorderClass(evaluation: any) {
  switch (evaluation.evaluation_status) {
    case 'not_evaluated':
      return 'border-gray-300 shadow-gray-200' 
    case 'ai_only':
      return 'border-yellow-400 shadow-yellow-200' 
    case 'human_verified':
      return 'border-green-500 shadow-green-200' 
    default:
      return 'border-gray-300 shadow-gray-200'
  }
}

function getTrustScoreBackgroundClass(evaluation: any) {
  switch (evaluation.evaluation_status) {
    case 'human_verified':
      return 'bg-green-50 border-green-300'
    case 'ai_only':
      return 'bg-yellow-50 border-yellow-300'
    case 'not_evaluated':
      return 'bg-gray-50 border-gray-300'
    default:
      return 'bg-gray-50 border-gray-300'
  }
}

function getTrustScoreTextClass(evaluation: any) {
  switch (evaluation.evaluation_status) {
    case 'human_verified':
      return 'text-green-800 bg-green-100'
    case 'ai_only':
      return 'text-yellow-800 bg-yellow-100'
    case 'not_evaluated':
      return 'text-gray-800 bg-gray-100'
    default:
      return 'text-gray-800 bg-gray-100'
  }
}

function getTrustScoreVerificationStatus(evaluation: any) {
  switch (evaluation.evaluation_status) {
    case 'human_verified':
      return 'High Trust Level - Expert Verified'
    case 'ai_only':
      return 'Medium Trust Level - AI Analysis Only'
    case 'not_evaluated':
      return 'Service Not Yet Fully Verified'
    default:
      return 'Unknown Status'
  }
}

function formatFileName(filePath?: string) {
  if (!filePath) return 'Document analysis'
  return filePath.split('/').pop() || 'Document analysis'
}

function getTrustScoreColor(score: number) {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
}

function getTrustScoreLabel(score: number) {
  if (score >= 80) return 'High transparency level'
  if (score >= 60) return 'Medium transparency level'
  return 'Low transparency level'
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'not_evaluated': return 'NOT EVALUATED'
    case 'ai_only': return 'AI ANALYSIS ONLY'
    case 'human_verified': return 'EXPERT VERIFIED'
    default: return status.toUpperCase()
  }
}

function getStatusDescription(status: string) {
  switch (status) {
    case 'not_evaluated': 
      return 'Service has not yet undergone full verification'
    case 'ai_only': 
      return 'Automatic AI assessment without expert confirmation'
    case 'human_verified': 
      return 'Verified and confirmed by accredited expert'
    default: 
      return ''
  }
}

function getAnalysisSummary(evaluation: any) {
  const issueCount = evaluation.dark_patterns_found.length
  const score = evaluation.transparency_score
  
  if (issueCount === 0) {
    return 'Congratulations! The analysis revealed no significant dark patterns. The service demonstrates a good level of transparency and fairness towards users.'
  } else if (score >= 70) {
    return `Found ${issueCount} potential issues, but overall transparency level remains acceptable. We recommend studying the identified remarks for further improvement.`
  } else {
    return `Found ${issueCount} serious transparency issues. We recommend exercising caution when interacting with this service and carefully reviewing all identified violations.`
  }
}

function getVisualIssues(evaluation: any) {
  return evaluation.dark_patterns_found.filter((pattern: any) => 
    ['urgency', 'scarcity', 'social_proof'].includes(pattern.pattern_type)
  ).map((pattern: any) => ({
    ...pattern,
    recommendation: getRecommendation(pattern.pattern_type)
  }))
}

function getLegalIssues(evaluation: any) {
  return evaluation.dark_patterns_found.filter((pattern: any) => 
    ['loss_aversion', 'commitment', 'reciprocity'].includes(pattern.pattern_type)
  )
}

function getRecommendation(patternType: string) {
  const recommendations: Record<string, string> = {
    urgency: 'Remove false timers and urgency indicators. Use honest information about availability.',
    scarcity: 'Show real product quantities or remove scarcity indicators.',
    social_proof: 'Use only verified reviews from real customers.',
    loss_aversion: 'Frame terms positively, avoid intimidation tactics.',
    commitment: 'Simplify cancellation process and make it more transparent.',
    reciprocity: 'Clearly state all obligations and conditions of "free" offers.'
  }
  return recommendations[patternType] || 'This element should be reconsidered.'
}

function formatPatternType(type: string) {
  const types: Record<string, string> = {
    urgency: 'False Urgency',
    scarcity: 'Artificial Scarcity',
    social_proof: 'Fake Reviews',
    loss_aversion: 'Fear Tactics',
    commitment: 'Forced Commitment',
    reciprocity: 'Hidden Reciprocity'
  }
  return types[type] || type.replace('_', ' ').split(' ').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'critical': return 'error'
    case 'high': return 'warning'
    case 'medium': return 'orange'
    case 'low': return 'info'
    default: return 'gray'
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function submitComplaint() {
  if (!complaintForm.value.type || !complaintForm.value.description) return
  
  try {
    isSubmittingComplaint.value = true
    await darkPatternStore.submitComplaint(
      darkPatternStore.currentEvaluation!.id,
      {
        text: complaintForm.value.description,
        complaint_type: complaintForm.value.type as 'false_positive' | 'missing_pattern' | 'incorrect_severity' | 'other'
      }
    )
    showComplaintDialog.value = false
    
  } catch (error) {
    console.error('Failed to submit complaint:', error)
  } finally {
    isSubmittingComplaint.value = false
  }
}

onMounted(async () => {
  const evaluationId = route.params.id as string
  if (evaluationId) {
    await darkPatternStore.fetchEvaluation(evaluationId)
    

    if (darkPatternStore.currentEvaluation?.task_id) {
      isLoadingAgentResults.value = true
      try {
        const taskResult = await agentService.getTaskResult(darkPatternStore.currentEvaluation.task_id)
        if (taskResult.result_json) {
          legalAnalysisResult.value = taskResult.result_json as DocumentAnalysisResult
        }
      } catch (error) {
        console.error('Failed to load agent results:', error)
      } finally {
        isLoadingAgentResults.value = false
      }
    }
  }
})
</script>