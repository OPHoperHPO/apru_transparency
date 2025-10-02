import apiClient from './api'

export interface Task {
  id: string
  url: string
  project?: string
  status: 'new' | 'queued' | 'in_progress' | 'done' | 'failed'
  priority: 'low' | 'normal' | 'high'
  created_at: string
  updated_at: string
  started_at?: string
  finished_at?: string
  progress?: number
  error?: string
  result_json?: any
}

export interface CreateTaskData {
  url: string
  project?: string
  priority?: Task['priority']
}

export const taskService = {
  async submitTask(data: CreateTaskData): Promise<Task> {
    try {
      const response = await apiClient.post('/v1/tasks/submit/', data)
      return response.data
    } catch (error) {
      console.error('Failed to submit task:', error)
      throw error
    }
  },

  async getTaskStatus(taskId: string): Promise<Task> {
    try {
      const response = await apiClient.get(`/v1/tasks/${taskId}/status/`)
      return response.data
    } catch (error) {
      console.error('Failed to get task status:', error)
      throw error
    }
  },

  async getTaskResult(taskId: string): Promise<any> {
    try {
      const response = await apiClient.get(`/v1/tasks/${taskId}/result/`)
      return response.data
    } catch (error) {
      console.error('Failed to get task result:', error)
      throw error
    }
  },

  async getTaskResultDownloadUrl(taskId: string): Promise<{ download_url: string }> {
    try {
      const response = await apiClient.get(`/v1/tasks/${taskId}/result/download_url/`)
      return response.data
    } catch (error) {
      console.error('Failed to get task result download URL:', error)
      throw error
    }
  }
}