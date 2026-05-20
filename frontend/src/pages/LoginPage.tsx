import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Form, Input, Button, Card, message, Typography } from 'antd'
import { LockOutlined, MailOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores'

const { Title, Text } = Typography

export function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const loginMutation = useMutation({
    mutationFn: (data: { email: string; password: string }) => api.auth.login(data),
    onSuccess: (data) => {
      setAuth(data.user, data.token)
      message.success('登录成功')
      navigate('/dashboard')
    },
    onError: () => {
      message.error('邮箱或密码错误')
      setLoading(false)
    },
  })

  const onFinish = (values: { email: string; password: string }) => {
    setLoading(true)
    loginMutation.mutate(values)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #001529 0%, #003a70 100%)',
        padding: 24,
      }}
    >
      <Card
        style={{
          width: 400,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
        }}
        styles={{
          body: { padding: 32 },
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 8 }}>
            AI教材开发系统
          </Title>
          <Text type="secondary">登录到您的账户</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
          initialValues={{ email: 'admin@example.com', password: 'password123' }}
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<MailOutlined style={{ color: '#999' }} />}
              placeholder="邮箱地址"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#999' }} />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loading}
            >
              登录
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">还没有账户？</Text>
            <Link to="/register" style={{ marginLeft: 8 }}>
              注册
            </Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}
