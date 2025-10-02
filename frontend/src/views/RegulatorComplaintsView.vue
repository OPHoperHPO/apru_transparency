<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Complaint Management</h1>
        <p class="text-gray-600">Review and respond to user complaints about evaluation accuracy.</p>
      </div>

      
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <v-card class="p-6 text-center border border-gray-200 rounded-xl">
          <div class="text-3xl font-bold text-red-600 mb-2">{{ stats.open }}</div>
          <p class="text-gray-700 font-medium">Open Complaints</p>
        </v-card>
        <v-card class="p-6 text-center border border-gray-200 rounded-xl">
          <div class="text-3xl font-bold text-yellow-600 mb-2">{{ stats.investigating }}</div>
          <p class="text-gray-700 font-medium">Under Investigation</p>
        </v-card>
        <v-card class="p-6 text-center border border-gray-200 rounded-xl">
          <div class="text-3xl font-bold text-green-600 mb-2">{{ stats.resolved }}</div>
          <p class="text-gray-700 font-medium">Resolved</p>
        </v-card>
        <v-card class="p-6 text-center border border-gray-200 rounded-xl">
          <div class="text-3xl font-bold text-blue-600 mb-2">{{ averageResponseTime }}h</div>
          <p class="text-gray-700 font-medium">Avg Response Time</p>
        </v-card>
      </div>

      
      <v-card class="p-6 mb-8 border border-gray-200 rounded-xl">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <v-select
            v-model="filters.status"
            :items="statusOptions"
            label="Filter by Status"
            prepend-inner-icon="mdi-filter"
            variant="outlined"
            clearable
            @update:modelValue="loadComplaints"
          />
          <v-select
            v-model="filters.type"
            :items="typeOptions"
            label="Filter by Type"
            prepend-inner-icon="mdi-tag"
            variant="outlined"
            clearable
            @update:modelValue="loadComplaints"
          />
          <v-text-field
            v-model="filters.search"
            label="Search complaints"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            clearable
            @update:modelValue="debounceSearch"
          />
        </div>
      </v-card>

      
      <v-card class="border border-gray-200 rounded-xl shadow-sm">
        <div class="p-6 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-gray-900">All Complaints</h2>
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
          <h3 class="text-xl font-semibold text-gray-900 mb-2">No complaints found</h3>
          <p class="text-gray-600">All user complaints have been resolved!</p>
        </div>
        
        <div v-else class="divide-y divide-gray-200">
          <div
            v-for="complaint in complaints"
            :key="complaint.id"
            class="p-6 hover:bg-gray-50 transition-colors"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <div class="flex items-center space-x-3 mb-2">
                  <h3 class="text-lg font-semibold text-gray-900">{{ complaint.subject }}</h3>
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
                </div>
                
                <div class="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                  <span>ID: {{ complaint.id.slice(0, 8) }}</span>
                  <span>Project: {{ complaint.project_name }}</span>
                  <span>User: {{ complaint.author_name || 'Anonymous' }}</span>
                  <span>{{ formatDate(complaint.created_at) }}</span>
                </div>
                
                <p class="text-gray-900 bg-gray-100 p-3 rounded-lg mb-4">{{ complaint.text }}</p>
                
                
                <div v-if="complaint.response_text" class="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-4">
                  <div class="flex items-center space-x-2 mb-2">
                    <v-icon icon="mdi-reply" color="blue" size="16" />
                    <span class="text-sm font-medium text-blue-800">Your Response</span>
                    <span class="text-sm text-blue-600">{{ formatDate(complaint.updated_at) }}</span>
                  </div>
                  <p class="text-blue-900">{{ complaint.response_text }}</p>
                </div>
              </div>
            </div>

            
            <div v-if="!complaint.response_text || complaint.status !== 'resolved'" class="border-t border-gray-200 pt-4">
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

      
      <v-dialog v-model="showSuccessDialog" max-width="400">
        <v-card class="pa-6 text-center">
          <v-icon icon="mdi-check-circle" color="success" size="48" class="mb-4" />
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Response Sent</h3>
          <p class="text-gray-600 mb-4">Your response has been sent to the user successfully.</p>
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
import { complaintService, type Complaint } from '@/services/complaints'

const isLoading = ref(false)
const complaints = ref<Complaint[]>([])
const showSuccessDialog = ref(false)
const submittingResponse = reactive<Record<string, boolean>>({})
const responseData = reactive<Record<string, { response_text: string, status: string }>>({})

const filters = ref({
  status: '',
  type: '',
  search: ''
})

const statusOptions = [
  { title: 'Open', value: 'open' },
  { title: 'Investigating', value: 'investigating' },
  { title: 'Resolved', value: 'resolved' },
  { title: 'Dismissed', value: 'dismissed' }
]

const typeOptions = [
  { title: 'False Positive', value: 'false_positive' },
  { title: 'Missing Pattern', value: 'missing_pattern' },
  { title: 'Incorrect Severity', value: 'incorrect_severity' },
  { title: 'Other', value: 'other' }
]

const responseStatusOptions = [
  { title: 'Under Investigation', value: 'investigating' },
  { title: 'Resolved', value: 'resolved' },
  { title: 'Dismissed', value: 'dismissed' }
]

const stats = computed(() => {
  const open = complaints.value.filter(c => c.status === 'open').length
  const investigating = complaints.value.filter(c => c.status === 'investigating').length
  const resolved = complaints.value.filter(c => c.status === 'resolved').length
  
  return { open, investigating, resolved }
})

const averageResponseTime = computed(() => {
  
  return 24
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
  const typeMap: Record<string, string> = {
    'false_positive': 'False Positive',
    'missing_pattern': 'Missing Pattern',
    'incorrect_severity': 'Incorrect Severity',
    'other': 'Other'
  }
  return typeMap[type] || type
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadComplaints() {
  try {
    isLoading.value = true
    complaints.value = await complaintService.getAllComplaints()
    
    
    complaints.value.forEach(complaint => {
      if (!responseData[complaint.id]) {
        responseData[complaint.id] = {
          response_text: complaint.response_text || '',
          status: complaint.status
        }
      }
    })
  } catch (error) {
    console.error('Failed to load complaints:', error)
  } finally {
    isLoading.value = false
  }
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

function debounceSearch() {
  
  loadComplaints()
}

onMounted(() => {
  loadComplaints()
})
</script>