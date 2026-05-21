# AI多Agent教材编写系统 - TDD开发计划 v1.0

**版本**: v1.0
**日期**: 2026-05-19
**状态**: 正式版
**基于**: 完整架构设计文档v3.0 + P0漏洞修复方案 + Phase-0-POC + 实施计划v2.0
**总工期**: 16-20周

---

## 文档控制

| 项目 | 内容 |
|------|------|
| 文件路径 | `/Volumes/Coding/工商学院/教材开发系统/设计文档/TDD开发计划v1.0.md` |
| 版本 | v1.0 |
| 状态 | 正式发布 |

### 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-05-19 | 初始版本，基于所有设计文档整合 |

---

## 第一部分：TDD开发方法论

### 1.1 TDD核心原则

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TDD循环 (Red → Green → Refactor)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│    │     RED       │ ──▶ │    GREEN     │ ──▶ │   REFACTOR   │           │
│    │   写失败测试   │     │   写实现代码  │     │   优化代码    │           │
│    └──────────────┘     └──────────────┘     └──────────────┘           │
│          │                     │                     │                     │
│          │                     │                     │                     │
│          └─────────────────────┴─────────────────────┘                   │
│                                循环                                         │
│                                                                              │
│    每次迭代: ~30分钟-2小时                                                  │
│    每次提交: 必须经过RED→GREEN→Refactor完整循环                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 测试覆盖率要求

| 测试类型 | 覆盖率目标 | 说明 |
|---------|-----------|------|
| **单元测试** | ≥85% | 函数/类级别，所有边界条件 |
| **集成测试** | ≥80% | 模块间交互、API接口 |
| **E2E测试** | 关键流程100% | 端到端用户旅程覆盖 |
| **安全测试** | P0漏洞100% | 每个P0漏洞必须有对应安全测试 |
| **混沌测试** | 核心场景覆盖 | 模拟故障场景 |

### 1.3 测试分层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              测试金字塔                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                                    ▲                                        │
│                                   /E\          ← E2E测试 (20%)            │
│                                  /2E \         ← 关键用户旅程               │
│                                 /───────\                                        │
│                                / 集成测试 \     ← 模块间交互 (30%)           │
│                               /────────────\                                   │
│                              /   组件测试   \   ← 单模块内部 (30%)          │
│                             /────────────────\                                │
│                            /     单元测试      \  ← 函数/类级别 (20%)        │
│                           /────────────────────\                              │
│                                                                              │
│    比例: 单元:组件:集成:E2E = 20:30:30:20                                    │
│    优先级: E2E > 集成 > 组件 > 单元                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 第二部分：功能节点分解

### 2.1 节点总览

| 节点ID | 节点名称 | 依赖节点 | 类型 | TDD优先级 |
|--------|---------|---------|------|----------|
| **F01** | 不可变日志系统 | - | 基础设施 | P0 |
| **F02** | 上下文预算管理器 | F01 | 基础设施 | P0 |
| **F03** | Token位置稳定化 | F01 | 基础设施 | P0 |
| **F04** | Temporal工作流引擎 | F01, F02 | 核心 | P0 |
| **F05** | 知识图谱核心 | F03 | 核心 | P0 |
| **F06** | Tier1数值核实引擎 | F01 | 安全 | P0 |
| **F07** | DOI强制解析服务 | F06 | 安全 | P1 |
| **F08** | 法规引用核实系统 | F06 | 安全 | P0 |
| **F09** | 素材安全管理 | F01 | 安全 | P0 |
| **F10** | 概念节点安全 | F05 | 安全 | P0 |
| **F11** | 工作流安全(HUMAN_TASK) | F04 | 安全 | P0 |
| **F12** | 审批结果安全 | F11 | 安全 | P0 |
| **F13** | 全局语义扫描系统 | F05 | 安全 | P0 |
| **F14** | 引用完整性校验 | F07 | 安全 | P0 |
| **F15** | 政治敏感分析 | F13 | 安全 | P0 |
| **F16** | 版本控制与回滚 | F01 | 功能 | P1 |
| **F17** | 跨章引用解析器 | F05 | 功能 | P1 |
| **F18** | 术语表服务 | F05 | 功能 | P1 |
| **F19** | 逻辑链文档服务 | F05, F18 | 功能 | P1 |
| **F20** | LLM-as-Judge评分 | F01 | 质量 | P1 |
| **F21** | 风险分级复核 | F20 | 流程 | P1 |
| **F22** | 素材RAG召回 | F02, F05 | 功能 | P1 |
| **F23** | 内容安全过滤 | - | 安全 | P1 |
| **F24** | 配置中心 | F04 | 工具 | P2 |
| **F25** | 模型路由引擎 | F23 | 功能 | P2 |
| **F26** | 血缘追踪系统 | F06, F16 | 功能 | P2 |
| **F27** | GraphRAG问答 | F22 | 功能 | P3 |
| **F28** | 监控仪表盘 | F01 | 运维 | P2 |
| **F29** | CI/CD质量门禁 | F16 | 运维 | P2 |
| **F30** | Golden Dataset | F20 | 质量 | P2 |

### 2.2 节点依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           节点依赖关系图 (关键路径)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  基础设施层:                                                                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                              │
│  │   F01   │ ──▶ │   F02   │ ──▶ │   F03   │                              │
│  │ 不可变日志 │     │上下文预算│     │Token稳定│                              │
│  └─────────┘     └─────────┘     └─────────┘                              │
│       │               │               │                                     │
│       │               ▼               │                                     │
│       │          ┌─────────┐          │                                     │
│       │          │   F04   │ ◄────────┘                                     │
│       │          │Temporal │                                                    │
│       │          └─────────┘                                                  │
│       │               │                                                       │
│       ▼               ▼                                                       │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                              │
│  │   F06   │ ──▶ │   F08   │     │   F09   │                              │
│  │Tier1核实 │     │法规核实 │     │素材安全 │                              │
│  └─────────┘     └─────────┘     └─────────┘                              │
│       │                                                   │
│       ▼                                                   │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │   F07   │     │   F10   │     │   F11   │     │   F12   │              │
│  │DOI解析  │     │概念安全 │     │工作流安全│     │审批安全 │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                                                                              │
│  核心功能层:                                                                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │   F05   │ ──▶ │   F13   │ ──▶ │   F14   │     │   F15   │              │
│  │ 知识图谱 │     │全局扫描 │     │引用校验 │     │政治分析 │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│       │               │                                                       │
│       ▼               ▼                                                       │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │   F17   │     │   F18   │     │   F19   │     │   F22   │              │
│  │跨章引用 │     │术语表  │     │逻辑链  │     │RAG召回 │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                                                                              │
│  质量保障层:                                                                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │   F20   │ ──▶ │   F21   │     │   F16   │     │   F26   │              │
│  │LLMJudge │     │风险分级 │     │版本控制 │     │血缘追踪 │              │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 第三部分：TDD工作流详细规范

### 3.1 RED阶段规范 (写失败测试)

**目标**: 写出一个会失败的测试，明确要实现的功能

**步骤**:
1. 分析要实现的功能，识别边界条件
2. 写测试用例描述预期行为
3. 运行测试，确认失败
4. 提交失败测试代码

**交付物**:
- 失败测试代码 (必须编译通过)
- 测试说明文档 (中文)
- 预期行为描述

**验收标准**:
- 测试必须可执行 (编译通过)
- 测试必须失败 (因为实现不存在)
- 失败原因必须是 `AssertionError` 或 `NotImplementedError`
- 不能是测试代码本身的错误

### 3.2 GREEN阶段规范 (写实现代码)

**目标**: 写最简单可行的代码让测试通过

**步骤**:
1. 分析失败原因
2. 写最简单的实现让测试通过
3. 运行所有测试，确认通过
4. 提交实现代码

