<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Complaints Management</h1>
        <p class="text-gray-600">Submit and manage complaints about evaluation accuracy and platform issues.</p>
      </div>

      
      <div v-if="canSubmitComplaint" class="mb-8">
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="regular">Platform Complaint</v-tab>
          <v-tab value="formal">Formal Legal Complaint</v-tab>
        </v-tabs>

        
        <v-card v-show="activeTab === 'regular'" class="p-8 border border-gray-200 rounded-xl shadow-sm">
        <div class="flex items-center space-x-3 mb-6">
          <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
            <v-icon icon="mdi-alert-circle" color="red" size="24" />
          </div>
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Submit a Complaint</h2>
            <p class="text-gray-600 text-sm">Report issues with evaluations or platform functionality</p>
          </div>
        </div>
        
        <v-form @submit.prevent="handleSubmitComplaint" ref="form">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <v-select
              v-model="complaintForm.project"
              :items="evaluationOptions"
              label="Select Website/Document"
              prepend-inner-icon="mdi-shield-search"
              variant="outlined"
              item-title="text"
              item-value="value"
              required
              class="rounded-lg"
            />
            
            <v-select
              v-model="complaintForm.complaint_type"
              :items="complaintTypes"
              label="Complaint Type"
              prepend-inner-icon="mdi-alert"
              variant="outlined" 
              item-title="text"
              item-value="value"
              required
              class="rounded-lg"
            />
          </div>
          
          <v-text-field
            v-model="complaintForm.subject"
            label="Subject"
            placeholder="Brief description of the issue"
            prepend-inner-icon="mdi-format-title"
            variant="outlined"
            required
            class="mb-6 rounded-lg"
          />
          
          <v-textarea
            v-model="complaintForm.text"
            label="Describe your complaint in detail"
            placeholder="Please provide detailed information about the issue..."
            prepend-inner-icon="mdi-message-text"
            variant="outlined"
            rows="4"
            required
            class="mb-6 rounded-lg"
          />
          
          <div class="flex justify-between items-center">
            <div class="text-sm text-gray-600">
              <v-icon icon="mdi-shield-check" color="success" size="16" class="mr-1" />
              Your complaint will be reviewed by our regulatory team within 48 hours
            </div>
            <v-btn
              type="submit"
              :loading="isSubmitting"
              size="large"
              class="bg-gradient-to-r from-red-500 to-pink-500 text-white px-8 rounded-xl"
            >
              <v-icon icon="mdi-send" class="mr-2" />
              Submit Complaint
            </v-btn>
          </div>
        </v-form>
        </v-card>

        
        <v-card v-show="activeTab === 'formal'" class="p-8 border border-gray-200 rounded-xl shadow-sm">
          <div class="flex items-center space-x-3 mb-6">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <v-icon icon="mdi-gavel" color="blue" size="24" />
            </div>
            <div>
              <h2 class="text-xl font-semibold text-gray-900">Formal Legal Complaint</h2>
              <p class="text-gray-600 text-sm">Submit a formal complaint to Thai Consumer Protection Council</p>
            </div>
          </div>

          <div class="bg-blue-50 p-4 rounded-lg mb-6 border border-blue-200">
            <h3 class="font-semibold text-blue-900 mb-2">ЖАЛОБА В СОВЕТ ПО ЗАЩИТЕ ПРАВ ПОТРЕБИТЕЛЕЙ ТАИЛАНДА</h3>
            <p class="text-blue-800 text-sm">на нарушение прав потребителя и несоответствие договора требованиям тайского законодательства</p>
          </div>
          
          <v-form @submit.prevent="handleSubmitFormalComplaint" ref="formalForm">
            
            <div class="mb-8">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <v-text-field
                  v-model="formalComplaintForm.applicant_name"
                  label="Full Name (Ф.И.О. заявителя)"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  required
                  class="rounded-lg"
                />
                <v-text-field
                  v-model="formalComplaintForm.applicant_address"
                  label="Address (Адрес заявителя)"
                  prepend-inner-icon="mdi-map-marker"
                  variant="outlined"
                  required
                  class="rounded-lg"
                />
                <v-text-field
                  v-model="formalComplaintForm.applicant_phone"
                  label="Phone Number (Контактный телефон)"
                  prepend-inner-icon="mdi-phone"
                  variant="outlined"
                  required
                  class="rounded-lg"
                />
                <v-text-field
                  v-model="formalComplaintForm.applicant_email"
                  label="Email (электронная почта)"
                  prepend-inner-icon="mdi-email"
                  variant="outlined"
                  type="email"
                  required
                  class="rounded-lg"
                />
              </div>
            </div>

            
            <div class="mb-8">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Contract Information</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <v-text-field
                  v-model="formalComplaintForm.company_name"
                  label="Company Name (название компании)"
                  prepend-inner-icon="mdi-domain"
                  variant="outlined"
                  required
                  class="rounded-lg"
                />
                <v-text-field
                  v-model="formalComplaintForm.contract_number"
                  label="Contract Number (№ договора)"
                  prepend-inner-icon="mdi-file-document"
                  variant="outlined"
                  required
                  class="rounded-lg"
                />
                <v-text-field
                  v-model="formalComplaintForm.contract_date"
                  label="Contract Date (дата договора)"
                  prepend-inner-icon="mdi-calendar"
                  variant="outlined"
                  type="date"
                  required
                  class="rounded-lg"
                />
              </div>
            </div>

            
            <div class="mb-8">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Identified Violations</h3>
              
              <div class="space-y-4 mb-6">
                <v-checkbox
                  v-model="formalComplaintForm.violations.unilateral_changes"
                  label="Одностороннее изменение условий договора"
                  color="primary"
                  hide-details
                />
                <v-checkbox
                  v-model="formalComplaintForm.violations.excessive_penalties"
                  label="Наличие штрафов в размере 20% от суммы договора"
                  color="primary"
                  hide-details
                />
                <v-checkbox
                  v-model="formalComplaintForm.violations.vague_terms"
                  label="Расплывчатые формулировки об оказываемой услуге"
                  color="primary"
                  hide-details
                />
                <v-checkbox
                  v-model="formalComplaintForm.violations.limited_liability"
                  label="Крайне ограниченная ответственность Исполнителя"
                  color="primary"
                  hide-details
                />
              </div>

              <v-textarea
                v-model="formalComplaintForm.additional_violations"
                label="Additional Violations (Дополнительные нарушения)"
                placeholder="Describe any additional violations..."
                prepend-inner-icon="mdi-message-text"
                variant="outlined"
                rows="3"
                class="rounded-lg"
              />
            </div>

            
            <div class="mb-8">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">В связи с вышеизложенным ПРОШУ:</h3>
              
              <div class="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <ul class="space-y-2 text-gray-700">
                  <li>• провести проверку договора на предмет соответствия требованиям тайского законодательства о защите прав потребителей;</li>
                  <li>• признать вышеуказанные условия договора недействительными в части нарушения моих прав;</li>
                  <li>• обязать Исполнителя привести договорные условия в соответствие с законодательством и предоставить мне отчёт о результатах проверки;</li>
                  <li>• рассмотреть вопрос о привлечении Исполнителя к ответственности за нарушение прав потребителей.</li>
                </ul>
              </div>
            </div>

            
            <div class="mb-8">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">Attachments (Приложения)</h3>
              
              <div class="space-y-4">
                <v-file-input
                  v-model="formalComplaintForm.contract_file"
                  label="Contract Copy (Копия договора)"
                  prepend-icon="mdi-file-document"
                  variant="outlined"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  class="rounded-lg"
                />
                
                <v-file-input
                  v-model="formalComplaintForm.correspondence_files"
                  label="Correspondence (Переписка с Исполнителем)"
                  prepend-icon="mdi-email-multiple"
                  variant="outlined"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                  multiple
                  class="rounded-lg"
                />
              </div>
            </div>

            
            <div class="mb-8">
              <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <p class="text-gray-700 mb-3">Подпись:</p>
                <v-text-field
                  v-model="formalComplaintForm.digital_signature"
                  label="Digital Signature (Цифровая подпись)"
                  prepend-inner-icon="mdi-draw"
                  variant="outlined"
                  placeholder="Enter your full name as digital signature"
                  required
                  class="rounded-lg"
                />
                <p class="text-sm text-gray-500 mt-2">By typing your full name, you confirm the authenticity of this complaint.</p>
              </div>
            </div>
            
            <div class="flex justify-between items-center">
              <div class="text-sm text-gray-600">
                <v-icon icon="mdi-scale-balance" color="primary" size="16" class="mr-1" />
                This formal complaint will be submitted to Thai Consumer Protection Council
              </div>
              <v-btn
                type="submit"
                :loading="isSubmittingFormal"
                size="large"
                class="bg-gradient-to-r from-blue-500 to-indigo-500 text-white px-8 rounded-xl"
              >
                <v-icon icon="mdi-gavel" class="mr-2" />
                Submit Formal Complaint
              </v-btn>
            </div>
          </v-form>
        </v-card>
      </div>

      
      <v-card v-else class="p-8 mb-8 border border-orange-200 rounded-xl shadow-sm bg-orange-50">
        <div class="flex items-center space-x-3 mb-4">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
            <v-icon icon="mdi-information" color="orange" size="24" />
          </div>
          <div>
            <h2 class="text-xl font-semibold text-gray-900">Complaint Submissions</h2>
            <p class="text-gray-600 text-sm">Information about complaint submission access</p>
          </div>
        </div>
        
        <div class="bg-white p-4 rounded-lg border border-orange-200">
          <p class="text-gray-700 mb-2">
            <span class="font-medium">{{ authStore.user?.user_type === 'business' ? 'Business users' : 'Government officials' }}</span> 
            cannot submit complaints as per platform policy.
          </p>
          <p class="text-gray-600 text-sm">
            {{ authStore.user?.user_type === 'business' 
              ? 'Business accounts can view evaluation results and work with regulatory responses through the dashboard.' 
              : 'Government accounts have access to all complaints through the regulatory dashboard for oversight and response.' }}
          </p>
        </div>
      </v-card>

      
      <v-card class="p-6 border border-gray-200 rounded-xl shadow-sm">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <v-icon icon="mdi-history" color="blue" size="24" />
            </div>
            <div>
              <h2 class="text-xl font-semibold text-gray-900">
                {{ authStore.user?.role === 'regulator' || authStore.user?.role === 'admin' ? 'All Complaints' : 'My Complaints' }}
              </h2>
              <p class="text-gray-600 text-sm">Track the status of your submitted complaints</p>
            </div>
          </div>
          
          <div class="flex space-x-2">
            <v-btn variant="outlined" prepend-icon="mdi-filter">
              Filter
            </v-btn>
            <v-btn variant="outlined" prepend-icon="mdi-refresh" @click="loadComplaints">
              Refresh
            </v-btn>
          </div>
        </div>
        
        <div v-if="isLoading" class="flex justify-center items-center h-48">
          <v-progress-circular indeterminate size="64" color="primary" />
        </div>
        
        <div v-else-if="complaints.length === 0" class="text-center py-12">
          <v-icon icon="mdi-check-circle" color="success" size="64" class="mb-4" />
          <h3 class="text-xl font-semibold text-gray-900 mb-2">No complaints submitted yet</h3>
          <p class="text-gray-600">Submit your first complaint using the form above</p>
        </div>
        
        <div v-else class="space-y-4">
          <div
            v-for="complaint in complaints"
            :key="complaint.id"
            class="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-all duration-200"
          >
            <div class="flex items-start justify-between mb-4">
              <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ complaint.subject }}</h3>
                <div class="flex items-center space-x-4 mb-3">
                  <v-chip
                    :color="getComplaintStatusColor(complaint.status)"
                    variant="tonal"
                    size="small"
                  >
                    {{ getStatusLabel(complaint.status) }}
                  </v-chip>
                  
                  <v-chip variant="outlined" size="small">
                    {{ formatComplaintType(complaint.complaint_type) }}
                  </v-chip>
                  
                  <span class="text-sm text-gray-500">
                    Project: {{ complaint.project_name }}
                  </span>
                  
                  
                  <span v-if="authStore.user?.role === 'regulator' || authStore.user?.role === 'admin'" class="text-sm text-gray-500">
                    ID: {{ complaint.id.slice(0, 8) }}
                  </span>
                  <span v-if="authStore.user?.role === 'regulator' || authStore.user?.role === 'admin'" class="text-sm text-gray-500">
                    User: {{ complaint.author_name || 'Anonymous' }}
                  </span>
                </div>
              </div>
              
              <div class="text-right">
                <div class="text-sm text-gray-500 mb-1">
                  Submitted {{ formatDate(complaint.created_at) }}
                </div>
                <div v-if="complaint.resolved_at" class="text-sm text-green-600">
                  Resolved {{ formatDate(complaint.resolved_at) }}
                </div>
              </div>
            </div>
            
            <p class="text-gray-900 mb-4 bg-gray-50 p-4 rounded-lg">{{ complaint.text }}</p>
            
            
            <div v-if="complaint.response_text" class="border-t border-gray-200 pt-4">
              <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div class="flex items-center space-x-2 mb-2">
                  <v-icon icon="mdi-reply" color="blue" size="16" />
                  <span class="text-sm font-medium text-blue-800">
                    {{ authStore.user?.role === 'regulator' || authStore.user?.role === 'admin' ? 'Your Response' : 'Official Response' }}
                  </span>
                  <span class="text-sm text-blue-600" v-if="complaint.responded_by || (authStore.user?.role === 'regulator' || authStore.user?.role === 'admin')">
                    {{ authStore.user?.role === 'regulator' || authStore.user?.role === 'admin' ? formatDate(complaint.updated_at) : 'by Regulator' }}
                  </span>
                </div>
                <p class="text-blue-900">{{ complaint.response_text }}</p>
              </div>
            </div>
            
            <div v-else-if="complaint.status === 'investigating'" class="border-t border-gray-200 pt-4">
              <div class="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <div class="flex items-center space-x-2">
                  <v-icon icon="mdi-clock" color="warning" size="16" />
                  <span class="text-sm font-medium text-yellow-800">Under Investigation</span>
                </div>
                <p class="text-yellow-700 text-sm mt-1">Our regulatory team is currently reviewing your complaint.</p>
              </div>
            </div>

            
            <div v-if="(authStore.user?.role === 'regulator' || authStore.user?.role === 'admin') && (!complaint.response_text || complaint.status !== 'resolved')" class="border-t border-gray-200 pt-4 mt-4">
              <div class="bg-white border border-gray-200 rounded-lg p-4">
                <h4 class="text-md font-semibold text-gray-900 mb-3">
                  {{ complaint.response_text ? 'Update Response' : 'Respond to Complaint' }}
                </h4>
                
                <v-form @submit.prevent="submitResponse(complaint)" :ref="`form-${complaint.id}`">
                  <div class="space-y-4">
                    <v-textarea
                      v-model="responseData[complaint.id].response_text"
                      label="Response"
                      placeholder="Provide a detailed response to this complaint..."
                      variant="outlined"
                      rows="3"
                      required
                    />
                    
                    <div class="flex items-center justify-between">
                      <v-select
                        v-model="responseData[complaint.id].status"
                        :items="responseStatusOptions"
                        label="Status"
                        variant="outlined"
                        class="max-w-xs"
                        required
                      />
                      
                      <v-btn
                        type="submit"
                        :loading="submittingResponse[complaint.id]"
                        color="primary"
                        prepend-icon="mdi-send"
                      >
                        {{ complaint.response_text ? 'Update Response' : 'Send Response' }}
                      </v-btn>
                    </div>
                  </div>
                </v-form>
              </div>
            </div>
          </div>
        </div>
      </v-card>

      
      <v-dialog v-model="showSuccessDialog" max-width="500">
        <v-card class="pa-6 text-center">
          <v-icon icon="mdi-check-circle" color="success" size="64" class="mb-4" />
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Complaint Submitted Successfully</h2>
          <p class="text-gray-600 mb-6">Your complaint has been submitted and will be reviewed by our regulatory team within 48 hours.</p>
          <v-btn color="success" @click="showSuccessDialog = false">
            Got it
          </v-btn>
        </v-card>
      </v-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import { useDarkPatternStore } from '@/stores/projects'
