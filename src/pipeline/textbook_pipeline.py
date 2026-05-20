"""
主编排器 — 教材编写全流程编排器。

将30个功能模块串联为完整的教材编写流水线:
  Stage 1: INITIALIZATION      — 事件总线/日志/配置/监控启动
  Stage 2: OUTLINE_GENERATION  — 知识图谱+模型路由+素材RAG → 生成提纲
  Stage 3: CONTEXT_SETUP       — 上下文预算分配+内容寻址
  Stage 4: CHAPTER_WRITING     — 并行章节写作 (Temporal子工作流)
  Stage 5: SECURITY_SCAN       — 7层安全扫描
  Stage 6: CONTENT_VERIFICATION — 8维内容核实
  Stage 7: QUALITY_ASSESSMENT  — 4维质量评估
  Stage 8: FINAL_GATE          — 质量门禁裁决

特性:
  - 断点续传 (通过不可变日志恢复状态)
  - 事件总线发布所有关键阶段事件
  - 每个阶段记录性能指标到监控仪表盘
  - Mock 模式下所有模块全模拟运行
"""

import asyncio
import hashlib
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from .exceptions import (
    BudgetExceededError,
    CheckpointError,
    PipelineAbortedError,
    PipelineError,
    SecurityViolationError,
    StageExecutionError,
)
from .integration_config import MockModeConfig, ModuleConfig, PipelineConfig, StageConfig
from .pipeline_stages import (
    STAGE_DEPENDENCIES,
    STAGE_MODULES,
    STAGE_ORDER,
    PipelineStage,
    PipelineStageStatus,
    PipelineState,
    StageResult,
)

logger = logging.getLogger(__name__)

MOCK_TEMPORAL = os.environ.get("MOCK_TEMPORAL", "true").lower() in ("1", "true", "yes")

# ─── Mock Module Implementations ─────────────────────────────────────────────


class MockEventBus:
    """F00: 模拟 Kafka 事件总线。"""

    def __init__(self):
        self._events: List[Dict[str, Any]] = []
        self._subscribers: Dict[str, List[Callable]] = {}

    async def publish(self, topic: str, event: Dict[str, Any]) -> None:
        record = {
            "topic": topic,
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "offset": len(self._events),
        }
        self._events.append(record)
        logger.debug(f"[EventBus] Published to '{topic}': {event.get('type', 'unknown')}")

    async def subscribe(self, topic: str, handler: Callable) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def consumed_events(self) -> List[Dict[str, Any]]:
        return self._events

    def event_count(self) -> int:
        return len(self._events)


class MockImmutableLog:
    """F01: 不可变日志 — 支持断点续传的状态持久化。"""

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    async def append(self, entry: Dict[str, Any]) -> int:
        record = {
            "index": len(self._entries),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hash": hashlib.sha256(str(entry).encode()).hexdigest()[:16],
            **entry,
        }
        self._entries.append(record)
        return len(self._entries) - 1

    async def read_since(self, index: int) -> List[Dict[str, Any]]:
        return self._entries[index:]

    async def save_snapshot(self, key: str, data: Dict[str, Any]) -> None:
        self._snapshots[key] = data

    async def load_snapshot(self, key: str) -> Optional[Dict[str, Any]]:
        return self._snapshots.get(key)

    async def entry_count(self) -> int:
        return len(self._entries)


class MockContextBudgetManager:
    """F02: 上下文预算管理器。"""

    def __init__(self, max_tokens: int = 128000):
        self.max_tokens = max_tokens
        self._allocations: Dict[str, int] = {}

    async def allocate(self, scope: str, tokens: int) -> bool:
        current = sum(self._allocations.values())
        if current + tokens > self.max_tokens:
            return False
        self._allocations[scope] = tokens
        return True

    async def release(self, scope: str) -> None:
        self._allocations.pop(scope, None)

    async def usage_total(self) -> int:
        return sum(self._allocations.values())

    async def remaining(self) -> int:
        return self.max_tokens - sum(self._allocations.values())


