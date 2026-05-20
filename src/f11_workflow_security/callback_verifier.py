"""
F11: 回调验证器
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib
import hmac


@dataclass
class VerificationResult:
    """验证结果"""
    is_valid: bool
    reason: str = ""
    hsm_verified: bool = False


class CallbackVerifier:
    """回调验证器"""

    def __init__(self, hsm_client=None):
        self.hsm_client = hsm_client
        self._verified_callbacks = set()

    def verify(self, callback) -> VerificationResult:
        """验证回调"""
        if not callback.signature:
            return VerificationResult(is_valid=False, reason="MISSING_SIGNATURE")

        callback_key = self._build_callback_key(callback)
        if callback_key in self._verified_callbacks:
            return VerificationResult(is_valid=False, reason="REPLAY_DETECTED")

        if not self._verify_signature(callback):
            return VerificationResult(is_valid=False, reason="INVALID_SIGNATURE")

        self._verified_callbacks.add(callback_key)
        return VerificationResult(is_valid=True, hsm_verified=True)

    def _build_callback_key(self, callback) -> str:
        """构建回调唯一键"""
        return f"{callback.workflow_id}|{callback.task_id}|{callback.content_hash}|{callback.timestamp.isoformat()}"

    def _verify_signature(self, callback) -> bool:
        """验证签名"""
        if self.hsm_client:
            payload = self._build_payload(callback)
            return self.hsm_client.verify(payload, callback.signature)

        expected_signature = self._generate_expected_signature(callback)
        return hmac.compare_digest(callback.signature, expected_signature)

    def _build_payload(self, callback) -> str:
        """构建签名字符串"""
        return f"{callback.workflow_id}|{callback.task_id}|{callback.content_hash}|{callback.reviewer_id}|{callback.timestamp.isoformat()}"

    def _generate_expected_signature(self, callback) -> str:
        """生成期望的签名"""
        payload = self._build_payload(callback)
        return hashlib.sha256(payload.encode()).hexdigest()
