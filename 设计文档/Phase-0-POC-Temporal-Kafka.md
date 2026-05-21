# Phase 0: Technical Spike - Temporal + Kafka POC

**版本**: v1.0
**日期**: 2026-05-19
**状态**: 进行中
**预计工期**: 2周
**负责人**: 架构团队

---

## 1. 目标

验证Temporal工作流引擎 + Kafka消息队列在教材编写场景下的技术可行性，构建最小可行实现（MVP）。

### 1.1 验证目标

| 验证项 | 成功标准 | 验证方法 |
|--------|---------|---------|
| **Temporal工作流** | 能够编排"大纲生成→章节写作→审核"的完整流程 | 端到端运行一个完整章节的流程 |
| **状态持久化** | 工作流中断后能正确恢复 | 模拟进程崩溃，检查状态恢复 |
| **Human-in-the-Loop** | 人工审核节点能正确暂停和恢复工作流 | 调用审核API，验证流程暂停 |
| **Kafka消息队列** | 跨章节事件能正确传递 | 发布事件，消费验证 |
| **集成延迟** | 单次API调用延迟 < 500ms | 性能测试 |

### 1.2 不在验证范围内

- 知识图谱存储（Phase 1）
- LLM集成（Phase 1）
- 上下文预算管理器（Phase 1）

---

## 2. 技术架构

### 2.1 组件架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 0 POC 架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Client     │────▶│  FastAPI     │────▶│  Temporal    │   │
│  │   (测试)    │     │  (Python)    │     │  Server      │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│                              │                    │              │
│                              │                    │              │
│                              ▼                    ▼              │
│                      ┌──────────────┐     ┌──────────────┐   │
│                      │   Kafka      │◄───▶│  Workflow    │   │
│                      │  (事件总线)  │     │  Workers     │   │
│                      └──────────────┘     └──────────────┘   │
│                              │                                   │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────┐                         │
│                      │  PostgreSQL  │                         │
│                      │  (状态存储)   │                         │
│                      └──────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 工作流定义

```
工作流名称: TextbookChapterWorkflow

工作流步骤:
1. GenerateOutline (异步)
   └─> 生成章节大纲

2. HumanOutlineReview (HUMAN_TASK)
   └─> 人工审核大纲 (暂停点)

3. WriteChapterContent (异步)
   └─> 根据大纲写章节内容

4. HumanContentReview (HUMAN_TASK)
   └─> 人工审核内容 (暂停点)

5. FinalizeChapter (同步)
   └─> 章节定稿

信号接口:
- SubmitOutlineReview(approved: bool, comments: str)
- SubmitContentReview(approved: bool, comments: str)

查询接口:
- GetWorkflowStatus() -> {state, current_step, chapter_id}
```

### 2.3 Kafka Topic设计

| Topic | 用途 | Key | Value Schema |
|-------|------|-----|--------------|
| `textbook.outline.generated` | 大纲生成完成 | chapter_id | `{chapter_id, outline, generated_at}` |
| `textbook.chapter.written` | 章节写作完成 | chapter_id | `{chapter_id, content, word_count, generated_at}` |
| `textbook.review.submitted` | 审核提交 | workflow_id | `{workflow_id, review_type, result, reviewer_id}` |
| `textbook.chapter.completed` | 章节完成 | chapter_id | `{chapter_id, final_content, completed_at}` |

---

## 3. 实现清单

### 3.1 环境准备

```yaml
# docker-compose.yml (Phase 0 POC专用)

services:
  temporal:
    image: temporalio/auto-setup:1.24.0
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PWD=postgres
      - POSTGRES_SEEDS=postgres
    
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=temporal_poc
  
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
    depends_on:
      - zookeeper
  
  zookeeper:
    image: confluentinc/czookeeper:7.5.0
    ports:
      - "2181:2181"
  
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    ports:
      - "8080:8080"
    depends_on:
      - kafka
```

### 3.2 Temporal工作流代码

