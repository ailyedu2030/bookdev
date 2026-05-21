"""
F20: LLM-as-Judge评分系统 - LLM评判服务

提供LLM评判接口和相关性计算
"""

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from f20_llm_judge.prompt_templates import PromptTemplates
from f20_llm_judge.scoring_engine import ScoringEngine


class JudgeServiceError(Exception):
    """评判服务异常"""

    pass


class JudgeStatus(Enum):
    """评判状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JudgeResult:
    """评判结果"""

    scores: dict[str, float]
    overall_score: float
    reasoning: str
    timestamp: datetime
    status: JudgeStatus = JudgeStatus.COMPLETED
    model_id: str | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scores": self.scores,
            "overall_score": self.overall_score,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "model_id": self.model_id,
            "latency_ms": self.latency_ms,
        }


class BaseLLMClient:
    """LLM客户端基类"""

    async def generate(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """模拟LLM客户端（用于测试）"""

    def __init__(self, response: str = None, should_fail: bool = False):
        self._response = response
        self._should_fail = should_fail

    async def generate(self, prompt: str, **kwargs) -> str:
        if self._should_fail:
            raise Exception("LLM API Error")

        if self._response:
            return self._response

        # 默认响应
        return json.dumps(
            {
                "scores": {
                    "terminology_consistency": 0.9,
                    "knowledge_accuracy": 0.85,
                    "citation_validity": 0.8,
                    "logical_coherence": 0.9,
                    "format_compliance": 0.95,
                },
                "overall_score": 0.88,
                "reasoning": "内容质量良好",
            }
        )


class JudgeService:
    """LLM评判服务"""

    def __init__(
        self,
        llm_client: BaseLLMClient | None = None,
        scoring_engine: ScoringEngine | None = None,
        prompt_templates: PromptTemplates | None = None,
    ):
        """
        初始化评判服务

        Args:
            llm_client: LLM客户端
            scoring_engine: 评分引擎
            prompt_templates: 提示模板
        """
        self._llm_client = llm_client or MockLLMClient()
        self._scoring_engine = scoring_engine or ScoringEngine()
        self._prompt_templates = prompt_templates or PromptTemplates()

    async def judge_content(self, content: str, rubric: dict[str, Any] = None, **kwargs) -> JudgeResult:
        """
        评判内容质量

        Args:
            content: 待评判的内容
            rubric: 评分标准（可选）
            **kwargs: 额外参数

        Returns:
            评判结果

        Raises:
            JudgeServiceError: 评判失败时
            ValueError: 内容为空时
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        try:
            # 构建提示
            prompt = self._prompt_templates.build_judge_prompt(content, rubric)

            # 调用LLM
            response = await self._llm_client.generate(prompt, **kwargs)

            # 解析响应
            result = self._parse_llm_response(response)

            return result

        except json.JSONDecodeError as e:
            raise JudgeServiceError(f"Failed to parse LLM response: {e}")
        except Exception as e:
            raise JudgeServiceError(f"Judge service error: {e}")

    async def batch_judge(self, contents: list[str], rubric: dict[str, Any] = None, **kwargs) -> list[JudgeResult]:
        """
        批量评判内容

        Args:
            contents: 内容列表
            rubric: 评分标准
            **kwargs: 额外参数

        Returns:
            评判结果列表
        """
        results = []
        for content in contents:
            try:
                result = await self.judge_content(content, rubric, **kwargs)
                results.append(result)
            except JudgeServiceError:
                # 跳过失败的内容
                continue
        return results

    def _parse_llm_response(self, response: str) -> JudgeResult:
        """
        解析LLM响应

        Args:
            response: LLM原始响应

        Returns:
            评判结果

        Raises:
            JudgeServiceError: 解析失败时
        """
        # 尝试提取JSON - 使用更健壮的方法
        json_str = self._extract_json(response)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            raise JudgeServiceError(f"Invalid JSON in response: {response[:200]}")

        # 验证必需字段
        if "scores" not in data:
            raise JudgeServiceError("Response missing 'scores' field")

        if "overall_score" not in data:
            raise JudgeServiceError("Response missing 'overall_score' field")

        scores = data["scores"]
        overall_score = data["overall_score"]
        reasoning = data.get("reasoning", "")

        return JudgeResult(
            scores=scores,
            overall_score=overall_score,
            reasoning=reasoning,
            timestamp=datetime.utcnow(),
            status=JudgeStatus.COMPLETED,
        )

    def _extract_json(self, response: str) -> str:
        """
        从响应中提取JSON，使用更健壮的方法处理嵌套JSON

        Args:
            response: LLM原始响应

        Returns:
            提取的JSON字符串
        """
        # 方法1: 尝试直接解析（最简单的情况）
        response = response.strip()
        if response.startswith("{") and response.endswith("}"):
            try:
                json.loads(response)
                return response
            except json.JSONDecodeError:
                pass

        # 方法2: 使用括号匹配提取最外层JSON
        start_idx = response.find("{")
        if start_idx != -1:
            # 找到第一个 {
            depth = 0
            for i in range(start_idx, len(response)):
                if response[i] == "{":
                    depth += 1
                elif response[i] == "}":
                    depth -= 1
                    if depth == 0:
                        return response[start_idx : i + 1]

        # 方法3: 尝试用正则找JSON（处理多行嵌套情况）
        # 匹配以 { 开头，scores 字段存在的内容
        json_pattern = r'\{(?:[^{}]|"(?:[^"\\]|\\.)*")*\}'
        for match in re.finditer(json_pattern, response, re.DOTALL):
            candidate = match.group(0)
            if '"scores"' in candidate and '"overall_score"' in candidate:
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue

        # 如果都失败，返回原响应让调用者处理
        return response


def calculate_correlation(llm_scores: list[float], human_scores: list[float]) -> float:
    """
    计算LLM评分与人工评分的相关性

    使用皮尔逊相关系数

    Args:
        llm_scores: LLM评分列表
        human_scores: 人工评分列表

    Returns:
        相关系数 (-1 到 1)，单样本时返回NaN
    """
    if len(llm_scores) != len(human_scores):
        raise ValueError("Score lists must have the same length")

    # QC-004 Fix: 单样本时返回NaN，数学上相关系数是未定义的
    if len(llm_scores) < 2:
        return math.nan

    n = len(llm_scores)

    # 计算均值
    llm_mean = sum(llm_scores) / n
    human_mean = sum(human_scores) / n

    # 计算协方差（sum of deviations products）
    covariance = sum((llm_scores[i] - llm_mean) * (human_scores[i] - human_mean) for i in range(n))

    # 计算标准差
    llm_std = (sum((x - llm_mean) ** 2 for x in llm_scores) / n) ** 0.5
    human_std = (sum((x - human_mean) ** 2 for x in human_scores) / n) ** 0.5

    if llm_std == 0 or human_std == 0:
        return 0.0

    # QC-001 Fix: 协方差已经是sum/n，不需要再除n
    # 皮尔逊相关系数 = covariance / (std_llm * std_human)
    correlation = covariance / (llm_std * human_std)

    return correlation
