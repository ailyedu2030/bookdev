"""
AI Multi-Agent Textbook Writing Pipeline — 完整教材编写流水线。

将30个功能模块串联为完整的教材生成流程:
  基础设施层: Kafka事件总线, 不可变日志, Temporal工作流
  协调层:     上下文预算, 内容寻址, 知识图谱
  生成层:     素材RAG, 模型路由, GraphRAG问答
  验证层:     Tier1核实, DOI验证, 法规核实, 引用完整性等
  安全层:     素材安全, 概念安全, 工作流安全等
  质量层:     LLM评判, 风险分级, 血缘追踪, Golden Dataset
  运维层:     配置中心, 监控仪表盘, 质量门禁
"""

from .exceptions import (
    BudgetExceededError,
    CheckpointError,
    PipelineAbortedError,
    PipelineError,
    SecurityViolationError,
    StageExecutionError,
)
from .integration_config import (
    MockModeConfig,
    ModuleConfig,
    PipelineConfig,
    StageConfig,
)
from .pipeline_stages import (
    STAGE_DEPENDENCIES,
    STAGE_ORDER,
    STAGES,
    PipelineStage,
    PipelineStageStatus,
    PipelineState,
    StageResult,
)
from .textbook_pipeline import (
    PipelineResult,
    TextbookPipeline,
)

__all__ = [
    "TextbookPipeline",
    "PipelineResult",
    "PipelineConfig",
    "StageConfig",
    "ModuleConfig",
    "MockModeConfig",
    "PipelineStage",
    "PipelineStageStatus",
    "StageResult",
    "PipelineState",
    "STAGES",
    "STAGE_DEPENDENCIES",
    "STAGE_ORDER",
    "PipelineError",
    "StageExecutionError",
    "SecurityViolationError",
    "BudgetExceededError",
    "CheckpointError",
    "PipelineAbortedError",
]
