import { Row, Col, Card, Statistic, Progress, List, Tag, Spin, Badge } from 'antd'
import {
  ApiOutlined,
  ProjectOutlined,
  BookOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { ApiStatus, QualityGate, ActivityLog } from '@/types'

dayjs.extend(relativeTime)

const mockApiStatus: ApiStatus = {
  minimax_api: 'connected',
  database: 'connected',
  redis: 'connected',
}

const mockQualityGate: QualityGate = {
  linter: 'passed',
  security: 'passed',
  coverage: 'pending',
}

const mockActivityLogs: ActivityLog[] = [
  {
    id: '1',
    action: '创建',
    user_id: '1',
    user_name: '张三',
    resource_type: 'chapter',
    resource_id: '1',
    resource_name: '第一章：计算机基础',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: '2',
    action: '提交审核',
    user_id: '2',
    user_name: '李四',
    resource_type: 'chapter',
    resource_id: '2',
    resource_name: '第二章：数据结构',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
  {
    id: '3',
    action: '审核通过',
    user_id: '3',
    user_name: '王五',
    resource_type: 'chapter',
    resource_id: '3',
    resource_name: '第三章：算法设计',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    id: '4',
    action: '生成内容',
    user_id: '1',
    user_name: '张三',
    resource_type: 'chapter',
    resource_id: '4',
    resource_name: '第四章：操作系统',
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
  },
  {
    id: '5',
    action: '更新术语',
    user_id: '2',
    user_name: '李四',
    resource_type: 'term',
    resource_id: '1',
    resource_name: '人工智能',
    timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
  },
]

const mockModules = [
  { name: '内容生成', status: 'running' },
  { name: '质量检查', status: 'idle' },
  { name: '安全扫描', status: 'idle' },
  { name: '知识图谱', status: 'running' },
  { name: '用户管理', status: 'idle' },
]

export function DashboardPage() {
  const { data: apiStatus = mockApiStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['apiStatus'],
    queryFn: () => api.dashboard.getStatus(),
    refetchInterval: 30000,
  })

  const { data: qualityGate = mockQualityGate, isLoading: gateLoading } = useQuery({
    queryKey: ['qualityGate'],
    queryFn: () => api.dashboard.getQualityGates(),
    refetchInterval: 60000,
  })

  const { data: activityLogs = mockActivityLogs, isLoading: logsLoading } = useQuery({
    queryKey: ['activityLogs'],
    queryFn: () => api.dashboard.getActivityLogs(10),
  })

  const isLoading = statusLoading || gateLoading || logsLoading

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'up':
      case 'passed':
        return 'success'
      case 'disconnected':
      case 'down':
      case 'failed':
        return 'error'
      case 'error':
      case 'degraded':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getQualityStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />
      default:
        return <SyncOutlined spin />
    }
  }

  const getModuleStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'processing'
      case 'idle':
        return 'default'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <div className="page-container">
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>仪表盘</h1>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Badge status={getStatusColor(apiStatus.minimax_api) as any} />
                <Statistic
                  title="MiniMax API 状态"
                  value={apiStatus.minimax_api === 'connected' ? '已连接' : '未连接'}
                  prefix={<ApiOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="活跃项目"
                  value={12}
                  prefix={<ProjectOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="章节总数"
                  value={48}
                  prefix={<BookOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="已完成章节"
                  value={23}
                  suffix="/ 48"
                  valueStyle={{ color: '#52c41a' }}
                />
                <Progress
                  percent={48}
                  size="small"
                  showInfo={false}
                  strokeColor="#52c41a"
                  style={{ marginTop: 8 }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={24}>
              <Card title="质量门禁检查">
                <div className="quality-gate">
                  <div className="quality-item">
                    <Badge status={getStatusColor(qualityGate.linter) as any} />
                    {getQualityStatusIcon(qualityGate.linter)}
                    <span style={{ marginTop: 8 }}>代码检查</span>
                    <Tag color={qualityGate.linter === 'passed' ? 'green' : qualityGate.linter === 'failed' ? 'red' : 'orange'}>
                      {qualityGate.linter === 'passed' ? '通过' : qualityGate.linter === 'failed' ? '失败' : '待定'}
                    </Tag>
                  </div>
                  <div className="quality-item">
                    <Badge status={getStatusColor(qualityGate.security) as any} />
                    {getQualityStatusIcon(qualityGate.security)}
                    <span style={{ marginTop: 8 }}>安全扫描</span>
                    <Tag color={qualityGate.security === 'passed' ? 'green' : qualityGate.security === 'failed' ? 'red' : 'orange'}>
                      {qualityGate.security === 'passed' ? '通过' : qualityGate.security === 'failed' ? '失败' : '待定'}
                    </Tag>
                  </div>
                  <div className="quality-item">
                    <Badge status={getStatusColor(qualityGate.coverage) as any} />
                    {getQualityStatusIcon(qualityGate.coverage)}
                    <span style={{ marginTop: 8 }}>覆盖率</span>
                    <Tag color={qualityGate.coverage === 'passed' ? 'green' : qualityGate.coverage === 'failed' ? 'red' : 'orange'}>
                      {qualityGate.coverage === 'passed' ? '通过' : qualityGate.coverage === 'failed' ? '失败' : '待定'}
                    </Tag>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="最近活动" style={{ marginBottom: 16 }}>
                <List
                  dataSource={activityLogs}
                  renderItem={(item) => (
                    <div className="activity-item">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Tag>{item.action}</Tag>
                        <span>{item.user_name}</span>
                        <span style={{ color: 'rgba(255,255,255,0.45)' }}>
                          {item.resource_type === 'chapter' ? '章节' : '术语'}
                        </span>
                        <span style={{ fontWeight: 500 }}>{item.resource_name}</span>
                      </div>
                      <div style={{ marginTop: 4, fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
                        {dayjs(item.timestamp).fromNow()}
                      </div>
                    </div>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="模块状态">
                <List
                  dataSource={mockModules}
                  renderItem={(module) => (
                    <div className="module-status" style={{ padding: '8px 0' }}>
                      <Badge status={getModuleStatusColor(module.status) as any} />
                      <span style={{ flex: 1 }}>{module.name}</span>
                      <Tag>
                        {module.status === 'running' ? '运行中' : module.status === 'idle' ? '空闲' : '错误'}
                      </Tag>
                    </div>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  )
}