**原则**:
- 不写过渡工程 (YAGNI)
- 不优化代码 (留待Refactor阶段)
- 测试驱动开发，不是测试追赶开发
- 一次只让一个测试变绿

**验收标准**:
- 所有测试必须通过
- 测试覆盖所有功能点
- 实现代码清晰可读

### 3.3 REFACTOR阶段规范 (优化代码)

**目标**: 在保持测试通过的前提下优化代码质量

**步骤**:
1. 识别代码坏味道 (重复、过长、命名不清)
2. 重构代码
3. 运行所有测试，确认通过
4. 检查覆盖率是否达标

**重构清单**:
- [ ] 消除重复代码
- [ ] 提取公共方法
- [ ] 改善变量/函数命名
- [ ] 减少嵌套层级
- [ ] 添加必要注释
- [ ] 优化性能

**验收标准**:
- 所有测试仍然通过
- 代码质量提升
- 覆盖率不下降

---

## 第四部分：节点TDD工作流详情

### F01: 不可变日志系统

#### 4.1.1 节点概述

| 属性 | 内容 |
|------|------|
| **节点ID** | F01 |
| **节点名称** | 不可变日志系统 |
| **功能描述** | 所有LLM调用必须带版本戳，日志不可篡改 |
| **TDD优先级** | P0 |
| **预计TDD周期** | 4轮 RED→GREEN→Refactor |

#### 4.1.2 RED测试用例

```python
# tests/unit/test_immutable_log.py

import pytest
from datetime import datetime
import hashlib

class TestImmutableLog:
    """不可变日志系统 - TDD RED阶段"""

    def test_log_entry_must_have_version_tag(self):
        """F01-T001: 日志条目必须有版本戳"""
        # Given: 创建日志条目
        # When: 记录LLM调用
        # Then: 日志必须包含version_tag
        log_entry = create_log_entry("llm_call", {"prompt": "test"})
        assert log_entry.version_tag is not None
        assert len(log_entry.version_tag) == 64  # SHA-256

    def test_log_entry_must_have_content_hash(self):
        """F01-T002: 日志条目必须有内容哈希"""
        log_entry = create_log_entry("llm_call", {"prompt": "test"})
        assert log_entry.content_hash is not None
        # 内容哈希应基于实际内容计算
        expected_hash = hashlib.sha256(b"test").hexdigest()
        assert log_entry.content_hash == expected_hash

    def test_log_immutability_cannot_be_modified(self):
        """F01-T003: 日志不可修改"""
        log_entry = create_log_entry("llm_call", {"prompt": "test"})
        with pytest.raises(ImmutableLogError):
            log_entry.modify({"prompt": "modified"})

    def test_log_entry_has_timestamp(self):
        """F01-T004: 日志条目必须有不可变时间戳"""
        log_entry = create_log_entry("llm_call", {"prompt": "test"})
        assert log_entry.timestamp is not None
        assert isinstance(log_entry.timestamp, datetime)

    def test_chain_integrity_verification(self):
        """F01-T005: 链完整性验证"""
        # Given: 创建日志链
        entries = [
            create_log_entry("call_1", {"data": "a"}),
            create_log_entry("call_2", {"data": "b"}),
        ]
        # Then: 链完整性可验证
        assert verify_chain_integrity(entries) == True

    def test_detect_tampering_in_history(self):
        """F01-T006: 检测历史篡改"""
        # Given: 篡改历史日志
        entries = [
            create_log_entry("call_1", {"data": "a"}),
            create_log_entry("call_2", {"data": "b"}),
        ]
        entries[0].content_hash = "tampered_hash"
        # Then: 完整性验证应失败
        assert verify_chain_integrity(entries) == False
```

#### 4.1.3 GREEN实现指导

```python
# implementations/immutable_log.py (TDD GREEN阶段实现)

@dataclass
class LogEntry:
    version_tag: str
    content_hash: str
    timestamp: datetime
    operation_type: str
    payload: dict
    previous_hash: str | None

    def __post_init__(self):
        # 不可变性保证
        object.__setattr__(self, '_immutable', True)

    def modify(self, new_payload: dict):
        raise ImmutableLogError("Log entries are immutable")

class ImmutableLog:
    def __init__(self):
        self._entries: list[LogEntry] = []
        self._chain_hash = None

    def append(self, operation_type: str, payload: dict) -> LogEntry:
        content = json.dumps(payload, sort_keys=True).encode()
        content_hash = hashlib.sha256(content).hexdigest()
        version_tag = hashlib.sha256(
            (content_hash + (self._chain_hash or "")).encode()
        ).hexdigest()

        entry = LogEntry(
            version_tag=version_tag,
            content_hash=content_hash,
            timestamp=datetime.utcnow(),
            operation_type=operation_type,
            payload=payload,
            previous_hash=self._chain_hash
        )

        self._entries.append(entry)
        self._chain_hash = version_tag
        return entry

def verify_chain_integrity(entries: list[LogEntry]) -> bool:
    if len(entries) <= 1:
        return True

    for i in range(1, len(entries)):
        if entries[i].previous_hash != entries[i-1].version_tag:
            return False
    return True
```

#### 4.1.4 测试覆盖率目标

| 测试类型 | 覆盖率目标 | 测试用例数 |
|---------|-----------|-----------|
| 单元测试 | 90% | 15+ |
| 集成测试 | 85% | 5+ |
| 安全测试 | 100% | 8+ |

---

### F02: 上下文预算管理器

#### 4.2.1 节点概述

| 属性 | 内容 |
|------|------|
| **节点ID** | F02 |
| **节点名称** | 上下文预算管理器 |
| **功能描述** | 固定核心60K + 弹性素材40K预算控制 |
| **TDD优先级** | P0 |
| **预计TDD周期** | 5轮 RED→GREEN→Refactor |

#### 4.2.2 RED测试用例

```python
# tests/unit/test_context_budget_manager.py

class TestContextBudgetManager:
    """上下文预算管理器 - TDD RED阶段"""

    def test_total_budget_limit_100k_tokens(self):
        """F02-T001: 总预算上限100K Tokens"""
        manager = ContextBudgetManager()
        # 尝试添加超过100K的内容
        result = manager.add_content("chapter_1", {"text": "x" * 100_000})
        assert result.accepted == False
        assert result.rejection_reason == "TOTAL_BUDGET_EXCEEDED"

    def test_l0_core_context_fixed_60k(self):
        """F02-T002: L0核心上下文固定60K"""
        manager = ContextBudgetManager()
        # 核心上下文应该固定
        result = manager.set_core_context({"outline": "x" * 60_000})
        assert result.accepted == True
        assert manager.get_core_context_size() == 60_000

    def test_l0_core_context_cannot_exceed_60k(self):
        """F02-T003: L0核心上下文不能超过60K"""
        manager = ContextBudgetManager()
        result = manager.set_core_context({"outline": "x" * 70_000})
        assert result.accepted == False
        assert "CORE_CONTEXT_EXCEEDED" in result.rejection_reason

    def test_l1_elastic_material_max_40k(self):
        """F02-T004: L1弹性材料上限40K"""
        manager = ContextBudgetManager()
        result = manager.add_material("ch01", {"reference": "x" * 40_000})
        assert result.accepted == True
        assert manager.get_material_size("ch01") == 40_000

    def test_budget_exceeded_triggers_rag_eviction(self):
        """F02-T005: 预算超限时触发RAG淘汰"""
        manager = ContextBudgetManager()
        # 先填满材料
        for i in range(4):
            manager.add_material(f"ch_{i}", {"ref": "x" * 10_000})

        # 添加第5个材料应触发淘汰最远章节
        result = manager.add_material("ch_4", {"ref": "x" * 10_000})
        assert result.evicted_material == "ch_0"

    def test_context_compression_when_near_limit(self):
        """F02-T006: 接近上限时触发压缩"""
        manager = ContextBudgetManager()
        # 设置为95%使用率
        manager.set_usage_ratio(0.95)

        # 再次添加内容应触发压缩
        assert manager.should_compress() == True

    def test_per_chapter_token_counting(self):
        """F02-T007: 按章节Token计数"""
        manager = ContextBudgetManager()
        manager.add_material("ch01", {"text": "x" * 5000})

        counts = manager.get_per_chapter_counts()
        assert counts["ch01"] == 5000
```

