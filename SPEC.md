# AI多Agent教材编写系统 - 完整技术规格说明书

## 1. 项目概述

**项目名称**: AI多Agent教材编写系统
**版本**: v1.0.0
**目标**: 基于AI多智能体协同的教材编写系统，支持20万汉字（约100万Tokens），符合中国出版行业规范
**模型**: MiniMax-M2.7 (200K上下文窗口, ¥2/1M tokens)

## 2. 技术栈

### 后端
- **语言**: Python 3.11+
- **框架**: FastAPI + Pydantic v2
- **ORM**: SQLAlchemy 2.0 + asyncpg
- **工作流引擎**: Temporal + Redis Streams
- **消息队列**: Kafka + aiokafka
- **主数据库**: PostgreSQL 15 + apoc扩展
- **向量检索**: Qdrant
- **缓存**: Redis Cluster
- **密钥管理**: HashiCorp Vault

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5
- **状态管理**: Zustand + React Query
- **路由**: React Router v6
- **构建工具**: Vite

### 基础设施
- **容器化**: Docker Compose + Kubernetes
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack

## 3. 功能模块 (F00-F32)

| 模块 | 名称 | 职责 | 状态 |
|------|------|------|------|
| F00 | Kafka事件总线 | 异步事件分发，日志聚合 | ✅ |
| F01 | 不可变日志 | SHA-256链式哈希，完整性验证 | ✅ |
| F02 | 上下文预算管理 | Token分配/压缩/淘汰策略 | ✅ |
| F03 | 内容寻址 | SHA-256内容哈希，自动去重 | ✅ |
| F04 | Temporal工作流 | 章节编写状态机，断点续写 | ✅ |
| F05 | 知识图谱(内存) | 章节/概念/术语关系 | ✅ |
| F06 | 一级验证引擎 | 数据血缘追踪，Git-like版本 | ✅ |
| F07 | DOI验证 | CrossRef API引用验证 | ✅ |
| F08 | 法规引用核实 | 三层验证(法律/条文/内容) | ✅ |
| F09 | 素材安全 | 来源注册，内容哈希验证 | ✅ |
| F10 | 概念安全 | 概念定义完整性验证 | ✅ |
| F11 | 工作流安全 | HSM签名，回调验证 | ✅ |
| F12 | 审批安全 | 审批记录，HSM签名验证 | ✅ |
| F13 | 全局语义扫描 | 向量嵌入语义搜索 | ✅ |
| F14 | 引用完整性 | 引用注册表，DOI验证 | ✅ |
| F15 | 政治敏感性 | 敏感词检测，政治内容追踪 | ✅ |
| F16 | 统计抽样 | 置信度计算，抽样验证 | ✅ |
| F17 | 交叉引用 | 引用解析，跨章引用解析 | ✅ |
| F18 | 术语表 | 术语注册，锁定，同义管理 | ✅ |
| F19 | 逻辑链 | 连贯性分析，依赖图 | ✅ |
| F20 | LLM评判 | LLM-as-Judge评分 | ✅ |
| F21 | 风险分级 | 分数→风险等级映射 | ✅ |
| F22 | 素材RAG | 向量存储，嵌入，RAG引擎 | ✅ |
| F23 | 内容安全过滤 | 脏话/仇恨/PII/政治/注入检测 | ✅ |
| F24 | 配置中心 | JSON配置，热重载 | ✅ |
| F25 | 模型路由 | 多模型路由，成本优化 | ✅ |
| F26 | 数据溯源追踪 | 全链路追踪，影响分析 | ✅ |
| F27 | 图RAG | 基于知识图谱的RAG查询 | ✅ |
| F28 | 监控仪表盘 | 指标收集，健康检查 | ✅ |
| F29 | 质量门禁 | Linter/Security/Coverage检查 | ✅ |
| F30 | 金标准数据集 | 参考教材样本库 | ✅ |
| F31 | MiniMax客户端 | M2.7 API集成，限流，成本追踪 | ✅ |
| F32 | PG知识图谱 | PostgreSQL图谱适配器 | ✅ |

## 4. 数据库Schema

### 核心业务表

