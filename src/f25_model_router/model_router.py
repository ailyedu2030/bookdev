"""
F25: 模型路由引擎

根据任务类型自动选择最合适的AI模型。
"""

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """任务类型枚举"""

    FACTUAL_VERIFICATION = "factual_verification"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    RISK_ASSESSMENT = "risk_assessment"
    GENERAL = "general"


@dataclass
class Task:
    """任务数据类"""

    task_type: TaskType
    prompt: str
    context: dict | None = None


@dataclass
class ModelSelection:
    """模型选择结果"""

    model_id: str
    confidence: float
    reason: str


class ModelRouter:
    """模型路由引擎"""

    DEFAULT_ROUTING_RULES = {
        "factual_verification": "claude",
        "creative_writing": "minimax",
        "code_generation": "gpt4o",
        "risk_assessment": "claude",
        "general": "gpt4o",
    }

    DEFAULT_MODEL_REGISTRY = {
        "claude": {"name": "Claude", "strengths": ["factual", "reasoning"]},
        "minimax": {"name": "MiniMax", "strengths": ["creative", "writing"]},
        "gpt4o": {"name": "GPT-4o", "strengths": ["code", "general"]},
    }

    def __init__(self, routing_rules: dict[str, str] | None = None):
        """初始化路由器

        Args:
            routing_rules: 自定义路由规则，如果为None使用默认规则
        """
        self.ROUTING_RULES = routing_rules or self.DEFAULT_ROUTING_RULES.copy()
        self.model_registry = self.DEFAULT_MODEL_REGISTRY.copy()

    def route(self, task: Task) -> str:
        """根据任务类型返回最佳模型ID

        Args:
            task: 任务对象

        Returns:
            模型ID字符串
        """
        task_type_key = task.task_type.value
        return self.ROUTING_RULES.get(task_type_key, self.ROUTING_RULES.get("general", "gpt4o"))

    def select_model_for_prompt(self, prompt: str, context: dict) -> ModelSelection:
        """为提示选择模型

        Args:
            prompt: 提示文本
            context: 上下文信息

        Returns:
            ModelSelection模型选择结果
        """
        prompt_lower = prompt.lower()
        context_str = str(context).lower()
        combined = prompt_lower + context_str

        if any(
            word in combined
            for word in ["代码", "程序", "函数", "server", "web", "python", "javascript", "code", "algorithm"]
        ):
            return ModelSelection(model_id="gpt4o", confidence=0.9, reason="最佳匹配代码生成任务")
        elif any(word in combined for word in ["验证", "核实", "确认", "verify", "factual", "fact"]):
            return ModelSelection(model_id="claude", confidence=0.9, reason="最佳匹配事实核实任务")
        elif any(word in combined for word in ["写", "创作", "创意", "write", "creative", "story"]):
            return ModelSelection(model_id="minimax", confidence=0.85, reason="最佳匹配创意写作任务")
        else:
            return ModelSelection(model_id="gpt4o", confidence=0.7, reason="默认模型选择")

    def get_available_models(self) -> list[str]:
        """获取可用模型列表

        Returns:
            可用模型ID列表
        """
        return list(self.model_registry.keys())