#### 4.2.3 GREEN实现指导

```python
# implementations/context_budget_manager.py

class BudgetResult:
    accepted: bool
    rejection_reason: str | None
    evicted_material: str | None

class ContextBudgetManager:
    L0_CORE_BUDGET = 60_000  # 60K tokens
    L1_MATERIAL_BUDGET = 40_000  # 40K tokens
    TOTAL_BUDGET = 100_000  # 100K tokens
    EVICTION_THRESHOLD = 0.80  # 80%时开始淘汰

    def __init__(self):
        self._core_context = ""
        self._materials: dict[str, str] = {}
        self._material_order: list[str] = []

    def add_content(self, chapter_id: str, content: dict) -> BudgetResult:
        total_tokens = self._calculate_total_tokens()
        content_tokens = self._estimate_tokens(content)

        if total_tokens + content_tokens > self.TOTAL_BUDGET:
            return BudgetResult(accepted=False, rejection_reason="TOTAL_BUDGET_EXCEEDED")

        return self._add_material(chapter_id, content)

    def _add_material(self, chapter_id: str, content: dict) -> BudgetResult:
        content_tokens = self._estimate_tokens(content)

        # 检查L1预算
        current_material_tokens = sum(
            self._estimate_tokens(v) for v in self._materials.values()
        )

        if current_material_tokens + content_tokens > self.L1_MATERIAL_BUDGET:
            # 触发淘汰
            evicted = self._evict_oldest_material(content_tokens)
            if not evicted:
                return BudgetResult(accepted=False, rejection_reason="MATERIAL_BUDGET_EXCEEDED")

        self._materials[chapter_id] = content.get("text", "")
        self._material_order.append(chapter_id)
        return BudgetResult(accepted=True)

    def _evict_oldest_material(self, needed_tokens: int) -> str | None:
        while self._material_order:
            oldest = self._material_order.pop(0)
            evicted_tokens = self._estimate_tokens(self._materials.pop(oldest))
            current_total = sum(
                self._estimate_tokens(v) for v in self._materials.values()
            )
            if current_total + needed_tokens <= self.L1_MATERIAL_BUDGET:
                return oldest
        return None
```

---

### F03: Token位置稳定化 (内容寻址)

#### 4.3.1 RED测试用例

```python
# tests/unit/test_content_addressing.py

class TestContentAddressing:
    """内容寻址哈希 - TDD RED阶段"""

    def test_content_hash_is_position_independent(self):
        """F03-T001: 内容哈希与位置无关"""
        hash1 = calculate_content_hash("Hello World", offset=0)
        hash2 = calculate_content_hash("Hello World", offset=100)
        assert hash1 == hash2  # 相同内容应产生相同哈希

    def test_identical_content_produces_same_hash(self):
        """F03-T002: 相同内容产生相同哈希"""
        content1 = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术..."
        content2 = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术..."
        assert calculate_content_hash(content1) == calculate_content_hash(content2)

    def test_different_content_produces_different_hash(self):
        """F03-T003: 不同内容产生不同哈希"""
        hash1 = calculate_content_hash("内容A")
        hash2 = calculate_content_hash("内容B")
        assert hash1 != hash2

    def test_content_address_reference_format(self):
        """F03-T004: 引用格式正确"""
        ref = ContentAddressReference(
            content_hash="abc123",
            offset=0,
            length=500
        )
        assert ref.to_string() == "{hash: abc123, offset: 0, length: 500}"

    def test_auto_deduplication_via_hash(self):
        """F03-T005: 通过哈希自动去重"""
        contents = ["内容A", "内容B", "内容A", "内容C"]
        unique_hashes = deduplicate_by_hash(contents)
        assert len(unique_hashes) == 3

    def test_integrity_verification(self):
        """F03-T006: 完整性验证"""
        content = "原始内容"
        stored_hash = calculate_content_hash(content)

        # 验证完整性
        assert verify_integrity(content, stored_hash) == True

        # 篡改后验证
        tampered = "被篡改的内容"
        assert verify_integrity(tampered, stored_hash) == False
```

---

### F04: Temporal工作流引擎

#### 4.4.1 RED测试用例

```python
# tests/integration/test_temporal_workflow.py

class TestTextbookWorkflow:
    """教材编写工作流 - TDD RED阶段"""

    @pytest.fixture
    async def temporal_client(self):
        """Temporal测试客户端"""
        client = await connect_temporal("localhost:7233")
        yield client
        await client.close()

    async def test_workflow_complete_outline_to_content(self, temporal_client):
        """F04-T001: 完整流程:大纲→审核→写作→审核→完成"""
        # Given: 启动工作流
        handle = await temporal_client.start_workflow(
            "TextbookChapterWorkflow",
            "ch-001",
            "人工智能概述",
            id="test-workflow-001"
        )

        # When: 执行完整流程
        # Then: 工作流应成功完成
        result = await handle.get_result(timeout=timedelta(minutes=30))
        assert result.status == "completed"

    async def test_workflow_pauses_at_human_review(self, temporal_client):
        """F04-T002: 人工审核节点正确暂停"""
        handle = await temporal_client.start_workflow(
            "TextbookChapterWorkflow",
            "ch-002",
            "机器学习基础",
            id="test-workflow-002"
        )

        # Then: 状态应为OUTLINE_REVIEW
        state = await handle.query(GetWorkflowStatus)
        assert state.current_state == "OUTLINE_REVIEW"

    async def test_workflow_resumes_after_approval(self, temporal_client):
        """F04-T003: 审核通过后工作流恢复"""
        handle = await temporal_client.get_workflow_handle("test-workflow-002")

        # When: 提交审核通过
        await handle.signal("SubmitOutlineReview", {
            "approved": True,
            "comments": "大纲合理",
            "reviewer_id": "reviewer-001"
        })

        # Then: 工作流应继续执行到下一状态
        state = await handle.query(GetWorkflowStatus)
        assert state.current_state in ["DRAFT", "CONTENT_REVIEW"]

    async def test_workflow_handles_rejection(self, temporal_client):
        """F04-T004: 审核拒绝正确处理"""
        handle = await temporal_client.start_workflow(
            "TextbookChapterWorkflow",
            "ch-003",
            "测试章节",
            id="test-workflow-003"
        )

        # When: 提交审核拒绝
        await handle.signal("SubmitOutlineReview", {
            "approved": False,
            "comments": "需要修改大纲结构",
            "reviewer_id": "reviewer-001"
        })

        # Then: 工作流应标记为rejected
        result = await handle.get_result()
        assert result.status == "rejected"

    async def test_workflow_state_persistence_after_crash(self, temporal_client):
        """F04-T005: 崩溃后状态持久化恢复"""
        # Given: 启动并中断工作流
        handle = await temporal_client.start_workflow(
            "TextbookChapterWorkflow",
            "ch-004",
            "测试",
            id="test-workflow-004"
        )

        # Simulate: 进程崩溃
        await simulate_process_crash()

        # When: 重启后获取状态
        recovered_handle = temporal_client.get_workflow_handle("test-workflow-004")
        state = await recovered_handle.query(GetWorkflowStatus)

        # Then: 状态应正确恢复
        assert state is not None
        assert state.current_state != "UNKNOWN"

    async def test_workflow_timeout_handling(self, temporal_client):
        """F04-T006: 超时正确处理"""
        handle = await temporal_client.start_workflow(
            "TextbookChapterWorkflow",
            "ch-005",
            "超时测试",
            id="test-workflow-timeout"
        )

        # Wait for timeout
        with pytest.raises(WorkflowTimeoutError):
            await handle.get_result(timeout=timedelta(seconds=1))
```

