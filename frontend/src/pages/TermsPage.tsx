import { useState } from 'react'
import {
  Card,
  Table,
  Input,
  Button,
  Tag,
  Modal,
  Form,
  message,
  Space,
  Popconfirm,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  LockOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import dayjs from 'dayjs'
import type { Term } from '@/types'

const mockTerms: Term[] = [
  {
    id: '1',
    term: '人工智能',
    definition: '人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。',
    subject_area: '计算机科学',
    is_locked: true,
    created_at: '2024-01-10T08:00:00Z',
    updated_at: '2024-02-15T10:30:00Z',
  },
  {
    id: '2',
    term: '机器学习',
    definition: '机器学习是一门多领域交叉学科，涉及概率论、统计学、逼近论、凸分析、计算复杂性理论等多门学科。',
    subject_area: '计算机科学',
    is_locked: false,
    created_at: '2024-01-12T08:00:00Z',
    updated_at: '2024-01-12T08:00:00Z',
  },
  {
    id: '3',
    term: '深度学习',
    definition: '深度学习是机器学习的一个分支，它是一种以人工神经网络为架构，对数据进行表征学习的算法。',
    subject_area: '计算机科学',
    is_locked: false,
    created_at: '2024-01-15T08:00:00Z',
    updated_at: '2024-01-15T08:00:00Z',
  },
  {
    id: '4',
    term: '数据结构',
    definition: '数据结构是计算机存储、组织数据的方式。数据结构是指相互之间存在一种或多种特定关系的数据元素的集合。',
    subject_area: '计算机科学',
    is_locked: true,
    created_at: '2024-01-20T08:00:00Z',
    updated_at: '2024-03-01T14:00:00Z',
  },
  {
    id: '5',
    term: '算法',
    definition: '算法是指解题方案的准确而完整的描述，是一系列解决问题的清晰指令。',
    subject_area: '计算机科学',
    is_locked: false,
    created_at: '2024-01-25T08:00:00Z',
    updated_at: '2024-01-25T08:00:00Z',
  },
]

export function TermsPage() {
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTerm, setEditingTerm] = useState<Term | null>(null)
  const [form] = Form.useForm()

  const { data: terms = mockTerms, isLoading } = useQuery({
    queryKey: ['terms', searchText],
    queryFn: () => api.terms.list(searchText),
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<Term>) => api.terms.create(data),
    onSuccess: () => {
      message.success('术语创建成功')
      queryClient.invalidateQueries({ queryKey: ['terms'] })
      closeModal()
    },
    onError: () => {
      message.error('术语创建失败')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Term> }) => api.terms.update(id, data),
    onSuccess: () => {
      message.success('术语更新成功')
      queryClient.invalidateQueries({ queryKey: ['terms'] })
      closeModal()
    },
    onError: () => {
      message.error('术语更新失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.terms.delete(id),
    onSuccess: () => {
      message.success('术语删除成功')
      queryClient.invalidateQueries({ queryKey: ['terms'] })
    },
    onError: () => {
      message.error('术语删除失败')
    },
  })

  const lockMutation = useMutation({
    mutationFn: (id: string) => api.terms.lock(id),
    onSuccess: () => {
      message.success('术语已锁定')
      queryClient.invalidateQueries({ queryKey: ['terms'] })
    },
    onError: () => {
      message.error('术语锁定失败')
    },
  })

  const openCreateModal = () => {
    setEditingTerm(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const openEditModal = (term: Term) => {
    if (term.is_locked) {
      message.warning('已锁定的术语无法编辑')
      return
    }
    setEditingTerm(term)
    form.setFieldsValue(term)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingTerm(null)
    form.resetFields()
  }

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      if (editingTerm) {
        updateMutation.mutate({ id: editingTerm.id, data: values })
      } else {
        createMutation.mutate(values)
      }
    })
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleLock = (id: string) => {
    lockMutation.mutate(id)
  }

  const columns = [
    {
      title: '术语',
      dataIndex: 'term',
      key: 'term',
      width: 200,
      render: (term: string, record: Term) => (
        <Space>
          <span style={{ fontWeight: 500 }}>{term}</span>
          {record.is_locked && <LockOutlined style={{ color: '#faad14' }} />}
        </Space>
      ),
    },
    {
      title: '定义',
      dataIndex: 'definition',
      key: 'definition',
      ellipsis: true,
    },
    {
      title: '学科领域',
      dataIndex: 'subject_area',
      key: 'subject_area',
      width: 150,
      render: (area: string) => <Tag>{area}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_locked',
      key: 'is_locked',
      width: 100,
      render: (locked: boolean) => (
        <Tag color={locked ? 'warning' : 'default'}>
          {locked ? '已锁定' : '可编辑'}
        </Tag>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: Term) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
            disabled={record.is_locked}
          />
          <Button
            type="text"
            size="small"
            icon={<LockOutlined />}
            onClick={() => handleLock(record.id)}
            disabled={record.is_locked}
          />
          <Popconfirm
            title="确定删除此术语？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>术语表</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          添加术语
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索术语..."
          prefix={<SearchOutlined style={{ color: '#999' }} />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ maxWidth: 300 }}
        />
      </Card>

      <Card>
        <Table
          dataSource={terms}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title={editingTerm ? '编辑术语' : '添加术语'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={closeModal}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="term"
            label="术语"
            rules={[{ required: true, message: '请输入术语' }]}
          >
            <Input placeholder="请输入术语" />
          </Form.Item>
          <Form.Item
            name="definition"
            label="定义"
            rules={[{ required: true, message: '请输入定义' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入定义" />
          </Form.Item>
          <Form.Item
            name="subject_area"
            label="学科领域"
            rules={[{ required: true, message: '请输入学科领域' }]}
          >
            <Input placeholder="请输入学科领域" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
