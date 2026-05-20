import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Tag,
  Progress,
  Modal,
  Form,
  Input,
  message,
  Spin,
  Empty,
} from 'antd'
import { PlusOutlined, ProjectOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { Project } from '@/types'

const mockProjects: Project[] = [
  {
    id: '1',
    name: '计算机科学导论',
    description: '介绍计算机科学基础知识，涵盖计算机系统、算法、数据结构等核心概念。',
    status: 'in_progress',
    created_at: '2024-01-15T08:00:00Z',
    updated_at: '2024-03-10T14:30:00Z',
    chapter_count: 12,
    completed_chapters: 5,
  },
  {
    id: '2',
    name: '人工智能基础',
    description: '讲解人工智能的基本原理、机器学习算法和神经网络基础知识。',
    status: 'in_progress',
    created_at: '2024-02-01T10:00:00Z',
    updated_at: '2024-03-12T09:15:00Z',
    chapter_count: 10,
    completed_chapters: 3,
  },
  {
    id: '3',
    name: '数据结构与算法',
    description: '深入探讨各种数据结构和算法设计技巧。',
    status: 'draft',
    created_at: '2024-03-05T12:00:00Z',
    updated_at: '2024-03-05T12:00:00Z',
    chapter_count: 8,
    completed_chapters: 0,
  },
  {
    id: '4',
    name: '软件工程实践',
    description: '介绍软件工程的方法论和最佳实践。',
    status: 'completed',
    created_at: '2023-11-01T08:00:00Z',
    updated_at: '2024-02-28T16:45:00Z',
    chapter_count: 15,
    completed_chapters: 15,
  },
]

const statusColors: Record<string, string> = {
  draft: 'default',
  in_progress: 'processing',
  completed: 'success',
}

const statusLabels: Record<string, string> = {
  draft: '草稿',
  in_progress: '进行中',
  completed: '已完成',
}

export function ProjectsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data: projects = mockProjects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<Project>) => api.projects.create(data),
    onSuccess: () => {
      message.success('项目创建成功')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsModalOpen(false)
      form.resetFields()
    },
    onError: () => {
      message.error('项目创建失败')
    },
  })

  const handleCreateProject = () => {
    form.validateFields().then((values) => {
      createMutation.mutate(values)
    })
  }

  const handleProjectClick = (projectId: string) => {
    navigate(`/projects/${projectId}`)
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>项目列表</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          创建项目
        </Button>
      </div>

      {projects.length === 0 ? (
        <Empty description="暂无项目" />
      ) : (
        <div className="card-grid">
          {projects.map((project) => (
            <Card
              key={project.id}
              hoverable
              onClick={() => handleProjectClick(project.id)}
              style={{ cursor: 'pointer' }}
              actions={[
                <span key="progress" style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
                  {project.completed_chapters}/{project.chapter_count} 章节
                </span>,
              ]}
            >
              <Card.Meta
                avatar={<ProjectOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {project.name}
                    <Tag color={statusColors[project.status]}>{statusLabels[project.status]}</Tag>
                  </div>
                }
                description={
                  <>
                    <p style={{ marginBottom: 16, color: 'rgba(255,255,255,0.65)' }}>
                      {project.description}
                    </p>
                    <Progress
                      percent={Math.round((project.completed_chapters / project.chapter_count) * 100)}
                      size="small"
                      strokeColor={project.status === 'completed' ? '#52c41a' : '#1890ff'}
                    />
                  </>
                }
              />
            </Card>
          ))}
        </div>
      )}

      <Modal
        title="创建新项目"
        open={isModalOpen}
        onOk={handleCreateProject}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="项目名称"
            rules={[{ required: true, message: '请输入项目名称' }]}
          >
            <Input placeholder="请输入项目名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="项目描述"
            rules={[{ required: true, message: '请输入项目描述' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入项目描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
