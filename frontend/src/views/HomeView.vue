<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-white">
    
    <header class="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <span class="text-white font-bold text-lg">T</span>
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-900">Transparency</h1>
              <p class="text-sm text-gray-500">Dark Pattern Detector</p>
            </div>
          </div>

          
          <nav class="hidden md:flex items-center space-x-8">
            <a href="#check" class="text-gray-700 hover:text-indigo-600 font-medium transition-colors">Check</a>
            <a href="#business" class="text-gray-700 hover:text-indigo-600 font-medium transition-colors">For Business</a>
            <a href="#government" class="text-gray-700 hover:text-indigo-600 font-medium transition-colors">For Government</a>
            <a href="#extension" class="text-gray-700 hover:text-indigo-600 font-medium transition-colors">Extension</a>
            <a href="#knowledge" class="text-gray-700 hover:text-indigo-600 font-medium transition-colors">Knowledge Base</a>
          </nav>

          
          <div class="flex items-center space-x-4">
            <router-link
              to="/login"
              class="px-4 py-2 text-indigo-600 font-medium hover:bg-indigo-50 rounded-lg transition-colors"
            >
              Sign In
            </router-link>
            <router-link
              to="/login"
              class="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all duration-300"
            >
              Get Started
            </router-link>
          </div>
        </div>
      </div>
    </header>

    
    <section class="py-20 px-6">
      <div class="max-w-4xl mx-auto text-center">
        <div 
          v-motion
          :initial="{ opacity: 0, y: -30 }"
          :enter="{ opacity: 1, y: 0 }"
          :duration="800"
          class="mb-8"
        >
          <h1 class="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Keep Thailand's digital economy clear and fair.
            <span class="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent">
              Fast dark-pattern checks.
            </span>
          </h1>
          <p class="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Scan any financial website or document with AI and spot risky design in seconds.
          </p>
        </div>

        
        <div 
          v-motion
          :initial="{ opacity: 0, y: 30 }"
          :enter="{ opacity: 1, y: 0 }"
          :duration="800"
          :delay="200"
          id="check"
          class="bg-white rounded-3xl shadow-2xl shadow-indigo-500/10 p-8 mb-16"
        >
          <v-tabs v-model="activeTab" class="mb-8" color="indigo" align-tabs="center">
            <v-tab value="website">
              <v-icon icon="mdi-web" class="mr-2" />
              Check Website
            </v-tab>
            <v-tab value="document">
              <v-icon icon="mdi-file-document" class="mr-2" />
              Check Document
            </v-tab>
          </v-tabs>

          <v-tabs-window v-model="activeTab">
            
            <v-tabs-window-item value="website">
              <div class="space-y-6">
                <v-text-field
                  v-model="websiteUrl"
                  label="Website URL"
                  placeholder="https://example-bank.com"
                  prepend-inner-icon="mdi-web"
                  variant="outlined"
                  size="large"
                  class="text-lg"
                  :rules="urlRules"
                />
                <v-btn
                  @click="checkWebsite"
                  :loading="isChecking"
                  size="x-large"
                  class="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-medium py-4"
                >
                  <v-icon icon="mdi-rocket-launch" class="mr-2" />
                  Check for Free
                </v-btn>
              </div>
            </v-tabs-window-item>

            
            <v-tabs-window-item value="document">
              <div class="space-y-6">
                <v-file-input
                  v-model="documentFile"
                  label="Upload Document"
                  prepend-inner-icon="mdi-paperclip"
                  variant="outlined"
                  size="large"
                  accept=".pdf,.doc,.docx,.txt"
                  show-size
                  :rules="fileRules"
                />
                <v-btn
                  @click="checkDocument"
                  :loading="isChecking"
                  :disabled="!documentFile"
                  size="x-large"
                  class="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl font-medium py-4"
                >
                  <v-icon icon="mdi-file-search" class="mr-2" />
                  Check for Free
                </v-btn>
              </div>
            </v-tabs-window-item>
          </v-tabs-window>
        </div>
      </div>
    </section>

    
    <section class="py-20 bg-gray-50">
      <div class="max-w-6xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
          <p class="text-xl text-gray-600">Three quick steps to clarity</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
          
          <div 
            v-motion
            :initial="{ opacity: 0, y: 30 }"
            :visible="{ opacity: 1, y: 0 }"
            :duration="600"
            class="text-center"
          >
            <div class="w-20 h-20 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <v-icon icon="mdi-upload" color="white" size="40" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">1. Share what to review</h3>
            <p class="text-gray-600 text-lg">
              Paste a URL or upload a document. All common formats are supported.
            </p>
          </div>

          
          <div 
            v-motion
            :initial="{ opacity: 0, y: 30 }"
            :visible="{ opacity: 1, y: 0 }"
            :duration="600"
            :delay="200"
            class="text-center"
          >
            <div class="w-20 h-20 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <v-icon icon="mdi-brain" color="white" size="40" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">2. AI scans for dark patterns</h3>
            <p class="text-gray-600 text-lg">
              Our models flag misleading language and design tricks in real time.
            </p>
          </div>

          
          <div 
            v-motion
            :initial="{ opacity: 0, y: 30 }"
            :visible="{ opacity: 1, y: 0 }"
            :duration="600"
            :delay="400"
            class="text-center"
          >
            <div class="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <v-icon icon="mdi-chart-line" color="white" size="40" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">3. Act on clear guidance</h3>
            <p class="text-gray-600 text-lg">
              Get a concise report with flagged issues and next steps for compliance.
            </p>
          </div>
        </div>
      </div>
    </section>

    
    <section class="py-20 bg-white" id="business">
      <div class="max-w-6xl mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-gray-900 mb-4">Built for Every Stakeholder</h2>
          <p class="text-xl text-gray-600">Tailored transparency tools for Thailand's digital finance ecosystem</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <div 
            v-motion
            :initial="{ opacity: 0, y: 30 }"
            :visible="{ opacity: 1, y: 0 }"
            :duration="600"
            class="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-8 border-2 border-blue-100 hover:border-blue-300 transition-all duration-300"
          >
            <div class="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center mb-6">
              <v-icon icon="mdi-account-heart" color="white" size="32" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">For Citizens</h3>
            <p class="text-blue-800 font-semibold mb-4">FREE ACCESS</p>
            <p class="text-gray-700 mb-6">
              Stay safe from hidden fees and manipulative design with easy transparency tools.
            </p>
            
            <div class="space-y-3 mb-6">
              <h4 class="font-semibold text-gray-900">✓ What You Can Do:</h4>
              <ul class="space-y-2 text-gray-700 ml-4">
                <li>• Check any fintech website for dark patterns</li>
                <li>• Send websites for professional analysis</li>
                <li>• Upload documents for legal review</li>
                <li>• Report evaluation errors</li>
                <li>• File complaints with regulators</li>
              </ul>
            </div>
            
            <div class="bg-blue-100 p-4 rounded-lg">
              <p class="text-blue-800 font-medium text-sm">
                <v-icon icon="mdi-shield-check" color="blue" size="16" class="mr-1" />
                100% Free - Funded by transparency fees from businesses
              </p>
            </div>
          </div>

          
          <div 
            v-motion
            :initial="{ opacity: 0, y: 30 }"
            :visible="{ opacity: 1, y: 0 }"
            :duration="600"
            :delay="200"
            class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 border-2 border-green-100 hover:border-green-300 transition-all duration-300"
          >
            <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mb-6">
              <v-icon icon="mdi-briefcase-check" color="white" size="32" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">For Business</h3>
            <p class="text-green-800 font-semibold mb-4">FREEMIUM MODEL</p>
            <p class="text-gray-700 mb-6">
              Build trust through verified transparency and stand out from competitors.
            </p>
            
            <div class="space-y-3 mb-4">
              <h4 class="font-semibold text-gray-900">✓ Free Services:</h4>
              <ul class="space-y-1 text-gray-700 ml-4 text-sm">
                <li>• Add your website to our database</li>
                <li>• Private evaluation testing</li>
                <li>• Document compliance checking</li>
              </ul>
            </div>
            
            <div class="space-y-3 mb-6">
              <h4 class="font-semibold text-gray-900">💎 Premium Services:</h4>
              <ul class="space-y-1 text-gray-700 ml-4 text-sm">
                <li>• Human expert verification</li>
                <li>• Trust Score certification</li>
                <li>• Marketing widget integration</li>
                <li>• Priority support & consulting</li>
              </ul>
            </div>
            
            <div class="bg-green-100 p-4 rounded-lg">
              <p class="text-green-800 font-medium text-sm">
                <v-icon icon="mdi-trophy" color="green" size="16" class="mr-1" />
                Turn transparency into your competitive advantage
              </p>
            </div>
          </div>

          
          <div 
            v-motion
            :initial="{ opacity: 0, y: 30 }"
            :visible="{ opacity: 1, y: 0 }"
            :duration="600"
            :delay="400"
            class="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-2xl p-8 border-2 border-purple-100 hover:border-purple-300 transition-all duration-300"
          >
            <div class="w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6">
              <v-icon icon="mdi-shield-account" color="white" size="32" />
            </div>
            <h3 class="text-2xl font-bold text-gray-900 mb-4">For Government</h3>
            <p class="text-purple-800 font-semibold mb-4">GRANT FUNDED</p>
            <p class="text-gray-700 mb-6">
              Cut complaint processing from 90 to 3 days with automated oversight.
            </p>
            
            <div class="space-y-3 mb-6">
              <h4 class="font-semibold text-gray-900">✓ Regulatory Tools:</h4>
              <ul class="space-y-2 text-gray-700 ml-4">
                <li>• Respond to citizen complaints</li>
                <li>• Review transparency evaluations</li>
                <li>• Verify website assessments</li>
                <li>• Access market analytics</li>
                <li>• Export legal evidence</li>
              </ul>
            </div>
            
            <div class="bg-purple-100 p-4 rounded-lg">
              <p class="text-purple-800 font-medium text-sm">
                <v-icon icon="mdi-trending-up" color="purple" size="16" class="mr-1" />
                Transform reactive regulation into proactive market protection
              </p>
            </div>
          </div>
        </div>

        
        <div class="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <a href="#check" class="block">
            <div class="text-center p-6 bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors">
              <h4 class="text-white font-bold mb-2">Citizens</h4>
              <p class="text-blue-100 text-sm">Start Checking Websites</p>
            </div>
          </a>
          
          <router-link to="/login" class="block">
            <div class="text-center p-6 bg-green-600 hover:bg-green-700 rounded-xl transition-colors">
              <h4 class="text-white font-bold mb-2">Business</h4>
              <p class="text-green-100 text-sm">Get Trust Score</p>
            </div>
          </router-link>
          
          <router-link to="/login" class="block">
            <div class="text-center p-6 bg-purple-600 hover:bg-purple-700 rounded-xl transition-colors">
              <h4 class="text-white font-bold mb-2">Regulators</h4>
              <p class="text-purple-100 text-sm">Access Dashboard</p>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    
    <section class="py-20 bg-gradient-to-r from-indigo-500 to-purple-600" id="extension">
      <div class="max-w-6xl mx-auto px-6 text-center text-white">
        <div 
          v-motion
          :initial="{ opacity: 0, y: 30 }"
          :visible="{ opacity: 1, y: 0 }"
          :duration="800"
          class="mb-12"
        >
          <h2 class="text-4xl font-bold mb-4">Real-time Protection</h2>
          <p class="text-xl opacity-90 max-w-3xl mx-auto">
            Install our browser extension for instant dark-pattern alerts on financial sites.
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div class="text-left">
            <div class="space-y-6">
              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                  <v-icon icon="mdi-shield-check" size="20" />
                </div>
                <div>
                  <h4 class="text-lg font-semibold mb-2">Automatic Detection</h4>
                  <p class="opacity-90">Extension automatically checks all fintech sites and shows Trust Score</p>
                </div>
              </div>
              
              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                  <v-icon icon="mdi-eye" size="20" />
                </div>
                <div>
                  <h4 class="text-lg font-semibold mb-2">Visual Indicators</h4>
                  <p class="opacity-90">Colored badges (green/yellow/gray) show the trust level of the site</p>
                </div>
              </div>
              
              <div class="flex items-start space-x-4">
                <div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                  <v-icon icon="mdi-file-document" size="20" />
                </div>
                <div>
                  <h4 class="text-lg font-semibold mb-2">Full Reports</h4>
                  <p class="opacity-90">One click to access detailed analysis on our website</p>
                </div>
              </div>
            </div>
          </div>

          <div class="relative">
            
            <div class="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <div class="bg-white rounded-xl p-4 shadow-2xl">
                <div class="flex items-center justify-between mb-4">
                  <div class="text-gray-900 font-semibold">CryptoTrade Pro</div>
                  <div class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    Trust Score: 85/100
                  </div>
                </div>
                <div class="text-sm text-gray-600 mb-3">✓ Verified by Expert</div>
                <div class="text-xs text-gray-500">Click for full report</div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-12 flex flex-col sm:flex-row gap-4 justify-center">
          <v-btn
            href="https://chrome.google.com/webstore"
            target="_blank"
            size="large"
            class="bg-white text-indigo-600 hover:bg-gray-50 rounded-xl px-8"
          >
            <v-icon icon="mdi-google-chrome" class="mr-2" />
            Download for Chrome
          </v-btn>
          <v-btn
            href="https://addons.mozilla.org"
            target="_blank"
            variant="outlined"
            size="large"
            class="border-white text-white hover:bg-white/10 rounded-xl px-8"
          >
            <v-icon icon="mdi-firefox" class="mr-2" />
            Download for Firefox
          </v-btn>
        </div>
      </div>
    </section>

    
    <footer class="bg-gray-900 text-white py-16">
      <div class="max-w-6xl mx-auto px-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div class="col-span-1 md:col-span-2">
            <div class="flex items-center space-x-3 mb-6">
              <div class="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span class="text-white font-bold text-lg">T</span>
              </div>
              <div>
                <h3 class="text-xl font-bold">Transparency</h3>
                <p class="text-gray-400">Dark Pattern Detector</p>
              </div>
            </div>
            <p class="text-gray-400 max-w-md">
              Driving transparency in Thailand's digital economy with ML insights and expert review.
            </p>
          </div>
          
          <div>
            <h4 class="font-semibold mb-4">Product</h4>
            <ul class="space-y-3 text-gray-400">
              <li><a href="#check" class="hover:text-white transition-colors">Check Website</a></li>
              <li><a href="#check" class="hover:text-white transition-colors">Check Document</a></li>
              <li><a href="#extension" class="hover:text-white transition-colors">Browser Extension</a></li>
              <li><router-link to="/login" class="hover:text-white transition-colors">Developer API</router-link></li>
            </ul>
          </div>
          
          <div>
            <h4 class="font-semibold mb-4">Support</h4>
            <ul class="space-y-3 text-gray-400">
              <li><a href="#knowledge" class="hover:text-white transition-colors">Knowledge Base</a></li>
              <li><a href="mailto:support@transparency.th" class="hover:text-white transition-colors">Technical Support</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Documentation</a></li>
              <li><a href="#" class="hover:text-white transition-colors">Report Bug</a></li>
            </ul>
          </div>
        </div>
        
        <div class="border-t border-gray-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p class="text-gray-400 text-sm">© 2025 Transparency. Все права защищены.</p>
          <div class="flex space-x-6 mt-4 md:mt-0">
            <a href="#" class="text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" class="text-gray-400 hover:text-white transition-colors">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>

    
    <v-dialog v-model="showAnalysisDialog" max-width="500" persistent>
      <v-card class="rounded-xl">
        <v-card-text class="text-center py-8">
          <div class="mb-6">
            <v-progress-circular
              :model-value="analysisProgress"
              :rotate="360"
              :size="100"
              :width="8"
              color="indigo"
            >
              {{ Math.round(analysisProgress) }}%
            </v-progress-circular>
          </div>
          
          <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ analysisStage }}</h3>
          <p class="text-gray-600">{{ analysisDescription }}</p>
          
          <div class="mt-6 space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600">Analyzing visual elements...</span>
              <v-icon :icon="analysisProgress > 25 ? 'mdi-check' : 'mdi-loading mdi-spin'" 
                     :color="analysisProgress > 25 ? 'success' : 'primary'" />
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600">Checking legal formulations...</span>
              <v-icon :icon="analysisProgress > 50 ? 'mdi-check' : analysisProgress > 25 ? 'mdi-loading mdi-spin' : 'mdi-circle-outline'" 
                     :color="analysisProgress > 50 ? 'success' : analysisProgress > 25 ? 'primary' : 'gray'" />
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600">Emulating user behavior...</span>
              <v-icon :icon="analysisProgress > 75 ? 'mdi-check' : analysisProgress > 50 ? 'mdi-loading mdi-spin' : 'mdi-circle-outline'" 
                     :color="analysisProgress > 75 ? 'success' : analysisProgress > 50 ? 'primary' : 'gray'" />
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600">Generating report...</span>
              <v-icon :icon="analysisProgress === 100 ? 'mdi-check' : analysisProgress > 75 ? 'mdi-loading mdi-spin' : 'mdi-circle-outline'" 
                     :color="analysisProgress === 100 ? 'success' : analysisProgress > 75 ? 'primary' : 'gray'" />
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDarkPatternStore } from '@/stores/projects'

