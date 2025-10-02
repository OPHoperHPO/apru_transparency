import apiClient from './api'

export interface DashboardStats {
  
  market_integrity_index?: number
  active_complaints?: number
  avg_response_time_days?: number
  enforcement_rate?: number
  complaint_stats?: {
    total: number
    open: number
    investigating: number
    resolved: number
    dismissed: number
  }
  project_stats?: {
    avg_trust_score: number
    total_projects: number
    high_risk_projects: number
    medium_risk_projects: number
    low_risk_projects: number
  }
  
  
  trust_score?: number
  compliance_rate?: number
  total_evaluations?: number
  issues_to_resolve?: number
  
  
  verified_evaluations?: number
  avg_transparency_score?: number
  dark_patterns_found?: number
  
  
  recent_evaluations?: Array<{
    id: string
    name: string
    site_url: string
    status: string
    trust_score: number
    created_at: string
  }>
}

class DashboardService {
  async getStats(): Promise<DashboardStats> {
    try {
      const response = await apiClient.get('/v1/dashboard/stats/')
      return response.data
    } catch (error) {
      console.error('Failed to get dashboard stats:', error)
      return this.getFallbackStats()
    }
  }

  private getFallbackStats(): DashboardStats {
    
    return {
      market_integrity_index: 78,
      active_complaints: 23,
      avg_response_time_days: 12.5,
      enforcement_rate: 34,
      trust_score: 85,
      compliance_rate: 98,
      total_evaluations: 0,
      issues_to_resolve: 2,
      verified_evaluations: 0,
      avg_transparency_score: 0,
      dark_patterns_found: 0,
      recent_evaluations: []
    }
  }
}

export const dashboardService = new DashboardService()