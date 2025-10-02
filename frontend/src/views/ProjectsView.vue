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
          <h1 class="text-3xl font-bold text-gray-900 mb-2">Projects</h1>
          <p class="text-gray-600">Manage your fintech projects and track their progress.</p>
        </div>
        
        <v-btn
          @click="showCreateDialog = true"
          color="primary"
          size="large"
          class="btn-hover mt-4 sm:mt-0"
          prepend-icon="mdi-plus"
        >
          New Project
        </v-btn>
      </div>

      
      <div v-if="projectStore.isLoading" class="flex justify-center items-center h-64">
        <v-progress-circular indeterminate size="64" color="primary" />
      </div>

      <div v-else-if="projectStore.projects.length === 0" class="text-center py-12">
        <div 
          v-motion
          :initial="{ opacity: 0, scale: 0.9 }"
          :enter="{ opacity: 1, scale: 1 }"
          :duration="500"
          class="max-w-md mx-auto"
        >
          <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <v-icon icon="mdi-briefcase-outline" size="48" color="gray" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">No projects yet</h3>
          <p class="text-gray-600 mb-6">Create your first project to get started with APRU platform.</p>
          <v-btn
            @click="showCreateDialog = true"
            color="primary"
            size="large"
            class="btn-hover"
            prepend-icon="mdi-plus"
          >
            Create Project
          </v-btn>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="(project, index) in projectStore.projects"
          :key="project.id"
          v-motion
          :initial="{ opacity: 0, y: 20 }"
          :enter="{ opacity: 1, y: 0 }"
          :delay="index * 100"
          :duration="500"
        >
          <v-card 
            class="h-full hover:shadow-xl transition-all duration-300 cursor-pointer btn-hover"
            @click="$router.push(`/projects/${project.id}`)"
          >
            <v-card-text class="p-6">
              <div class="flex items-center justify-between mb-4">
                <v-chip
                  :color="getStatusColor(project.status)"
                  variant="tonal"
                  size="small"
                >
                  {{ project.status.replace('_', ' ').toUpperCase() }}
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
                      prepend-icon="mdi-pencil"
                      title="Edit"
                      @click.stop="editProject(project)"
                    />
                    <v-list-item
                      prepend-icon="mdi-delete"
                      title="Delete"
                      @click.stop="confirmDelete(project)"
                    />
                  </v-list>
                </v-menu>
              </div>

              <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ project.name }}</h3>
              
              <div class="flex items-center text-sm text-gray-600 mb-4">
                <v-icon icon="mdi-web" size="16" class="mr-1" />
                <span class="truncate">{{ project.site_url }}</span>
              </div>

              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                  <div class="text-center">
                    <p class="text-2xl font-bold text-indigo-600">{{ project.trust_score.toFixed(1) }}</p>
                    <p class="text-xs text-gray-500">Trust Score</p>
                  </div>
                </div>
                
                <div class="text-right">
                  <p class="text-sm font-medium text-gray-900">{{ formatDate(project.created_at) }}</p>
                  <p class="text-xs text-gray-500">Created</p>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div>

    
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card class="rounded-xl">
        <v-card-title class="text-xl font-semibold bg-gray-50 px-6 py-4">
          {{ isEditing ? 'Edit Project' : 'Create New Project' }}
        </v-card-title>
        
        <v-card-text class="p-6">
          <v-form @submit.prevent="handleSubmit" ref="form">
            <div class="space-y-6">
              <v-text-field
                v-model="projectForm.name"
                :rules="nameRules"
                label="Project Name"
                prepend-inner-icon="mdi-briefcase"
                variant="outlined"
                required
              />

              <v-text-field
                v-model="projectForm.site_url"
                :rules="urlRules"
                label="Site URL"
                prepend-inner-icon="mdi-web"
                variant="outlined"
                required
              />
            </div>
          </v-form>
        </v-card-text>
        
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn
            @click="closeDialog"
            variant="text"
            color="gray"
          >
            Cancel
          </v-btn>
          <v-btn
            @click="handleSubmit"
            :loading="projectStore.isLoading"
            color="primary"
            class="btn-hover"
          >
            {{ isEditing ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card class="rounded-xl">
        <v-card-title class="text-lg font-semibold px-6 pt-6 pb-2">Confirm Delete</v-card-title>
        <v-card-text class="px-6 pb-6">
          Are you sure you want to delete "{{ projectToDelete?.name }}"? This action cannot be undone.
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn @click="showDeleteDialog = false" variant="text">Cancel</v-btn>
          <v-btn
            @click="handleDelete"
            :loading="projectStore.isLoading"
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
import { ref, reactive, onMounted } from 'vue'
import { useProjectStore } from '@/stores/projects'
import type { Project } from '@/services/projects'

const projectStore = useProjectStore()

const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const isEditing = ref(false)
const projectToDelete = ref<Project | null>(null)
const form = ref()

const projectForm = reactive({
  name: '',
  site_url: ''
})

const nameRules = [
  (v: string) => !!v || 'Project name is required',
  (v: string) => v.length >= 3 || 'Name must be at least 3 characters'
]

const urlRules = [
  (v: string) => !!v || 'Site URL is required',
  (v: string) => {
    try {
      new URL(v)
      return true
    } catch {
      return 'Please enter a valid URL'
    }
  }
]

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
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

function editProject(project: Project) {
  projectForm.name = project.name
  projectForm.site_url = project.site_url || ''
  isEditing.value = true
  showCreateDialog.value = true
}

function confirmDelete(project: Project) {
  projectToDelete.value = project
  showDeleteDialog.value = true
}

async function handleSubmit() {
  const { valid } = await form.value.validate()
  
  if (valid) {
    try {
      if (isEditing.value && projectToDelete.value) {
        await projectStore.updateProject(projectToDelete.value.id, projectForm)
      } else {
        await projectStore.createProject(projectForm)
      }
      closeDialog()
    } catch (error) {
      console.error('Failed to save project:', error)
    }
  }
}

async function handleDelete() {
  if (projectToDelete.value) {
    try {
      await projectStore.deleteProject(projectToDelete.value.id)
      showDeleteDialog.value = false
      projectToDelete.value = null
    } catch (error) {
      console.error('Failed to delete project:', error)
    }
  }
}

function closeDialog() {
  showCreateDialog.value = false
  isEditing.value = false
  projectForm.name = ''
  projectForm.site_url = ''
  projectToDelete.value = null
  if (form.value) {
    form.value.resetValidation()
  }
}

onMounted(async () => {
  await projectStore.fetchProjects()
})
</script>