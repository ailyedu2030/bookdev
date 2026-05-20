"""
质量检查活动 - 对教材内容进行多维度质量评分。

检查维度:
- 准确性 (Accuracy): 0-100
- 完整性 (Completeness): 0-100
- 可读性 (Readability): 0-100
- 教育有效性 (Pedagogical Effectiveness): 0-100
- 结构合理性 (Structure): 0-100

幂等: 相同 content_hash 返回相同评分结果
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from ..workflows.mock_client import TemporalActivity

logger = logging.getLogger(__name__)


@TemporalActivity.defn(
    name="ScoreChapterQuality",
    idempotent=True,
)
async def score_chapter_quality(
    chapter_id: str,
    content: str,
    criteria: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """对单个章节进行质量评分 (幂等)"""
    logger.info(f"[QualityCheck] Scoring chapter '{chapter_id}'")

    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    criteria = criteria or ["accuracy", "completeness", "readability", "pedagogy", "structure"]

    scores = {}
    for criterion in criteria:
        scores[criterion] = _compute_score(criterion, content)

    overall = sum(scores.values()) / len(scores) if scores else 0

    # 确定等级
    if overall >= 85:
        grade = "A"
        recommendation = "PASS - 内容质量优秀，可直接使用"
    elif overall >= 70:
        grade = "B"
        recommendation = "PASS_WITH_MINOR_REVISIONS - 建议进行小幅修改"
    elif overall >= 55:
        grade = "C"
        recommendation = "REVISION_REQUIRED - 需要较大篇幅修改"
    else:
        grade = "D"
        recommendation = "REWRITE_REQUIRED - 需要重新编写"

    result = {
        "chapter_id": chapter_id,
        "content_hash": content_hash,
        "scores": scores,
        "overall_score": round(overall, 1),
        "grade": grade,
        "recommendation": recommendation,
        "issues": _identify_issues(scores),
    }

    logger.info(f"[QualityCheck] Chapter '{chapter_id}' scored {overall:.1f} (Grade: {grade})")
    return result


@TemporalActivity.defn(
    name="BatchScoreChapters",
    idempotent=True,
)
async def batch_score_chapters(
    chapters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """批量质量评分 (幂等)"""
    logger.info(f"[QualityCheck] Batch scoring {len(chapters)} chapters")

    results = []
    for ch in chapters:
        score = await score_chapter_quality(
            chapter_id=ch.get("chapter_id", "unknown"),
            content=ch.get("content", ""),
            criteria=ch.get("criteria"),
        )
        results.append(score)

    # 计算整体统计
    if results:
        avg_score = sum(r["overall_score"] for r in results) / len(results)
        logger.info(
            f"[QualityCheck] Batch complete: {len(results)} chapters, avg score: {avg_score:.1f}"
        )

    return results


def _compute_score(criterion: str, content: str) -> float:
    """模拟评分算法 - 基于内容特征"""
    import random

    # 使用内容哈希作为种子，保证幂等性
    seed = int(hashlib.sha256(content.encode() + criterion.encode()).hexdigest()[:8], 16)
    random.seed(seed)

    # 根据不同维度计算基础分
    base_map = {
        "accuracy": random.uniform(65, 95),
        "completeness": random.uniform(60, 90),
        "readability": random.uniform(70, 98),
        "pedagogy": random.uniform(55, 88),
        "structure": random.uniform(60, 92),
    }

    base = base_map.get(criterion, 70)

    # 根据内容长度微调
    word_count = len(content.split())
    if word_count > 5000:
        adjustment = -(random.uniform(0, 5))  # 太长可能冗余
    elif word_count > 2000:
        adjustment = random.uniform(0, 5)  # 适中更好
    elif word_count > 500:
        adjustment = 0
    else:
        adjustment = -(random.uniform(0, 10))  # 太短

    score = max(0, min(100, base + adjustment))
    random.seed(None)  # 重置随机种子
    return round(score, 1)


def _identify_issues(scores: Dict[str, float]) -> List[Dict[str, str]]:
    """根据评分识别问题"""
    issues = []

    thresholds = {
        "accuracy": (70, "内容准确性不足，建议增加事实核查"),
        "completeness": (65, "内容覆盖不够完整，建议补充关键知识点"),
        "readability": (75, "可读性有待提高，建议调整语言难度和段落结构"),
        "pedagogy": (65, "教学效果不够理想，建议增加互动元素和思考题"),
        "structure": (68, "章节结构可以优化，建议调整小节组织"),
    }

    for criterion, (threshold, message) in thresholds.items():
        if scores.get(criterion, 100) < threshold:
            issues.append({
                "criterion": criterion,
                "score": scores[criterion],
                "threshold": threshold,
                "suggestion": message,
            })

    return issues


class QualityCheck:
    """质量检查活动集合"""

    @staticmethod
    async def score(chapter_id: str, content: str, **kwargs) -> Dict[str, Any]:
        return await score_chapter_quality(chapter_id, content, kwargs.get("criteria"))

    @staticmethod
    async def batch_score(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return await batch_score_chapters(chapters)
