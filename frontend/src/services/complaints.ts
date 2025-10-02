import apiClient from './api'

export interface Complaint {
  id: string
  project: string
  project_name: string
  complaint_type: 'false_positive' | 'missing_pattern' | 'incorrect_severity' | 'other'
  subject: string
  text: string
  status: 'open' | 'investigating' | 'resolved' | 'dismissed'
  response_text?: string
  author?: string
  author_name?: string
  responded_by?: string
  created_at: string
  updated_at: string
  resolved_at?: string
}

export interface ComplaintCreate {
  project: string
  complaint_type: string
  subject: string
  text: string
}

export interface ComplaintResponse {
  response_text: string
  status: 'investigating' | 'resolved' | 'dismissed'
}

class ComplaintService {
  async submitComplaint(complaintData: ComplaintCreate): Promise<Complaint> {
    try {
      const response = await apiClient.post('/v1/complaints/', complaintData)
      return response.data
    } catch (error) {
      console.error('Failed to submit complaint:', error)
      throw error
    }
  }

  async getMyComplaints(): Promise<Complaint[]> {
    try {
      const response = await apiClient.get('/v1/complaints/')
      return response.data.results || response.data || []
    } catch (error) {
      console.error('Failed to get complaints:', error)
      throw error
    }
  }

  async getAllComplaints(): Promise<Complaint[]> {
    try {
      const response = await apiClient.get('/v1/complaints/')
      return response.data.results || response.data || []
    } catch (error) {
      console.error('Failed to get all complaints:', error)
      throw error
    }
  }

  async respondToComplaint(complaintId: string, responseData: ComplaintResponse): Promise<Complaint> {
    try {
      const response = await apiClient.post(`/v1/complaints/${complaintId}/respond/`, responseData)
      return response.data.complaint || response.data
    } catch (error) {
      console.error('Failed to respond to complaint:', error)
      throw error
    }
  }

  async getComplaint(complaintId: string): Promise<Complaint> {
    try {
      const response = await apiClient.get(`/v1/complaints/${complaintId}/`)
      return response.data
    } catch (error) {
      console.error('Failed to get complaint:', error)
      throw error
    }
  }
}

export const complaintService = new ComplaintService()