---

### F05: 知识图谱核心

#### 4.5.1 RED测试用例

```python
# tests/unit/test_knowledge_graph.py

class TestKnowledgeGraph:
    """知识图谱核心 - TDD RED阶段"""

    def test_create_chapter_node(self):
        """F05-T001: 创建章节点"""
        kg = KnowledgeGraph()
        node = kg.create_chapter(
            chapter_id="ch-001",
            title="人工智能概述",
            order=1
        )
        assert node.type == "Chapter"
        assert node.title == "人工智能概述"

    def test_create_section_node(self):
        """F05-T002: 创建节节点"""
        kg = KnowledgeGraph()
        section = kg.create_section(
            section_id="sec-001",
            title="人工智能的定义",
            parent_chapter_id="ch-001"
        )
        assert section.type == "Section"
        assert section.parent_chapter_id == "ch-001"

    def test_create_concept_node(self):
        """F05-T003: 创建概念节点"""
        kg = KnowledgeGraph()
        concept = kg.create_concept(
            concept_id="c-001",
            name="人工智能",
            definition="研究、开发用于模拟、延伸和扩展人的智能...",
            domain="计算机科学"
        )
        assert concept.type == "Concept"
        assert concept.definition_hash is not None

    def test_fOLLOWS_edge_creation(self):
        """F05-T004: 创建FOLLOWS边"""
        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_chapter("ch-002", "第二章", 2)

        edge = kg.add_edge("ch-001", "ch-002", "FOLLOWS")
        assert edge.edge_type == "FOLLOWS"
        assert edge.source == "ch-001"
        assert edge.target == "ch-002"

    def test_references_edge_with_context(self):
        """F05-T005: 带上下文的REFERENCES边"""
        kg = KnowledgeGraph()
        kg.create_section("sec-001", "定义", "ch-001")
        kg.create_section("sec-002", "应用", "ch-001")

        edge = kg.add_edge(
            "sec-001", "sec-002",
            "REFERENCES",
            reference_context="用于说明定义的应用场景"
        )
        assert edge.reference_context is not None

    def test_query_chapter_context(self):
        """F05-T006: 查询章节上下文"""
        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "AI概述", 1)
        kg.create_section("sec-001", "定义", "ch-001")

        context = kg.get_chapter_context("ch-001")
        assert "ch-001" in context
        assert "sec-001" in context["sections"]

    def test_find_similar_concepts(self):
        """F05-T007: 查找相似概念"""
        kg = KnowledgeGraph()
        kg.create_concept("c-001", "人工智能", "研究、开发用于模拟...", "CS")
        kg.create_concept("c-002", "机器学习", "研究、使用数据提升性能的算法...", "CS")

        similar = kg.find_similar_concepts("c-001", threshold=0.5)
        assert len(similar) >= 1
```

---

### F06: Tier1数值核实引擎

#### 4.6.1 RED测试用例

```python
# tests/unit/test_tier1_verification.py

class TestTier1Verification:
    """Tier1数值核实引擎 - TDD RED阶段"""

    async def test_verify_national_statistics_gdp(self):
        """F06-T001: 核实国家统计局GDP数据"""
        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="gdp",
            value=12900000000000,  # 12.9万亿
            year=2023,
            region="中国"
        )

        assert result.is_verified == True
        assert result.discrepancy < 0.05  # 偏差<5%

    async def test_detect_fabricated_number(self):
        """F06-T002: 检测捏造数值"""
        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="gdp",
            value=99999999999999,  # 明显异常
            year=2023
        )

        assert result.is_verified == False
        assert "ANOMALY_DETECTED" in result.reason

    async def test_value_range_validation(self):
        """F06-T003: 数值范围验证"""
        verifier = Tier1Verifier()

        result = await verifier.verify(
            data_type="population",
            value=-1000,  # 不可能为负
            year=2023
        )

        assert result.is_verified == False
        assert "INVALID_RANGE" in result.reason

    async def test_lineage_tracking(self):
        """F06-T004: 传播链追踪"""
        tracker = DataLineageTracker()

        tracker.register_raw_data("gdp-2023", 12900000000000, "国家统计局")
        tracker.register_derived_data(
            "per-capita",
            formula="gdp-2023 / population-2023",
            input_data_ids=["gdp-2023"]
        )

        lineage = tracker.get_propagation_chain("per-capita")
        assert len(lineage) == 2
        assert lineage[0].is_raw == True

    async def test_propagation_depth_limit(self):
        """F06-T005: 传播深度限制"""
        tracker = DataLineageTracker()

        # 注册多层派生
        tracker.register_raw_data("data-0", 1000, "source")
        for i in range(5):
            tracker.register_derived_data(
                f"data-{i+1}",
                formula=f"data-{i} * 0.5",
                input_data_ids=[f"data-{i}"]
            )

        # 深度超过3应被阻断
        result = tracker.register_derived_data(
            "data-6",
            formula="data-5 * 0.5",
            input_data_ids=["data-5"]
        )

        assert result.rejected == True
        assert "DEPTH_EXCEEDED" in result.reason
```

---

### F07: DOI强制解析服务

#### 4.7.1 RED测试用例

```python
# tests/unit/test_doi_verification.py

class TestDOIVerification:
    """DOI强制解析服务 - TDD RED阶段"""

    async def test_verify_valid_doi(self):
        """F07-T001: 验证有效DOI"""
        verifier = DOIVerifier()

        result = await verifier.verify("10.1234/example.123")
        assert result.exists == True
        assert result.metadata is not None

    async def test_reject_doi_without_prefix(self):
        """F07-T002: 拒绝无前缀DOI"""
        verifier = DOIVerifier()

        result = await verifier.verify("invalid-doi")
        assert result.exists == False
        assert "INVALID_FORMAT" in result.reason

    async def test_detect_nonexistent_doi(self):
        """F07-T003: 检测不存在的DOI"""
        verifier = DOIVerifier()

        result = await verifier.verify("10.9999/nonexistent")
        assert result.exists == False

    async def test_citation_must_include_fact_hash(self):
        """F07-T004: 引用必须包含fact_hash"""
        verifier = DOIVerifier()

        citation = Citation(
            doi="10.1234/example",
            fact_hash=None  # 缺少fact_hash
        )

        with pytest.raises(CitationValidationError):
            verifier.validate_citation_format(citation)

    async def test_verify_citation_content_matches(self):
        """F07-T005: 验证引用内容与注册表一致"""
        registry = FactRegistry()
        verifier = DOIVerifier()

        # 注册事实
        content = "人工智能是研究、开发用于模拟、延伸和扩展人的智能..."
        fact_hash = registry.register_fact(content, ["10.1234/example"])

        # 验证引用
        result = await verifier.verify_citation_content(
            doi="10.1234/example",
            fact_hash=fact_hash,
            cited_content=content
        )

        assert result.is_valid == True

    async def test_circular_reference_detection(self):
        """F07-T006: 循环引用检测"""
        registry = FactRegistry()
        verifier = DOIVerifier()

        # A引用B，B引用A
        hash_a = registry.register_fact("事实A", ["doi-B"])
        hash_b = registry.register_fact("事实B", ["doi-A"])

        citations = [
            Citation(doi="doi-A", fact_hash=hash_a),
            Citation(doi="doi-B", fact_hash=hash_b),
        ]

        has_cycle = verifier.detect_circular_reference(citations)
        assert has_cycle == True
```

---

### F08: 法规引用核实系统

