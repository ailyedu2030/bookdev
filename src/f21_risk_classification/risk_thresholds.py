"""
F21: 风险分级复核系统 - 风险阈值配置

定义风险等级及其阈值
"""

from typing import Dict, Any


RISK_LEVELS: Dict[str, Dict[str, Any]] = {
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
    if 0.0 <= score <= 0.3:
        return "CRITICAL"
    elif 0.31 <= score <= 0.6:
        return "HIGH"
    elif 0.61 <= score <= 0.8:
        return "MEDIUM"
    elif 0.81 <= score <= 1.0:
        return "LOW"
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
