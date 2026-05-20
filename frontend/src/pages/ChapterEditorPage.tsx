import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Card,
  Button,
  Tag,
  Space,
  Spin,
  Breadcrumb,
  message,
  Tooltip,
  Divider,
  Typography,
} from 'antd'
import {
  SaveOutlined,
  ThunderboltOutlined,
  SendOutlined,
  CheckOutlined,
  CloseOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { api } from '@/api/client'
import dayjs from 'dayjs'
import type { Chapter, Version } from '@/types'

const { Text } = Typography

const mockChapter: Chapter = {
  id: '1',
  project_id: '1',
  title: '第一章：计算机基础',
  content: '<h1>计算机基础知识</h1><p>计算机是一种用于高速计算的电子计算机器，可以进行数值计算、逻辑计算，具有存储记忆功能，是能够按照程序运行，自动、高速处理海量数据的现代化智能电子设备。</p><h2>计算机的发展历程</h2><p>计算机的发展经历了从大型机到个人电脑，从单机到网络的演变过程。</p><h2>计算机的组成</h2><p>计算机主要由硬件系统和软件系统两大部分组成。</p>',
  status: 'draft',
  order: 1,
  version: 3,
  created_at: '2024-01-15T08:00:00Z',
  updated_at: '2024-03-10T14:30:00Z',
}

const mockVersions: Version[] = [
  {
    id: '1',
    chapter_id: '1',
    version_number: 3,
    content: '<h1>计算机基础知识</h1><p>计算机是一种用于高速计算的电子计算机器...</p>',
    created_at: '2024-03-10T14:30:00Z',
    created_by: '张三',
  },
  {
    id: '2',
    chapter_id: '1',
    version_number: 2,
    content: '<h1>计算机基础</h1><p>计算机是一种电子设备...</p>',
    created_at: '2024-02-20T10:15:00Z',
    created_by: '李四',
  },
  {
    id: '3',
    chapter_id: '1',
    version_number: 1,
    content: '<h1>计算机</h1><p>计算机是现代电子设备...</p>',
    created_at: '2024-01-15T08:00:00Z',
    created_by: '张三',
  },
]

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

export function ChapterEditorPage() {
  const { id, cid } = useParams<{ id: string; cid: string }>()
  const queryClient = useQueryClient()
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [showVersions, setShowVersions] = useState(true)

  const { data: chapter = mockChapter, isLoading } = useQuery({
    queryKey: ['chapter', id, cid],
    queryFn: () => api.chapters.get(id!, cid!),
  })

  const { data: versions = mockVersions } = useQuery({
    queryKey: ['versions', id, cid],
    queryFn: () => api.versions.list(id!, cid!),
  })

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: '开始编写章节内容...',
      }),
    ],
    content: chapter.content,
    onUpdate: () => {},
  })

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Chapter>) => api.chapters.update(id!, cid!, data),
    onSuccess: () => {
      message.success('保存成功')
      queryClient.invalidateQueries({ queryKey: ['chapter', id, cid] })
      setSaving(false)
    },
    onError: () => {
      message.error('保存失败')
      setSaving(false)
    },
  })

  const generateMutation = useMutation({
    mutationFn: () => api.chapters.generate(id!, cid!),
    onSuccess: (data) => {
      message.success('AI生成完成')
      editor?.commands.setContent(data.content)
      queryClient.invalidateQueries({ queryKey: ['chapter', id, cid] })
      setGenerating(false)
    },
    onError: () => {
      message.error('AI生成失败')
      setGenerating(false)
    },
  })

  const submitReviewMutation = useMutation({
    mutationFn: () => api.chapters.submitReview(id!, cid!),
    onSuccess: () => {
      message.success('已提交审核')
      queryClient.invalidateQueries({ queryKey: ['chapter', id, cid] })
    },
    onError: () => {
      message.error('提交审核失败')
    },
  })

  const approveMutation = useMutation({
    mutationFn: () => api.chapters.approve(id!, cid!),
    onSuccess: () => {
      message.success('审核通过')
      queryClient.invalidateQueries({ queryKey: ['chapter', id, cid] })
    },
    onError: () => {
      message.error('操作失败')
    },
  })

  const handleSave = () => {
    if (!editor) return
    setSaving(true)
    updateMutation.mutate({ content: editor.getHTML() })
  }

  const handleGenerate = () => {
    setGenerating(true)
    generateMutation.mutate()
  }

  const handleSubmitReview = () => {
    submitReviewMutation.mutate()
  }

  const handleApprove = () => {
    approveMutation.mutate()
  }

  const handleVersionSelect = (version: Version) => {
    editor?.commands.setContent(version.content)
    message.info(`已加载版本 ${version.version_number}`)
  }

  useEffect(() => {
    if (editor && chapter.content) {
      editor.commands.setContent(chapter.content)
    }
  }, [editor, chapter.content])

  if (isLoading) {
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
          { title: '项目详情', href: `/projects/${id}` },
          { title: chapter.title },
        ]}
      />

      <Card
        title={
          <Space>
            <span>{chapter.title}</span>
            <Tag color={statusColors[chapter.status]}>{statusLabels[chapter.status]}</Tag>
            <Text type="secondary" style={{ fontSize: 12 }}>
              v{chapter.version}
            </Text>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="AI生成内容">
              <Button
                icon={<ThunderboltOutlined />}
                onClick={handleGenerate}
                loading={generating}
              >
                AI生成
              </Button>
            </Tooltip>
            <Button icon={<SaveOutlined />} onClick={handleSave} loading={saving}>
              保存
            </Button>
            <Divider type="vertical" />
            {chapter.status === 'draft' && (
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSubmitReview}
                loading={submitReviewMutation.isPending}
              >
                提交审核
              </Button>
            )}
            {chapter.status === 'in_review' && (
              <>
                <Button
                  icon={<CheckOutlined />}
                  onClick={handleApprove}
                  loading={approveMutation.isPending}
                  style={{ background: '#52c41a', borderColor: '#52c41a' }}
                >
                  通过
                </Button>
                <Button
                  danger
                  icon={<CloseOutlined />}
                >
                  拒绝
                </Button>
              </>
            )}
          </Space>
        }
      >
        <div className="editor-container">
          <div className="editor-main">
            <div
              style={{
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8,
                padding: 16,
                minHeight: 500,
                background: 'rgba(255,255,255,0.02)',
              }}
            >
              <EditorContent
                editor={editor}
                style={{ height: '100%' }}
              />
            </div>
          </div>

          <div className="editor-sidebar">
            <Card
              title={
                <Space>
                  <HistoryOutlined />
                  版本历史
                </Space>
              }
              size="small"
              extra={
                <Button
                  type="text"
                  size="small"
                  onClick={() => setShowVersions(!showVersions)}
                >
                  {showVersions ? '隐藏' : '显示'}
                </Button>
              }
            >
              {showVersions && (
                <div>
                  {versions.map((version) => (
                    <div
                      key={version.id}
                      className="version-item"
                      onClick={() => handleVersionSelect(version)}
                    >
                      <div style={{ fontWeight: 500 }}>版本 {version.version_number}</div>
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
                        {version.created_by}
                      </div>
                      <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>
                        {dayjs(version.created_at).format('YYYY-MM-DD HH:mm')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      </Card>
    </div>
  )
}
