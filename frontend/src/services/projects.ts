import apiClient from './api'


export interface Project {
  id: string
  name: string
  site_url: string
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected'
  trust_score: number
  created_at: string
  updated_at: string
  owner?: string
}


export interface DarkPatternEvaluation {
  id: string
  name: string
  site_url: string
  evaluation_type: 'free' | 'paid' | 'government'
  evaluation_status: 'not_evaluated' | 'ai_only' | 'human_verified'
  transparency_score: number
  dark_patterns_found: DarkPattern[]
  evaluation_method: 'website' | 'document'
  created_at: string
  updated_at: string
  evaluated_by: string | null
  file_path?: string
  
  task_id?: string
  task_status?: 'new' | 'queued' | 'in_progress' | 'done' | 'failed'
  task_progress?: number
}

export interface DarkPattern {
  id: string
  pattern_type: 'urgency' | 'scarcity' | 'social_proof' | 'loss_aversion' | 'commitment' | 'reciprocity'
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  location: string
  screenshot_url?: string
}

export interface CreateEvaluationData {
  name: string
  site_url?: string
  evaluation_method: 'website' | 'document'
  file?: File
}

export interface Complaint {
  id: string
  project: string
  text: string
  author?: string
  created_at: string
}

export interface UpdateEvaluationData extends Partial<CreateEvaluationData> {
  evaluation_status?: DarkPatternEvaluation['evaluation_status']
}


export interface Task {
  id: string
  url: string
  status: 'new' | 'queued' | 'in_progress' | 'done' | 'failed'
  priority: 'low' | 'normal' | 'high'
  progress?: number
  created_at: string
  updated_at: string
  started_at?: string
  finished_at?: string
  error?: string
  result_json?: any
}

