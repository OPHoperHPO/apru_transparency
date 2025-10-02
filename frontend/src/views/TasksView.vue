<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-6xl mx-auto">
      
      <div 
        v-motion
        :initial="{ opacity: 0, y: -20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="500"
        class="flex flex-col sm:flex-row sm:items-center justify-between mb-8"
      >
        <div>
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Tasks</h1>
          <p class="text-gray-600">Submit and monitor processing tasks for your projects.</p>
        </div>
        
        <v-btn
          @click="showSubmitDialog = true"
          color="primary"
          size="large"
          class="btn-hover mt-4 sm:mt-0"
          prepend-icon="mdi-rocket-launch"
        >
          Submit Task
        </v-btn>
      </div>

      
      <v-card 
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0 }"
        :duration="500"
        class="p-6 mb-8"
      >
        <h2 class="text-xl font-semibold text-gray-900 mb-6">Quick Task Submission</h2>
        
        <v-form @submit.prevent="submitTask" ref="form">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
            <v-text-field
              v-model="taskForm.url"
              :rules="urlRules"
              label="URL to Process"
              prepend-inner-icon="mdi-web"
              variant="outlined"
              required
            />
            
            <v-select
              v-model="taskForm.project"
              :items="projectOptions"
              label="Associated Project (Optional)"
              prepend-inner-icon="mdi-briefcase"
              variant="outlined"
              clearable
            />
            
            <v-select
              v-model="taskForm.priority"
              :items="priorityOptions"
              label="Priority"
              prepend-inner-icon="mdi-flag"
              variant="outlined"
            />
          </div>
          
          <v-btn
            type="submit"
            :loading="isSubmitting"
            color="primary"
            class="btn-hover"
            prepend-icon="mdi-send"
          >
            Submit Task
          </v-btn>
        </v-form>
      </v-card>

      
      <v-card 
        v-motion
        :initial="{ opacity: 0, y: 20 }"
        :enter="{ opacity: 1, y: 0 }"
        :delay="200"
        :duration="500"
        class="p-6"
      >
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-gray-900">Recent Tasks</h2>
          <v-btn
            @click="refreshTasks"
            variant="outlined"
            size="small"
            icon="mdi-refresh"
          />
        </div>

        <div v-if="isLoading" class="flex justify-center items-center h-48">
          <v-progress-circular indeterminate size="64" color="primary" />
        </div>

        <div v-else-if="tasks.length === 0" class="text-center py-12">
          <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <v-icon icon="mdi-clipboard-outline" size="48" color="gray" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">No tasks yet</h3>
          <p class="text-gray-600 mb-6">Submit your first task to get started with processing.</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
          >
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-2">
                <v-chip
                  :color="getStatusColor(task.status)"
                  variant="tonal"
                  size="small"
                >
                  {{ task.status.replace('_', ' ').toUpperCase() }}
                </v-chip>
                
                <v-chip
                  :color="getPriorityColor(task.priority)"
                  variant="outlined"
                  size="small"
                >
                  {{ task.priority.toUpperCase() }}
                </v-chip>
              </div>
              
              <p class="font-medium text-gray-900 mb-1">{{ task.url }}</p>
              <p class="text-sm text-gray-600">
                Created {{ formatDate(task.created_at) }}
              </p>
              
              <div v-if="task.progress !== null" class="mt-2">
                <v-progress-linear
                  :model-value="task.progress"
                  height="6"
                  rounded
                  color="primary"
                />
                <p class="text-xs text-gray-500 mt-1">{{ task.progress }}% complete</p>
              </div>
            </div>
            
            <div class="flex items-center space-x-2 ml-4">
              <v-btn
                @click="viewTaskDetails(task)"
                variant="outlined"
                size="small"
                icon="mdi-eye"
              />
              
              <v-btn
                v-if="task.status === 'done'"
                @click="downloadResult(task)"
                variant="outlined"
                size="small"
                icon="mdi-download"
              />
            </div>
          </div>
        </div>
      </v-card>
    </div>

    
    <v-dialog v-model="showDetailsDialog" max-width="600">
      <v-card v-if="selectedTask" class="rounded-xl">
        <v-card-title class="text-xl font-semibold bg-gray-50 px-6 py-4">
          Task Details
        </v-card-title>
        
        <v-card-text class="p-6">
          <div class="space-y-4">
            <div>
              <h3 class="text-sm font-medium text-gray-500 mb-1">URL</h3>
              <p class="text-gray-900">{{ selectedTask.url }}</p>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-gray-500 mb-1">Status</h3>
              <v-chip
                :color="getStatusColor(selectedTask.status)"
                variant="tonal"
                size="small"
              >
                {{ selectedTask.status.replace('_', ' ').toUpperCase() }}
              </v-chip>
            </div>
            
            <div v-if="selectedTask.error">
              <h3 class="text-sm font-medium text-gray-500 mb-1">Error</h3>
              <v-alert type="error" variant="tonal" class="text-sm">
                {{ selectedTask.error }}
              </v-alert>
            </div>
            
            <div v-if="selectedTask.result_json">
              <h3 class="text-sm font-medium text-gray-500 mb-1">Result</h3>
              <pre class="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">{{ JSON.stringify(selectedTask.result_json, null, 2) }}</pre>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn @click="showDetailsDialog = false" variant="text">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useProjectStore } from '@/stores/projects'
