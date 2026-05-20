"""
F12: 审批结果安全 - TDD测试文件
P0漏洞: W-002 人工介入欺骗-审批伪装

安全机制:
1. HSM签名
2. content_hash验证
3. 重放检测
4. 多重审批
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import hashlib


class TestApprovalSecurity:
    """审批结果安全测试套件"""

    def test_approval_record_requires_signature(self):
        """F12-T001: 审批记录必须包含签名"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager,
            SecurityException
        )

        manager = ApprovalSecurityManager()

        with pytest.raises(SecurityException) as exc_info:
            manager.submit_approval(
                content_id="content-001",
                content_hash="abc123",
                reviewer_id="reviewer-001",
                result="APPROVED",
                comments="Test approval",
                signature=None
            )

        assert "MISSING_SIGNATURE" in str(exc_info.value)

    def test_hsm_signature_required(self):
        """F12-T002: 必须使用HSM签名"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager,
            ApprovalRecord
        )
        from f12_approval_security.hsm_client import MockHSMClient

        manager = ApprovalSecurityManager(hsm_client=MockHSMClient())

        record = ApprovalRecord(
            record_id="rec-001",
            content_id="content-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Test",
            signature="software_signature",
            signature_source="SOFTWARE",
            timestamp=datetime.utcnow(),
            reviewer_ip="127.0.0.1"
        )

        result = manager.verify_record(record)
        assert result.is_valid is False
        assert "HSM_REQUIRED" in result.reason

    def test_content_hash_verification_on_read(self):
        """F12-T003: 读取时验证内容哈希"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager,
            ApprovalRecord
        )

        manager = ApprovalSecurityManager()

        content = {"text": "Original content"}
        content_hash = manager.calculate_content_hash(content)

        manager.submit_approval(
            content_id="content-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Looks good",
            signature="valid_signature"
        )

        stored_record = manager.get_record("content-001")

        tampered_record = ApprovalRecord(
            record_id=stored_record.record_id,
            content_id=stored_record.content_id,
            content_hash="tampered_hash_123",
            reviewer_id=stored_record.reviewer_id,
            result=stored_record.result,
            comments=stored_record.comments,
            signature="valid_signature",
            signature_source="HSM",
            timestamp=stored_record.timestamp,
            reviewer_ip=stored_record.reviewer_ip
        )

        result = manager.verify_record(tampered_record)
        assert result.is_valid is False
        assert "CONTENT_HASH_MISMATCH" in result.reason

    def test_replay_attack_blocked(self):
        """F12-T004: 重放攻击被阻断"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager
        )

        manager = ApprovalSecurityManager()

        content_hash = "abc123"

        manager.submit_approval(
            content_id="content-replay",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="First approval",
            signature="valid_signature"
        )

        result1 = manager.verify_record(manager.get_record("content-replay"))
        assert result1.is_valid is True

        result2 = manager.verify_record(manager.get_record("content-replay"))
        assert result2.is_valid is False
        assert "REPLAY_DETECTED" in result2.reason

    def test_timestamp_validation(self):
        """F12-T005: 时间戳验证"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager,
            ApprovalRecord
        )

        manager = ApprovalSecurityManager()

        old_timestamp = datetime.utcnow() - timedelta(minutes=10)

        record = ApprovalRecord(
            record_id="rec-old",
            content_id="content-old",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Old approval",
            signature="valid_signature",
            signature_source="HSM",
            timestamp=old_timestamp,
            reviewer_ip="127.0.0.1"
        )

        manager._records["content-old"] = record

        result = manager.verify_record(record)
        assert result.is_valid is False
        assert "TIMESTAMP_TOO_OLD" in result.reason

    def test_multi_approval_required_for_high_risk(self):
        """F12-T006: 高风险内容需要多重审批"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager
        )

        manager = ApprovalSecurityManager(require_multi_approval=True)

        content_hash = "high_risk_hash"

        manager.submit_approval(
            content_id="content-high-risk",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="First approval",
            signature="valid_signature",
            is_high_risk=True
        )

        record = manager.get_record("content-high-risk")
        result = manager.verify_record(record)

        assert result.is_valid is False
        assert "MULTI_APPROVAL_REQUIRED" in result.reason

    def test_valid_approval_accepted(self):
        """F12-T007: 合法审批被接受"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager
        )

        manager = ApprovalSecurityManager()

        content = {"text": "Valid content"}
        content_hash = manager.calculate_content_hash(content)

        manager.submit_approval(
            content_id="content-valid",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Looks good",
            signature="valid_signature"
        )

        record = manager.get_record("content-valid")
        result = manager.verify_record(record)

        assert result.is_valid is True

    def test_hsm_client_verification(self):
        """F12-T008: HSM客户端验证"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager
        )
        from f12_approval_security.hsm_client import MockHSMClient

        manager = ApprovalSecurityManager(hsm_client=MockHSMClient())

        content = {"text": "HSM content"}
        content_hash = manager.calculate_content_hash(content)

        manager.submit_approval(
            content_id="content-hsm",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="HSM verified",
            signature="valid_signature"
        )

        record = manager.get_record("content-hsm")
        result = manager.verify_record(record)

        assert result.is_valid is True
        assert result.hsm_verified is True

    def test_signature_content_verification(self):
        """F12-T009: 签名内容验证"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager,
            ApprovalRecord
        )

        manager = ApprovalSecurityManager()

        record = ApprovalRecord(
            record_id="rec-001",
            content_id="content-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Test",
            signature="valid_signature",
            signature_source="HSM",
            timestamp=datetime.utcnow(),
            reviewer_ip="127.0.0.1"
        )

        signable_string = record.to_signable_string()
        assert "content-001" in signable_string
        assert "abc123" in signable_string
        assert "reviewer-001" in signable_string
        assert "APPROVED" in signable_string

    def test_approval_record_creation(self):
        """F12-T010: 审批记录创建"""
        from f12_approval_security.approval_record import ApprovalRecord

        record = ApprovalRecord.create(
            content_id="content-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Test approval"
        )

        assert record.content_id == "content-001"
        assert record.content_hash == "abc123"
        assert record.reviewer_id == "reviewer-001"
        assert record.result == "APPROVED"
        assert record.record_id is not None

    def test_record_immutability(self):
        """F12-T011: 记录不可变性"""
        from f12_approval_security.approval_record import ApprovalRecord

        record = ApprovalRecord.create(
            content_id="content-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Original"
        )

        with pytest.raises(AttributeError):
            record.result = "REJECTED"

    def test_fraud_detection_workflow(self):
        """F12-T012: 欺诈检测工作流"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager,
            SecurityException
        )

        manager = ApprovalSecurityManager()

        content_hash = "fraud_hash"

        manager.submit_approval(
            content_id="content-fraud",
            content_hash=content_hash,
            reviewer_id="unknown_reviewer",
            result="APPROVED",
            comments="Suspicious",
            signature="forged_signature"
        )

        record = manager.get_record("content-fraud")
        result = manager.verify_record(record)

        assert result.is_valid is False
        assert "INVALID_SIGNATURE" in result.reason

    def test_approval_audit_trail(self):
        """F12-T013: 审批审计追踪"""
        from f12_approval_security.approval_security_manager import (
            ApprovalSecurityManager
        )

        manager = ApprovalSecurityManager()

        content_hash = "audit_hash"

        manager.submit_approval(
            content_id="content-audit",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Audit test",
            signature="audit_signature"
        )

        audit_trail = manager.get_audit_trail("content-audit")
        assert len(audit_trail) >= 1
        assert audit_trail[0]["reviewer_id"] == "reviewer-001"


class TestHSMClient:
    """HSM客户端测试"""

    def test_mock_hsm_sign(self):
        """F12-T014: MockHSM签名 (covers line 38)"""
        from f12_approval_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        signature = client.sign("test_data")
        assert signature.startswith("hsm_signature_")
        assert len(signature) > len("hsm_signature_")

    def test_mock_hsm_verify_valid_pattern(self):
        """F12-T015: MockHSM验证合法HSM签名 (covers lines 43-44)"""
        from f12_approval_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        data = "test_content"
        signature = client.sign(data)
        assert client.verify(data, signature) is True

    def test_mock_hsm_verify_valid_signature_string(self):
        """F12-T016: MockHSM验证valid_signature (covers lines 45-46)"""
        from f12_approval_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.verify("data", "valid_signature") is True

    def test_mock_hsm_verify_software_signature_rejected(self):
        """F12-T017: MockHSM拒绝software_signature (covers lines 47-48)"""
        from f12_approval_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.verify("data", "software_signature") is False

    def test_mock_hsm_verify_invalid_signature(self):
        """F12-T018: MockHSM拒绝完全无效签名 (covers line 49)"""
        from f12_approval_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.verify("data", "random_garbage") is False
        assert client.verify("data", "") is False

    def test_mock_hsm_get_public_key_pem(self):
        """F12-T019: MockHSM获取公钥 (covers line 53)"""
        from f12_approval_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.get_public_key_pem() == "mock_public_key_for_testing"


class TestApprovalRecordUncovered:
    """覆盖ApprovalRecord未测试的分支"""

    def test_to_signable_string(self):
        """to_signable_string构建待签名字符串 (覆盖line 27)"""
        from f12_approval_security.approval_record import ApprovalRecord
        from datetime import datetime

        record = ApprovalRecord(
            record_id="rec-001",
            content_id="content-001",
            content_hash="hash123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Test",
            signature="sig123",
            signature_source="HSM",
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            reviewer_ip="192.168.1.1"
        )

        signable = record.to_signable_string()

        assert "content-001" in signable
        assert "hash123" in signable
        assert "reviewer-001" in signable
        assert "APPROVED" in signable
        assert "2025-01-15" in signable

    def test_create_generates_unique_record_id(self):
        """create生成唯一record_id (覆盖lines 52-53)"""
        from f12_approval_security.approval_security_manager import ApprovalRecord

        record1 = ApprovalRecord.create(
            content_id="content-001",
            content_hash="hash1",
            reviewer_id="reviewer-001",
            result="APPROVED",
            comments="Test 1"
        )

        record2 = ApprovalRecord.create(
            content_id="content-002",
            content_hash="hash2",
            reviewer_id="reviewer-002",
            result="REJECTED",
            comments="Test 2"
        )

        assert record1.record_id != record2.record_id
        assert len(record1.record_id) == 36
        assert len(record2.record_id) == 36


class TestApprovalSecurityManagerUncovered:
    """覆盖ApprovalSecurityManager未测试的分支"""

    def test_get_record_not_found(self):
        """get_record处理不存在的content_id (覆盖line 151)"""
        from f12_approval_security.approval_security_manager import ApprovalSecurityManager

        manager = ApprovalSecurityManager()

        with pytest.raises(ValueError, match="No record found"):
            manager.get_record("nonexistent-content-id")
