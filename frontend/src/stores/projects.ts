import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { 
  darkPatternService, 
  type DarkPatternEvaluation, 
  type CreateEvaluationData, 
  type UpdateEvaluationData,
  type Complaint
} from '@/services/projects'
import { taskService } from '@/services/tasks'

export const useDarkPatternStore = defineStore('darkPatterns', () => {
  const evaluations = ref<DarkPatternEvaluation[]>([])
  const currentEvaluation = ref<DarkPatternEvaluation | null>(null)
  const complaints = ref<Complaint[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const evaluationsByStatus = computed(() => {
    const grouped: Record<string, DarkPatternEvaluation[]> = {
      not_evaluated: [],
      ai_only: [],
      human_verified: []
    }
    
    evaluations.value.forEach(evaluation => {
      if (grouped[evaluation.evaluation_status]) {
        grouped[evaluation.evaluation_status].push(evaluation)
      }
    })
    
    return grouped
  })

  const totalEvaluations = computed(() => evaluations.value.length)
  const verifiedEvaluations = computed(() => 
    evaluations.value.filter(e => e.evaluation_status === 'human_verified').length
  )
  const averageTransparencyScore = computed(() => {
    if (evaluations.value.length === 0) return 0
    return evaluations.value.reduce((sum, e) => sum + e.transparency_score, 0) / evaluations.value.length
  })

  
  const projects = computed(() => 
    evaluations.value.map(evaluation => ({
      id: evaluation.id,
      name: evaluation.name,
      description: evaluation.site_url || evaluation.file_path || 'Document analysis',
      status: darkPatternService.mapEvaluationStatusToStatus(evaluation.evaluation_status),
      site_url: evaluation.site_url,
      trust_score: evaluation.transparency_score,
      created_at: evaluation.created_at,
      updated_at: evaluation.updated_at
    }))
  )

  const currentProject = computed(() => {
    if (!currentEvaluation.value) return null
    return {
      id: currentEvaluation.value.id,
      name: currentEvaluation.value.name,
      description: currentEvaluation.value.site_url || currentEvaluation.value.file_path || 'Document analysis',
      status: currentEvaluation.value.evaluation_status,
      site_url: currentEvaluation.value.site_url,
      trust_score: currentEvaluation.value.transparency_score,
      created_at: currentEvaluation.value.created_at,
      updated_at: currentEvaluation.value.updated_at
    }
  })

  const getEvaluationBorderColor = (evaluation: DarkPatternEvaluation) => {
    switch (evaluation.evaluation_status) {
      case 'not_evaluated':
        return 'border-gray-300'
      case 'ai_only':
        return 'border-yellow-400'
      case 'human_verified':
        return 'border-green-500'
      default:
        return 'border-gray-300'
    }
  }

  const getEvaluationStatusColor = (status: string) => {
    switch (status) {
      case 'human_verified': return 'success'
      case 'ai_only': return 'warning'  
      case 'not_evaluated': return 'gray'
      default: return 'gray'
    }
  }

  
  let pollInterval: number | null = null

  function pollTaskStatus(taskId: string) {
    if (pollInterval) {
      clearInterval(pollInterval)
    }

    pollInterval = window.setInterval(async () => {
      try {
        const task = await taskService.getTaskStatus(taskId)
        
        if (currentEvaluation.value && currentEvaluation.value.task_id === taskId) {
          currentEvaluation.value.task_status = task.status
          currentEvaluation.value.task_progress = task.progress
          
          if (task.status === 'done' || task.status === 'failed') {
            clearInterval(pollInterval!)
            pollInterval = null
            
            if (task.status === 'done') {
              await fetchEvaluation(currentEvaluation.value.id)
            }
          }
        }
      } catch (err) {
        console.error('Error polling task status:', err)
      }
    }, 2000)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  async function fetchEvaluations() {
    try {
      isLoading.value = true
      error.value = null
      evaluations.value = await darkPatternService.getEvaluations()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch evaluations'
      console.error('Error fetching evaluations:', err)
    } finally {
      isLoading.value = false
    }
  }

  async function fetchEvaluation(id: string) {
    try {
      isLoading.value = true  
      error.value = null
      currentEvaluation.value = await darkPatternService.getEvaluation(id)
      
      if (currentEvaluation.value.task_id && 
          currentEvaluation.value.task_status && 
          ['new', 'queued', 'in_progress'].includes(currentEvaluation.value.task_status)) {
        pollTaskStatus(currentEvaluation.value.task_id)
      }
      
      return currentEvaluation.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch evaluation'
      console.error('Error fetching evaluation:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createEvaluation(data: CreateEvaluationData): Promise<DarkPatternEvaluation> {
    try {
      isLoading.value = true
      error.value = null
      const evaluation = await darkPatternService.createEvaluation(data)
      evaluations.value.push(evaluation)
      currentEvaluation.value = evaluation
      
      if (evaluation.task_id) {
        pollTaskStatus(evaluation.task_id)
      }
      
      return evaluation
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create evaluation'
      console.error('Error creating evaluation:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateEvaluation(id: string, data: UpdateEvaluationData): Promise<DarkPatternEvaluation> {
    try {
      isLoading.value = true
      error.value = null
      const updatedEvaluation = await darkPatternService.updateEvaluation(id, data)
      
      const index = evaluations.value.findIndex(e => e.id === id)
      if (index !== -1) {
        evaluations.value[index] = updatedEvaluation
      }
      
      if (currentEvaluation.value?.id === id) {
        currentEvaluation.value = updatedEvaluation
      }
      
      return updatedEvaluation
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update evaluation'
      console.error('Error updating evaluation:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteEvaluation(id: string): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      await darkPatternService.deleteEvaluation(id)
      
      evaluations.value = evaluations.value.filter(e => e.id !== id)
      if (currentEvaluation.value?.id === id) {
        currentEvaluation.value = null
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete evaluation'
      console.error('Error deleting evaluation:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function submitComplaint(evaluationId: string, complaint: Partial<Complaint> & { complaint_type?: 'false_positive' | 'missing_pattern' | 'incorrect_severity' | 'other' }): Promise<Complaint> {
    try {
      error.value = null
      const newComplaint = await darkPatternService.submitComplaint(evaluationId, complaint)
      complaints.value.push(newComplaint)
      return newComplaint
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to submit complaint'
      console.error('Error submitting complaint:', err)
      throw err
    }
  }

  async function fetchComplaints(evaluationId?: string): Promise<void> {
    try {
      isLoading.value = true
      error.value = null
      complaints.value = await darkPatternService.getComplaints(evaluationId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch complaints'
      console.error('Error fetching complaints:', err)
    } finally {
      isLoading.value = false
    }
  }

  
  async function fetchProject(id: string) {
    return await fetchEvaluation(id)
  }

  async function fetchProjects() {
    return await fetchEvaluations()
  }

  async function createProject(data: any) {
    return await createEvaluation({
      name: data.name,
      site_url: data.site_url,
      evaluation_method: 'website'
    })
  }

  async function updateProject(id: string, data: any) {
    return await updateEvaluation(id, {
      name: data.name,
      site_url: data.site_url
    })
  }

  async function deleteProject(id: string) {
    return await deleteEvaluation(id)
  }

  return {
    evaluations,
    currentEvaluation,
    complaints,
    isLoading,
    error,
    evaluationsByStatus,
    totalEvaluations,
    verifiedEvaluations,
    averageTransparencyScore,
    projects,
    currentProject,
    getEvaluationBorderColor,
    getEvaluationStatusColor,
    fetchEvaluations,
    fetchEvaluation,
    createEvaluation,
    updateEvaluation,
    deleteEvaluation,
    submitComplaint,
    fetchComplaints,
    pollTaskStatus,
    stopPolling,
    fetchProject,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject
  }
})


export const useProjectStore = useDarkPatternStore