import { complaintService, type Complaint } from '@/services/complaints'
import { useAuthStore } from '@/stores/auth'

const darkPatternStore = useDarkPatternStore()
const authStore = useAuthStore()

const form = ref()
const formalForm = ref()
const activeTab = ref('regular')
const isSubmitting = ref(false)
const isSubmittingFormal = ref(false)
const isLoading = ref(false)
const complaints = ref<Complaint[]>([])
const showSuccessDialog = ref(false)
const submittingResponse = reactive<Record<string, boolean>>({})
const responseData = reactive<Record<string, { response_text: string, status: string }>>({})

const formalComplaintForm = ref({
  applicant_name: '',
  applicant_address: '',
  applicant_phone: '',
  applicant_email: '',
  company_name: '',
  contract_number: '',
  contract_date: '',
  violations: {
    unilateral_changes: false,
    excessive_penalties: false,
    vague_terms: false,
    limited_liability: false
  },
  additional_violations: '',
  contract_file: null as File[] | null,
  correspondence_files: [] as File[],
  digital_signature: ''
})

const complaintForm = ref({
  project: '',
  complaint_type: '',
  subject: '',
  text: ''
})

const complaintTypes = [
  { text: 'False Positive - Incorrectly flagged as dark pattern', value: 'false_positive' },
  { text: 'Missing Pattern - Dark pattern not detected', value: 'missing_pattern' },
  { text: 'Incorrect Severity - Wrong risk assessment', value: 'incorrect_severity' },
  { text: 'Formal Legal Complaint - Consumer protection violation', value: 'formal_legal' },
  { text: 'Other Issue', value: 'other' }
]

