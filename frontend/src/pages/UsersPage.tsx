import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Popconfirm,
  Avatar,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import dayjs from 'dayjs'
import type { User } from '@/types'

const mockUsers: User[] = [
  {
    id: '1',
    email: 'admin@example.com',
    name: '管理员',
    role: 'admin',
    created_at: '2024-01-01T08:00:00Z',
  },
  {
    id: '2',
    email: 'editor1@example.com',
    name: '张三',
    role: 'editor',
    created_at: '2024-01-10T08:00:00Z',
  },
  {
    id: '3',
    email: 'editor2@example.com',
    name: '李四',
    role: 'editor',
    created_at: '2024-01-15T08:00:00Z',
  },
  {
    id: '4',
    email: 'viewer1@example.com',
    name: '王五',
    role: 'viewer',
    created_at: '2024-02-01T08:00:00Z',
  },
  {
    id: '5',
    email: 'viewer2@example.com',
    name: '赵六',
    role: 'viewer',
    created_at: '2024-02-10T08:00:00Z',
  },
]

const roleColors: Record<string, string> = {
  admin: 'red',
  editor: 'blue',
  viewer: 'green',
}

const roleLabels: Record<string, string> = {
  admin: '管理员',
  editor: '编辑',
  viewer: '查看者',
}

export function UsersPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [form] = Form.useForm()

  const { data: users = mockUsers, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.users.list(),
  })

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.users.create(data),
    onSuccess: () => {
      message.success('用户创建成功')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      closeModal()
    },
    onError: () => {
      message.error('用户创建失败')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<User> }) => api.users.update(id, data),
    onSuccess: () => {
      message.success('用户更新成功')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      closeModal()
    },
    onError: () => {
      message.error('用户更新失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.users.delete(id),
    onSuccess: () => {
      message.success('用户删除成功')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: () => {
      message.error('用户删除失败')
    },
  })

  const openCreateModal = () => {
    setEditingUser(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const openEditModal = (user: User) => {
    setEditingUser(user)
    form.setFieldsValue({
      name: user.name,
      email: user.email,
      role: user.role,
      password: '',
    })
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingUser(null)
    form.resetFields()
  }

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      if (editingUser) {
        updateMutation.mutate({
          id: editingUser.id,
          data: {
            name: values.name,
            email: values.email,
            role: values.role,
            ...(values.password ? { password: values.password } : {}),
          },
        })
      } else {
        createMutation.mutate({
          name: values.name,
          email: values.email,
          role: values.role,
          password: values.password,
        })
      }
    })
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const columns = [
    {
      title: '用户',
      key: 'user',
      render: (_: unknown, record: User) => (
        <Space>
          <Avatar icon={<UserOutlined />} style={{ background: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 500 }}>{record.name}</div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (role: string) => (
        <Tag color={roleColors[role]}>{roleLabels[role]}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: User) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title="确定删除此用户？"
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
        <h1 style={{ fontSize: 24, margin: 0 }}>用户管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          添加用户
        </Button>
      </div>

      <Card>
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={closeModal}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select
              placeholder="请选择角色"
              options={[
                { value: 'admin', label: '管理员' },
                { value: 'editor', label: '编辑' },
                { value: 'viewer', label: '查看者' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: !editingUser, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder={editingUser ? '留空则不修改密码' : '请输入密码'} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
