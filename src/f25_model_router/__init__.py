"""
F25: 模型路由引擎

根据任务类型自动选择最合适的AI模型。
"""

from f25_model_router.model_router import (
    ModelRouter,
    TaskType,
    Task,
    ModelSelection,
)

__all__ = ["ModelRouter", "TaskType", "Task", "ModelSelection"]
