import axios, { AxiosError } from 'axios'
import type {
  User,
  Project,
  Chapter,
  Version,
  Term,
  KnowledgeNode,
  KnowledgeEdge,
  ActivityLog,
  ApiStatus,
  QualityGate,
  SecurityScanResult,
  Metrics,
  SystemHealth,
  LoginRequest,
  RegisterRequest,
} from '@/types'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const api = {
  auth: {
    login: async (data: LoginRequest) => {
      const response = await client.post<{ token: string; user: User }>('/auth/login', data)
      return response.data
    },
    register: async (data: RegisterRequest) => {
      const response = await client.post<{ token: string; user: User }>('/auth/register', data)
      return response.data
    },
    me: async () => {
      const response = await client.get<User>('/auth/me')
      return response.data
    },
  },

  projects: {
    list: async () => {
      const response = await client.get<Project[]>('/projects')
      return response.data
    },
    get: async (id: string) => {
      const response = await client.get<Project>(`/projects/${id}`)
      return response.data
    },
    create: async (data: Partial<Project>) => {
      const response = await client.post<Project>('/projects', data)
      return response.data
    },
    update: async (id: string, data: Partial<Project>) => {
      const response = await client.put<Project>(`/projects/${id}`, data)
      return response.data
    },
    delete: async (id: string) => {
      await client.delete(`/projects/${id}`)
    },
  },

  chapters: {
    list: async (projectId: string) => {
      const response = await client.get<Chapter[]>(`/projects/${projectId}/chapters`)
      return response.data
    },
    get: async (projectId: string, chapterId: string) => {
      const response = await client.get<Chapter>(`/projects/${projectId}/chapters/${chapterId}`)
      return response.data
    },
    create: async (projectId: string, data: Partial<Chapter>) => {
      const response = await client.post<Chapter>(`/projects/${projectId}/chapters`, data)
      return response.data
    },
    update: async (projectId: string, chapterId: string, data: Partial<Chapter>) => {
      const response = await client.put<Chapter>(`/projects/${projectId}/chapters/${chapterId}`, data)
      return response.data
    },
    delete: async (projectId: string, chapterId: string) => {
      await client.delete(`/projects/${projectId}/chapters/${chapterId}`)
    },
    generate: async (projectId: string, chapterId: string) => {
      const response = await client.post<Chapter>(`/projects/${projectId}/chapters/${chapterId}/generate`)
      return response.data
    },
    submitReview: async (projectId: string, chapterId: string) => {
      const response = await client.post<Chapter>(`/projects/${projectId}/chapters/${chapterId}/submit-review`)
      return response.data
    },
    approve: async (projectId: string, chapterId: string) => {
      const response = await client.post<Chapter>(`/projects/${projectId}/chapters/${chapterId}/approve`)
      return response.data
    },
    reject: async (projectId: string, chapterId: string, reason: string) => {
      const response = await client.post<Chapter>(`/projects/${projectId}/chapters/${chapterId}/reject`, { reason })
      return response.data
    },
  },

  versions: {
    list: async (projectId: string, chapterId: string) => {
      const response = await client.get<Version[]>(`/projects/${projectId}/chapters/${chapterId}/versions`)
      return response.data
    },
    get: async (projectId: string, chapterId: string, versionId: string) => {
      const response = await client.get<Version>(`/projects/${projectId}/chapters/${chapterId}/versions/${versionId}`)
      return response.data
    },
  },

  terms: {
    list: async (search?: string) => {
      const response = await client.get<Term[]>('/terms', { params: { search } })
      return response.data
    },
    get: async (id: string) => {
      const response = await client.get<Term>(`/terms/${id}`)
      return response.data
    },
    create: async (data: Partial<Term>) => {
      const response = await client.post<Term>('/terms', data)
      return response.data
    },
    update: async (id: string, data: Partial<Term>) => {
      const response = await client.put<Term>(`/terms/${id}`, data)
      return response.data
    },
    delete: async (id: string) => {
      await client.delete(`/terms/${id}`)
    },
    lock: async (id: string) => {
      const response = await client.post<Term>(`/terms/${id}/lock`)
      return response.data
    },
  },

  knowledge: {
    getGraph: async () => {
      const response = await client.get<{ nodes: KnowledgeNode[]; edges: KnowledgeEdge[] }>('/knowledge/graph')
      return response.data
    },
  },

  dashboard: {
    getStatus: async () => {
      const response = await client.get<ApiStatus>('/dashboard/status')
      return response.data
    },
    getQualityGates: async () => {
      const response = await client.get<QualityGate>('/dashboard/quality-gates')
      return response.data
    },
    getActivityLogs: async (limit = 10) => {
      const response = await client.get<ActivityLog[]>('/dashboard/activity', { params: { limit } })
      return response.data
    },
    getModuleStatus: async () => {
      const response = await client.get<{ name: string; status: string }[]>('/dashboard/modules')
      return response.data
    },
  },

  security: {
    scanText: async (text: string) => {
      const response = await client.post<SecurityScanResult>('/security/scan', { text, type: 'text' })
      return response.data
    },
    verifyDoi: async (doi: string) => {
      const response = await client.post<SecurityScanResult>('/security/verify-doi', { doi })
      return response.data
    },
    verifyRegulation: async (text: string) => {
      const response = await client.post<SecurityScanResult>('/security/verify-regulation', { text })
      return response.data
    },
  },

  monitor: {
    getMetrics: async () => {
      const response = await client.get<Metrics>('/monitor/metrics')
      return response.data
    },
    getHealth: async () => {
      const response = await client.get<SystemHealth>('/monitor/health')
      return response.data
    },
  },

  users: {
    list: async () => {
      const response = await client.get<User[]>('/admin/users')
      return response.data
    },
    get: async (id: string) => {
      const response = await client.get<User>(`/admin/users/${id}`)
      return response.data
    },
    create: async (data: Record<string, unknown>) => {
      const response = await client.post<User>('/admin/users', data)
      return response.data
    },
    update: async (id: string, data: Record<string, unknown>) => {
      const response = await client.put<User>(`/admin/users/${id}`, data)
      return response.data
    },
    delete: async (id: string) => {
      await client.delete(`/admin/users/${id}`)
    },
  },

  settings: {
    get: async () => {
      const response = await client.get<Record<string, unknown>>('/settings')
      return response.data
    },
    update: async (data: Record<string, unknown>) => {
      const response = await client.put<Record<string, unknown>>('/settings', data)
      return response.data
    },
  },
}

export default api