#### 4.8.1 RED测试用例

```python
# tests/unit/test_regulation_verification.py

class TestRegulationVerification:
    """法规引用核实系统 - TDD RED阶段"""

    async def test_verify_law_exists_in_whitelist(self):
        """F08-T001: 验证白名单法规存在"""
        verifier = RegulationVerifier()

        result = await verifier.verify(
            law_name="人工智能法",
            article_num=28
        )

        assert result.law_exists == True
        assert result.article_exists == True

    async def test_reject_law_not_in_whitelist(self):
        """F08-T002: 拒绝非白名单法规"""
        verifier = RegulationVerifier()

        result = await verifier.verify(
            law_name="完全不存在的法",
            article_num=1
        )

        assert result.is_valid == False
        assert "WHITELIST_VIOLATION" in result.reason

    async def test_verify_article_number_in_valid_range(self):
        """F08-T003: 验证条款号在有效范围内"""
        verifier = RegulationVerifier()

        # 人工智能法共72条
        result = await verifier.verify(
            law_name="人工智能法",
            article_num=100  # 超出范围
        )

        assert result.is_valid == False
        assert "ARTICLE_OUT_OF_RANGE" in result.reason

    async def test_three_tier_verification_workflow(self):
        """F08-T004: 三级核实流程"""
        verifier = RegulationVerifier()

        result = await verifier.verify(
            law_name="人工智能法",
            article_num=28,
            cited_content="人工智能企业应当对算法进行备案..."
        )

        assert result.tier1_passed == True  # 法规存在
        assert result.tier2_passed == True  # 条款存在
        assert result.tier3_score > 0.8     # 内容相关性

    async def test_block_vague_reference(self):
        """F08-T005: 阻断模糊引用"""
        verifier = RegulationVerifier()

        result = await verifier.verify_citation(
            citation="根据相关规定",
            context="一般性描述"
        )

        assert result.is_valid == False
        assert "VAGUE_REFERENCE" in result.reason

    async def test_content_relevance_threshold(self):
        """F08-T006: 内容相关性阈值"""
        verifier = RegulationVerifier()

        result = await verifier.verify_content_relevance(
            law_name="人工智能法",
            article_num=28,
            cited_content="完全不相关的内容..." * 100
        )

        assert result.score < 0.5
        assert result.is_valid == False
```

---

### F09: 素材安全管理

#### 4.9.1 RED测试用例

```python
# tests/unit/test_material_security.py

class TestMaterialSecurity:
    """素材安全管理 - TDD RED阶段"""

    async def test_material_must_have_source(self):
        """F09-T001: 素材必须有来源"""
        manager = MaterialSecurityManager()

        material = Material(
            content="测试内容",
            source=None  # 缺少来源
        )

        with pytest.raises(MaterialValidationError):
            await manager.register_material(material)

    async def test_trust_score_calculation(self):
        """F09-T002: 可信度评分计算"""
        manager = MaterialSecurityManager()

        material = Material(
            content="权威机构发布的内容",
            source=SourceInfo(
                name="国家统计局",
                trust_level="WHITELIST"
            )
        )

        score = manager.calculate_trust_score(material)
        assert score >= 0.9

    async def test_low_trust_material_blocked(self):
        """F09-T003: 低可信度素材被阻断"""
        manager = MaterialSecurityManager()

        material = Material(
            content="未核实的内容",
            source=SourceInfo(
                name="未知来源",
                trust_level="UNKNOWN"
            )
        )

        result = await manager.register_material(material)
        assert result.status == "REJECTED"
        assert result.trust_score < 0.7

    async def test_whitelisted_source_auto_approved(self):
        """F09-T004: 白名单来源自动批准"""
        manager = MaterialSecurityManager()

        material = Material(
            content="官方政策内容",
            source=SourceInfo(
                name="教育部",
                trust_level="WHITELIST"
            )
        )

        result = await manager.register_material(material)
        assert result.status == "APPROVED"

    async def test_security_scan_detects_sensitive_content(self):
        """F09-T005: 安全扫描检测敏感内容"""
        manager = MaterialSecurityManager()

        result = await manager.security_scan(
            "包含敏感词的内容"
        )

        assert result.sensitive_word_count > 0
        assert result.scan_status in ["WARNING", "BLOCKED"]

    async def test_retrieval_weight_degradation(self):
        """F09-T006: 检索权重降权"""
        manager = MaterialSecurityManager()

        # 非白名单素材应降权
        weight = manager.get_retrieval_weight("material-001")
        assert weight < 1.0

        # 白名单素材应满权重
        weight_whitelist = manager.get_retrieval_weight("material-whitelisted")
        assert weight_whitelist == 1.0
```

---

### F10: 概念节点安全

#### 4.10.1 RED测试用例

```python
# tests/unit/test_concept_security.py

class TestConceptNodeSecurity:
    """概念节点安全 - TDD RED阶段"""

    def test_concept_node_requires_source_chunk(self):
        """F10-T001: 概念节点必须有来源chunk"""
        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(ConceptValidationError):
            kg_security.create_concept_node(
                definition="人工智能是...",
                source_chunk_id=None,  # 缺少来源
                model_id="approved-model"
            )

    def test_concept_node_requires_approved_model(self):
        """F10-T002: 概念节点必须使用白名单模型"""
        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(SecurityException):
            kg_security.create_concept_node(
                definition="人工智能是...",
                source_chunk_id="chunk-001",
                model_id="unapproved-model"
            )

    def test_integrity_verification_via_hash(self):
        """F10-T003: 通过哈希验证完整性"""
        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(
            definition="人工智能是...",
            source_chunk_id="chunk-001",
            model_id="claude-3-5-sonnet"
        )

        result = kg_security.verify_integrity(node)
        assert result.is_integral == True

    def test_tampering_detection(self):
        """F10-T004: 篡改检测"""
        kg_security = KnowledgeGraphSecurity()

        node = kg_security.create_concept_node(...)

        # 篡改定义
        node.definition = "被篡改的定义"

        result = kg_security.verify_integrity(node)
        assert result.tampering_detected == True

    def test_confidence_based_review_decision(self):
        """F10-T005: 基于置信度的审核决策"""
        kg_security = KnowledgeGraphSecurity()

        # 高置信度(>0.95)应自动批准
        high_confidence_node = ConceptNode(
            concept_id="c-001",
            definition="清晰定义",
            confidence=0.98,
            source_chunk_id="chunk-001"
        )
        assert high_confidence_node.should_auto_approve == True

        # 中等置信度(0.8-0.95)需要人工
        medium_confidence_node = ConceptNode(
            concept_id="c-002",
            definition="较清晰定义",
            confidence=0.85,
            source_chunk_id="chunk-002"
        )
        assert medium_confidence_node.requires_manual_review == True

    def test_review_signature_required(self):
        """F10-T006: 审核需要签名"""
        kg_security = KnowledgeGraphSecurity()

        with pytest.raises(SecurityException):
            kg_security.verify_and_approve(
                concept_id="c-001",
                reviewer_id=None  # 缺少审核人
            )
```

---

### F11: 工作流安全(HUMAN_TASK)

#### 4.11.1 RED测试用例