const router = useRouter()
const darkPatternStore = useDarkPatternStore()

const activeTab = ref('website')
const websiteUrl = ref('')
const documentFile = ref<File[]>([])
const isChecking = ref(false)
const showAnalysisDialog = ref(false)
const analysisProgress = ref(0)
const analysisStage = ref('')
const analysisDescription = ref('')

const urlRules = [
  (v: string) => !!v || 'Please enter a website URL',
  (v: string) => /^https?:\/\/.+/.test(v) || 'Please enter a valid URL (starting with http:// or https://)'
]

const fileRules = [
  (v: File[]) => v.length > 0 || 'Please select a file for analysis',
  (v: File[]) => !v[0] || v[0].size < 10 * 1024 * 1024 || 'File size must not exceed 10 MB'
]

async function checkWebsite() {
  if (!websiteUrl.value) return
  
  isChecking.value = true
  showAnalysisDialog.value = true
  analysisProgress.value = 0
  
  try {
    
    const stages = [
      { progress: 25, stage: 'Interface Analysis', description: 'Scanning visual elements and UX patterns...' },
      { progress: 50, stage: 'Legal Analysis', description: 'Checking user agreements and policies...' },
      { progress: 75, stage: 'Behavioral Analysis', description: 'Modeling user scenarios...' },
      { progress: 100, stage: 'Completion', description: 'Generating final report and recommendations...' }
    ]
    
    for (const stage of stages) {
      analysisStage.value = stage.stage
      analysisDescription.value = stage.description
      
      
      const startProgress = analysisProgress.value
      const targetProgress = stage.progress
      const duration = 2000 
      const steps = 50
      const stepDuration = duration / steps
      const progressStep = (targetProgress - startProgress) / steps
      
      for (let i = 0; i < steps; i++) {
        await new Promise(resolve => setTimeout(resolve, stepDuration))
        analysisProgress.value = startProgress + (progressStep * (i + 1))
      }
      
      await new Promise(resolve => setTimeout(resolve, 500)) 
    }
    
    
    const evaluation = await darkPatternStore.createEvaluation({
      name: `Analysis for ${websiteUrl.value}`,
      site_url: websiteUrl.value,
      evaluation_method: 'website'
    })
    
    showAnalysisDialog.value = false
    router.push(`/evaluations/${evaluation.id}`)
    
  } catch (error) {
    console.error('Analysis failed:', error)
    showAnalysisDialog.value = false
  } finally {
    isChecking.value = false
  }
}