```python
# workflows/textbook_chapter.py

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from enum import Enum

class WorkflowState(Enum):
    DRAFT = "draft"
    OUTLINE_REVIEW = "outline_review"
    OUTLINE_APPROVED = "outline_approved"
    OUTLINE_REJECTED = "outline_rejected"
    CONTENT_REVIEW = "content_review"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ChapterContext:
    chapter_id: str
    title: str
    outline: dict | None = None
    content: str | None = None
    state: WorkflowState = WorkflowState.DRAFT
    review_comments: list[str] = None
    
    def __post_init__(self):
        if self.review_comments is None:
            self.review_comments = []

@dataclass
class OutlineReviewSignal:
    approved: bool
    comments: str
    reviewer_id: str

@dataclass
class ContentReviewSignal:
    approved: bool
    comments: str
    reviewer_id: str

@workflow.defn
class TextbookChapterWorkflow:
    """教材章节编写工作流"""
    
    def __init__(self):
        self.ctx: ChapterContext | None = None
        self.outline_review_signal: OutlineReviewSignal | None = None
        self.content_review_signal: ContentReviewSignal | None = None
    
    @workflow.run
    async def run(self, chapter_id: str, title: str) -> dict:
        # 初始化上下文
        self.ctx = ChapterContext(chapter_id=chapter_id, title=title)
        
        try:
            # Step 1: 生成大纲 (异步)
            self.ctx.state = WorkflowState.DRAFT
            self.ctx.outline = await workflow.execute_activity(
                generate_outline,
                self.ctx.title,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # 发布大纲生成完成事件
            await workflow.execute_activity(
                publish_event,
                "textbook.outline.generated",
                self.ctx.chapter_id,
                {"chapter_id": self.ctx.chapter_id, "outline": self.ctx.outline},
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            # Step 2: 等待大纲审核 (HUMAN_TASK)
            self.ctx.state = WorkflowState.OUTLINE_REVIEW
            self.outline_review_signal = await workflow.wait_until_signal(
                OutlineReviewSignal,
                timeout=timedelta(days=7)  # 7天审核期限
            )
            
            if not self.outline_review_signal.approved:
                self.ctx.state = WorkflowState.OUTLINE_REJECTED
                self.ctx.review_comments.append(self.outline_review_signal.comments)
                return {"status": "rejected", "ctx": self.ctx}
            
            self.ctx.state = WorkflowState.OUTLINE_APPROVED
            self.ctx.review_comments.append(self.outline_review_signal.comments)
            
            # Step 3: 写章节内容 (异步)
            self.ctx.content = await workflow.execute_activity(
                write_chapter_content,
                self.ctx.chapter_id,
                self.ctx.outline,
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # 发布章节写作完成事件
            await workflow.execute_activity(
                publish_event,
                "textbook.chapter.written",
                self.ctx.chapter_id,
                {
                    "chapter_id": self.ctx.chapter_id,
                    "content_length": len(self.ctx.content)
                },
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            # Step 4: 等待内容审核 (HUMAN_TASK)
            self.ctx.state = WorkflowState.CONTENT_REVIEW
            self.content_review_signal = await workflow.wait_until_signal(
                ContentReviewSignal,
                timeout=timedelta(days=7)
            )
            
            if not self.content_review_signal.approved:
                self.ctx.state = WorkflowState.OUTLINE_REJECTED
                self.ctx.review_comments.append(self.content_review_signal.comments)
                return {"status": "needs_revision", "ctx": self.ctx}
            
            # Step 5: 定稿
            self.ctx.state = WorkflowState.COMPLETED
            await workflow.execute_activity(
                publish_event,
                "textbook.chapter.completed",
                self.ctx.chapter_id,
                {"chapter_id": self.ctx.chapter_id, "completed": True},
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            return {
                "status": "completed",
                "chapter_id": self.ctx.chapter_id,
                "content": self.ctx.content
            }
            
        except Exception as e:
            self.ctx.state = WorkflowState.FAILED
            raise
```

### 3.3 Activity代码

