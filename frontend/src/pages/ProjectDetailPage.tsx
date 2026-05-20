import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Tag,
  Progress,
  List,
  Modal,
  Form,
  Input,
  message,
  Spin,
  Breadcrumb,
  Space,
} from 'antd'
import {
  PlusOutlined,
  BookOutlined,
  EditOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import dayjs from 'dayjs'
import type { Chapter } from '@/types'

const mockProject = {
  id: '1',
  name: '计算机科学导论',
  description: '介绍计算机科学基础知识，涵盖计算机系统、算法、数据结构等核心概念。',
  status: 'in_progress' as const,
  created_at: '2024-01-15T08:00:00Z',
  updated_at: '2024-03-10T14:30:00Z',
  chapter_count: 12,
  completed_chapters: 5,
}

const mockChapters: Chapter[] = [
  {
    id: '1',
    project_id: '1',
    title: '第一章：计算机基础',
    content: '',
    status: 'approved',
    order: 1,
    version: 3,
    created_at: '2024-01-15T08:00:00Z',
    updated_at: '2024-02-01T10:00:00Z',
  },
  {
    id: '2',
    project_id: '1',
    title: '第二章：算法入门',
    content: '',
    status: 'in_review',
    order: 2,
    version: 2,
    created_at: '2024-01-20T08:00:00Z',
    updated_at: '2024-02-15T14:00:00Z',
  },
  {
    id: '3',
    project_id: '1',
    title: '第三章：数据结构',
    content: '',
    status: 'draft',
    order: 3,
    version: 1,
    created_at: '2024-02-01T08:00:00Z',
    updated_at: '2024-02-01T08:00:00Z',
  },
  {
    id: '4',
    project_id: '1',
    title: '第四章：操作系统',
    content: '',
    status: 'published',
    order: 4,
    version: 5,
    created_at: '2024-02-10T08:00:00Z',
    updated_at: '2024-03-01T16:00:00Z',
  },
  {
    id: '5',
    project_id: '1',
    title: '第五章：计算机网络',
    content: '',
    status: 'draft',
    order: 5,
    version: 1,
    created_at: '2024-02-20T08:00:00Z',
    updated_at: '2024-02-20T08:00:00Z',
  },
]

const statusIcons: Record<string, React.ReactNode> = {
  draft: <ClockCircleOutlined style={{ color: '#faad14' }} />,
  in_review: <EditOutlined style={{ color: '#1890ff' }} />,
  approved: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
  published: <CheckCircleOutlined style={{ color: '#722ed1' }} />,
}

const statusColors: Record<string, string> = {
  draft: 'warning',
  in_review: 'processing',
  approved: 'success',
  published: 'purple',
}

const statusLabels: Record<string, string> = {
  draft: '草稿',
  in_review: '审核中',
  approved: '已批准',
  published: '已发布',
}

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data: project = mockProject, isLoading: projectLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => api.projects.get(id!),
  })

  const { data: chapters = mockChapters, isLoading: chaptersLoading } = useQuery({
    queryKey: ['chapters', id],
    queryFn: () => api.chapters.list(id!),
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<Chapter>) => api.chapters.create(id!, data),
    onSuccess: () => {
      message.success('章节创建成功')
      queryClient.invalidateQueries({ queryKey: ['chapters', id] })
      setIsModalOpen(false)
      form.resetFields()
    },
    onError: () => {
      message.error('章节创建失败')
    },
  })

  const handleCreateChapter = () => {
    form.validateFields().then((values) => {
      createMutation.mutate({
        ...values,
        order: chapters.length + 1,
      })
    })
  }

  const handleChapterClick = (chapterId: string) => {
    navigate(`/projects/${id}/chapters/${chapterId}`)
  }

  const progress = Math.round((chapters.filter((c) => c.status === 'approved' || c.status === 'published').length / chapters.length) * 100)

  if (projectLoading || chaptersLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="page-container">
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: '项目列表', href: '/projects' },
          { title: project.name },
        ]}
      />

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ fontSize: 24, marginBottom: 8 }}>{project.name}</h1>
            <p style={{ color: 'rgba(255,255,255,0.65)', marginBottom: 16 }}>{project.description}</p>
            <Space>
              <Tag color={project.status === 'completed' ? 'success' : project.status === 'in_progress' ? 'processing' : 'default'}>
                {project.status === 'completed' ? '已完成' : project.status === 'in_progress' ? '进行中' : '草稿'}
              </Tag>
              <span style={{ color: 'rgba(255,255,255,0.45)' }}>
                创建于 {dayjs(project.created_at).format('YYYY-MM-DD')}
              </span>
            </Space>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
            添加章节
          </Button>
        </div>

        <div style={{ marginTop: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span>项目进度</span>
            <span>{progress}%</span>
          </div>
          <Progress percent={progress} strokeColor="#1890ff" />
        </div>
      </Card>

      <Card title={<><BookOutlined /> 章节列表 ({chapters.length})</>}>
        <List
          dataSource={chapters}
          renderItem={(chapter) => (
            <List.Item
              style={{ cursor: 'pointer' }}
              onClick={() => handleChapterClick(chapter.id)}
              actions={[
                <span key="version" style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12 }}>
                  v{chapter.version}
                </span>,
                <span key="date" style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12 }}>
                  {dayjs(chapter.updated_at).format('MM-DD HH:mm')}
                </span>,
              ]}
            >
              <List.Item.Meta
                avatar={statusIcons[chapter.status]}
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span>{chapter.title}</span>
                    <Tag color={statusColors[chapter.status]}>{statusLabels[chapter.status]}</Tag>
                  </div>
                }
                description={`第 ${chapter.order} 章`}
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="添加新章节"
        open={isModalOpen}
        onOk={handleCreateChapter}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="title"
            label="章节标题"
            rules={[{ required: true, message: '请输入章节标题' }]}
          >
            <Input placeholder="请输入章节标题" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