class MockKnowledgeGraph:
    """F05: 知识图谱。"""

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Tuple[str, str, str]] = []

    async def add_node(self, node_id: str, data: Dict[str, Any]) -> None:
        self._nodes[node_id] = data

    async def add_edge(self, source: str, target: str, relation: str) -> None:
        self._edges.append((source, target, relation))

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self._nodes.get(node_id)

    async def node_count(self) -> int:
        return len(self._nodes)

    async def edge_count(self) -> int:
        return len(self._edges)


class MockMaterialRAG:
    """F22: 素材RAG召回。"""

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return [
            {
                "doc_id": f"doc-{i}",
                "content": f"Mock material content for '{query}' - chunk {i}",
                "score": 0.95 - i * 0.05,
                "source": "mock_corpus",
            }
            for i in range(min(top_k, 3))
        ]


class MockModelRouter:
    """F25: 模型路由引擎。"""

    async def route(self, task_type: str, context_size: int = 0) -> str:
        models = {
            "outline": "mock-gpt4-v2",
            "chapter_writing": "mock-gpt4-v2",
            "security": "mock-classifier-v1",
            "judge": "mock-judge-v1",
        }
        return models.get(task_type, "mock-gpt3.5-v1")

    async def generate(self, prompt: str, model: str = "mock-gpt4-v2") -> str:
        return f"[{model}] Generated content for prompt: {prompt[:80]}..."


class MockContentSecurityFilter:
    """F09-F15, F23: 组合安全过滤器。"""

    async def scan_all(self, content: str) -> Dict[str, Any]:
        return {
            "status": "PASS",
            "violations": [],
            "categories": {
                "material_security": "PASS",
                "concept_security": "PASS",
                "workflow_security": "PASS",
                "political_sensitivity": "PASS",
                "global_semantic": "PASS",
                "content_security": "PASS",
            },
        }

    async def scan_with_injection(self, content: str, inject_violation: bool = False) -> Dict[str, Any]:
        if inject_violation:
            return {
                "status": "FAIL",
                "violations": [
                    {
                        "rule_id": "C001",
                        "severity": "CRITICAL",
                        "message": "Injected test violation detected",
                    }
                ],
                "categories": {"content_security": "FAIL"},
            }
        return await self.scan_all(content)


class MockTier1Verification:
    """F06: Tier1 数值核实。"""

    async def verify(self, content: str) -> Dict[str, Any]:
        return {"status": "PASS", "verified_facts": 15, "failed_facts": 0, "accuracy": 0.98}


class MockDoiVerification:
    """F07: DOI 验证。"""

    async def verify(self, references: List[str]) -> Dict[str, Any]:
        return {"status": "PASS", "total_refs": len(references), "valid_dois": len(references)}


class MockRegulationVerification:
    """F08: 法规核实。"""

    async def verify(self, content: str, jurisdiction: str = "CN") -> Dict[str, Any]:
        return {"status": "PASS", "jurisdiction": jurisdiction, "compliance_score": 1.0}


class MockCitationIntegrity:
    """F14: 引用完整性。"""

    async def check(self, content: str) -> Dict[str, Any]:
        return {"status": "PASS", "citations_found": 5, "broken_citations": 0}


class MockCrossReference:
    """F17: 跨章引用。"""

    async def validate(self, chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"status": "PASS", "cross_refs_found": 10, "broken_refs": 0}


class MockTermGlossary:
    """F18: 术语表。"""

    async def extract(self, chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {"term": "低空经济", "definition": "以低空空域为依托的经济活动总称", "occurrences": 5},
            {"term": "eVTOL", "definition": "电动垂直起降飞行器", "occurrences": 3},
        ]


class MockLogicChain:
    """F19: 逻辑链。"""

    async def validate(self, content: str) -> Dict[str, Any]:
        return {"status": "PASS", "logical_fallacies": 0, "coherence_score": 0.92}


class MockStatisticalSampling:
    """F16: 统计抽样。"""

    async def sample(self, chapters: List[Dict[str, Any]], sample_rate: float = 0.2) -> Dict[str, Any]:
        return {"sampled_count": max(1, int(len(chapters) * sample_rate)), "confidence_level": 0.95}


class MockLLMJudge:
    """F20: LLM 评判。"""

    async def evaluate(self, content: str, rubric: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "overall_score": 82.5,
            "dimensions": {
                "accuracy": 85.0,
                "completeness": 80.0,
                "readability": 88.0,
                "pedagogy": 78.0,
                "structure": 82.0,
            },
            "grade": "B",
            "recommendation": "PASS",
        }


