import apiClient from './api'

export interface AgentAnalysisResult {
  id: string
  status: 'new' | 'queued' | 'in_progress' | 'done' | 'failed'
  progress?: number
  result?: any
  error?: string
}

export interface DocumentAnalysisResult {
  contract_id?: string
  analysis_date: string
  overall_compliance_score: number
  summary: string
  critical_issues: string[]
  recommendations: string[]
  criteria: Record<string, {
    status: string
    explanation: string
    recommendations: string
    confidence_score: number
  }>
}

export interface WebsiteAnalysisResult {
  url: string
  analysis_date: string
  transparency_score: number
  dark_patterns: any[]
  summary: string
  status: string
}

export const agentService = {
  
  async analyzeDocument(file: File, projectId?: string): Promise<{ id: string; status: string }> {
    const formData = new FormData()
    formData.append('file', file, file.name)
    if (projectId) {
      formData.append('project_id', projectId)
    }
    

    const response = await apiClient.post('/v1/agents/analyze-document/', formData)
    return response.data
  },

  
  async analyzeWebsite(url: string, projectId?: string): Promise<{ id: string; status: string }> {
    const response = await apiClient.post('/v1/agents/analyze-website/', {
      url,
      project_id: projectId,
    })
    return response.data
  },

  
  async getTaskStatus(taskId: string): Promise<AgentAnalysisResult> {
    const response = await apiClient.get(`/v1/tasks/${taskId}/status/`)
    return response.data
  },

  
  async getTaskResult(taskId: string): Promise<AgentAnalysisResult> {
    const response = await apiClient.get(`/v1/tasks/${taskId}/result/`)
    return response.data
  },

  
  async pollTaskUntilComplete(
    taskId: string, 
    onProgress?: (progress: number) => void,
    maxAttempts: number = 60,
    intervalMs: number = 2000
  ): Promise<AgentAnalysisResult> {
    let attempts = 0
    
    while (attempts < maxAttempts) {
      const status = await this.getTaskStatus(taskId)
      
      if (onProgress) {

        const progress = status.progress || (
          status.status === 'in_progress' ? 50 :
          status.status === 'done' ? 100 :
          status.status === 'queued' ? 10 : 0
        )
        onProgress(progress)
      }
      
      if (status.status === 'done' || status.status === 'failed') {
        const result = await this.getTaskResult(taskId)
        return result
      }
      
      await new Promise(resolve => setTimeout(resolve, intervalMs))
      attempts++
    }
    
    throw new Error('Task polling timeout')
  },

  
  convertDocumentResultToDarkPatterns(result: DocumentAnalysisResult): any[] {
    const darkPatterns: any[] = []
    
    if (result.criteria) {
      Object.entries(result.criteria).forEach(([key, criterion]) => {
        if (criterion.status === 'non_compliant') {
          darkPatterns.push({
            id: key,
            pattern_type: 'compliance_violation',
            severity: criterion.confidence_score > 0.8 ? 'critical' : 
                     criterion.confidence_score > 0.5 ? 'high' : 'medium',
            description: criterion.explanation,
            location: key.replace(/_/g, ' '),
            recommendations: criterion.recommendations
          })
        }
      })
    }
    
    return darkPatterns
  }
}