async function checkDocument() {
  if (!documentFile.value[0]) return
  
  isChecking.value = true
  showAnalysisDialog.value = true
  analysisProgress.value = 0
  
  try {
    
    const stages = [
      { progress: 30, stage: 'Text Extraction', description: 'Converting and analyzing document content...' },
      { progress: 70, stage: 'Legal Analysis', description: 'Looking for hidden conditions and unfair terms...' },
      { progress: 100, stage: 'Completion', description: 'Generating document transparency report...' }
    ]
    
    for (const stage of stages) {
      analysisStage.value = stage.stage
      analysisDescription.value = stage.description
      
      const startProgress = analysisProgress.value
      const targetProgress = stage.progress
      const duration = 2000
      const steps = 50
      const stepDuration = duration / steps
      const progressStep = (targetProgress - startProgress) / steps
      
      for (let i = 0; i < steps; i++) {
        await new Promise(resolve => setTimeout(resolve, stepDuration))
        analysisProgress.value = startProgress + (progressStep * (i + 1))
      }
      
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    
    const evaluation = await darkPatternStore.createEvaluation({
      name: `Analysis for ${documentFile.value[0].name}`,
      evaluation_method: 'document',
      file: documentFile.value[0]
    })
    
    showAnalysisDialog.value = false
    router.push(`/evaluations/${evaluation.id}`)
    
  } catch (error) {
    console.error('Analysis failed:', error)
    showAnalysisDialog.value = false
  } finally {
    isChecking.value = false
  }
}


onMounted(() => {
  document.addEventListener('click', (e) => {
    const target = e.target as HTMLAnchorElement
    if (target.tagName === 'A' && target.hash) {
      e.preventDefault()
      const element = document.querySelector(target.hash)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }
  })
})
</script>
