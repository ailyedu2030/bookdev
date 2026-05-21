"""集成配置 — PipelineConfig 定义流水线的所有可配置参数。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockModeConfig:
    """Mock 模式配置 — 所有模块在 Mock 模式下运行。"""

    enabled: bool = True
    mock_llm_model: str = "mock-gpt4-v2"
    mock_rag_k: int = 5
    mock_kg_depth: int = 3
    mock_security_pass: bool = True
    mock_quality_score: float = 82.5
    mock_verification_pass: bool = True
    mock_temporal: bool = True
    mock_eventbus_async: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mock_llm_model": self.mock_llm_model,
            "mock_rag_k": self.mock_rag_k,
            "mock_kg_depth": self.mock_kg_depth,
            "mock_security_pass": self.mock_security_pass,
            "mock_quality_score": self.mock_quality_score,
            "mock_verification_pass": self.mock_verification_pass,
        }


@dataclass
class ModuleConfig:
    """单个功能模块的配置。"""

    module_id: str
    module_name: str
    enabled: bool = True
    timeout_seconds: int = 120
    retry_count: int = 2
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "params": self.params,
        }


@dataclass
class StageConfig:
    """单个流水线阶段的配置。"""

    stage_name: str
    modules: list[str]
    timeout_seconds: int = 300
    parallel: bool = False
    required: bool = True
    checkpoint_after: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "modules": self.modules,
            "timeout_seconds": self.timeout_seconds,
            "parallel": self.parallel,
            "required": self.required,
            "checkpoint_after": self.checkpoint_after,
        }


@dataclass
class PipelineConfig:
    """流水线总配置。"""

    pipeline_id: str = "textbook-v1"
    testing: bool = False
    mock: MockModeConfig = field(default_factory=MockModeConfig)

    event_bus: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F00",
            module_name="KafkaEventBus",
            timeout_seconds=30,
        )
    )
    immutable_log: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F01",
            module_name="ImmutableLog",
            timeout_seconds=30,
        )
    )
    context_budget: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F02",
            module_name="ContextBudgetManager",
            timeout_seconds=30,
            params={"max_context_tokens": 128000, "per_chapter_budget": 16000},
        )
    )
    content_addressing: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F03",
            module_name="ContentAddressing",
            timeout_seconds=30,
        )
    )
    temporal_workflow: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F04",
            module_name="TemporalWorkflow",
            timeout_seconds=600,
        )
    )
    knowledge_graph: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F05",
            module_name="KnowledgeGraph",
            timeout_seconds=120,
            params={"max_nodes": 10000, "relationship_types": ["PREREQUISITE", "EXTENDS", "REFERENCES"]},
        )
    )
    tier1_verification: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F06",
            module_name="Tier1Verification",
            timeout_seconds=300,
        )
    )
    doi_verification: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F07",
            module_name="DoiVerification",
            timeout_seconds=180,
        )
    )
    regulation_verification: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F08",
            module_name="RegulationVerification",
            timeout_seconds=180,
        )
    )
    material_security: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F09",
            module_name="MaterialSecurity",
            timeout_seconds=120,
        )
    )
    concept_security: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F10",
            module_name="ConceptSecurity",
            timeout_seconds=120,
        )
    )
    workflow_security: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F11",
            module_name="WorkflowSecurity",
            timeout_seconds=60,
        )
    )
    approval_security: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F12",
            module_name="ApprovalSecurity",
            timeout_seconds=60,
        )
    )
    global_semantic_scanner: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F13",
            module_name="GlobalSemanticScanner",
            timeout_seconds=300,
        )
    )
    citation_integrity: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F14",
            module_name="CitationIntegrity",
            timeout_seconds=180,
        )
    )
    political_sensitivity: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F15",
            module_name="PoliticalSensitivity",
            timeout_seconds=120,
        )
    )
    statistical_sampling: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F16",
            module_name="StatisticalSampling",
            timeout_seconds=60,
        )
    )
    cross_reference: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F17",
            module_name="CrossReference",
            timeout_seconds=120,
        )
    )
    term_glossary: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F18",
            module_name="TermGlossary",
            timeout_seconds=60,
        )
    )
    logic_chain: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F19",
            module_name="LogicChain",
            timeout_seconds=120,
        )
    )
    llm_judge: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F20",
            module_name="LLMJudge",
            timeout_seconds=180,
        )
    )
    risk_classification: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F21",
            module_name="RiskClassification",
            timeout_seconds=60,
        )
    )
    material_rag: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F22",
            module_name="MaterialRAG",
            timeout_seconds=120,
            params={"top_k": 5, "similarity_threshold": 0.7},
        )
    )
    content_security: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F23",
            module_name="ContentSecurity",
            timeout_seconds=120,
        )
    )
    config_center: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F24",
            module_name="ConfigCenter",
            timeout_seconds=30,
        )
    )
    model_router: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F25",
            module_name="ModelRouter",
            timeout_seconds=30,
            params={"default_model": "gpt-4", "fallback_models": ["gpt-3.5-turbo", "claude-3"]},
        )
    )
    lineage_tracker: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F26",
            module_name="LineageTracker",
            timeout_seconds=60,
        )
    )
    graph_rag: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F27",
            module_name="GraphRAG",
            timeout_seconds=120,
        )
    )
    monitoring_dashboard: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F28",
            module_name="MonitoringDashboard",
            timeout_seconds=30,
        )
    )
    quality_gate: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F29",
            module_name="QualityGate",
            timeout_seconds=60,
            params={"pass_threshold": 70.0},
        )
    )
    golden_dataset: ModuleConfig = field(
        default_factory=lambda: ModuleConfig(
            module_id="F30",
            module_name="GoldenDataset",
            timeout_seconds=60,
        )
    )

    stages: list[StageConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.stages:
            self.stages = self._default_stages()

    def _default_stages(self) -> list[StageConfig]:
        return [
            StageConfig(
                stage_name="INITIALIZATION",
                modules=["F00", "F01", "F24", "F28"],
                timeout_seconds=60,
            ),
            StageConfig(
                stage_name="OUTLINE_GENERATION",
                modules=["F04", "F05", "F25", "F22", "F27"],
                timeout_seconds=600,
                checkpoint_after=True,
            ),
            StageConfig(
                stage_name="CONTEXT_SETUP",
                modules=["F02", "F03"],
                timeout_seconds=60,
            ),
            StageConfig(
                stage_name="CHAPTER_WRITING",
                modules=["F04", "F05", "F22", "F25", "F26"],
                timeout_seconds=3600,
                parallel=True,
                checkpoint_after=True,
            ),
            StageConfig(
                stage_name="SECURITY_SCAN",
                modules=["F09", "F10", "F11", "F12", "F13", "F15", "F23"],
                timeout_seconds=600,
                checkpoint_after=True,
            ),
            StageConfig(
                stage_name="CONTENT_VERIFICATION",
                modules=["F06", "F07", "F08", "F14", "F16", "F17", "F18", "F19"],
                timeout_seconds=600,
                parallel=True,
            ),
            StageConfig(
                stage_name="QUALITY_ASSESSMENT",
                modules=["F20", "F21", "F26", "F30"],
                timeout_seconds=300,
                checkpoint_after=True,
            ),
            StageConfig(
                stage_name="FINAL_GATE",
                modules=["F29"],
                timeout_seconds=60,
            ),
        ]

    def get_module_config(self, module_id: str) -> ModuleConfig | None:
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, ModuleConfig) and attr.module_id == module_id:
                return attr
        return None

    def all_modules(self) -> list[ModuleConfig]:
        result = []
        for attr_name in sorted(dir(self)):
            attr = getattr(self, attr_name)
            if isinstance(attr, ModuleConfig):
                result.append(attr)
        return result
