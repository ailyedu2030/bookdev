"""
F11: 外部审核服务
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass
class ReviewSession:
    """审核会话"""
    session_id: str
    workflow_id: str
    task_id: str
    content: str
    reviewer_id: str
    status: str
    created_at: datetime


class ExternalReviewService:
    """外部审核服务"""

    def __init__(self, hsm_client=None):
        self.hsm_client = hsm_client
        self._sessions: Dict[str, ReviewSession] = {}

    def initiate_review(
        self,
        workflow_id: str,
        task_id: str,
        content: str,
        reviewer_id: str
    ) -> ReviewSession:
        """发起审核会话"""
        session_id = str(uuid.uuid4())
        session = ReviewSession(
            session_id=session_id,
            workflow_id=workflow_id,
            task_id=task_id,
            content=content,
            reviewer_id=reviewer_id,
            status="PENDING",
            created_at=datetime.utcnow()
        )
        self._sessions[session_id] = session
        return session

    def submit_review(
        self,
        session_id: str,
        result: str,
        comments: str = ""
    ):
        """提交审核结果"""
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._sessions[session_id]
        session.status = "COMPLETED"
        timestamp = datetime.utcnow()

        return ReviewCallback(
            workflow_id=session.workflow_id,
            task_id=session.task_id,
            content_hash=self._calculate_content_hash(session.content),
            reviewer_id=session.reviewer_id,
            result=result,
            signature=self._sign_review(session, result, timestamp),
            timestamp=timestamp
        )

    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()

    def _sign_review(self, session: ReviewSession, result: str, timestamp: datetime) -> str:
        """签名审核结果"""
        content_hash = self._calculate_content_hash(session.content)
        if self.hsm_client:
            payload = f"{session.workflow_id}|{session.task_id}|{content_hash}|{session.reviewer_id}|{timestamp.isoformat()}"
            return self.hsm_client.sign(payload)
        import hashlib
        payload = f"{session.workflow_id}|{session.task_id}|{content_hash}|{session.reviewer_id}|{timestamp.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class ReviewCallback:
    """审核回调"""
    workflow_id: str
    task_id: str
    content_hash: str
    reviewer_id: str
    result: str
    signature: str
    timestamp: datetime
