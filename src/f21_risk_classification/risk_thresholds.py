"""
F21: 风险分级复核系统 - 风险阈值配置

定义风险等级及其阈值
"""

from typing import Any

RISK_LEVELS: dict[str, dict[str, Any]] = {
    "CRITICAL": {
        "score_range": [0.0, 0.3],  # 0 <= score <= 0.3
        "review_ratio": 1.0,
        "auto_approve": False
    },
    "HIGH": {
        "score_range": [0.31, 0.6],  # 0.31 <= score <= 0.6
        "review_ratio": 0.5,
        "auto_approve": False
    },
    "MEDIUM": {
        "score_range": [0.61, 0.8],  # 0.61 <= score <= 0.8
        "review_ratio": 0.1,
        "auto_approve": True
    },
    "LOW": {
        "score_range": [0.81, 1.0],  # 0.81 <= score <= 1.0
        "review_ratio": 0.0,
        "auto_approve": True
    }
}


def get_risk_level_for_score(score: float) -> str:
    """
    根据分数获取风险等级

    Args:
        score: 质量分数 (0-1)

    Returns:
        风险等级字符串
    """
    # QC-002 Fix: 使用RISK_LEVELS动态计算边界，避免硬编码和不一致
    # 按优先级顺序检查（从高风险到低风险）
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if level in RISK_LEVELS:
            score_range = RISK_LEVELS[level]["score_range"]
            min_score, max_score = score_range
            if min_score <= score <= max_score:
                return level

    # 边界情况处理（由于RISK_LEVELS边界定义有间隙，0.301会在此被处理）
    # 如果分数不在任何范围内，默认为CRITICAL
    return "CRITICAL"


def get_review_ratio_for_level(level: str) -> float:
    """获取风险等级的复核比例"""
    if level in RISK_LEVELS:
        return RISK_LEVELS[level]["review_ratio"]
    return 1.0


def is_auto_approvable(level: str) -> bool:
    """判断风险等级是否可自动批准"""
    if level in RISK_LEVELS:
        return RISK_LEVELS[level]["auto_approve"]
    return False