export const darkPatternService = {
  
  async getEvaluations(): Promise<DarkPatternEvaluation[]> {
    try {
      const response = await apiClient.get('/v1/projects/')
      const projects = response.data.results || response.data || []
      return projects.map((project: Project) => this.mapProjectToEvaluation(project))
    } catch (error) {
      console.error('Failed to get evaluations:', error)
      throw error
    }
  },

  async getEvaluation(id: string): Promise<DarkPatternEvaluation> {
    try {
      const [projectResponse, taskResponse] = await Promise.allSettled([
        apiClient.get(`/v1/projects/${id}/`),
        
        this.getProjectTask(id).catch(() => null)
      ])
      
      if (projectResponse.status === 'rejected') {
        throw new Error('Project not found')
      }
      
      const project = projectResponse.value.data
      const task = taskResponse.status === 'fulfilled' ? taskResponse.value : null
      
      return this.mapProjectToEvaluation(project, task)
    } catch (error) {
      console.error('Failed to get evaluation:', error)
      throw error
    }
  },

  async createEvaluation(data: CreateEvaluationData): Promise<DarkPatternEvaluation> {
    try {
      
      const projectData = {
        name: data.name,
        site_url: data.site_url || '',
      }
      
      const projectResponse = await apiClient.post('/v1/projects/', projectData)
      const project = projectResponse.data
      
      
      if (data.site_url) {
        const taskResponse = await apiClient.post('/v1/tasks/submit/', {
          url: data.site_url
        })
        
        const task = await this.getTaskStatus(taskResponse.data.id)
        return this.mapProjectToEvaluation(project, task)
      }
      
      return this.mapProjectToEvaluation(project)
    } catch (error) {
      console.error('Failed to create evaluation:', error)
      throw error
    }
  },

  async updateEvaluation(id: string, data: UpdateEvaluationData): Promise<DarkPatternEvaluation> {
    const updateData = {
      name: data.name,
      site_url: data.site_url,
    }
    
    const response = await apiClient.patch(`/v1/projects/${id}/`, updateData)
    return this.mapProjectToEvaluation(response.data)
  },

  async deleteEvaluation(id: string): Promise<void> {
    await apiClient.delete(`/v1/projects/${id}/`)
  },

  async submitComplaint(evaluationId: string, complaint: Partial<Complaint> & { complaint_type?: 'false_positive' | 'missing_pattern' | 'incorrect_severity' | 'other' }): Promise<Complaint> {
    const response = await apiClient.post(`/v1/projects/${evaluationId}/complaints/`, {
      text: complaint.text,
      complaint_type: complaint.complaint_type
    })
    return {
      id: response.data.id,
      project: evaluationId,
      text: complaint.text || '',
      complaint_type: complaint.complaint_type || 'other',
      created_at: new Date().toISOString()
    } as Complaint
  },

  async getComplaints(evaluationId?: string): Promise<Complaint[]> {
    if (evaluationId) {
      const response = await apiClient.get(`/v1/projects/${evaluationId}/complaints/`)
      return response.data.results || response.data
    }
    
    return []
  },

  
  async getTaskStatus(taskId: string): Promise<Task> {
    const response = await apiClient.get(`/v1/tasks/${taskId}/status/`)
    return response.data
  },

  async getTaskResult(taskId: string): Promise<any> {
    const response = await apiClient.get(`/v1/tasks/${taskId}/result/`)
    return response.data
  },

  async submitTask(url: string): Promise<{ id: string }> {
    const response = await apiClient.post('/v1/tasks/submit/', { url })
    return response.data
  },

  
  async getRegulatorStats() {
    const response = await apiClient.get('/v1/regulator/stats/')
    return response.data
  },

  async getTransparencyTrends() {
    const response = await apiClient.get('/v1/regulator/stats/expanded/')
    return response.data
  },

  async getDarkPatternCategories() {
    
    return [
      { id: 'urgency', name: 'False Urgency', description: 'Fake time pressure' },
      { id: 'scarcity', name: 'Artificial Scarcity', description: 'Fake limited availability' },
      { id: 'social_proof', name: 'Fake Social Proof', description: 'Fake reviews or testimonials' },
      { id: 'loss_aversion', name: 'Fear Tactics', description: 'Threatening consequences' },
      { id: 'commitment', name: 'Forced Commitment', description: 'Hard to cancel or opt out' },
      { id: 'reciprocity', name: 'Hidden Reciprocity', description: 'Disguised obligations' },
    ]
  },

  
  async getProjectTask(projectId: string): Promise<Task | null> {
    
    
    return null
  },

  mapProjectToEvaluation(project: Project, task?: Task | null): DarkPatternEvaluation {
    
    return {
      id: project.id,
      name: project.name,
      site_url: project.site_url,
      evaluation_type: 'free', 
      evaluation_status: this.mapStatusToEvaluationStatus(project.status),
      transparency_score: project.trust_score,
      dark_patterns_found: this.generateMockPatterns(project.trust_score), 
      evaluation_method: 'website',
      created_at: project.created_at,
      updated_at: project.updated_at || project.created_at,
      evaluated_by: null,
      task_id: task?.id,
      task_status: task?.status,
      task_progress: task?.progress,
    }
  },

  mapStatusToEvaluationStatus(status: Project['status']): DarkPatternEvaluation['evaluation_status'] {
    switch (status) {
      case 'approved':
        return 'human_verified'
      case 'under_review':
      case 'submitted':
        return 'ai_only'
      case 'draft':
      case 'rejected':
      default:
        return 'not_evaluated'
    }
  },

  mapEvaluationStatusToStatus(evaluationStatus: DarkPatternEvaluation['evaluation_status']): Project['status'] {
    switch (evaluationStatus) {
      case 'human_verified':
        return 'approved'
      case 'ai_only':
        return 'submitted'
      case 'not_evaluated':
      default:
        return 'draft'
    }
  },

  generateMockPatterns(trustScore: number): DarkPattern[] {
    
    const patterns: DarkPattern[] = []
    
    if (trustScore < 50) {
      patterns.push({
        id: '1',
        pattern_type: 'urgency',
        severity: 'high',
        description: 'False urgency timer on signup page',
        location: 'Homepage signup section'
      })
    }
    
    if (trustScore < 70) {
      patterns.push({
        id: '2',
        pattern_type: 'commitment',
        severity: 'medium',
        description: 'Difficult cancellation process',
        location: 'Account settings'
      })
    }
    
    if (trustScore < 80) {
      patterns.push({
        id: '3',
        pattern_type: 'scarcity',
        severity: 'low',
        description: 'Limited time offer without actual time limit',
        location: 'Pricing page'
      })
    }
    
    return patterns
  }
}