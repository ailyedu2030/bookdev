export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'editor' | 'viewer'
  created_at: string
}

export interface Project {
  id: string
  name: string
  description: string
  status: 'draft' | 'in_progress' | 'completed'
  created_at: string
  updated_at: string
  chapter_count: number
  completed_chapters: number
}

export interface Chapter {
  id: string
  project_id: string
  title: string
  content: string
  status: 'draft' | 'in_review' | 'approved' | 'published'
  order: number
  version: number
  created_at: string
  updated_at: string
}

export interface Version {
  id: string
  chapter_id: string
  version_number: number
  content: string
  created_at: string
  created_by: string
}

export interface Term {
  id: string
  term: string
  definition: string
  subject_area: string
  is_locked: boolean
  created_at: string
  updated_at: string
}

export interface KnowledgeNode {
  id: string
  type: 'Chapter' | 'Section' | 'Concept' | 'Term'
  label: string
  properties?: Record<string, unknown>
}

export interface KnowledgeEdge {
  source: string
  target: string
  type: 'CONTAINS' | 'FOLLOWS' | 'DEFINES' | 'USES' | 'REFERENCES'
}

export interface ActivityLog {
  id: string
  action: string
  user_id: string
  user_name: string
  resource_type: string
  resource_id: string
  resource_name: string
  timestamp: string
}

export interface ApiStatus {
  minimax_api: 'connected' | 'disconnected' | 'error'
  database: 'connected' | 'disconnected' | 'error'
  redis: 'connected' | 'disconnected' | 'error'
}

export interface QualityGate {
  linter: 'passed' | 'failed' | 'pending'
  security: 'passed' | 'failed' | 'pending'
  coverage: 'passed' | 'failed' | 'pending'
}

export interface SecurityScanResult {
  type: 'doi' | 'regulation' | 'text'
  status: 'safe' | 'warning' | 'danger'
  message: string
  details?: string[]
}

export interface Metrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_connections: number
  requests_per_second: number
  average_response_time: number
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  components: {
    api: 'up' | 'down' | 'degraded'
    database: 'up' | 'down' | 'degraded'
    cache: 'up' | 'down' | 'degraded'
    queue: 'up' | 'down' | 'degraded'
  }
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
}

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
}