class MockRiskClassifier:
    """F21: 风险分级。"""

    async def classify(self, quality_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"overall_risk": "LOW", "risk_levels": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 1, "LOW": 5}}


class MockLineageTracker:
    """F26: 血缘追踪。"""

    def __init__(self):
        self._lineage: List[Dict[str, Any]] = []

    async def record(self, source_id: str, target_id: str, operation: str, metadata: Dict[str, Any] = {}) -> None:
        self._lineage.append({
            "source_id": source_id,
            "target_id": target_id,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        })

    async def trace(self, target_id: str) -> List[Dict[str, Any]]:
        return [r for r in self._lineage if r["target_id"] == target_id]


class MockGraphRAG:
    """F27: GraphRAG 问答。"""

    async def query(self, question: str, kg_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"answer": f"Mock GraphRAG answer for: {question[:60]}", "sources": ["kg_node_1", "kg_node_2"], "confidence": 0.89}


class MockConfigCenter:
    """F24: 配置中心。"""

    def __init__(self):
        self._config: Dict[str, Any] = {}

    async def load(self) -> Dict[str, Any]:
        self._config = {"version": "1.0.0", "mock_mode": True}
        return self._config

    async def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        self._config[key] = value


class MockMonitoringDashboard:
    """F28: 监控仪表盘。"""

    def __init__(self):
        self._metrics: List[Dict[str, Any]] = []

    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = {}) -> None:
        self._metrics.append({
            "name": name,
            "value": value,
            "tags": tags,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def get_metrics(self) -> List[Dict[str, Any]]:
        return self._metrics

    async def stage_latency(self, stage: str) -> Optional[float]:
        latencies = [m["value"] for m in self._metrics if m["name"] == "stage_latency" and m["tags"].get("stage") == stage]
        return sum(latencies) / len(latencies) if latencies else None


class MockQualityGate:
    """F29: 质量门禁。"""

    async def evaluate(self, pipeline_result: Dict[str, Any], threshold: float = 70.0) -> Dict[str, Any]:
        overall = pipeline_result.get("summary", {}).get("average_quality_score", 0)
        passed = overall >= threshold
        return {
            "passed": passed,
            "overall_score": overall,
            "threshold": threshold,
            "decision": "APPROVED" if passed else "REJECTED",
        }


class MockGoldenDataset:
    """F30: Golden Dataset。"""

    async def compare(self, generated_content: str, reference: Optional[str] = None) -> Dict[str, Any]:
        return {"similarity_score": 0.88, "passed": True, "benchmark_name": "textbook_golden_v1"}


class MockContentAddressing:
    """F03: 内容寻址。"""

    async def hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    async def store(self, content: str) -> str:
        return await self.hash_content(content)

    async def retrieve(self, content_hash: str) -> Optional[str]:
        return None


# ─── Pipeline Result ─────────────────────────────────────────────────────────


class PipelineResult:
    """流水线执行结果。"""

    def __init__(
        self,
        pipeline_id: str,
        status: str,
        state: PipelineState,
        output: Dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
    ):
        self.pipeline_id = pipeline_id
        self.status = status
        self.state = state
        self.output = output
        self.started_at = started_at
        self.finished_at = finished_at

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 3),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "state": self.state.to_dict(),
            "output": self.output,
        }


# ─── Textbook Pipeline ──────────────────────────────────────────────────────


