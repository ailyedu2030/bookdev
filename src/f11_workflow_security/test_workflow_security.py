"""
F11: 工作流安全(HUMAN_TASK) - TDD测试文件
P0漏洞: W-001 状态机绕过-审核节点跳过

安全机制:
1. 直接Signal阻断
2. 回调签名验证
3. content_hash验证
4. 时间戳验证
"""

from datetime import datetime, timedelta

import pytest


class TestWorkflowSecurity:
    """工作流安全测试套件"""

    def test_direct_signal_blocked(self):
        """F11-T001: 直接Signal调用被阻断"""
        from f11_workflow_security.workflow_security_manager import SecurityException, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        with pytest.raises(SecurityException) as exc_info:
            security.receive_signal(
                signal_type="SubmitOutlineReview", direct_call=True, workflow_id="wf-001", task_id="task-001"
            )

        assert "DIRECT_SIGNAL_BLOCKED" in str(exc_info.value)

    def test_callback_without_signature_rejected(self):
        """F11-T002: 缺少签名的回调被拒绝"""
        from f11_workflow_security.workflow_security_manager import (
            ReviewCallback,
            SecurityException,
            WorkflowSecurityManager,
        )

        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=None,
            timestamp=datetime.utcnow(),
        )

        with pytest.raises(SecurityException) as exc_info:
            security.verify_callback(callback)

        assert "MISSING_SIGNATURE" in str(exc_info.value)

    def test_callback_with_invalid_signature_rejected(self):
        """F11-T003: 无效签名的回调被拒绝"""
        from f11_workflow_security.workflow_security_manager import (
            ReviewCallback,
            WorkflowSecurityManager,
        )

        security = WorkflowSecurityManager()

        security.register_workflow("wf-001", {"content": "test"})

        now = datetime.utcnow()
        security._generate_signature("wf-001", "task-001", "abc123", "reviewer-001", now)

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature="invalid_signature",
            timestamp=now,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is False
        assert "INVALID_SIGNATURE" in result.reason

    def test_callback_content_hash_mismatch_rejected(self):
        """F11-T004: 内容哈希不匹配的回调被拒绝"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        security.register_workflow("wf-001", {"content": "original content"})

        now = datetime.utcnow()
        valid_sig = security._generate_signature("wf-001", "task-001", "wrong_hash", "reviewer-001", now)

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="wrong_hash",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_sig,
            timestamp=now,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is False
        assert "HASH_MISMATCH" in result.reason

    def test_callback_timestamp_too_old_rejected(self):
        """F11-T005: 时间戳过旧的回调被拒绝"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        content = {"content": "content for timestamp test"}
        content_hash = security.calculate_content_hash(content)

        security.register_workflow("wf-timestamp", content)

        old_timestamp = datetime.utcnow() - timedelta(minutes=10)
        valid_sig = security._generate_signature(
            "wf-timestamp", "task-001", content_hash, "reviewer-001", old_timestamp
        )

        callback = ReviewCallback(
            workflow_id="wf-timestamp",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_sig,
            timestamp=old_timestamp,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is False
        assert "TIMESTAMP_TOO_OLD" in result.reason

    def test_callback_workflow_not_found_rejected(self):
        """F11-T006: workflow_id不存在时回调被拒绝"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        callback = ReviewCallback(
            workflow_id="nonexistent-wf",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature="valid_signature",
            timestamp=datetime.utcnow(),
        )

        result = security.verify_callback(callback)
        assert result.is_valid is False
        assert "WORKFLOW_NOT_FOUND" in result.reason

    def test_valid_callback_accepted(self):
        """F11-T007: 合法回调被接受"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        content = {"content": "test content for review"}
        content_hash = security.calculate_content_hash(content)

        security.register_workflow("wf-001", content)

        now = datetime.utcnow()
        valid_signature = security._generate_signature("wf-001", "task-001", content_hash, "reviewer-001", now)

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_signature,
            timestamp=now,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is True

    def test_callback_signature_verification_with_hsm(self):
        """F11-T008: 使用HSM进行回调签名验证"""
        from f11_workflow_security.hsm_client import MockHSMClient
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager(hsm_client=MockHSMClient())

        content = {"content": "HSM signed content"}
        content_hash = security.calculate_content_hash(content)

        security.register_workflow("wf-002", content)

        now = datetime.utcnow()
        hsm_client = security.hsm_client
        payload = f"wf-002|task-001|{content_hash}|reviewer-001|{now.isoformat()}"
        hsm_signature = hsm_client.sign(payload)

        callback = ReviewCallback(
            workflow_id="wf-002",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=hsm_signature,
            timestamp=now,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is True
        assert result.hsm_verified is True

    def test_replay_attack_detection(self):
        """F11-T009: 重放攻击检测"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        content = {"content": "replay test content"}
        content_hash = security.calculate_content_hash(content)

        security.register_workflow("wf-003", content)

        now = datetime.utcnow()
        valid_sig = security._generate_signature("wf-003", "task-001", content_hash, "reviewer-001", now)

        callback = ReviewCallback(
            workflow_id="wf-003",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_sig,
            timestamp=now,
        )

        result1 = security.verify_callback(callback)
        assert result1.is_valid is True

        callback2 = ReviewCallback(
            workflow_id="wf-003",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_sig,
            timestamp=now,
        )

        result2 = security.verify_callback(callback2)
        assert result2.is_valid is False
        assert "REPLAY_DETECTED" in result2.reason

    def test_callback_verifier_external_service_integration(self):
        """F11-T010: 外部审核服务集成验证"""
        from f11_workflow_security.callback_verifier import CallbackVerifier
        from f11_workflow_security.external_review_service import ExternalReviewService

        verifier = CallbackVerifier()
        external_service = ExternalReviewService()

        session = external_service.initiate_review(
            workflow_id="wf-010", task_id="task-001", content="Review content", reviewer_id="reviewer-001"
        )

        assert session.workflow_id == "wf-010"
        assert session.status == "PENDING"

        callback = external_service.submit_review(
            session_id=session.session_id, result="APPROVED", comments="Looks good"
        )

        result = verifier.verify(callback)
        assert result.is_valid is True

    def test_multiple_reviewers_multi_approval(self):
        """F11-T011: 多重审批验证"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager(require_multi_approval=True)

        content = {"content": "Multi-approval content"}
        content_hash = security.calculate_content_hash(content)

        security.register_workflow("wf-multi", content)

        now = datetime.utcnow()
        reviewer1_sig = security._generate_signature("wf-multi", "task-001", content_hash, "reviewer-001", now)
        reviewer2_sig = security._generate_signature("wf-multi", "task-001", content_hash, "reviewer-002", now)

        callback1 = ReviewCallback(
            workflow_id="wf-multi",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=reviewer1_sig,
            timestamp=now,
        )

        result1 = security.verify_callback(callback1)
        assert result1.is_valid is True
        assert result1.approval_count == 1

        callback2 = ReviewCallback(
            workflow_id="wf-multi",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-002",
            result="APPROVED",
            signature=reviewer2_sig,
            timestamp=now,
        )

        result2 = security.verify_callback(callback2)
        assert result2.is_valid is True
        assert result2.approval_count == 2
        assert result2.multi_approval_complete is True

    def test_signal_whitelist_only(self):
        """F11-T012: 仅允许白名单中的Signal"""
        from f11_workflow_security.workflow_security_manager import SecurityException, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        with pytest.raises(SecurityException):
            security.receive_signal(
                signal_type="SubmitOutlineReview", direct_call=True, workflow_id="wf-001", task_id="task-001"
            )

        result = security.receive_signal(
            signal_type="PauseWorkflow", direct_call=True, workflow_id="wf-001", task_id="task-001"
        )
        assert result.is_valid is True

    def test_callback_content_hash_calculation(self):
        """F11-T013: 内容哈希计算验证"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        content = {"text": "Test content", "metadata": {"author": "test"}}
        content_hash = security.calculate_content_hash(content)

        security.register_workflow("wf-hash", content)

        now = datetime.utcnow()
        valid_sig = security._generate_signature("wf-hash", "task-001", content_hash, "reviewer-001", now)

        callback = ReviewCallback(
            workflow_id="wf-hash",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_sig,
            timestamp=now,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is True

    def test_workflow_state_advance_after_valid_callback(self):
        """F11-T014: 有效回调后工作流状态推进"""
        from f11_workflow_security.workflow_security_manager import ReviewCallback, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        content = {"content": "State advance test"}
        content_hash = security.calculate_content_hash(content)

        workflow_id = "wf-state"
        security.register_workflow(workflow_id, content)

        initial_state = security.get_workflow_state(workflow_id)
        assert initial_state == "OUTLINE_REVIEW"

        now = datetime.utcnow()
        valid_signature = security._generate_signature(workflow_id, "task-001", content_hash, "reviewer-001", now)

        callback = ReviewCallback(
            workflow_id=workflow_id,
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=valid_signature,
            timestamp=now,
        )

        result = security.verify_callback(callback)
        assert result.is_valid is True

        security.advance_workflow_state(callback, "DRAFT")

        new_state = security.get_workflow_state(workflow_id)
        assert new_state == "DRAFT"


class TestHSMClient:
    """HSM客户端测试"""

    def test_mock_hsm_sign(self):
        """F11-T015: MockHSM签名 (covers MockHSMClient.sign)"""
        from f11_workflow_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        signature = client.sign("test_data")
        assert signature.startswith("hsm_signature_")
        assert len(signature) > len("hsm_signature_")

    def test_mock_hsm_verify_valid_pattern(self):
        """F11-T016: MockHSM验证合法签名 (covers lines 43-45)"""
        from f11_workflow_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        data = "hello_world"
        signature = client.sign(data)
        assert client.verify(data, signature) is True

    def test_mock_hsm_verify_valid_signature_string(self):
        """F11-T017: MockHSM验证valid_signature字符串 (covers lines 46-47)"""
        from f11_workflow_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.verify("any_data", "valid_signature") is True

    def test_mock_hsm_verify_hsm_signature_string(self):
        """F11-T018: MockHSM验证hsm_signature字符串 (covers lines 48-49)"""
        from f11_workflow_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.verify("any_data", "hsm_signature") is True

    def test_mock_hsm_verify_invalid_signature(self):
        """F11-T019: MockHSM拒绝无效签名 (covers line 50)"""
        from f11_workflow_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.verify("data", "invalid_signature_xyz") is False
        assert client.verify("data", "") is False

    def test_mock_hsm_get_public_key_pem(self):
        """F11-T020: MockHSM获取公钥 (covers line 54)"""
        from f11_workflow_security.hsm_client import MockHSMClient

        client = MockHSMClient()
        assert client.get_public_key_pem() == "mock_public_key_for_testing"


class TestCallbackVerifierUncovered:
    """覆盖CallbackVerifier未测试的分支"""

    def test_verify_missing_signature(self):
        """verify处理缺失签名 (覆盖line 30)"""
        from datetime import datetime

        from f11_workflow_security.callback_verifier import CallbackVerifier
        from f11_workflow_security.external_review_service import ReviewCallback

        verifier = CallbackVerifier()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature="",  # empty signature
            timestamp=datetime.utcnow(),
        )

        result = verifier.verify(callback)
        assert result.is_valid is False
        assert "MISSING_SIGNATURE" in result.reason

    def test_verify_replay_detected(self):
        """verify处理重放攻击 (覆盖line 34)"""
        import hashlib
        from datetime import datetime

        from f11_workflow_security.callback_verifier import CallbackVerifier
        from f11_workflow_security.external_review_service import ReviewCallback

        verifier = CallbackVerifier()

        now = datetime.utcnow()
        content_hash = "abc123"
        reviewer_id = "reviewer-001"
        payload = f"wf-001|task-001|{content_hash}|{reviewer_id}|{now.isoformat()}"
        valid_signature = hashlib.sha256(payload.encode()).hexdigest()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id=reviewer_id,
            result="APPROVED",
            signature=valid_signature,
            timestamp=now,
        )

        result1 = verifier.verify(callback)
        assert result1.is_valid is True

        callback2 = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash=content_hash,
            reviewer_id=reviewer_id,
            result="APPROVED",
            signature=valid_signature,
            timestamp=now,
        )
        result2 = verifier.verify(callback2)
        assert result2.is_valid is False
        assert "REPLAY_DETECTED" in result2.reason

    def test_verify_invalid_signature(self):
        """verify处理无效签名 (覆盖line 37)"""
        from datetime import datetime

        from f11_workflow_security.callback_verifier import CallbackVerifier
        from f11_workflow_security.external_review_service import ReviewCallback

        verifier = CallbackVerifier()

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature="wrong_signature",
            timestamp=datetime.utcnow(),
        )

        result = verifier.verify(callback)
        assert result.is_valid is False
        assert "INVALID_SIGNATURE" in result.reason

    def test_verify_with_hsm_client(self):
        """verify使用HSM客户端验证 (覆盖lines 49-50)"""
        from datetime import datetime

        from f11_workflow_security.callback_verifier import CallbackVerifier
        from f11_workflow_security.external_review_service import ReviewCallback
        from f11_workflow_security.hsm_client import MockHSMClient

        hsm = MockHSMClient()
        verifier = CallbackVerifier(hsm_client=hsm)

        now = datetime.utcnow()
        payload = f"wf-001|task-001|abc123|reviewer-001|{now.isoformat()}"
        hsm_signature = hsm.sign(payload)

        callback = ReviewCallback(
            workflow_id="wf-001",
            task_id="task-001",
            content_hash="abc123",
            reviewer_id="reviewer-001",
            result="APPROVED",
            signature=hsm_signature,
            timestamp=now,
        )

        result = verifier.verify(callback)
        assert result.is_valid is True
        assert result.hsm_verified is True

    def test_get_workflow_state_not_found(self):
        """get_workflow_state处理不存在的workflow (覆盖line 82)"""
        from f11_workflow_security.workflow_security_manager import SecurityException, WorkflowSecurityManager

        security = WorkflowSecurityManager()

        with pytest.raises(SecurityException) as exc_info:
            security.get_workflow_state("nonexistent-workflow")

        assert "WORKFLOW_NOT_FOUND" in str(exc_info.value)


class TestExternalReviewServiceUncovered:
    """覆盖ExternalReviewService未测试的分支"""

    def test_submit_review_session_not_found(self):
        """submit_review处理不存在的session (覆盖line 59)"""
        from f11_workflow_security.external_review_service import ExternalReviewService

        service = ExternalReviewService()

        with pytest.raises(ValueError, match="Session .* not found"):
            service.submit_review(session_id="nonexistent-session", result="APPROVED")

    def test_sign_review_with_hsm_client(self):
        """_sign_review使用HSM客户端签名 (覆盖lines 84-85)"""
        from datetime import datetime

        from f11_workflow_security.external_review_service import ExternalReviewService, ReviewSession
        from f11_workflow_security.hsm_client import MockHSMClient

        hsm_client = MockHSMClient()
        service = ExternalReviewService(hsm_client=hsm_client)

        session = ReviewSession(
            session_id="test-session",
            workflow_id="wf-001",
            task_id="task-001",
            content="Test content",
            reviewer_id="reviewer-001",
            status="PENDING",
            created_at=datetime.utcnow(),
        )

        signature = service._sign_review(session, "APPROVED", datetime.utcnow())

        assert signature.startswith("hsm_signature_")

    def test_sign_review_without_hsm_client(self):
        """_sign_review不使用HSM时使用hashlib (覆盖lines 87-88)"""
        from datetime import datetime

        from f11_workflow_security.external_review_service import ExternalReviewService, ReviewSession

        service = ExternalReviewService(hsm_client=None)

        session = ReviewSession(
            session_id="test-session",
            workflow_id="wf-001",
            task_id="task-001",
            content="Test content",
            reviewer_id="reviewer-001",
            status="PENDING",
            created_at=datetime.utcnow(),
        )

        signature = service._sign_review(session, "APPROVED", datetime.utcnow())

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest length
