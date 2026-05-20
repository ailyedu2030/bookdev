import { Row, Col, Card, Statistic, Progress, Spin, Tag } from 'antd'
import {
  DesktopOutlined,
  HddOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  RocketOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { Metrics, SystemHealth } from '@/types'

const mockMetrics: Metrics = {
  cpu_usage: 45,
  memory_usage: 62,
  disk_usage: 38,
  active_connections: 128,
  requests_per_second: 1523,
  average_response_time: 45,
}

const mockHealth: SystemHealth = {
  status: 'healthy',
  components: {
    api: 'up',
    database: 'up',
    cache: 'up',
    queue: 'up',
  },
}

export function MonitorPage() {
  const { data: metrics = mockMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => api.monitor.getMetrics(),
    refetchInterval: 5000,
  })

  const { data: health = mockHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.monitor.getHealth(),
    refetchInterval: 10000,
  })

  const isLoading = metricsLoading || healthLoading

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'up':
      case 'healthy':
        return 'healthy'
      case 'degraded':
        return 'warning'
      case 'down':
      case 'critical':
        return 'critical'
      default:
        return ''
    }
  }

  const getHealthLabel = (status: string) => {
    switch (status) {
      case 'up':
        return '正常'
      case 'down':
        return '故障'
      case 'degraded':
        return '降级'
      default:
        return status
    }
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
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>系统监控</h1>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <div className="metric-card">
              <DesktopOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              <div className="metric-value">{metrics.cpu_usage}%</div>
              <div className="metric-label">CPU 使用率</div>
              <Progress
                percent={metrics.cpu_usage}
                size="small"
                showInfo={false}
                strokeColor="#1890ff"
                style={{ marginTop: 8, width: '80%' }}
              />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <div className="metric-card">
              <HddOutlined style={{ fontSize: 32, color: '#722ed1' }} />
              <div className="metric-value">{metrics.memory_usage}%</div>
              <div className="metric-label">内存使用率</div>
              <Progress
                percent={metrics.memory_usage}
                size="small"
                showInfo={false}
                strokeColor="#722ed1"
                style={{ marginTop: 8, width: '80%' }}
              />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <div className="metric-card">
              <DatabaseOutlined style={{ fontSize: 32, color: '#52c41a' }} />
              <div className="metric-value">{metrics.disk_usage}%</div>
              <div className="metric-label">磁盘使用率</div>
              <Progress
                percent={metrics.disk_usage}
                size="small"
                showInfo={false}
                strokeColor="#52c41a"
                style={{ marginTop: 8, width: '80%' }}
              />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <div className="metric-card">
              <CloudServerOutlined style={{ fontSize: 32, color: '#fa8c16' }} />
              <div className="metric-value">{metrics.active_connections}</div>
              <div className="metric-label">活跃连接数</div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic
              title="每秒请求数 (RPS)"
              value={metrics.requests_per_second}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={metrics.average_response_time}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="系统健康状态"
        extra={
          <Tag color={health.status === 'healthy' ? 'success' : health.status === 'warning' ? 'warning' : 'error'}>
            {health.status === 'healthy' ? '健康' : health.status === 'warning' ? '警告' : '危险'}
          </Tag>
        }
      >
        <Row gutter={16}>
          <Col xs={24} sm={12} lg={6}>
            <Card size="small">
              <div className="health-indicator">
                <div className={`health-dot ${getHealthColor(health.components.api)}`} />
                <span style={{ flex: 1 }}>API 服务</span>
                <Tag color={health.components.api === 'up' ? 'success' : 'error'}>
                  {getHealthLabel(health.components.api)}
                </Tag>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card size="small">
              <div className="health-indicator">
                <div className={`health-dot ${getHealthColor(health.components.database)}`} />
                <span style={{ flex: 1 }}>数据库</span>
                <Tag color={health.components.database === 'up' ? 'success' : 'error'}>
                  {getHealthLabel(health.components.database)}
                </Tag>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card size="small">
              <div className="health-indicator">
                <div className={`health-dot ${getHealthColor(health.components.cache)}`} />
                <span style={{ flex: 1 }}>缓存服务</span>
                <Tag color={health.components.cache === 'up' ? 'success' : 'error'}>
                  {getHealthLabel(health.components.cache)}
                </Tag>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card size="small">
              <div className="health-indicator">
                <div className={`health-dot ${getHealthColor(health.components.queue)}`} />
                <span style={{ flex: 1 }}>队列服务</span>
                <Tag color={health.components.queue === 'up' ? 'success' : 'error'}>
                  {getHealthLabel(health.components.queue)}
                </Tag>
              </div>
            </Card>
          </Col>
        </Row>
      </Card>

      <Card title="Prometheus 指标" style={{ marginTop: 16 }}>
        <pre
          style={{
            background: 'rgba(0, 0, 0, 0.2)',
            padding: 16,
            borderRadius: 8,
            overflow: 'auto',
            fontSize: 12,
          }}
        >
          {`# HELP textbook_api_requests_total Total number of API requests
# TYPE textbook_api_requests_total counter
textbook_api_requests_total{method="GET",endpoint="/api/projects"} 15234
textbook_api_requests_total{method="POST",endpoint="/api/chapters"} 3421
textbook_api_requests_total{method="PUT",endpoint="/api/chapters"} 1234

# HELP textbook_content_generation_duration_seconds Time spent generating content
# TYPE textbook_content_generation_duration_seconds histogram
textbook_content_generation_duration_seconds_bucket{le="1"} 120
textbook_content_generation_duration_seconds_bucket{le="5"} 450
textbook_content_generation_duration_seconds_bucket{le="10"} 890
textbook_content_generation_duration_seconds_bucket{le="+Inf"} 1000

# HELP textbook_quality_score Current quality score
# TYPE textbook_quality_score gauge
textbook_quality_score 0.87

# HELP textbook_active_projects Number of active projects
# TYPE textbook_active_projects gauge
textbook_active_projects 12`}
        </pre>
      </Card>
    </div>
  )
}
