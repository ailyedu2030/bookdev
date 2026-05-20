"""
F21: 风险分级复核系统 - 审核调度器

管理审核任务的调度和状态跟踪
"""

import random
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from f21_risk_classification.risk_thresholds import RISK_LEVELS


class ReviewStatus(Enum):
    """审核状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReviewPriority(Enum):
    """审核优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ReviewTask:
    """审核任务"""
    task_id: str
    content_id: str
    risk_level: str
    content_hash: str
    status: ReviewStatus
    priority: int
    created_at: datetime
    due_date: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    reviewer_id: Optional[str] = None
    comments: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = ReviewStatus(self.status)


class ReviewScheduler:
    """审核调度器"""

    # 复核截止时间配置（小时）
    REVIEW_DEADLINE_HOURS = {
        "CRITICAL": 24,
        "HIGH": 72,
        "MEDIUM": 168,  # 1周
        "LOW": 336      # 2周
    }

    # 优先级映射
    PRIORITY_MAP = {
        "CRITICAL": ReviewPriority.CRITICAL.value,
        "HIGH": ReviewPriority.HIGH.value,
        "MEDIUM": ReviewPriority.MEDIUM.value,
        "LOW": ReviewPriority.LOW.value
    }

    def __init__(self, seed: Optional[int] = None):
        """
        初始化审核调度器

        Args:
            seed: 随机种子（用于测试）
        """
        self._tasks: Dict[str, ReviewTask] = {}
        if seed is not None:
            random.seed(seed)

    def requires_review(self, risk_level: str) -> bool:
        """
        判断风险等级是否需要审核

        Args:
            risk_level: 风险等级

        Returns:
            是否需要审核
        """
        if risk_level not in RISK_LEVELS:
            return True

        config = RISK_LEVELS[risk_level]

        # 如果复核比例为1.0或0.5等明确值
        review_ratio = config["review_ratio"]

        if review_ratio >= 1.0:
            return True
        if review_ratio <= 0.0:
            return False

        # 概率性复核
        return random.random() < review_ratio

    def schedule_review(
        self,
        content_id: str,
        risk_level: str,
        content_hash: str
    ) -> ReviewTask:
        """
        调度审核任务

        Args:
            content_id: 内容ID
            risk_level: 风险等级
            content_hash: 内容哈希

        Returns:
            创建的审核任务
        """
        task_id = str(uuid.uuid4())
        created_at = datetime.utcnow()

        # 计算截止时间
        deadline_hours = self.REVIEW_DEADLINE_HOURS.get(
            risk_level,
            self.REVIEW_DEADLINE_HOURS["MEDIUM"]
        )
        due_date = created_at + timedelta(hours=deadline_hours)

        # 获取优先级
        priority = self.PRIORITY_MAP.get(
            risk_level,
            ReviewPriority.MEDIUM.value
        )

        task = ReviewTask(
            task_id=task_id,
            content_id=content_id,
            risk_level=risk_level,
            content_hash=content_hash,
            status=ReviewStatus.PENDING,
            priority=priority,
            created_at=created_at,
            due_date=due_date
        )

        self._tasks[task_id] = task
        return task

    def get_pending_reviews(self) -> List[ReviewTask]:
        """
        获取待审核任务列表

        Returns:
            待审核任务列表（按优先级排序）
        """
        pending = [
            task for task in self._tasks.values()
            if task.status == ReviewStatus.PENDING
        ]
        return sorted(pending, key=lambda t: t.priority)

    def get_review_task(self, task_id: str) -> Optional[ReviewTask]:
        """
        获取审核任务

        Args:
            task_id: 任务ID

        Returns:
            审核任务，不存在返回None
        """
        return self._tasks.get(task_id)

    def complete_review(
        self,
        task_id: str,
        result: str,
        reviewer_id: str,
        comments: str = ""
    ) -> bool:
        """
        完成审核

        Args:
            task_id: 任务ID
            result: 审核结果
            reviewer_id: 审核人ID
            comments: 审核意见

        Returns:
            是否成功
        """
        task = self._tasks.get(task_id)
        if task is None:
            return False

        task.status = ReviewStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = result
        task.reviewer_id = reviewer_id
        task.comments = comments

        return True

    def cancel_review(self, task_id: str) -> bool:
        """
        取消审核

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        task = self._tasks.get(task_id)
        if task is None:
            return False

        task.status = ReviewStatus.CANCELLED
        return True

    def get_task_count(self) -> int:
        """获取任务总数"""
        return len(self._tasks)

    def get_tasks_by_status(self, status: ReviewStatus) -> List[ReviewTask]:
        """获取指定状态的任务"""
        return [
            task for task in self._tasks.values()
            if task.status == status
        ]