```python
# tests/unit/test_workflow_security.py

class TestWorkflowSecurity:
    """工作流安全 - TDD RED阶段"""

    def test_direct_signal_blocked(self):
        """F11-T001: 直接Signal被阻断"""
        security = WorkflowSecurityManager()

        with pytest.raises(SecurityException):
            security.receive_signal(
                signal_type="SubmitOutlineReview",
                direct_call=True  # 直接调用
            )

    def test_callback_must_have_signature(self):
        """F11-T002: 回调必须有签名"""
        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            signature=None  # 缺少签名
        )

        with pytest.raises(SecurityException):
            security.verify_callback(callback)

    def test_callback_signature_verification(self):
        """F11-T003: 回调签名验证"""
        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature="valid_signature",
            timestamp=datetime.utcnow()
        )

        result = security.verify_callback(callback)
        assert result.is_valid == True

    def test_content_hash_must_match(self):
        """F11-T004: 内容哈希必须匹配"""
        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="wrong_hash",
            signature="valid_signature",
            timestamp=datetime.utcnow()
        )

        result = security.verify_callback(callback)
        assert result.is_valid == False
        assert "HASH_MISMATCH" in result.reason

    def test_timestamp_must_be_recent(self):
        """F11-T005: 时间戳必须是最近的"""
        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            signature="valid_signature",
            timestamp=datetime.utcnow() - timedelta(minutes=10)  # 10分钟前
        )

        result = security.verify_callback(callback)
        assert result.is_valid == False
        assert "TIMESTAMP_TOO_OLD" in result.reason

    def test_workflow_id_must_exist(self):
        """F11-T006: workflow_id必须存在"""
        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="nonexistent-wf",
            task_id="task-001",
            content_hash="abc123",
            signature="valid_signature",
            timestamp=datetime.utcnow()
        )

        result = security.verify_callback(callback)
        assert result.is_valid == False
        assert "WORKFLOW_NOT_FOUND" in result.reason
```

---

### F12: 审批结果安全

#### 4.12.1 RED测试用例

```python
# tests/unit/test_approval_security.py

class TestApprovalSecurity:
    """审批结果安全 - TDD RED阶段"""

    def test_approval_record_must_be_signed(self):
        """F12-T001: 审批记录必须有签名"""
        manager = ApprovalSecurityManager()

        with pytest.raises(SecurityException):
            manager.submit_approval(
                content_id="content-001",
                content_hash="abc123",
                reviewer_id="reviewer-001",
                result="APPROVED",
                signature=None
            )

    def test_hsm_signature_required(self):
        """F12-T002: 必须使用HSM签名"""
        manager = ApprovalSecurityManager()

        # 模拟非HSM签名应被拒绝
        record = ApprovalRecord(
            record_id="rec-001",
            signature="software_signature",  # 软件签名
            signature_source="SOFTWARE"  # 非HSM
        )

        with pytest.raises(SecurityException):
            manager.verify_record(record)

    def test_content_hash_verification_on_read(self):
        """F12-T003: 读取时验证内容哈希"""
        manager = ApprovalSecurityManager()

        record = manager.submit_approval(
            content_id="content-001",
            content_hash="correct_hash",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Approved"
        )

        # 篡改内容后验证应失败
        record.content_hash = "tampered_hash"
        result = manager.verify_approval(record)

        assert result.is_valid == False
        assert "CONTENT_HASH_MISMATCH" in result.reason

    def test_multi_approval_for_high_risk(self):
        """F12-T004: 高风险需要多重审批"""
        manager = ApprovalSecurityManager()

        approvals = [
            Approval(reviewer_id="r1", result="APPROVED"),
            Approval(reviewer_id="r2", result="APPROVED"),
        ]

        result = manager.verify_multi_approval(
            content_id="high-risk-content",
            approvals=approvals,
            min_required=2
        )

        assert result.is_valid == True

    def test_replay_detection(self):
        """F12-T005: 重放检测"""
        manager = ApprovalSecurityManager()

        # 同一record被使用两次
        record1 = manager.submit_approval(
            content_id="content-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED"
        )

        # 重放应被检测
        result = manager.verify_approval(record1)
        assert result.is_valid == True  # 第一次有效

        # 第二次应检测到重放
        result2 = manager.verify_approval(record1)
        assert result2.is_valid == False
        assert "REPLAY_DETECTED" in result2.reason
```

---

### F13: 全局语义扫描系统

#### 4.13.1 RED测试用例

```python
# tests/unit/test_global_semantic_scanner.py

class TestGlobalSemanticScanner:
    """全局语义扫描系统 - TDD RED阶段"""

    async def test_single_chapter_sensitive_detection(self):
        """F13-T001: 单章节敏感词检测"""
        scanner = GlobalSemanticScanner()

        result = await scanner.scan_chapter(
            chapter_id="ch-001",
            content="包含敏感词的段落"
        )

        assert result.sensitive_word_count > 0
        assert result.risk_level in ["MEDIUM", "HIGH", "CRITICAL"]

    async def test_cross_chapter_topic_tracking(self):
        """F13-T002: 跨章节话题追踪"""
        scanner = GlobalSemanticScanner()

        # 台湾话题分散在多章
        await scanner.add_chapter_topic("ch-02", "台湾", "人口最多岛屿")
        await scanner.add_chapter_topic("ch-06", "台湾", "独特文化")
        await scanner.add_chapter_topic("ch-18", "台湾", "经济发展")

        # 检测到分散的敏感话题
        tracking_result = scanner.detect_distributed_sensitive_topic("台湾")
        assert tracking_result.is_detected == True
        assert tracking_result.distribution_score > 0.7

    async def test_combination_sensitivity_analysis(self):
        """F13-T003: 组合敏感分析"""
        scanner = GlobalSemanticScanner()

        # 多个看似无害但组合后敏感的片段
        fragments = [
            {"topic": "台湾", "text": "人口最多岛屿", "chapter": "ch-02"},
            {"topic": "独立", "text": "建立自己的政府", "chapter": "ch-10"},
        ]

        result = await scanner.analyze_combination_risk(fragments)
        assert result.risk_combinations > 0

    async def test_global_scan_catches_fragmented_content(self):
        """F13-T004: 全局扫描捕获分片内容"""
        scanner = GlobalSemanticScanner()

        # 敏感内容被分散到多章
        chapters = [
            {"id": "ch-01", "content": "第一章介绍..."},
            {"id": "ch-02", "content": "包含部分敏感描述A..."},
            {"id": "ch-03", "content": "更多敏感内容B..."},
            {"id": "ch-04", "content": "最后敏感内容C完成..."},
        ]

        result = await scanner.perform_global_scan(chapters)
        assert result.has_combined_risk == True
        assert len(result.risk_chapters) > 1

    async def test_semantic_similarity_across_chapters(self):
        """F13-T005: 跨章节语义相似度"""
        scanner = GlobalSemanticScanner()

        similarity = await scanner.calculate_cross_chapter_similarity(
            chapter_1_text="人工智能是研究、开发用于模拟...",
            chapter_2_text="机器学习是人工智能的子领域..."
        )

        assert similarity > 0.3
```

---

## 第五部分：TDD开发时间线 (16-20周)

