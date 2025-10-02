import apiClient from './api'

export interface LoginCredentials {
  username: string
  password: string
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role?: 'individual' | 'owner' | 'regulator' | 'admin'
  user_type?: 'individual' | 'business' | 'government'
  is_superuser?: boolean
}

export interface AuthTokens {
  access: string
  refresh: string
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<{ tokens: AuthTokens, user: User }> {
    try {
      
      const backendCredentials = {
        username: credentials.username === 'business' ? 'owner' : credentials.username,
        password: credentials.password === 'business123' ? 'owner123' : credentials.password
      }
      
      
      const tokenResponse = await apiClient.post('/token/', backendCredentials)
      const tokens = tokenResponse.data
      
      
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)
      
      
      const user: User = {
        id: 1,
        username: credentials.username,  
        email: `${credentials.username}@example.com`,
        first_name: this.capitalizeFirst(credentials.username),
        last_name: 'User',
        role: this.getUserRoleFromUsername(credentials.username)
      }
      
      return { tokens, user }
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  },

  async logout(): Promise<void> {
    try {
      
      
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  },

  async getCurrentUser(): Promise<User> {
    try {
      const token = this.getToken()
      if (!token) {
        throw new Error('No authentication token')
      }
      
      
      try {
        const response = await apiClient.get('/users/me/')
        const backendUser = response.data
        
        
        const role = this.mapBackendRoleToFrontendRole(backendUser.role)
        let user_type: User['user_type'] = 'individual'
        
        if (role === 'regulator' || role === 'admin') {
          user_type = 'government'
        } else if (role === 'owner') {
          user_type = 'business'
        }
        
        return {
          id: backendUser.id,
          username: backendUser.username,
          email: backendUser.email || `${backendUser.username}@example.com`,
          first_name: backendUser.first_name || this.capitalizeFirst(backendUser.username),
          last_name: backendUser.last_name || 'User',
          role: role,
          user_type: user_type,
          is_superuser: backendUser.is_superuser
        }
      } catch (apiError) {
        
        console.warn('Backend user API failed, falling back to token parsing:', apiError)
        
        const userId = this.getUserIdFromToken()
        const username = this.getUsernameFromUserId(userId)
        
        if (!username) {
          throw new Error('Invalid token: cannot determine user')
        }
        
        
        const role = this.getUserRoleFromUsername(username)
        let user_type: User['user_type'] = 'individual'
        
        if (role === 'regulator' || role === 'admin') {
          user_type = 'government'
        } else if (role === 'owner') {
          user_type = 'business'
        }
        
        return {
          id: parseInt(userId || '1'),
          username: username,
          email: `${username}@example.com`,
          first_name: this.capitalizeFirst(username),
          last_name: 'User',
          role: role,
          user_type: user_type
        }
      }
    } catch (error) {
      console.error('Failed to get current user:', error)
      throw error
    }
  },

  capitalizeFirst(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1)
  },

  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token')
    if (!token) return false
    
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expiry = payload.exp * 1000 
      const hasValidUserId = payload.user_id && typeof payload.user_id === 'string'
      return Date.now() < expiry && hasValidUserId
    } catch {
      return false
    }
  },

  getToken(): string | null {
    return localStorage.getItem('access_token')
  },

  getUsernameFromToken(): string | null {
    const token = localStorage.getItem('access_token')
    if (!token) return null
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      
      const userId = payload.user_id
      return this.getUsernameFromUserId(userId)
    } catch {
      return null
    }
  },

  getUserIdFromToken(): string | null {
    const token = localStorage.getItem('access_token')
    if (!token) return null
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.user_id
    } catch {
      return null
    }
  },

  getUsernameFromUserId(userId: string | null): string | null {
    if (!userId) return null
    
    
    
    const userIdMap: Record<string, string> = {
      '1': 'admin',     
      '2': 'reg',       
      '3': 'owner',     
      '4': 'user'       
    }
    
    return userIdMap[userId] || null
  },

  mapBackendRoleToFrontendRole(backendRole: string): User['role'] {
    
    switch (backendRole) {
      case 'admin': return 'admin'
      case 'regulator': return 'regulator'
      case 'owner': return 'owner'
      case 'user': return 'individual'
      default: return 'individual'
    }
  },

  getUserRoleFromUsername(username: string): User['role'] {
    
    if (username === 'admin') return 'admin'
    if (username === 'reg' || username === 'regulator') return 'regulator'
    if (username === 'owner') return 'owner'
    if (username === 'business') return 'owner'  
    if (username === 'user') return 'individual'  
    return 'individual'  
  }
}