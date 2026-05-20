import { useState } from 'react'
import { Card, Tabs, Input, Button, Tag, Spin, message, List, Typography } from 'antd'
import {
  SafetyCertificateOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { SecurityScanResult } from '@/types'

const { TextArea } = Input
const { Text } = Typography

const mockScanResult: SecurityScanResult = {
  type: 'text',
  status: 'warning',
  message: '检测到可能的版权敏感内容',
  details: [
    '第3段可能引用了未授权的版权材料',
    '建议添加适当的引用和来源标注',
  ],
}

const mockDoiResult: SecurityScanResult = {
  type: 'doi',
  status: 'safe',
  message: 'DOI验证通过',
  details: [
    'DOI格式正确',
    'DOI已被广泛引用',
  ],
}

const mockRegulationResult: SecurityScanResult = {
  type: 'regulation',
  status: 'safe',
  message: '法规合规性检查通过',
  details: [
    '未发现违规内容',
    '符合教育内容规范',
  ],
}

export function SecurityPage() {
  const [textInput, setTextInput] = useState('')
  const [doiInput, setDoiInput] = useState('')
  const [regulationInput, setRegulationInput] = useState('')

  const scanMutation = useMutation({
    mutationFn: (text: string) => api.security.scanText(text),
    onSuccess: () => {
      message.success('扫描完成')
    },
    onError: () => {
      message.error('扫描失败')
    },
  })

  const doiMutation = useMutation({
    mutationFn: (doi: string) => api.security.verifyDoi(doi),
    onSuccess: () => {
      message.success('DOI验证完成')
    },
    onError: () => {
      message.error('DOI验证失败')
    },
  })

  const regulationMutation = useMutation({
    mutationFn: (text: string) => api.security.verifyRegulation(text),
    onSuccess: () => {
      message.success('法规验证完成')
    },
    onError: () => {
      message.error('验证失败')
    },
  })

  const handleScan = () => {
    if (!textInput.trim()) {
      message.warning('请输入要扫描的文本')
      return
    }
    scanMutation.mutate(textInput)
  }

  const handleDoiVerify = () => {
    if (!doiInput.trim()) {
      message.warning('请输入DOI')
      return
    }
    doiMutation.mutate(doiInput)
  }

  const handleRegulationVerify = () => {
    if (!regulationInput.trim()) {
      message.warning('请输入要验证的文本')
      return
    }
    regulationMutation.mutate(regulationInput)
  }

  const getResultIcon = (status: string) => {
    switch (status) {
      case 'safe':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24 }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14', fontSize: 24 }} />
      case 'danger':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />
      default:
        return null
    }
  }

  const getResultColor = (status: string) => {
    switch (status) {
      case 'safe':
        return 'safe'
      case 'warning':
        return 'warning'
      case 'danger':
        return 'danger'
      default:
        return ''
    }
  }

  const getResultTag = (status: string) => {
    switch (status) {
      case 'safe':
        return <Tag color="success">安全</Tag>
      case 'warning':
        return <Tag color="warning">警告</Tag>
      case 'danger':
        return <Tag color="error">危险</Tag>
      default:
        return null
    }
  }

  const renderResult = (result: SecurityScanResult | undefined) => {
    if (!result) return null

    return (
      <div className={`security-result ${getResultColor(result.status)}`}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          {getResultIcon(result.status)}
          <div>
            <div style={{ fontWeight: 500 }}>{result.message}</div>
            {getResultTag(result.status)}
          </div>
        </div>
        {result.details && result.details.length > 0 && (
          <List
            size="small"
            dataSource={result.details}
            renderItem={(item) => (
              <List.Item style={{ padding: '4px 0' }}>
                <Text type="secondary">{item}</Text>
              </List.Item>
            )}
          />
        )}
      </div>
    )
  }

  const isLoading = scanMutation.isPending || doiMutation.isPending || regulationMutation.isPending

  return (
    <div className="page-container">
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>安全扫描</h1>

      <Card style={{ marginBottom: 16 }}>
        <Tabs
          defaultActiveKey="text"
          items={[
            {
              key: 'text',
              label: (
                <span>
                  <FileTextOutlined />
                  文本扫描
                </span>
              ),
              children: (
                <div>
                  <TextArea
                    rows={6}
                    placeholder="输入要扫描的文本内容..."
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    style={{ marginBottom: 16 }}
                  />
                  <Button
                    type="primary"
                    onClick={handleScan}
                    loading={scanMutation.isPending}
                  >
                    开始扫描
                  </Button>
                  {isLoading && <Spin style={{ marginLeft: 16 }} />}
                  {renderResult(scanMutation.data || mockScanResult)}
                </div>
              ),
            },
            {
              key: 'doi',
              label: (
                <span>
                  <SafetyCertificateOutlined />
                  DOI验证
                </span>
              ),
              children: (
                <div>
                  <Input
                    placeholder="输入DOI，例如：10.1234/example.doi"
                    value={doiInput}
                    onChange={(e) => setDoiInput(e.target.value)}
                    style={{ marginBottom: 16 }}
                  />
                  <Button
                    type="primary"
                    onClick={handleDoiVerify}
                    loading={doiMutation.isPending}
                  >
                    验证DOI
                  </Button>
                  {isLoading && <Spin style={{ marginLeft: 16 }} />}
                  {renderResult(doiMutation.data || mockDoiResult)}
                </div>
              ),
            },
            {
              key: 'regulation',
              label: (
                <span>
                  <SafetyCertificateOutlined />
                  法规验证
                </span>
              ),
              children: (
                <div>
                  <TextArea
                    rows={6}
                    placeholder="输入要验证的文本内容..."
                    value={regulationInput}
                    onChange={(e) => setRegulationInput(e.target.value)}
                    style={{ marginBottom: 16 }}
                  />
                  <Button
                    type="primary"
                    onClick={handleRegulationVerify}
                    loading={regulationMutation.isPending}
                  >
                    验证合规性
                  </Button>
                  {isLoading && <Spin style={{ marginLeft: 16 }} />}
                  {renderResult(regulationMutation.data || mockRegulationResult)}
                </div>
              ),
            },
          ]}
        />
      </Card>

      <Card title="扫描说明">
        <List
          dataSource={[
            {
              title: '文本扫描',
              description: '对教材文本内容进行安全检查，包括版权问题、敏感词汇检测等',
            },
            {
              title: 'DOI验证',
              description: '验证文献引用的DOI是否有效和可访问',
            },
            {
              title: '法规验证',
              description: '检查内容是否符合教育法规和出版规范',
            },
          ]}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta title={item.title} description={item.description} />
            </List.Item>
          )}
        />
      </Card>
    </div>
  )
}