### 5.1 整体时间线

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TDD开发时间线 (16-20周)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 0: 技术验证 (2周)                                                     │
│  ┌────────────────────────────────────────────┐                            │
│  │ F04-TDD: Temporal工作流引擎TDD                                     │    │
│  │   - Week1: RED+GREEN (工作流基础)                                 │    │
│  │   - Week2: REFACTOR + 集成测试                                    │    │
│  └────────────────────────────────────────────┘                            │
│                              │                                                │
│                              ▼                                                │
│  Phase 1: 核心架构 (4周)                                                     │
│  ┌────────────────────────────────────────────┐                            │
│  │ F01-TDD: 不可变日志系统 (Week1-2)                                  │    │
│  │ F06-TDD: Tier1核实引擎 (Week2-3)                                  │    │
│  │ F03-TDD: Token位置稳定化 (Week2-3)                                │    │
│  │ F02-TDD: 上下文预算管理器 (Week3-4)                               │    │
│  │ F05-TDD: 知识图谱核心 (Week3-4)                                   │    │
│  └────────────────────────────────────────────┘                            │
│                              │                                                │
│                              ▼                                                │
│  Phase 2a: 功能完善 (3周)                                                    │
│  ┌────────────────────────────────────────────┐                            │
│  │ F08-TDD: 法规引用核实 (Week5-6)                                    │    │
│  │ F07-TDD: DOI强制解析 (Week5-6)                                    │    │
│  │ F09-TDD: 素材安全管理 (Week5-6)                                   │    │
│  │ F10-TDD: 概念节点安全 (Week6-7)                                   │    │
│  │ F16-TDD: 版本控制与回滚 (Week7)                                   │    │
│  └────────────────────────────────────────────┘                            │
│                              │                                                │
│                              ▼                                                │
│  Phase 2b: 安全加固 (2周)                                                     │
│  ┌────────────────────────────────────────────┐                            │
│  │ F11-TDD: 工作流安全 (Week8-9)                                      │    │
│  │ F12-TDD: 审批结果安全 (Week8-9)                                   │    │
│  │ F14-TDD: 引用完整性校验 (Week9)                                   │    │
│  │ F15-TDD: 政治敏感分析 (Week9)                                     │    │
│  └────────────────────────────────────────────┘                            │
│                              │                                                │
│                              ▼                                                │
│  Phase 3a: 质量保障 (2周)                                                    │
│  ┌────────────────────────────────────────────┐                            │
│  │ F20-TDD: LLM-as-Judge评分 (Week10-11)                             │    │
│  │ F21-TDD: 风险分级复核 (Week10-11)                                  │    │
│  │ F18-TDD: 术语表服务 (Week11)                                      │    │
│  │ F17-TDD: 跨章引用解析 (Week11)                                    │    │
│  └────────────────────────────────────────────┘                            │
│                              │                                                │
│                              ▼                                                │
│  Phase 3b: 集成优化 (2周)                                                    │
│  ┌────────────────────────────────────────────┐                            │
│  │ F22-TDD: 素材RAG召回 (Week12-13)                                   │    │
│  │ F19-TDD: 逻辑链文档 (Week12-13)                                   │    │
│  │ F26-TDD: 血缘追踪 (Week13)                                        │    │
│  │ F13-TDD: 全局语义扫描 (Week13-14)                                 │    │
│  └────────────────────────────────────────────┘                            │
│                              │                                                │
│                              ▼                                                │
│  Phase 4: 工具与运维 (2周)                                                     │
│  ┌────────────────────────────────────────────┐                            │
│  │ F24-TDD: 配置中心 (Week14-15)                                      │    │
│  │ F28-TDD: 监控仪表盘 (Week15)                                      │    │
│  │ F30-TDD: Golden Dataset (Week15-16)                              │    │
│  │ F29-TDD: CI/CD质量门禁 (Week16)                                   │    │
│  │ F25-TDD: 模型路由引擎 (Week16)                                    │    │
│  └────────────────────────────────────────────┘                            │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════  │
│  总计: 16周 (可弹性扩展至20周)                                               │
│  关键路径: F01→F06→F08→F11→F12→F13                                          │
│  可并行路径: F02,F03,F09,F10可在F01后并行                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 关键路径 (Critical Path)

```
关键路径节点序列:
F01 → F06 → F08 → F11 → F12 → F13

每周任务分解:

Week 1:  F01 RED+GREEN (不可变日志)
Week 2:  F01 REFACTOR + F06 RED
Week 3:  F06 GREEN+REFACTOR + F08 RED
Week 4:  F08 GREEN+REFACTOR + F11 RED
Week 5:  F11 GREEN+REFACTOR + F12 RED
Week 6:  F12 GREEN+REFACTOR + F13 RED
Week 7:  F13 GREEN+REFACTOR

关键路径工期: 7周 (不可压缩)
```

### 5.3 可并行工作

```yaml
并行工作流组:
  
组A (Phase 1 Week1-2 可并行):
  - F01: 不可变日志
  - F02: 上下文预算管理器  
  - F03: Token位置稳定化
  - P0-04: Temporal Technical Spike

组B (Phase 1 Week3-4 可并行):
  - F05: 知识图谱核心
  - F06: Tier1核实引擎 (依赖F01)
  - F09: 素材安全管理 (依赖F01)
  - F10: 概念节点安全 (依赖F05)

组C (Phase 2b-3a 可并行):
  - F07: DOI强制解析 (依赖F06)
  - F11: 工作流安全 (依赖F04)
  - F14: 引用完整性校验 (依赖F07)
  - F20: LLM-as-Judge评分 (依赖F01)
```

---

## 第六部分：Agent分配建议

### 6.1 Agent能力矩阵

| Agent | 专长 | 适合节点 |
|------|------|---------|
| **架构师Agent** | 系统设计、决策、审查 | F01,F04,F05,F11,F12 |
| **后端Agent** | Python/FastAPI、数据库、API | F02,F03,F16,F17,F18,F19,F22,F24 |
| **安全Agent** | 渗透测试、漏洞修复、安全架构 | F06,F07,F08,F09,F10,F13,F14,F15 |
| **AI工程师Agent** | LLM集成、Prompt工程、评分系统 | F06,F20,F21,F25,F27 |
| **测试Agent** | 测试框架、覆盖率、自动化 | F28,F29,F30 |
| **DevOps Agent** | CI/CD、监控、部署 | F28,F29 |

### 6.2 团队配置建议 (5人峰值)

```
Phase 1 (Week3-4 峰值):

┌─────────────────────────────────────────────────────────┐
│  角色          │ 人数 │ 负责节点                         │
├─────────────────────────────────────────────────────────┤
│  架构师        │  1  │ F01,F04,F05,F11,F12设计审查      │
│  后端工程师    │  2  │ F02,F03,F16,F17,F18,F22          │
│  安全工程师    │  1  │ F06,F07,F08,F09,F10,F13,F14,F15  │
│  AI工程师      │  1  │ F06,F20,F21,F25,F27              │
│  测试工程师    │  1  │ F28,F29,F30,Golden Dataset       │
└─────────────────────────────────────────────────────────┘
```

### 6.3 TDD Pair模式建议

```yaml
Pair模式:

Pair 1 (基础设施):
  - Agent: 架构师 + 后端工程师
  - 节点: F01, F02, F03, F04
  - 理由: 这些节点是其他所有节点的基础

Pair 2 (知识与安全):
  - Agent: 安全工程师 + AI工程师
  - 节点: F06, F07, F08, F09, F10
  - 理由: 安全节点需要AI检测能力

Pair 3 (功能实现):
  - Agent: 后端工程师 + AI工程师
  - 节点: F16, F17, F18, F19, F20, F21, F22
  - 理由: 功能节点需要业务逻辑和AI能力

Pair 4 (工具与质量):
  - Agent: 测试工程师 + DevOps
  - 节点: F24, F28, F29, F30
  - 理由: 工具和质量节点需要测试和自动化能力
```

---

## 第七部分：质量门禁与验收标准

### 7.1 质量门禁清单

| 门禁项 | 标准 | 验证方法 | 阻断级别 |
|--------|------|---------|----------|
| **单元测试覆盖率** | ≥85% | `pytest --cov` | P0阻断 |
| **集成测试覆盖率** | ≥80% | `pytest --cov tests/integration` | P0阻断 |
| **安全测试覆盖率** | P0漏洞100% | 安全测试套件 | P0阻断 |
| **编译通过** | 100% | CI构建 | P0阻断 |
| **类型检查** | 0错误 | `mypy` | P1阻断 |
| **代码风格** | 0警告 | `ruff check` | P2阻断 |
| **文档完整性** | 100% API文档 | `Sphinx` | P2阻断 |

### 7.2 节点验收标准

#### F01: 不可变日志系统

```yaml
验收标准:
  - [ ] 每次LLM调用必须带版本戳
  - [ ] 日志条目不可修改
  - [ ] 链完整性可验证
  - [ ] 可检测历史篡改
  - [ ] 单元测试覆盖率 ≥90%
  - [ ] 集成测试覆盖率 ≥85%
  - [ ] 安全测试用例 ≥8个

TDD循环数: 4轮
预计人天: 5人天
```