class TextbookPipeline:
    """教材编写全流程编排器。

    将30个功能模块串联为完整的教材编写流水线，支持:
      - Mock 模式运行 (默认)
      - 断点续传 (通过不可变日志)
      - 事件总线发布
      - 监控指标采集

    Usage:
        config = PipelineConfig(testing=True)
        pipeline = TextbookPipeline(config)
        result = await pipeline.run(textbook_config)
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig(testing=True)
        self.mock = self.config.mock

        # 基础设施层
        self.event_bus = MockEventBus()
        self.log = MockImmutableLog()
        self.config_center = MockConfigCenter()
        self.monitoring = MockMonitoringDashboard()

        # 协调层
        self.budget = MockContextBudgetManager(
            max_tokens=self.config.context_budget.params.get("max_context_tokens", 128000)
        )
        self.addressing = MockContentAddressing()
        self.kg = MockKnowledgeGraph()
        self.lineage = MockLineageTracker()

        # 生成层
        self.rag = MockMaterialRAG()
        self.router = MockModelRouter()
        self.graph_rag = MockGraphRAG()

        # 安全层
        self.security_filter = MockContentSecurityFilter()

        # 验证层
        self.tier1 = MockTier1Verification()
        self.doi = MockDoiVerification()
        self.regulation = MockRegulationVerification()
        self.citation = MockCitationIntegrity()
        self.cross_ref = MockCrossReference()
        self.term_glossary = MockTermGlossary()
        self.logic_chain = MockLogicChain()
        self.stats_sampling = MockStatisticalSampling()

        # 质量层
        self.judge = MockLLMJudge()
        self.risk = MockRiskClassifier()
        self.golden = MockGoldenDataset()
        self.quality_gate = MockQualityGate()

        # Module handler registry (built in __init__ for testability)
        self._handlers = self._build_handlers()

        # Pipeline state and abort flag
        self.state: PipelineState = PipelineState.new("pending")
        self._abort_flag = False

    # ── Public API ──────────────────────────────────────────────────────

    async def run(self, textbook_config: Dict[str, Any]) -> PipelineResult:
        """运行完整教材编写流水线。"""
        pipeline_id = textbook_config.get("pipeline_id", f"pipeline-{uuid.uuid4().hex[:8]}")
        self.state = PipelineState.new(pipeline_id)
        self._abort_flag = False
        started_at = datetime.now(timezone.utc)

        logger.info(f"[Pipeline:{pipeline_id}] Starting textbook pipeline: {textbook_config.get('title', 'Untitled')}")

        try:
            await self._execute_stages(textbook_config)
            status = "COMPLETED"
            logger.info(f"[Pipeline:{pipeline_id}] Completed successfully")
        except SecurityViolationError:
            status = "ABORTED_SECURITY"
            logger.error(f"[Pipeline:{pipeline_id}] Aborted due to security violation")
        except PipelineAbortedError:
            status = "ABORTED"
            logger.warning(f"[Pipeline:{pipeline_id}] Aborted by request")
        except Exception as e:
            status = "FAILED"
            logger.error(f"[Pipeline:{pipeline_id}] Failed: {e}")
            self.state.failed_stages.append(
                self.state.current_stage or PipelineStage.INITIALIZATION
            )

        finished_at = datetime.now(timezone.utc)
        output = self._build_output(textbook_config)

        result = PipelineResult(
            pipeline_id=pipeline_id,
            status=status,
            state=self.state,
            output=output,
            started_at=started_at,
            finished_at=finished_at,
        )

        await self.event_bus.publish("pipeline.completed", result.to_dict())
        return result

    async def resume(self, checkpoint_data: Dict[str, Any], textbook_config: Dict[str, Any]) -> PipelineResult:
        """从断点恢复执行流水线。"""
        self.state = PipelineState.from_checkpoint(checkpoint_data)
        pipeline_id = self.state.pipeline_id
        resumed_stage = checkpoint_data.get("current_stage")

        if resumed_stage is None and not self.state.completed_stages:
            raise CheckpointError(
                "Invalid checkpoint: no stage to resume from and no completed stages",
                checkpoint_id=pipeline_id,
            )

        logger.info(f"[Pipeline:{pipeline_id}] Resuming from stage: {resumed_stage}")

        started_at = datetime.now(timezone.utc)
        self.state.start_time = started_at

        try:
            await self._execute_stages(textbook_config, resume_from=PipelineStage(resumed_stage))
            status = "COMPLETED"
        except SecurityViolationError:
            status = "ABORTED_SECURITY"
        except PipelineAbortedError:
            status = "ABORTED"
        except Exception as e:
            status = "FAILED"
            logger.error(f"[Pipeline:{pipeline_id}] Resume failed: {e}")

        finished_at = datetime.now(timezone.utc)
        output = self._build_output(textbook_config)

        return PipelineResult(
            pipeline_id=pipeline_id,
            status=status,
            state=self.state,
            output=output,
            started_at=started_at,
            finished_at=finished_at,
        )

    def abort(self, reason: str = "user_requested") -> None:
        """主动中止流水线。"""
        self._abort_flag = True
        logger.warning(f"[Pipeline] Abort requested: {reason}")

    # ── Stage Execution ─────────────────────────────────────────────────

    async def _execute_stages(
        self,
        textbook_config: Dict[str, Any],
        resume_from: Optional[PipelineStage] = None,
    ) -> None:
        """顺序执行所有流水线阶段，支持从指定阶段恢复。"""
        skip_until = resume_from is not None

        for stage in PipelineStage:
            if skip_until:
                if stage == resume_from:
                    skip_until = False
                else:
                    continue

            if self._abort_flag:
                raise PipelineAbortedError("Pipeline aborted during execution")

            if not self._check_dependencies(stage):
                raise StageExecutionError(
                    f"Stage '{stage.value}' dependencies not met",
                    stage=stage.value,
                )

            await self._execute_stage(stage, textbook_config)

    def _check_dependencies(self, stage: PipelineStage) -> bool:
        """验证阶段依赖是否已满足。"""
        deps = STAGE_DEPENDENCIES.get(stage, [])
        return all(d in self.state.completed_stages for d in deps)

    async def _execute_stage(
        self,
        stage: PipelineStage,
        textbook_config: Dict[str, Any],
    ) -> None:
        """执行单个流水线阶段。"""
        result = self.state.stage_results[stage]
        result.status = PipelineStageStatus.RUNNING
        result.start_time = datetime.now(timezone.utc)
        self.state.current_stage = stage

        logger.info(f"[Pipeline] Stage START: {stage.value}")
        await self.event_bus.publish("stage.started", {"stage": stage.value})

        modules = STAGE_MODULES.get(stage, [])
        stage_config = self._get_stage_config(stage)

        try:
            if stage_config and stage_config.parallel:
                outputs = await self._execute_modules_parallel(modules, stage, textbook_config)
            else:
                outputs = await self._execute_modules_sequential(modules, stage, textbook_config)

            result.output = outputs
            result.modules_executed = list(outputs.keys())
            result.status = PipelineStageStatus.COMPLETED

            self.state.completed_stages.append(stage)
            await self.log.append({
                "type": "stage_completed",
                "stage": stage.value,
                "modules": result.modules_executed,
            })

        except Exception as e:
            result.status = PipelineStageStatus.FAILED
            result.errors.append(str(e))
            await self.log.append({
                "type": "stage_failed",
                "stage": stage.value,
                "error": str(e),
            })
            raise

        finally:
            result.end_time = datetime.now(timezone.utc)
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()

            await self.monitoring.record_metric(
                "stage_latency",
                result.duration_seconds,
                {"stage": stage.value, "status": result.status.value},
            )
            await self.monitoring.record_metric(
                "stage_modules",
                len(result.modules_executed),
                {"stage": stage.value},
            )

            await self.event_bus.publish("stage.completed", {
                "stage": stage.value,
                "status": result.status.value,
                "duration": result.duration_seconds,
                "modules": result.modules_executed,
            })

            if stage_config and stage_config.checkpoint_after:
                await self._create_checkpoint(stage)

        logger.info(
            f"[Pipeline] Stage DONE: {stage.value} ({result.duration_seconds:.2f}s, "
            f"{len(result.modules_executed)} modules)"
        )

    async def _execute_modules_sequential(
        self,
        module_ids: List[str],
        stage: PipelineStage,
        textbook_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        outputs = {}
        for mid in module_ids:
            if self._abort_flag:
                raise PipelineAbortedError("Pipeline aborted during module execution")
            outputs[mid] = await self._execute_module(mid, stage, textbook_config)
        return outputs

    async def _execute_modules_parallel(
        self,
        module_ids: List[str],
        stage: PipelineStage,
        textbook_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        tasks = [self._execute_module(mid, stage, textbook_config) for mid in module_ids]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        outputs = {}
        for mid, result in zip(module_ids, results_list):
            if isinstance(result, Exception):
                raise StageExecutionError(
                    f"Module {mid} failed: {result}",
                    stage=stage.value,
                    component=mid,
                )
            outputs[mid] = result
        return outputs

    async def _execute_module(
        self,
        module_id: str,
        stage: PipelineStage,
        textbook_config: Dict[str, Any],
    ) -> Any:
        """执行单个模块。分发到对应的 mock 方法。"""
        module_start = time.monotonic()

        handler = self._module_handlers.get(module_id)
        if handler is None:
            logger.debug(f"[Pipeline] Module {module_id}: no handler, skipping")
            return {"status": "SKIPPED", "module_id": module_id}

        try:
            result = await handler(stage, textbook_config)
            elapsed = time.monotonic() - module_start
            await self.monitoring.record_metric(
                f"module_{module_id}_latency",
                elapsed,
                {"stage": stage.value},
            )
            await self.event_bus.publish("module.completed", {
                "module_id": module_id,
                "stage": stage.value,
                "latency": elapsed,
            })
            return result
        except Exception as e:
            elapsed = time.monotonic() - module_start
            await self.monitoring.record_metric(
                f"module_{module_id}_error",
                1,
                {"stage": stage.value, "error": type(e).__name__},
            )
            await self.event_bus.publish("module.failed", {
                "module_id": module_id,
                "stage": stage.value,
                "error": str(e),
                "latency": elapsed,
            })
            raise

    # ── Module Handlers ─────────────────────────────────────────────────

    @property
    def _module_handlers(self) -> Dict[str, Callable]:
        return self._handlers

    def _build_handlers(self) -> Dict[str, Callable]:
        return {
            # 基础设施层
            "F00": self._h_init_eventbus,
            "F01": self._h_init_immutable_log,
            "F24": self._h_config_center,
            "F28": self._h_monitoring_init,
            # 协调层
            "F02": self._h_context_budget,
            "F03": self._h_content_addressing,
            "F04": self._h_temporal_workflow,
            "F05": self._h_knowledge_graph,
            # 生成层
            "F22": self._h_material_rag,
            "F25": self._h_model_router,
            "F27": self._h_graph_rag,
            # 安全层
            "F09": self._h_security_scanner,
            "F10": self._h_security_scanner,
            "F11": self._h_security_scanner,
            "F12": self._h_security_scanner,
            "F13": self._h_security_scanner,
            "F15": self._h_security_scanner,
            "F23": self._h_security_scanner,
            # 验证层
            "F06": self._h_tier1_verify,
            "F07": self._h_doi_verify,
            "F08": self._h_regulation_verify,
            "F14": self._h_citation_check,
            "F16": self._h_stats_sampling,
            "F17": self._h_cross_reference,
            "F18": self._h_term_glossary,
            "F19": self._h_logic_chain,
            # 质量层
            "F20": self._h_llm_judge,
            "F21": self._h_risk_classify,
            "F26": self._h_lineage,
            "F30": self._h_golden_dataset,
            # 门禁
            "F29": self._h_quality_gate,
        }

    # 基础设施层 handlers
    async def _h_init_eventbus(self, stage, cfg): return {"status": "INITIALIZED"}
    async def _h_init_immutable_log(self, stage, cfg): return {"status": "INITIALIZED", "entry_count": 0}
    async def _h_config_center(self, stage, cfg): return await self.config_center.load()
    async def _h_monitoring_init(self, stage, cfg): return {"dashboard": "ready", "metrics_count": 0}

    # 协调层 handlers
    async def _h_context_budget(self, stage, cfg):
        chapters = cfg.get("chapters", [])
        per_chapter = self.config.context_budget.params.get("per_chapter_budget", 16000)
        for ch in chapters[:5]:
            ok = await self.budget.allocate(ch.get("chapter_id", "unknown"), per_chapter)
            if not ok:
                raise BudgetExceededError(
                    f"Budget exceeded at chapter {ch.get('chapter_id')}",
                    current_usage=await self.budget.usage_total(),
                    budget_limit=self.budget.max_tokens,
                    stage=stage.value,
                )
        return {"allocated_chapters": min(len(chapters), 5), "usage": await self.budget.usage_total()}

    async def _h_content_addressing(self, stage, cfg):
        title = cfg.get("title", "Untitled")
        content_hash = await self.addressing.hash_content(title)
        return {"hash": content_hash, "stored": True}

    async def _h_temporal_workflow(self, stage, cfg):
        if stage == PipelineStage.OUTLINE_GENERATION:
            return {"workflow": "outline_generation", "status": "COMPLETED", "outline": self._mock_outline(cfg)}
        elif stage == PipelineStage.CHAPTER_WRITING:
            chapters = cfg.get("chapters", [])
            results = []
            for ch in chapters:
                results.append({
                    "chapter_id": ch.get("chapter_id", "unknown"),
                    "title": ch.get("title", "Untitled"),
                    "status": "COMPLETED",
                    "content": self._mock_chapter_content(ch, cfg),
                    "quality": {"grade": "B", "overall_score": self.mock.mock_quality_score},
                    "security": {"status": "PASS"},
                })
            return {"chapters": results, "total": len(results)}
        return {"status": "NOOP"}

    async def _h_knowledge_graph(self, stage, cfg):
        chapters = cfg.get("chapters", [])
        for ch in chapters:
            await self.kg.add_node(ch.get("chapter_id", "unknown"), {
                "title": ch.get("title", "Untitled"),
                "order": ch.get("order", 0),
                "learning_objectives": ch.get("learning_objectives", []),
            })
        for i in range(len(chapters) - 1):
            await self.kg.add_edge(
                chapters[i].get("chapter_id", f"ch{i}"),
                chapters[i + 1].get("chapter_id", f"ch{i+1}"),
                "PREREQUISITE",
            )
        return {"nodes": await self.kg.node_count(), "edges": await self.kg.edge_count()}

    # 生成层 handlers
    async def _h_material_rag(self, stage, cfg):
        subject = cfg.get("subject", "低空经济")
        return await self.rag.retrieve(subject, top_k=self.mock.mock_rag_k)

    async def _h_model_router(self, stage, cfg):
        model = await self.router.route(
            "outline" if stage == PipelineStage.OUTLINE_GENERATION else "chapter_writing"
        )
        return {"selected_model": model, "task_type": stage.value}

    async def _h_graph_rag(self, stage, cfg):
        return await self.graph_rag.query(
            f"Key concepts for {cfg.get('subject', '低空经济')} textbook",
            kg_context={"node_count": await self.kg.node_count()},
        )

    # 安全层 handlers
    async def _h_security_scanner(self, stage, cfg):
        content = cfg.get("_security_content", "mock content for security scan")
        inject = cfg.get("_inject_security_violation", False)
        result = await self.security_filter.scan_with_injection(content, inject)
        if result["status"] == "FAIL":
            violations = result.get("violations", [])
            if violations:
                v = violations[0]
                raise SecurityViolationError(
                    v.get("message", "Security violation detected"),
                    rule_id=v.get("rule_id", "UNKNOWN"),
                    severity=v.get("severity", "CRITICAL"),
                    stage=stage.value,
                )
        return result

    # 验证层 handlers
    async def _h_tier1_verify(self, stage, cfg):
        content = cfg.get("_mock_chapter_content", "mock")
        return await self.tier1.verify(content)

    async def _h_doi_verify(self, stage, cfg):
        refs = cfg.get("_references", ["10.1000/xyz123", "10.1000/abc456"])
        return await self.doi.verify(refs)

    async def _h_regulation_verify(self, stage, cfg):
        content = cfg.get("_mock_chapter_content", "mock")
        return await self.regulation.verify(content)

    async def _h_citation_check(self, stage, cfg):
        content = cfg.get("_mock_chapter_content", "mock")
        return await self.citation.check(content)

    async def _h_stats_sampling(self, stage, cfg):
        chapters = cfg.get("chapters", [])
        return await self.stats_sampling.sample(chapters)

    async def _h_cross_reference(self, stage, cfg):
        chapters = cfg.get("chapters", [])
        return await self.cross_ref.validate(chapters)

    async def _h_term_glossary(self, stage, cfg):
        chapters = cfg.get("chapters", [])
        return await self.term_glossary.extract(chapters)

    async def _h_logic_chain(self, stage, cfg):
        content = cfg.get("_mock_chapter_content", "mock")
        return await self.logic_chain.validate(content)

    # 质量层 handlers
    async def _h_llm_judge(self, stage, cfg):
        content = cfg.get("_mock_chapter_content", "mock")
        return await self.judge.evaluate(content)

    async def _h_risk_classify(self, stage, cfg):
        quality_scores = cfg.get("_quality_scores", [{"grade": "B", "overall_score": 82.5}])
        return await self.risk.classify(quality_scores)

    async def _h_lineage(self, stage, cfg):
        chapters = cfg.get("chapters", [])
        for ch in chapters:
            await self.lineage.record(
                source_id="textbook_config",
                target_id=ch.get("chapter_id", "unknown"),
                operation="CHAPTER_GENERATED",
            )
        return {"lineage_records": len(chapters)}

    async def _h_golden_dataset(self, stage, cfg):
        content = cfg.get("_mock_chapter_content", "mock")
        return await self.golden.compare(content)

    # 门禁
    async def _h_quality_gate(self, stage, cfg):
        summary = cfg.get("_pipeline_summary", {"average_quality_score": 82.5})
        return await self.quality_gate.evaluate(summary, self.config.quality_gate.params.get("pass_threshold", 70.0))

    # ── Helpers ─────────────────────────────────────────────────────────

    def _get_stage_config(self, stage: PipelineStage) -> Optional[StageConfig]:
        for sc in self.config.stages:
            if sc.stage_name == stage.value:
                return sc
        return None

    async def _create_checkpoint(self, stage: PipelineStage) -> None:
        self.state.record_checkpoint(stage)
        await self.log.save_snapshot(
            f"checkpoint_{stage.value}",
            self.state.to_dict(),
        )
        await self.event_bus.publish("checkpoint.created", {
            "stage": stage.value,
            "completed": [s.value for s in self.state.completed_stages],
        })

    def _build_output(self, textbook_config: Dict[str, Any]) -> Dict[str, Any]:
        chapter_results = []
        temporal_output = None
        for sr in self.state.stage_results.values():
            if "chapters" in sr.output:
                temporal_output = sr.output
                chapter_results = sr.output.get("chapters", [])

        avg_score = self.mock.mock_quality_score
        return {
            "textbook_id": textbook_config.get("pipeline_id", "unknown"),
            "title": textbook_config.get("title", "Untitled"),
            "subject": textbook_config.get("subject", "低空经济"),
            "outline": temporal_output.get("outline", {}) if temporal_output else {},
            "chapters": chapter_results,
            "stage_summary": {
                sr.stage.value: {
                    "status": sr.status.value,
                    "duration": sr.duration_seconds,
                    "modules": len(sr.modules_executed),
                }
                for sr in self.state.stage_results.values()
            },
            "summary": {
                "total_chapters": len(textbook_config.get("chapters", [])),
                "completed_chapters": len(chapter_results),
                "average_quality_score": avg_score,
                "overall_grade": "B" if avg_score >= 70 else "C",
                "overall_risk": "LOW",
            },
            "metrics": [
                {"name": m["name"], "value": m["value"], "tags": m["tags"]}
                for m in self.monitoring._metrics
            ],
        }

    def _mock_outline(self, textbook_config: Dict[str, Any]) -> Dict[str, Any]:
        chapters = textbook_config.get("chapters", [])
        outline = []
        for i, ch in enumerate(chapters, 1):
            outline.append({
                "chapter_number": i,
                "chapter_id": ch.get("chapter_id", f"ch{i}"),
                "title": ch.get("title", f"Chapter {i}"),
                "sections": [
                    {"section_number": f"{i}.{j}", "title": f"Section {j}: {ch.get('title', 'Topic')} Overview"}
                    for j in range(1, 4)
                ],
            })
        return {"textbook_outline": outline, "total_chapters": len(chapters)}

    def _mock_chapter_content(self, chapter_config: Dict[str, Any], textbook_config: Dict[str, Any]) -> str:
        title = chapter_config.get("title", "Untitled")
        subject = textbook_config.get("subject", "低空经济")
        return (
            f"# {title}\n\n"
            f"## 学习目标\n"
            f"本章将介绍{subject}领域的核心概念和应用。\n\n"
            f"## 核心内容\n"
            f"在{subject}的框架下，本章涵盖理论基础、实践应用和关联知识。\n\n"
            f"## 本章小结\n"
            f"本章系统介绍了{title}的基础知识。\n\n"
            f"## 参考文献\n"
            f"1. 教材编写组. (2026). 现代教材编写指南\n"
        )