```sql
-- 章节表
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    order_num INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    word_count INTEGER DEFAULT 0,
    version VARCHAR(20) NOT NULL,
    content_hash VARCHAR(64),
    parent_chapter_id UUID REFERENCES chapters(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 章节内容表
CREATE TABLE chapter_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    content TEXT,
    version VARCHAR(20) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 小节表
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    order_num INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    word_count INTEGER DEFAULT 0,
    parent_section_id UUID REFERENCES sections(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 概念表
CREATE TABLE concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    definition TEXT NOT NULL,
    domain VARCHAR(100),
    related_terms TEXT[],
    source_chapter_id UUID REFERENCES chapters(id),
    locked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 术语表
CREATE TABLE terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term VARCHAR(200) NOT NULL,
    definition TEXT NOT NULL,
    synonyms TEXT[],
    domain VARCHAR(100),
    first_defined_at VARCHAR(50),
    locked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    organization_id UUID,
    clearance_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 角色表
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户角色关联表
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 权限表
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    UNIQUE(resource, action)
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    owner_id UUID REFERENCES users(id),
    total_chapters INTEGER DEFAULT 0,
    current_progress INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 项目成员表
CREATE TABLE project_members (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

-- 审核记录表
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES users(id),
    status VARCHAR(20) NOT NULL,
    comments TEXT,
    reviewed_at TIMESTAMP DEFAULT NOW()
);

-- 审计日志表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    user_id UUID,
    resource_type VARCHAR(100),
    resource_id UUID,
    action VARCHAR(50),
    result VARCHAR(20),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    signature VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 内容版本表
CREATE TABLE content_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    merkle_root VARCHAR(128),
    change_reason TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 素材资产表
CREATE TABLE material_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_hash VARCHAR(64),
    file_size INTEGER,
    mime_type VARCHAR(100),
    source_url TEXT,
    copyright_info TEXT,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 引用表
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    doi VARCHAR(255),
    title TEXT,
    authors TEXT[],
    journal VARCHAR(255),
    year INTEGER,
    url TEXT,
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 图谱节点表 (F32)
CREATE TABLE graph_nodes (
    id TEXT PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,
    properties JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 图谱边表 (F32)
CREATE TABLE graph_edges (
    id SERIAL PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES graph_nodes(id),
    target_id TEXT NOT NULL REFERENCES graph_nodes(id),
    edge_type VARCHAR(50) NOT NULL,
    properties JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 索引

```sql
CREATE INDEX idx_chapters_project ON chapters(project_id);
CREATE INDEX idx_chapters_status ON chapters(status);
CREATE INDEX idx_sections_chapter ON sections(chapter_id);
CREATE INDEX idx_concepts_domain ON concepts(domain);
CREATE INDEX idx_terms_domain ON terms(domain);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_graph_nodes_type ON graph_nodes(node_type);
CREATE INDEX idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX idx_graph_edges_target ON graph_edges(target_id);
CREATE INDEX idx_graph_edges_type ON graph_edges(edge_type);
CREATE INDEX idx_graph_edges_source_target ON graph_edges(source_id, target_id);
CREATE INDEX idx_graph_nodes_properties ON graph_nodes USING GIN(properties);
CREATE INDEX idx_graph_edges_properties ON graph_edges USING GIN(properties);
```

## 5. API端点

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新Token
- `POST /api/auth/logout` - 登出

### 项目管理
- `GET /api/projects` - 列表
- `POST /api/projects` - 创建
- `GET /api/projects/{id}` - 详情
- `PUT /api/projects/{id}` - 更新
- `DELETE /api/projects/{id}` - 删除
- `POST /api/projects/{id}/members` - 添加成员

### 章节管理
- `GET /api/chapters/{project_id}` - 列表
- `POST /api/chapters` - 创建
- `GET /api/chapters/{id}` - 详情
- `PUT /api/chapters/{id}` - 更新
- `DELETE /api/chapters/{id}` - 删除
- `POST /api/chapters/{id}/generate` - AI生成
- `POST /api/chapters/{id}/review` - 提交审核
- `POST /api/chapters/{id}/approve` - 审核通过
- `POST /api/chapters/{id}/reject` - 审核拒绝

### 知识图谱
- `GET /api/knowledge-graph/nodes` - 节点列表
- `POST /api/knowledge-graph/nodes` - 创建节点
- `GET /api/knowledge-graph/nodes/{id}` - 节点详情
- `GET /api/knowledge-graph/edges` - 边列表
- `POST /api/knowledge-graph/edges` - 创建边
- `GET /api/knowledge-graph/query` - 图谱查询

### 术语管理
- `GET /api/terms` - 列表
- `POST /api/terms` - 创建
- `PUT /api/terms/{id}` - 更新
- `POST /api/terms/{id}/lock` - 锁定

### 安全扫描
- `POST /api/security/scan` - 内容扫描
- `POST /api/security/doi/verify` - DOI验证
- `POST /api/security/regulation/verify` - 法规验证
- `POST /api/security/semantic/scan` - 语义扫描

### 监控
- `GET /api/monitor/health` - 健康检查
- `GET /api/monitor/metrics` - 指标
- `GET /api/monitor/logs` - 日志

### 工作流
- `GET /api/workflows` - 列表
- `GET /api/workflows/{id}` - 详情
- `POST /api/workflows/{id}/signal` - 发送信号
- `POST /api/workflows/{id}/cancel` - 取消

### 用户管理 (Admin)
- `GET /api/users` - 列表
- `POST /api/users` - 创建
- `PUT /api/users/{id}` - 更新
- `DELETE /api/users/{id}` - 删除
- `PUT /api/users/{id}/role` - 更新角色

## 6. 安全架构

### L1 边界安全
- API Gateway (Nginx) + WAF
- Rate Limiting: 30/min (匿名), 300/min (认证)
- TLS 1.3 强制

### L2 应用安全
- 输入验证 (Pydantic)
- CSRF Token (double submit)
- Security Headers (HSTS/CSP/X-Frame-Options)

### L3 数据安全
- TLS 1.3 传输加密
- AES-256 静态加密 (Vault)
- HashiCorp Vault 密钥管理

### L4 AI安全
- Prompt注入检测
- 指令签名链 (HMAC-SHA256)
- 外部内容沙箱 (gVisor)
- AI输出校验

### L5 审计合规
- RBAC (6角色)
- 不可变审计日志
- 内容版本追溯 (Merkle Tree)

## 7. 前端页面

| 页面 | 路由 | 描述 |
|------|------|------|
| 登录 | `/login` | 用户登录 |
| 注册 | `/register` | 用户注册 |
| 仪表盘 | `/dashboard` | 系统概览，实时指标 |
| 项目列表 | `/projects` | 项目管理 |
| 项目详情 | `/projects/:id` | 项目详情，章节列表 |
| 章节编辑 | `/projects/:id/chapters/:cid` | 富文本编辑 |
| 知识图谱 | `/knowledge-graph` | 图谱可视化 |
| 术语管理 | `/terms` | 术语表管理 |
| 安全扫描 | `/security` | DOI/法规/语义扫描 |
| 监控面板 | `/monitor` | Prometheus数据 |
| 用户管理 | `/admin/users` | Admin功能 |
| 设置 | `/settings` | 系统配置 |

## 8. 测试策略

### 单元测试 (每个模块)
- 函数级测试
- Mock外部依赖
- 覆盖率 ≥80%

### 集成测试
- API端点测试
- 数据库操作测试
- 外部服务Mock测试

### E2E测试 (Playwright)
- 完整用户流程
- 20万字教材生成完整流程

### Golden Dataset回归测试
- GD-001: 高质量样本 (9-10分)
- GD-002: 中等质量 (7-8分)
- GD-003: 低质量边界 (3-4分)
- GD-004: 幻觉注入样本
- GD-005: 法规错误样本

## 9. 部署架构

```
                    ┌─────────────────────────────────────────────────┐
                    │                   Cloud Server                 │
                    │  ┌─────────────────────────────────────────┐  │
                    │  │            Kubernetes Cluster            │  │
                    │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │  │
                    │  │  │ textbook│  │worker   │  │ nginx   │  │  │
                    │  │  │  (API)  │  │(Temporal)│  │(Ingress)│  │  │
                    │  │  └────┬────┘  └────┬────┘  └────┬────┘  │  │
                    │  └───────┼─────────────┼─────────────┼───────┘  │
                    │          │             │             │          │
                    │  ┌───────▼─────────────▼─────────────▼───────┐  │
                    │  │              Service Mesh                  │  │
                    │  │  PostgreSQL │ Redis │ Kafka │ Qdrant    │  │
                    │  └───────────────────────────────────────────┘  │
                    └─────────────────────────────────────────────────┘
```

## 10. 质量标准

- **测试覆盖率**: ≥80%
- **API响应时间**: P95 < 200ms
- **LLM生成延迟**: P95 < 10s
- **系统可用性**: 99.9%
- **安全扫描**: 0 P0/P1漏洞