```python
# activities/chapter_activities.py

from temporalio import activity
from kafka import KafkaProducer
import json
import logging

logger = logging.getLogger(__name__)

kafka_producer = None

def get_kafka_producer():
    global kafka_producer
    if kafka_producer is None:
        kafka_producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return kafka_producer

@activity.defn
async def generate_outline(title: str) -> dict:
    """生成章节大纲"""
    logger.info(f"Generating outline for: {title}")
    
    # POC阶段: 模拟生成
    # 实际实现将在Phase 1集成LLM
    outline = {
        "title": title,
        "sections": [
            {"id": "s1", "title": "概述", "subsections": ["定义", "背景"]},
            {"id": "s2", "title": "核心内容", "subsections": ["理论", "实践"]},
            {"id": "s3", "title": "案例分析", "subsections": ["案例1", "案例2"]},
        ],
        "estimated_words": 5000
    }
    
    return outline

@activity.defn
async def write_chapter_content(chapter_id: str, outline: dict) -> str:
    """写章节内容"""
    logger.info(f"Writing content for chapter: {chapter_id}")
    
    # POC阶段: 模拟生成
    # 实际实现将在Phase 1集成LLM
    content = f"# {outline['title']}\n\n"
    for section in outline['sections']:
        content += f"## {section['title']}\n\n"
        for subsection in section.get('subsections', []):
            content += f"### {subsection}\n\n"
            content += f"这是{subsection}的内容。\n\n"
    
    return content

@activity.defn
async def publish_event(topic: str, key: str, value: dict) -> None:
    """发布事件到Kafka"""
    producer = get_kafka_producer()
    future = producer.send(topic, key=key.encode('utf-8'), value=value)
    await future  # 等待发送完成
    logger.info(f"Published event to {topic}: {key}")
```

### 3.4 FastAPI服务代码

```python
# api/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from temporalio.client import Client
import logging

app = FastAPI(title="Textbook POC API")

# 全局客户端
temporal_client: Client | None = None

class StartWorkflowRequest(BaseModel):
    chapter_id: str
    title: str

class SubmitReviewRequest(BaseModel):
    workflow_id: str
    approved: bool
    comments: str
    reviewer_id: str

@app.on_event("startup")
async def startup():
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")
    logging.info("Connected to Temporal")

@app.post("/workflows/start")
async def start_workflow(req: StartWorkflowRequest):
    """启动章节编写工作流"""
    handle = await temporal_client.start_workflow(
        "TextbookChapterWorkflow",
        req.chapter_id,
        req.title,
        id=f"textbook-chapter-{req.chapter_id}",
        task_queue="textbook-poc"
    )
    
    return {
        "workflow_id": str(handle.id),
        "status": "started"
    }

@app.post("/workflows/{workflow_id}/outline-review")
async def submit_outline_review(workflow_id: str, req: SubmitReviewRequest):
    """提交大纲审核结果"""
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    await handle.signal(
        "SubmitOutlineReview",
        {
            "approved": req.approved,
            "comments": req.comments,
            "reviewer_id": req.reviewer_id
        }
    )
    
    return {"status": "signaled"}

@app.post("/workflows/{workflow_id}/content-review")
async def submit_content_review(workflow_id: str, req: SubmitReviewRequest):
    """提交内容审核结果"""
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    await handle.signal(
        "SubmitContentReview",
        {
            "approved": req.approved,
            "comments": req.comments,
            "reviewer_id": req.reviewer_id
        }
    )
    
    return {"status": "signaled"}

@app.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    handle = temporal_client.get_workflow_handle(workflow_id)
    
    # 获取当前状态
    # POC阶段: 返回简化状态
    return {
        "workflow_id": workflow_id,
        "status": "running",  # 简化
        "can_cancel": True
    }
```

### 3.5 Kafka消费者代码

```python
# consumers/textbook_consumer.py

from kafka import KafkaConsumer
import json
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def consume_events():
    """消费教材编写事件"""
    consumer = KafkaConsumer(
        'textbook.outline.generated',
        'textbook.chapter.written',
        'textbook.chapter.completed',
        bootstrap_servers=['localhost:9092'],
        group_id='textbook-poc-consumer',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'
    )
    
    logger.info("Starting Kafka consumer...")
    
    for message in consumer:
        topic = message.topic
        value = message.value
        
        logger.info(f"Received event: {topic} - {value}")
        
        # 根据topic处理不同事件
        if topic == 'textbook.outline.generated':
            await handle_outline_generated(value)
        elif topic == 'textbook.chapter.written':
            await handle_chapter_written(value)
        elif topic == 'textbook.chapter.completed':
            await handle_chapter_completed(value)

async def handle_outline_generated(event: dict):
    """处理大纲生成完成事件"""
    logger.info(f"Outline generated for chapter: {event['chapter_id']}")

async def handle_chapter_written(event: dict):
    """处理章节写作完成事件"""
    logger.info(f"Chapter written: {event['chapter_id']}, length: {event.get('content_length', 0)}")

async def handle_chapter_completed(event: dict):
    """处理章节完成事件"""
    logger.info(f"Chapter completed: {event['chapter_id']}")

if __name__ == "__main__":
    asyncio.run(consume_events())
```

