import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  message,
  Divider,
  Select,
  Tag,
} from 'antd'
import {
  SaveOutlined,
  KeyOutlined,
  BellOutlined,
  GlobalOutlined,
  LockOutlined,
} from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores'

export function SettingsPage() {
  const { user } = useAuthStore()
  const [generalForm] = Form.useForm()
  const [apiForm] = Form.useForm()
  const [notificationForm] = Form.useForm()

  const updateSettingsMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.settings.update(data),
    onSuccess: () => {
      message.success('设置保存成功')
    },
    onError: () => {
      message.error('设置保存失败')
    },
  })

  const handleGeneralSave = () => {
    const values = generalForm.getFieldsValue()
    updateSettingsMutation.mutate(values)
  }

  const handleApiSave = () => {
    const values = apiForm.getFieldsValue()
    updateSettingsMutation.mutate(values)
  }

  const handleNotificationSave = () => {
    const values = notificationForm.getFieldsValue()
    updateSettingsMutation.mutate(values)
  }

  return (
    <div className="page-container">
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>系统设置</h1>

      <Card
        title={
          <span>
            <LockOutlined /> 个人资料
          </span>
        }
        style={{ marginBottom: 16 }}
      >
        <Form layout="vertical" initialValues={user ? { name: user.name, email: user.email } : {}}>
          <Form.Item name="name" label="姓名">
            <Input disabled />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input disabled />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Select
              disabled
              options={[
                { value: 'admin', label: '管理员' },
                { value: 'editor', label: '编辑' },
                { value: 'viewer', label: '查看者' },
              ]}
            />
          </Form.Item>
        </Form>
      </Card>

      <Card
        title={
          <span>
            <GlobalOutlined /> 常规设置
          </span>
        }
        style={{ marginBottom: 16 }}
      >
        <Form
          form={generalForm}
          layout="vertical"
          initialValues={{
            language: 'zh-CN',
            timezone: 'Asia/Shanghai',
            theme: 'dark',
            autoSave: true,
            autoSaveInterval: 30,
          }}
        >
          <Form.Item name="language" label="界面语言">
            <Select
              options={[
                { value: 'zh-CN', label: '简体中文' },
                { value: 'en-US', label: 'English' },
              ]}
            />
          </Form.Item>
          <Form.Item name="timezone" label="时区">
            <Select
              options={[
                { value: 'Asia/Shanghai', label: '中国时区 (UTC+8)' },
                { value: 'UTC', label: '世界时 (UTC)' },
              ]}
            />
          </Form.Item>
          <Form.Item name="theme" label="主题">
            <Select
              options={[
                { value: 'dark', label: '深色' },
                { value: 'light', label: '浅色' },
              ]}
            />
          </Form.Item>
          <Divider />
          <Form.Item name="autoSave" label="自动保存">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item name="autoSaveInterval" label="自动保存间隔（秒）">
            <Select
              options={[
                { value: 15, label: '15秒' },
                { value: 30, label: '30秒' },
                { value: 60, label: '60秒' },
              ]}
            />
          </Form.Item>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleGeneralSave}>
            保存设置
          </Button>
        </Form>
      </Card>

      <Card
        title={
          <span>
            <KeyOutlined /> API 设置
          </span>
        }
        style={{ marginBottom: 16 }}
      >
        <Form
          form={apiForm}
          layout="vertical"
          initialValues={{
            minimaxApiKey: '',
            minimaxApiEndpoint: 'https://api.minimax.chat',
          }}
        >
          <Form.Item name="minimaxApiKey" label="MiniMax API Key">
            <Input.Password placeholder="输入API Key" />
          </Form.Item>
          <Form.Item name="minimaxApiEndpoint" label="API 端点">
            <Input placeholder="API端点地址" />
          </Form.Item>
          <Tag color="warning">API Key将安全存储，不会明文显示</Tag>
          <Divider />
          <Button type="primary" icon={<SaveOutlined />} onClick={handleApiSave}>
            保存API设置
          </Button>
        </Form>
      </Card>

      <Card
        title={
          <span>
            <BellOutlined /> 通知设置
          </span>
        }
      >
        <Form
          form={notificationForm}
          layout="vertical"
          initialValues={{
            emailNotification: true,
            reviewNotification: true,
            qualityAlert: true,
            systemNotification: false,
          }}
        >
          <Form.Item name="emailNotification" label="邮件通知">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item name="reviewNotification" label="审核通知">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item name="qualityAlert" label="质量告警">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item name="systemNotification" label="系统公告">
            <Switch />
          </Form.Item>
          <Divider />
          <Button type="primary" icon={<SaveOutlined />} onClick={handleNotificationSave}>
            保存通知设置
          </Button>
        </Form>
      </Card>
    </div>
  )
}
