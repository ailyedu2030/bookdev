import { useState, useEffect, useRef } from 'react'
import { Card, Select, Tag, Spin, Empty, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { KnowledgeNode, KnowledgeEdge } from '@/types'

const { Text } = Typography

const mockNodes: KnowledgeNode[] = [
  { id: '1', type: 'Chapter', label: '计算机基础' },
  { id: '2', type: 'Section', label: '计算机发展史' },
  { id: '3', type: 'Section', label: '计算机组成' },
  { id: '4', type: 'Concept', label: '算法' },
  { id: '5', type: 'Concept', label: '数据结构' },
  { id: '6', type: 'Term', label: '人工智能' },
  { id: '7', type: 'Term', label: '机器学习' },
  { id: '8', type: 'Chapter', label: '数据结构' },
  { id: '9', type: 'Section', label: '线性结构' },
  { id: '10', type: 'Concept', label: '链表' },
]

const mockEdges: KnowledgeEdge[] = [
  { source: '1', target: '2', type: 'CONTAINS' },
  { source: '1', target: '3', type: 'CONTAINS' },
  { source: '8', target: '9', type: 'CONTAINS' },
  { source: '2', target: '4', type: 'DEFINES' },
  { source: '3', target: '5', type: 'USES' },
  { source: '4', target: '5', type: 'FOLLOWS' },
  { source: '6', target: '7', type: 'REFERENCES' },
  { source: '5', target: '10', type: 'DEFINES' },
  { source: '9', target: '10', type: 'CONTAINS' },
]

const nodeTypeColors: Record<string, string> = {
  Chapter: 'blue',
  Section: 'cyan',
  Concept: 'purple',
  Term: 'orange',
}

const edgeTypeColors: Record<string, string> = {
  CONTAINS: 'blue',
  FOLLOWS: 'green',
  DEFINES: 'purple',
  USES: 'orange',
  REFERENCES: 'red',
}

export function KnowledgeGraphPage() {
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null)
  const [filterType, setFilterType] = useState<string>('all')
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const { data: graphData, isLoading } = useQuery({
    queryKey: ['knowledgeGraph'],
    queryFn: () => api.knowledge.getGraph(),
  })

  const nodes = graphData?.nodes || mockNodes
  const edges = graphData?.edges || mockEdges

  const filteredNodes = filterType === 'all' ? nodes : nodes.filter((n) => n.type === filterType)

  useEffect(() => {
    if (!canvasRef.current || filteredNodes.length === 0) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * 2
    canvas.height = rect.height * 2
    ctx.scale(2, 2)

    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'
    ctx.fillRect(0, 0, rect.width, rect.height)

    const nodePositions = new Map<string, { x: number; y: number }>()
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    const radius = Math.min(rect.width, rect.height) / 3

    filteredNodes.forEach((node, index) => {
      const angle = (index / filteredNodes.length) * 2 * Math.PI
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)
      nodePositions.set(node.id, { x, y })
    })

    ctx.lineWidth = 1
    edges.forEach((edge) => {
      const source = nodePositions.get(edge.source)
      const target = nodePositions.get(edge.target)
      if (source && target) {
        ctx.beginPath()
        ctx.strokeStyle = edgeTypeColors[edge.type] + '80'
        ctx.moveTo(source.x, source.y)
        ctx.lineTo(target.x, target.y)
        ctx.stroke()

        const midX = (source.x + target.x) / 2
        const midY = (source.y + target.y) / 2
        ctx.fillStyle = edgeTypeColors[edge.type]
        ctx.font = '10px monospace'
        ctx.fillText(edge.type, midX - 20, midY - 5)
      }
    })

    filteredNodes.forEach((node) => {
      const pos = nodePositions.get(node.id)
      if (!pos) return

      const isSelected = selectedNode?.id === node.id
      const nodeRadius = isSelected ? 30 : 25

      ctx.beginPath()
      ctx.arc(pos.x, pos.y, nodeRadius, 0, 2 * Math.PI)

      const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, nodeRadius)
      const baseColor = nodeTypeColors[node.type]
      gradient.addColorStop(0, baseColor)
      gradient.addColorStop(1, baseColor + '40')
      ctx.fillStyle = gradient
      ctx.fill()

      if (isSelected) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.stroke()
      }

      ctx.fillStyle = '#fff'
      ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(node.label.substring(0, 8), pos.x, pos.y + nodeRadius + 16)
    })
  }, [filteredNodes, edges, selectedNode])

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const centerX = rect.width / 2
    const centerY = rect.height / 2
    const radius = Math.min(rect.width, rect.height) / 3

    let closestNode: KnowledgeNode | null = null
    let closestDistance = Infinity

    filteredNodes.forEach((node, index) => {
      const angle = (index / filteredNodes.length) * 2 * Math.PI
      const nodeX = centerX + radius * Math.cos(angle)
      const nodeY = centerY + radius * Math.sin(angle)

      const distance = Math.sqrt(Math.pow(x - nodeX, 2) + Math.pow(y - nodeY, 2))
      if (distance < 30 && distance < closestDistance) {
        closestDistance = distance
        closestNode = node
      }
    })

    setSelectedNode(closestNode)
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
        <h1 style={{ fontSize: 24, margin: 0 }}>知识图谱</h1>
        <Select
          value={filterType}
          onChange={setFilterType}
          style={{ width: 200 }}
          options={[
            { value: 'all', label: '全部类型' },
            { value: 'Chapter', label: '章节' },
            { value: 'Section', label: '小节' },
            { value: 'Concept', label: '概念' },
            { value: 'Term', label: '术语' },
          ]}
        />
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {Object.entries(nodeTypeColors).map(([type, color]) => (
          <Tag key={type} color={color}>
            {type === 'Chapter' ? '章节' : type === 'Section' ? '小节' : type === 'Concept' ? '概念' : '术语'}
          </Tag>
        ))}
      </div>

      <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {Object.entries(edgeTypeColors).map(([type, color]) => (
          <Text key={type} style={{ fontSize: 12, color }}>
            {type}
          </Text>
        ))}
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <canvas
          ref={canvasRef}
          className="knowledge-graph-container"
          onClick={handleCanvasClick}
          style={{ cursor: 'pointer' }}
        />
        {filteredNodes.length === 0 && (
          <Empty description="暂无知识图谱数据" style={{ paddingTop: 100 }} />
        )}
      </Card>

      {selectedNode && (
        <Card
          size="small"
          title="节点详情"
          style={{ marginTop: 16 }}
          extra={
            <Tag color={nodeTypeColors[selectedNode.type]}>
              {selectedNode.type === 'Chapter' ? '章节' : selectedNode.type === 'Section' ? '小节' : selectedNode.type === 'Concept' ? '概念' : '术语'}
            </Tag>
          }
        >
          <p><strong>名称：</strong>{selectedNode.label}</p>
          <p><strong>ID：</strong>{selectedNode.id}</p>
          <p><strong>类型：</strong>{selectedNode.type}</p>
        </Card>
      )}
    </div>
  )
}