---

## 4. 测试用例

### 4.1 功能测试

```python
# tests/test_workflow.py

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

@pytest.fixture
async def workflow_env():
    env = await WorkflowEnvironment.start_local()
    yield env
    await env.shutdown()

async def test_generate_outline(workflow_env):
    """测试大纲生成"""
    result = await workflow_env.client.execute_workflow(
        "GenerateOutline",
        "人工智能概述",
        id="test-outline-1"
    )
    
    assert result is not None
    assert "sections" in result
    assert len(result["sections"]) > 0

async def test_workflow_with_human_review(workflow_env):
    """测试带人工审核的工作流"""
    # 启动工作流
    handle = await workflow_env.client.start_workflow(
        "TextbookChapterWorkflow",
        "ch-001",
        "人工智能概述",
        id="test-workflow-1"
    )
    
    # 等待大纲生成完成
    # 注意: 这需要实际运行Temporal
    
    # 提交审核
    # await handle.signal("SubmitOutlineReview", {"approved": True, "comments": "OK", "reviewer_id": "reviewer1"})
    
    pass

async def test_workflow_resume_after_crash():
    """测试工作流在崩溃后恢复"""
    # 1. 启动工作流
    # 2. 中断进程
    # 3. 重启进程
    # 4. 验证状态恢复
    pass
```

### 4.2 集成测试

```python
# tests/test_integration.py

import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_start_workflow():
    """测试启动工作流"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/workflows/start",
            json={"chapter_id": "ch-001", "title": "人工智能概述"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data

async def test_submit_outline_review():
    """测试提交大纲审核"""
    async with httpx.AsyncClient() as client:
        # 先启动工作流
        start_response = await client.post(
            f"{BASE_URL}/workflows/start",
            json={"chapter_id": "ch-002", "title": "机器学习基础"}
        )
        workflow_id = start_response.json()["workflow_id"]
        
        # 提交审核
        review_response = await client.post(
            f"{BASE_URL}/workflows/{workflow_id}/outline-review",
            json={
                "workflow_id": workflow_id,
                "approved": True,
                "comments": "大纲结构合理",
                "reviewer_id": "reviewer-001"
            }
        )
        
        assert review_response.status_code == 200

async def test_kafka_event_consumption():
    """测试Kafka事件消费"""
    # 启动工作流，验证事件发布和消费
    pass
```

---

## 5. 验收标准

### 5.1 完成标准

| 验收项 | 标准 | 验证方法 |
|--------|------|---------|
| **工作流编排** | 能编排"大纲→审核→写作→审核→完成"流程 | 端到端测试 |
| **状态持久化** | 进程重启后工作流状态正确恢复 | 崩溃恢复测试 |
| **Human-in-the-Loop** | 审核节点能暂停和恢复工作流 | API调用测试 |
| **Kafka集成** | 事件正确发布和消费 | 消费者日志验证 |
| **API接口** | 所有接口响应正确 | 集成测试 |
| **文档** | README包含运行说明 | 代码审查 |

### 5.2 性能指标

| 指标 | 目标 | 验收方法 |
|------|------|---------|
| API响应时间 | < 500ms | 性能测试 |
| 工作流启动时间 | < 2s | 计时测试 |
| 事件发布延迟 | < 100ms | 性能测试 |

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Temporal学习曲线陡峭 | 中 | 使用官方示例代码 |
| Kafka配置复杂 | 低 | 使用docker-compose |
| 状态恢复测试困难 | 中 | 设计专用测试用例 |
| Human-in-the-Loop实现复杂 | 中 | 先实现Signal机制 |

---

## 7. 交付物

1. **POC代码仓库**
   - `docker-compose.yml`
   - Temporal工作流代码
   - FastAPI服务代码
   - Kafka消费者代码
   - 测试用例

2. **测试报告**
   - 功能测试结果
   - 集成测试结果
   - 性能测试结果

3. **技术建议**
   - Phase 1技术选型确认
   - 潜在问题及建议

---

## 8. 下一步

Phase 0验证通过后，进入 **Phase 1: 核心架构**（4-6周）：

- P0-01: 不可变日志
- P0-02: Tier1核实
- P0-03: Token稳定化
- P0-05: 上下文预算管理器

---

**文档状态**: 进行中
**下次审查**: POC完成时
**维护责任人**: 架构团队