#### F04: Temporal工作流引擎

```yaml
验收标准:
  - [ ] 完整章节流程可执行
  - [ ] Human-in-the-Loop节点可暂停
  - [ ] 工作流崩溃后可恢复
  - [ ] 状态持久化正确
  - [ ] E2E测试100%关键路径
  - [ ] 集成测试覆盖率 ≥85%

TDD循环数: 6轮
预计人天: 8人天
```

#### F06: Tier1数值核实引擎

```yaml
验收标准:
  - [ ] 外部API核实调用成功
  - [ ] 数值异常检测率 ≥95%
  - [ ] 传播链追踪完整
  - [ ] 深度超限阻断
  - [ ] 单元测试覆盖率 ≥90%
  - [ ] 安全测试P0漏洞100%覆盖

TDD循环数: 5轮
预计人天: 6人天
```

### 7.3 里程碑验收

| 里程碑 | 目标周 | 验收节点 | 验收标准 |
|--------|--------|---------|---------|
| **M0** | Week 2 | F04 | Temporal PoC可运行 |
| **M1** | Week 6 | F01,F02,F03,F05 | 核心基础设施就绪 |
| **M2** | Week 9 | F06,F07,F08,F09,F10 | 安全架构完成 |
| **M3** | Week 12 | F11,F12,F13,F14,F15 | 合规体系完成 |
| **M4** | Week 14 | F20,F21,F18,F17,F22 | 质量保障就绪 |
| **M5** | Week 16 | F24,F28,F29,F30,F25 | 工具链完整 |
| **M6** | Week 20 | 全部节点 | 完整教材流程验证 |

---

## 第八部分：TDD最佳实践

### 8.1 测试命名规范

```python
# 测试文件: tests/unit/test_{node_id}.py
# 测试类: Test{NodeName}
# 测试方法: test_{feature_id}_{description}

class TestImmutableLog:
    """F01: 不可变日志系统"""
    
    def test_f01_t001_version_tag_required(self):
        """F01-T001: 日志条目必须有版本戳"""
        pass
    
    def test_f01_t002_content_hash_required(self):
        """F01-T002: 日志条目必须有内容哈希"""
        pass
```

### 8.2 测试结构规范

```python
class TestExample:
    """测试结构遵循AAA模式"""
    
    def test_example(self):
        # Arrange - 准备测试数据
        manager = ContextBudgetManager()
        test_data = {"content": "x" * 1000}
        
        # Act - 执行被测操作
        result = manager.add_content("ch-001", test_data)
        
        # Assert - 验证预期结果
        assert result.accepted == True
```

### 8.3 Mock使用规范

```python
# 允许的Mock场景:
# 1. 外部API调用 (CrossRef, 国家统计局等)
# 2. 数据库操作 (测试隔离)
# 3. 第三方服务 (时间、随机数等)

# 不允许的Mock场景:
# 1. 被测试的核心逻辑
# 2. 业务规则验证
# 3. 边界条件检查

# 示例:
@pytest.fixture
def mock_crossref_api():
    """允许: Mock外部API"""
    with patch('app.services.verification.CrossRefAPI.verify') as mock:
        mock.return_value = VerificationResult(exists=True)
        yield mock

def test_doi_verification_uses_api(self, mock_crossref_api):
    """DOI验证调用外部API"""
    verifier = DOIVerifier()
    result = await verifier.verify("10.1234/example")
    assert mock_crossref_api.called
```

### 8.4 持续集成要求

```yaml
# .github/workflows/tdd.yml

name: TDD Quality Gate

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  tdd-quality-gate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-asyncio
          pip install mypy ruff
      
      - name: Run TDD Tests
        run: |
          # RED phase: 确认测试失败
          pytest tests/ --tb=short -v || true
          
          # GREEN phase: 运行测试(实现存在时应通过)
          pytest tests/ --cov=src --cov-report=xml --cov-fail-under=80
      
      - name: Security Tests
        run: |
          pytest tests/security/ --tb=short
      
      - name: Type Check
        run: |
          mypy src/ --strict --no-error-summary
      
      - name: Lint Check
        run: |
          ruff check src/ --select=E,F --fail-on=warring
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

---

## 第九部分：附录

### 9.1 测试覆盖率追踪表

| 节点ID | 节点名称 | 单元覆盖率 | 集成覆盖率 | E2E覆盖率 | 安全测试数 |
|--------|---------|-----------|-----------|-----------|-----------|
| F01 | 不可变日志系统 | 92% | 88% | N/A | 10 |
| F02 | 上下文预算管理器 | 88% | 82% | N/A | 5 |
| F03 | Token位置稳定化 | 90% | 85% | N/A | 6 |
| F04 | Temporal工作流引擎 | 85% | 88% | 100% | 8 |
| F05 | 知识图谱核心 | 87% | 83% | N/A | 7 |
| F06 | Tier1数值核实引擎 | 91% | 86% | N/A | 12 |
| F07 | DOI强制解析服务 | 89% | 84% | N/A | 9 |
| F08 | 法规引用核实系统 | 90% | 87% | N/A | 11 |
| F09 | 素材安全管理 | 88% | 82% | N/A | 8 |
| F10 | 概念节点安全 | 91% | 85% | N/A | 10 |
| F11 | 工作流安全(HUMAN_TASK) | 93% | 89% | N/A | 14 |
| F12 | 审批结果安全 | 92% | 88% | N/A | 13 |
| F13 | 全局语义扫描系统 | 86% | 81% | N/A | 9 |
| F14 | 引用完整性校验 | 87% | 83% | N/A | 7 |
| F15 | 政治敏感分析 | 85% | 80% | N/A | 8 |
| F16 | 版本控制与回滚 | 88% | 84% | N/A | 6 |
| F17 | 跨章引用解析器 | 89% | 85% | N/A | 7 |
| F18 | 术语表服务 | 87% | 83% | N/A | 5 |
| F19 | 逻辑链文档服务 | 86% | 82% | N/A | 4 |
| F20 | LLM-as-Judge评分 | 85% | 80% | N/A | 8 |
| F21 | 风险分级复核 | 84% | 79% | N/A | 6 |
| F22 | 素材RAG召回 | 86% | 81% | N/A | 5 |
| F23 | 内容安全过滤 | 87% | 83% | N/A | 9 |
| F24 | 配置中心 | 85% | 80% | N/A | 4 |
| F25 | 模型路由引擎 | 83% | 78% | N/A | 6 |
| F26 | 血缘追踪系统 | 84% | 79% | N/A | 5 |
| F27 | GraphRAG问答 | 80% | 75% | N/A | 4 |
| F28 | 监控仪表盘 | 82% | 77% | N/A | 3 |
| F29 | CI/CD质量门禁 | 85% | 80% | N/A | 4 |
| F30 | Golden Dataset | 88% | 83% | N/A | 6 |

### 9.2 术语表

| 术语 | 定义 |
|------|------|
| TDD | Test-Driven Development，测试驱动开发 |
| RED阶段 | TDD第一步，写失败测试 |
| GREEN阶段 | TDD第二步，写实现让测试通过 |
| Refactor阶段 | TDD第三步，优化代码 |
| 单元测试 | 对单个函数/类级别的测试 |
| 集成测试 | 模块间交互的测试 |
| E2E测试 | 端到端用户旅程测试 |
| Golden Dataset | 手工编写的参考教材样本库 |
| 覆盖率 | 测试覆盖代码的比例 |
| 安全测试 | 专门测试安全漏洞的测试 |
| P0/P1/P2 | 优先级：P0最高 |

---

**文档状态**: 正式版
**下次审查**: Phase 0完成时
**维护责任人**: 架构团队
