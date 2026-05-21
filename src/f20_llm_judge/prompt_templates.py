"""
F20: LLM-as-Judge评分系统 - 提示模板

包含LLM评判所需的提示模板定义
"""

from typing import Any


class PromptTemplates:
    """LLM评判提示模板"""

    JUDGE_PROMPT = """你是一个专业的教材质量评估专家。请对以下教材内容进行质量评判。

评分维度：
1. terminology_consistency (权重0.25): 术语使用与术语表的一致性
2. knowledge_accuracy (权重0.30): 知识陈述的准确性
3. citation_validity (权重0.20): 引用的有效性和完整性
4. logical_coherence (权重0.15): 论证逻辑的连贯性
5. format_compliance (权重0.10): 格式规范的遵循程度

评分标准：
- 每个维度评分范围为0.0到1.0
- 1.0表示完全符合标准
- 0.0表示完全不符合

请对以下内容进行评判：

{content}

评分标准：
{rubric}

请以JSON格式返回评判结果：
{{
    "scores": {{
        "terminology_consistency": <分数>,
        "knowledge_accuracy": <分数>,
        "citation_validity": <分数>,
        "logical_coherence": <分数>,
        "format_compliance": <分数>
    }},
    "overall_score": <综合分数>,
    "reasoning": "<评判推理说明>"
}}
"""

    @classmethod
    def build_judge_prompt(cls, content: str, rubric: dict[str, Any] = None) -> str:
        """
        构建评判提示

        Args:
            content: 待评判的教材内容
            rubric: 评分标准（可选）

        Returns:
            格式化后的评判提示
        """
        rubric_str = rubric if rubric else "默认评分标准"
        return cls.JUDGE_PROMPT.format(content=content, rubric=rubric_str)
