"""流水线阶段定义 — 定义教材编写流水线的8个阶段及其状态机。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class PipelineStageStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    PAUSED = "PAUSED"


class PipelineStage(Enum):
    INITIALIZATION = "INITIALIZATION"
    OUTLINE_GENERATION = "OUTLINE_GENERATION"
    CONTEXT_SETUP = "CONTEXT_SETUP"
    CHAPTER_WRITING = "CHAPTER_WRITING"
    SECURITY_SCAN = "SECURITY_SCAN"
    CONTENT_VERIFICATION = "CONTENT_VERIFICATION"
    QUALITY_ASSESSMENT = "QUALITY_ASSESSMENT"
    FINAL_GATE = "FINAL_GATE"

    @property
    def index(self) -> int:
        return list(PipelineStage).index(self)

    @property
    def next_stage(self) -> Optional["PipelineStage"]:
        stages = list(PipelineStage)
        idx = stages.index(self)
        return stages[idx + 1] if idx + 1 < len(stages) else None

    @property
    def prev_stage(self) -> Optional["PipelineStage"]:
        stages = list(PipelineStage)
        idx = stages.index(self)
        return stages[idx - 1] if idx > 0 else None


STAGES = list(PipelineStage)
STAGE_ORDER = {s: i for i, s in enumerate(STAGES)}

STAGE_DEPENDENCIES: Dict[PipelineStage, List[PipelineStage]] = {
    PipelineStage.INITIALIZATION: [],
    PipelineStage.OUTLINE_GENERATION: [PipelineStage.INITIALIZATION],
    PipelineStage.CONTEXT_SETUP: [PipelineStage.OUTLINE_GENERATION],
    PipelineStage.CHAPTER_WRITING: [PipelineStage.CONTEXT_SETUP],
    PipelineStage.SECURITY_SCAN: [PipelineStage.CHAPTER_WRITING],
    PipelineStage.CONTENT_VERIFICATION: [PipelineStage.SECURITY_SCAN],
    PipelineStage.QUALITY_ASSESSMENT: [PipelineStage.CONTENT_VERIFICATION],
    PipelineStage.FINAL_GATE: [PipelineStage.QUALITY_ASSESSMENT],
}

STAGE_MODULES: Dict[PipelineStage, List[str]] = {
    PipelineStage.INITIALIZATION: ["F00", "F01", "F24", "F28"],
    PipelineStage.OUTLINE_GENERATION: ["F04", "F05", "F25", "F22", "F27"],
    PipelineStage.CONTEXT_SETUP: ["F02", "F03"],
    PipelineStage.CHAPTER_WRITING: ["F04", "F05", "F22", "F25", "F26"],
    PipelineStage.SECURITY_SCAN: ["F09", "F10", "F11", "F12", "F13", "F15", "F23"],
    PipelineStage.CONTENT_VERIFICATION: ["F06", "F07", "F08", "F14", "F16", "F17", "F18", "F19"],
    PipelineStage.QUALITY_ASSESSMENT: ["F20", "F21", "F26", "F30"],
    PipelineStage.FINAL_GATE: ["F29"],
}


@dataclass
class StageResult:
    stage: PipelineStage
    status: PipelineStageStatus = PipelineStageStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    modules_executed: List[str] = field(default_factory=list)
    modules_failed: List[str] = field(default_factory=list)
    output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == PipelineStageStatus.COMPLETED

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 3),
            "modules_executed": self.modules_executed,
            "modules_failed": self.modules_failed,
            "has_errors": self.has_errors,
            "errors": self.errors,
            "metrics": self.metrics,
        }


@dataclass
class PipelineState:
    pipeline_id: str
    current_stage: Optional[PipelineStage] = None
    stage_results: Dict[PipelineStage, StageResult] = field(default_factory=dict)
    completed_stages: List[PipelineStage] = field(default_factory=list)
    failed_stages: List[PipelineStage] = field(default_factory=list)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(cls, pipeline_id: str) -> "PipelineState":
        state = cls(pipeline_id=pipeline_id, start_time=datetime.now())
        for stage in PipelineStage:
            state.stage_results[stage] = StageResult(stage=stage)
        return state

    @classmethod
    def from_checkpoint(cls, checkpoint_data: Dict[str, Any]) -> "PipelineState":
        state = cls(pipeline_id=checkpoint_data["pipeline_id"])
        current_stage_val = checkpoint_data.get("current_stage")
        if current_stage_val is not None:
            state.current_stage = PipelineStage(current_stage_val)
        state.completed_stages = [PipelineStage(s) for s in checkpoint_data.get("completed_stages", [])]
        state.failed_stages = [PipelineStage(s) for s in checkpoint_data.get("failed_stages", [])]
        state.checkpoints = checkpoint_data.get("checkpoints", [])
        state.metadata = checkpoint_data.get("metadata", {})

        for stage_dict in checkpoint_data.get("stage_results", []):
            stage = PipelineStage(stage_dict["stage"])
            state.stage_results[stage] = StageResult(
                stage=stage,
                status=PipelineStageStatus(stage_dict["status"]),
                modules_executed=stage_dict.get("modules_executed", []),
                modules_failed=stage_dict.get("modules_failed", []),
                output=stage_dict.get("output", {}),
                errors=stage_dict.get("errors", []),
            )

        # Initialize missing stage results
        for stage in PipelineStage:
            if stage not in state.stage_results:
                state.stage_results[stage] = StageResult(stage=stage)

        return state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "completed_stages": [s.value for s in self.completed_stages],
            "failed_stages": [s.value for s in self.failed_stages],
            "checkpoints": self.checkpoints,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata,
            "stage_results": [r.to_dict() for r in self.stage_results.values()],
        }

    def record_checkpoint(self, stage: PipelineStage) -> None:
        self.checkpoints.append({
            "stage": stage.value,
            "timestamp": datetime.now().isoformat(),
            "completed_stages": [s.value for s in self.completed_stages],
            "failed_stages": [s.value for s in self.failed_stages],
        })