import { taskService, type Task, type CreateTaskData } from '@/services/tasks'

const projectStore = useProjectStore()

const isLoading = ref(false)
const isSubmitting = ref(false)
const showSubmitDialog = ref(false)
const showDetailsDialog = ref(false)
const selectedTask = ref<Task | null>(null)
const tasks = ref<Task[]>([])
const form = ref()

const taskForm = reactive({
  url: '',
  project: null as string | null,
  priority: 'normal' as 'low' | 'normal' | 'high'
})

const urlRules = [
  (v: string) => !!v || 'URL is required',
  (v: string) => {
    try {
      new URL(v)
      return true
    } catch {
      return 'Please enter a valid URL'
    }
  }
]

const priorityOptions = [
  { title: 'Low', value: 'low' },
  { title: 'Normal', value: 'normal' },
  { title: 'High', value: 'high' }
]

const projectOptions = computed(() => [
  ...projectStore.projects.map(p => ({
    title: p.name,
    value: p.id
  }))
])

function getStatusColor(status: string) {
  switch (status) {
    case 'done': return 'success'
    case 'failed': return 'error'
    case 'in_progress': return 'warning'
    case 'queued': return 'info'
    default: return 'gray'
  }
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'high': return 'error'
    case 'normal': return 'info'
    case 'low': return 'gray'
    default: return 'gray'
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function submitTask() {
  const { valid } = await form.value.validate()
  
  if (valid) {
    try {
      isSubmitting.value = true
      
      const taskData: CreateTaskData = {
        url: taskForm.url,
        priority: taskForm.priority
      }
      
      if (taskForm.project) {
        taskData.project = taskForm.project
      }
      
      const newTask = await taskService.submitTask(taskData)
      tasks.value.unshift(newTask)
      
      
      taskForm.url = ''
      taskForm.project = null
      taskForm.priority = 'normal'
      form.value.resetValidation()
      
    } catch (error) {
      console.error('Failed to submit task:', error)
    } finally {
      isSubmitting.value = false
    }
  }
}

function viewTaskDetails(task: Task) {
  selectedTask.value = task
  showDetailsDialog.value = true
}

async function downloadResult(task: Task) {
  try {
    const result = await taskService.getTaskResultDownloadUrl(task.id)
    window.open(result.download_url, '_blank')
  } catch (error) {
    console.error('Failed to get download URL:', error)
  }
}

async function refreshTasks() {
  
  
  tasks.value = [
    {
      id: '1',
      url: 'https://example.com',
      status: 'done',
      priority: 'normal',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      progress: 100
    },
    {
      id: '2', 
      url: 'https://test.com',
      status: 'in_progress',
      priority: 'high',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      updated_at: new Date().toISOString(),
      progress: 65
    }
  ]
}

onMounted(async () => {
  await projectStore.fetchProjects()
  await refreshTasks()
})
</script>