const responseStatusOptions = [
  { title: 'Under Investigation', value: 'investigating' },
  { title: 'Resolved', value: 'resolved' },
  { title: 'Dismissed', value: 'dismissed' }
]

const evaluationOptions = computed(() => {
  return darkPatternStore.evaluations.map(evaluation => ({
    text: `${evaluation.name} (${evaluation.site_url})`,
    value: evaluation.id
  }))
})

const canSubmitComplaint = computed(() => {
  const user = authStore.user
  
  
  return user?.role === 'individual' || user?.user_type === 'individual'
})

function getComplaintStatusColor(status: string) {
  switch (status) {
    case 'open': return 'error'
    case 'investigating': return 'warning'
    case 'resolved': return 'success'
    case 'dismissed': return 'gray'
    default: return 'gray'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'open': return 'Open'
    case 'investigating': return 'Investigating'
    case 'resolved': return 'Resolved'
    case 'dismissed': return 'Dismissed'
    default: return status
  }
}

function formatComplaintType(type: string) {
  return complaintTypes.find(t => t.value === type)?.text || type
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

async function handleSubmitComplaint() {
  const { valid } = await form.value.validate()
  
  if (valid) {
    try {
      isSubmitting.value = true
      
      await complaintService.submitComplaint(complaintForm.value)
      
      
      complaintForm.value = {
        project: '',
        complaint_type: '',
        subject: '',
        text: ''
      }
      
      showSuccessDialog.value = true
      await loadComplaints()
      
    } catch (error) {
      console.error('Failed to submit complaint:', error)
    } finally {
      isSubmitting.value = false
    }
  }
}

async function handleSubmitFormalComplaint() {
  const { valid } = await formalForm.value.validate()
  
  if (valid) {
    try {
      isSubmittingFormal.value = true
      
      
      const formalComplaintData = {
        type: 'formal_legal',
        subject: `Formal Complaint to Thai Consumer Protection Council - ${formalComplaintForm.value.company_name}`,
        text: generateFormalComplaintText(),
        applicant_data: {
          name: formalComplaintForm.value.applicant_name,
          address: formalComplaintForm.value.applicant_address,
          phone: formalComplaintForm.value.applicant_phone,
          email: formalComplaintForm.value.applicant_email
        },
        contract_data: {
          company_name: formalComplaintForm.value.company_name,
          contract_number: formalComplaintForm.value.contract_number,
          contract_date: formalComplaintForm.value.contract_date
        },
        violations: formalComplaintForm.value.violations,
        additional_violations: formalComplaintForm.value.additional_violations,
        digital_signature: formalComplaintForm.value.digital_signature
      }
      
      
      await complaintService.submitComplaint({
        project: '', 
        complaint_type: 'formal_legal',
        subject: formalComplaintData.subject,
        text: formalComplaintData.text
      })
      
      
      formalComplaintForm.value = {
        applicant_name: '',
        applicant_address: '',
        applicant_phone: '',
        applicant_email: '',
        company_name: '',
        contract_number: '',
        contract_date: '',
        violations: {
          unilateral_changes: false,
          excessive_penalties: false,
          vague_terms: false,
          limited_liability: false
        },
        additional_violations: '',
        contract_file: null,
        correspondence_files: [],
        digital_signature: ''
      }
      
      activeTab.value = 'regular' 
      showSuccessDialog.value = true
      await loadComplaints()
      
    } catch (error) {
      console.error('Failed to submit formal complaint:', error)
    } finally {
      isSubmittingFormal.value = false
    }
  }
}

function generateFormalComplaintText() {
  const form = formalComplaintForm.value
  const currentDate = new Date().toLocaleDateString('ru-RU')
  
  let violationsList = []
  if (form.violations.unilateral_changes) {
    violationsList.push('1. Одностороннее изменение условий договора со стороны Исполнителя без согласия Заказчика, что противоречит принципам добросовестности и равенства сторон согласно Закону о защите прав потребителей Тайского Королевства.')
  }
  if (form.violations.excessive_penalties) {
    violationsList.push('2. Наличие штрафов в размере 20% от суммы договора при расторжении по инициативе Заказчика, что является чрезмерно обременительным и необоснованным условием в договоре.')
  }
  if (form.violations.vague_terms) {
    violationsList.push('3. Расплывчатые формулировки об оказываемой услуге, не позволяющие однозначно определить точный перечень и качество услуг, что нарушает требование о прозрачности и ясности договорных условий.')
  }
  if (form.violations.limited_liability) {
    violationsList.push('4. Крайне ограниченная ответственность Исполнителя, фактически исключающая возможность возмещения убытков и ущерба, причинённых ненадлежащим оказанием услуг, что противоречит нормам законодательства о защите прав потребителей.')
  }

  return `
ЖАЛОБА В СОВЕТ ПО ЗАЩИТЕ ПРАВ ПОТРЕБИТЕЛЕЙ ТАИЛАНДА
на нарушение прав потребителя и несоответствие договора требованиям тайского законодательства

${form.applicant_name}
${form.applicant_address}
${form.applicant_phone}, ${form.applicant_email}

Дата: ${currentDate}

Я являюсь потребителем услуг, оказываемых компанией ${form.company_name} (далее — Исполнитель).

Внимательно изучив договор № ${form.contract_number} от ${form.contract_date}, заключенный между мной и Исполнителем, выявил(а) следующие нарушения моих прав и требований тайского законодательства в сфере защиты прав потребителей:

${violationsList.join('\n\n')}

${form.additional_violations ? '\nДополнительные нарушения:\n' + form.additional_violations : ''}

В связи с вышеизложенным ПРОШУ:
- провести проверку договора на предмет соответствия требованиям тайского законодательства о защите прав потребителей;
- признать вышеуказанные условия договора недействительными в части нарушения моих прав;
- обязать Исполнителя привести договорные условия в соответствие с законодательством и предоставить мне отчёт о результатах проверки;
- рассмотреть вопрос о привлечении Исполнителя к ответственности за нарушение прав потребителей.

Приложения:
- Копия договора № ${form.contract_number} от ${form.contract_date}
- Копии переписки с Исполнителем (если имеются)

Подпись: ${form.digital_signature}
Дата: ${currentDate}
`
}

async function submitResponse(complaint: Complaint) {
  try {
    submittingResponse[complaint.id] = true
    
    const response = responseData[complaint.id]
    const validResponse = {
      response_text: response.response_text,
      status: response.status as 'investigating' | 'resolved' | 'dismissed'
    }
    await complaintService.respondToComplaint(complaint.id, validResponse)
    
    showSuccessDialog.value = true
    await loadComplaints()
  } catch (error) {
    console.error('Failed to submit response:', error)
  } finally {
    submittingResponse[complaint.id] = false
  }
}

async function loadComplaints() {
  try {
    isLoading.value = true
    
    
    if (authStore.user?.role === 'regulator' || authStore.user?.role === 'admin') {
      complaints.value = await complaintService.getAllComplaints()
      
      
      complaints.value.forEach(complaint => {
        if (!responseData[complaint.id]) {
          responseData[complaint.id] = {
            response_text: complaint.response_text || '',
            status: complaint.status
          }
        }
      })
    } else {
      complaints.value = await complaintService.getMyComplaints()
    }
  } catch (error) {
    console.error('Failed to load complaints:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  await darkPatternStore.fetchEvaluations()
  await loadComplaints()
})
</script>