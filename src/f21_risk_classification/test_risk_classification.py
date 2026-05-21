"""
F21: 风险分级复核系统 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。
按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量

验收标准:
- 风险分级正确
- 单元测试覆盖率 ≥84%
"""

from datetime import datetime, timedelta

import pytest

RISK_LEVELS = {
    "CRITICAL": {"score_range": [0, 0.3], "review_ratio": 1.0, "auto_approve": False},
    "HIGH": {"score_range": [0.3, 0.6], "review_ratio": 0.5, "auto_approve": False},
    "MEDIUM": {"score_range": [0.6, 0.8], "review_ratio": 0.1, "auto_approve": True},
    "LOW": {"score_range": [0.8, 1.0], "review_ratio": 0.0, "auto_approve": True},
}


class TestRiskLevels:
    """风险等级定义测试"""

    def test_risk_levels_defined(self):
        """F21-T001: 风险等级必须正确定义"""
        from f21_risk_classification.risk_thresholds import RISK_LEVELS

        assert "CRITICAL" in RISK_LEVELS
        assert "HIGH" in RISK_LEVELS
        assert "MEDIUM" in RISK_LEVELS
        assert "LOW" in RISK_LEVELS

    def test_risk_levels_have_score_ranges(self):
        """F21-T002: 每个风险等级必须有分数范围"""
        from f21_risk_classification.risk_thresholds import RISK_LEVELS

        for _level, config in RISK_LEVELS.items():
            assert "score_range" in config
            assert len(config["score_range"]) == 2
            assert config["score_range"][0] < config["score_range"][1]

    def test_risk_levels_cover_full_range(self):
        """F21-T003: 风险等级覆盖0-1全范围"""
        from f21_risk_classification.risk_thresholds import RISK_LEVELS

        all_ranges = [(level, config["score_range"]) for level, config in RISK_LEVELS.items()]
        sorted_ranges = sorted(all_ranges, key=lambda x: x[1][0])

        assert sorted_ranges[0][1][0] == 0
        assert sorted_ranges[-1][1][1] == 1.0

    def test_review_ratios_valid(self):
        """F21-T004: 复核比例必须在0-1之间"""
        from f21_risk_classification.risk_thresholds import RISK_LEVELS

        for level, config in RISK_LEVELS.items():
            assert "review_ratio" in config
            ratio = config["review_ratio"]
            assert 0.0 <= ratio <= 1.0, f"{level} review_ratio {ratio} invalid"

    def test_auto_approve_boolean(self):
        """F21-T005: auto_approve必须是布尔值"""
        from f21_risk_classification.risk_thresholds import RISK_LEVELS

        for _level, config in RISK_LEVELS.items():
            assert "auto_approve" in config
            assert isinstance(config["auto_approve"], bool)

    def test_get_risk_level_for_score_gap(self):
        """F21-T005a: 分数在间隙时返回默认CRITICAL"""
        from f21_risk_classification.risk_thresholds import get_risk_level_for_score

        assert get_risk_level_for_score(0.301) == "CRITICAL"
        assert get_risk_level_for_score(0.605) == "CRITICAL"
        assert get_risk_level_for_score(0.805) == "CRITICAL"

    def test_get_review_ratio_for_invalid_level(self):
        """F21-T005b: 获取无效风险等级的复核比例"""
        from f21_risk_classification.risk_thresholds import get_review_ratio_for_level

        assert get_review_ratio_for_level("INVALID_LEVEL") == 1.0

    def test_is_auto_approvable_invalid_level(self):
        """F21-T005c: 判断无效风险等级是否可自动批准"""
        from f21_risk_classification.risk_thresholds import is_auto_approvable

        assert is_auto_approvable("INVALID_LEVEL") is False

    def test_get_review_ratio_for_valid_levels(self):
        """F21-T005d: 获取各有效等级的复核比例"""
        from f21_risk_classification.risk_thresholds import get_review_ratio_for_level

        assert get_review_ratio_for_level("CRITICAL") == 1.0
        assert get_review_ratio_for_level("HIGH") == 0.5
        assert get_review_ratio_for_level("MEDIUM") == 0.1
        assert get_review_ratio_for_level("LOW") == 0.0

    def test_is_auto_approvable_valid_levels(self):
        """F21-T005e: 判断各有效等级是否可自动批准"""
        from f21_risk_classification.risk_thresholds import is_auto_approvable

        assert is_auto_approvable("CRITICAL") is False
        assert is_auto_approvable("HIGH") is False
        assert is_auto_approvable("MEDIUM") is True
        assert is_auto_approvable("LOW") is True


class TestRiskClassifier:
    """风险分级器测试"""

    def test_classify_critical_risk(self):
        """F21-T010: 0-0.3分数应分类为CRITICAL"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.classify(0.0) == "CRITICAL"
        assert classifier.classify(0.15) == "CRITICAL"
        assert classifier.classify(0.3) == "CRITICAL"

    def test_classify_high_risk(self):
        """F21-T011: 0.3-0.6分数应分类为HIGH"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.classify(0.31) == "HIGH"
        assert classifier.classify(0.45) == "HIGH"
        assert classifier.classify(0.6) == "HIGH"

    def test_classify_medium_risk(self):
        """F21-T012: 0.6-0.8分数应分类为MEDIUM"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.classify(0.61) == "MEDIUM"
        assert classifier.classify(0.7) == "MEDIUM"
        assert classifier.classify(0.8) == "MEDIUM"

    def test_classify_low_risk(self):
        """F21-T013: 0.8-1.0分数应分类为LOW"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.classify(0.81) == "LOW"
        assert classifier.classify(0.9) == "LOW"
        assert classifier.classify(1.0) == "LOW"

    def test_classify_boundary_0_3(self):
        """F21-T014: 边界值0.3正确分类"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        # 0.3应该是CRITICAL（范围[0, 0.3]）
        assert classifier.classify(0.3) == "CRITICAL"

    def test_classify_boundary_0_6(self):
        """F21-T015: 边界值0.6正确分类"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        # 0.6应该是HIGH（范围[0.3, 0.6]）
        assert classifier.classify(0.6) == "HIGH"

    def test_classify_boundary_0_8(self):
        """F21-T016: 边界值0.8正确分类"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        # 0.8应该是MEDIUM（范围[0.6, 0.8]）
        assert classifier.classify(0.8) == "MEDIUM"

    def test_classify_invalid_score_raises(self):
        """F21-T017: 无效分数抛出异常"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        with pytest.raises(ValueError):
            classifier.classify(-0.1)

        with pytest.raises(ValueError):
            classifier.classify(1.1)

    def test_get_review_ratio(self):
        """F21-T018: 获取复核比例"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.get_review_ratio("CRITICAL") == 1.0
        assert classifier.get_review_ratio("HIGH") == 0.5
        assert classifier.get_review_ratio("MEDIUM") == 0.1
        assert classifier.get_review_ratio("LOW") == 0.0

    def test_get_review_ratio_invalid_level(self):
        """F21-T019: 无效风险等级返回None"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.get_review_ratio("INVALID") is None

    def test_is_auto_approvable(self):
        """F21-T020: 检查是否可自动批准"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.is_auto_approvable("CRITICAL") is False
        assert classifier.is_auto_approvable("HIGH") is False
        assert classifier.is_auto_approvable("MEDIUM") is True
        assert classifier.is_auto_approvable("LOW") is True

    def test_classify_with_metadata(self):
        """F21-T021: 带元数据的分类"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        result = classifier.classify_with_metadata(0.75)

        assert "level" in result
        assert "review_ratio" in result
        assert "auto_approve" in result
        assert result["level"] == "MEDIUM"
        assert result["review_ratio"] == 0.1
        assert result["auto_approve"] is True

    def test_get_review_ratio_for_score(self):
        """F21-T022: 根据分数获取复核比例"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.get_review_ratio_for_score(0.25) == 1.0
        assert classifier.get_review_ratio_for_score(0.5) == 0.5
        assert classifier.get_review_ratio_for_score(0.75) == 0.1
        assert classifier.get_review_ratio_for_score(0.95) == 0.0

    def test_is_auto_approvable_by_score(self):
        """F21-T023: 根据分数判断是否可自动批准"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.is_auto_approvable_by_score(0.25) is False
        assert classifier.is_auto_approvable_by_score(0.5) is False
        assert classifier.is_auto_approvable_by_score(0.75) is True
        assert classifier.is_auto_approvable_by_score(0.95) is True

    def test_get_score_range_valid(self):
        """F21-T024: 获取有效风险等级的分数范围"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        critical_range = classifier.get_score_range("CRITICAL")
        assert critical_range == (0.0, 0.3)

        low_range = classifier.get_score_range("LOW")
        assert low_range == (0.81, 1.0)

    def test_get_score_range_invalid(self):
        """F21-T025: 获取无效风险等级的分数范围"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.get_score_range("INVALID") is None

    def test_is_auto_approvable_invalid_level(self):
        """F21-T026: 判断无效等级是否可自动批准"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.is_auto_approvable("INVALID") is False

    def test_classify_with_metadata_all_levels(self):
        """F21-T027: 各等级的带元数据分类"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        result = classifier.classify_with_metadata(0.15)
        assert result["level"] == "CRITICAL"
        assert result["review_ratio"] == 1.0

        result = classifier.classify_with_metadata(0.45)
        assert result["level"] == "HIGH"
        assert result["review_ratio"] == 0.5

        result = classifier.classify_with_metadata(0.85)
        assert result["level"] == "LOW"
        assert result["review_ratio"] == 0.0

    def test_classifier_custom_risk_levels(self):
        """F21-T028: 使用自定义风险等级配置"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        custom_levels = {
            "HIGH_RISK": {"score_range": [0.0, 0.5], "review_ratio": 1.0, "auto_approve": False},
            "LOW_RISK": {"score_range": [0.51, 1.0], "review_ratio": 0.0, "auto_approve": True},
        }

        classifier = RiskClassifier(risk_levels=custom_levels)

        assert classifier.get_review_ratio("HIGH_RISK") == 1.0
        assert classifier.get_review_ratio("LOW_RISK") == 0.0
        assert classifier.get_review_ratio("UNKNOWN") is None

        score_range = classifier.get_score_range("HIGH_RISK")
        assert score_range == (0.0, 0.5)


class TestReviewScheduler:
    """审核调度器测试"""

    def test_requires_review_critical(self):
        """F21-T030: CRITICAL级别必须审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        assert scheduler.requires_review("CRITICAL") is True

    def test_requires_review_high(self):
        """F21-T031: HIGH级别50%概率需要审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        # HIGH级别50%概率需要审核
        results = [scheduler.requires_review("HIGH") for _ in range(100)]
        true_count = sum(results)

        # 应该有大约50次返回True（50%）
        assert 30 <= true_count <= 70, f"Expected ~50 True results, got {true_count}"

    def test_requires_review_medium_probabilistic(self):
        """F21-T032: MEDIUM级别概率性审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        # MEDIUM级别10%概率需要审核
        # 多次调用应该有时返回True有时返回False
        results = [scheduler.requires_review("MEDIUM") for _ in range(100)]
        true_count = sum(results)

        # 应该有大约10次返回True（10%）
        assert 1 <= true_count <= 30, f"Expected ~10 True results, got {true_count}"

    def test_requires_review_low(self):
        """F21-T033: LOW级别不需要审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        # LOW级别0%复核
        results = [scheduler.requires_review("LOW") for _ in range(100)]
        assert all(r is False for r in results)

    def test_schedule_review(self):
        """F21-T034: 调度审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler, ReviewStatus

        scheduler = ReviewScheduler()

        review_task = scheduler.schedule_review(content_id="content-001", risk_level="HIGH", content_hash="abc123")

        assert review_task is not None
        assert review_task.content_id == "content-001"
        assert review_task.risk_level == "HIGH"
        assert review_task.content_hash == "abc123"
        assert review_task.status == ReviewStatus.PENDING

    def test_schedule_review_sets_priority(self):
        """F21-T035: 调度时设置优先级"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        critical_task = scheduler.schedule_review("c1", "CRITICAL", "hash1")
        low_task = scheduler.schedule_review("c2", "LOW", "hash2")

        # CRITICAL优先级数值小于LOW（数值越小优先级越高）
        assert critical_task.priority < low_task.priority

    def test_get_pending_reviews(self):
        """F21-T036: 获取待审核列表"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        scheduler.schedule_review("content-001", "CRITICAL", "hash1")
        scheduler.schedule_review("content-002", "HIGH", "hash2")
        scheduler.schedule_review("content-003", "LOW", "hash3")

        pending = scheduler.get_pending_reviews()

        assert len(pending) == 3

    def test_complete_review(self):
        """F21-T037: 完成审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler, ReviewStatus

        scheduler = ReviewScheduler()

        task = scheduler.schedule_review("content-001", "HIGH", "hash1")

        completed = scheduler.complete_review(
            task_id=task.task_id, result="APPROVED", reviewer_id="reviewer-001", comments="内容合格"
        )

        assert completed is True
        assert task.status == ReviewStatus.COMPLETED
        assert task.result == "APPROVED"

    def test_complete_review_not_found(self):
        """F21-T038: 完成不存在的审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        result = scheduler.complete_review(
            task_id="nonexistent-id", result="APPROVED", reviewer_id="reviewer-001", comments=""
        )

        assert result is False

    def test_review_task_has_timestamp(self):
        """F21-T039: 审核任务有时间戳"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        task = scheduler.schedule_review("content-001", "HIGH", "hash1")

        assert task.created_at is not None
        assert isinstance(task.created_at, datetime)

    def test_review_task_due_date(self):
        """F21-T040: 审核任务有到期日"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        task = scheduler.schedule_review("content-001", "CRITICAL", "hash1")

        assert task.due_date is not None
        assert isinstance(task.due_date, datetime)
        # CRITICAL应该24小时内到期
        assert task.due_date - task.created_at <= timedelta(hours=24)

    def test_get_task_count_returns_correct_number(self):
        """F21-T041: get_task_count返回任务数量 (覆盖line 232)"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        assert scheduler.get_task_count() == 0

        scheduler.schedule_review("content-001", "HIGH", "hash1")
        scheduler.schedule_review("content-002", "LOW", "hash2")

        assert scheduler.get_task_count() == 2

        scheduler.schedule_review("content-003", "MEDIUM", "hash3")

        assert scheduler.get_task_count() == 3


class TestRiskClassificationIntegration:
    """风险分级集成测试"""

    def test_full_classification_workflow(self):
        """F21-T050: 完整分类工作流"""
        from f21_risk_classification.review_scheduler import ReviewScheduler
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()
        scheduler = ReviewScheduler()

        # 模拟评分结果
        scores = [0.25, 0.55, 0.75, 0.92]
        expected_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        for score, expected_level in zip(scores, expected_levels):
            risk_level = classifier.classify(score)
            assert risk_level == expected_level

            # 如果需要审核，调度审核任务
            if scheduler.requires_review(risk_level):
                task = scheduler.schedule_review(
                    content_id=f"content-{score}", risk_level=risk_level, content_hash=f"hash-{score}"
                )
                assert task is not None

    def test_risk_level_decision_tree(self):
        """F21-T051: 风险级别决策树"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        # 决策路径验证
        test_cases = [
            (0.0, "CRITICAL", True),
            (0.15, "CRITICAL", True),
            (0.29, "CRITICAL", True),
            (0.3, "CRITICAL", True),  # 边界 - CRITICAL always requires review
            (0.31, "HIGH", True),
            (0.59, "HIGH", True),
            (0.6, "HIGH", True),  # 边界 - HIGH always requires review
            (0.61, "MEDIUM", False),  # MEDIUM auto_approvable
            (0.79, "MEDIUM", False),
            (0.8, "MEDIUM", False),  # 边界 - MEDIUM auto_approvable
            (0.81, "LOW", False),  # LOW auto_approvable
            (0.95, "LOW", False),
            (1.0, "LOW", False),
        ]

        for score, expected_level, expected_review in test_cases:
            level = classifier.classify(score)
            should_review = classifier.is_auto_approvable(level) is False

            assert level == expected_level, f"Score {score}: expected {expected_level}, got {level}"
            assert should_review == expected_review, f"Score {score}: review expected {expected_review}"


class TestReviewSchedulerUncovered:
    """覆盖ReviewScheduler和ReviewTask未测试的分支"""

    def test_review_task_string_status_conversion(self):
        """ReviewTask接受string status并转换为enum (覆盖line 51)"""
        from datetime import datetime, timedelta

        from f21_risk_classification.review_scheduler import ReviewStatus, ReviewTask

        task = ReviewTask(
            task_id="t1",
            content_id="c1",
            risk_level="HIGH",
            content_hash="h1",
            priority=1,
            status="pending",  # lowercase string to match enum value
            created_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(hours=72),
        )
        assert task.status == ReviewStatus.PENDING

    def test_scheduler_init_with_seed(self):
        """ReviewScheduler接受seed参数 (覆盖line 82)"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler(seed=42)
        assert scheduler is not None

    def test_requires_review_unknown_level(self):
        """requires_review对未知风险等级返回True (覆盖line 95)"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        assert scheduler.requires_review("UNKNOWN_LEVEL") is True

    def test_get_review_task_not_found(self):
        """get_review_task对不存在返回None (覆盖line 180)"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        result = scheduler.get_review_task("nonexistent")
        assert result is None

    def test_cancel_review_not_found(self):
        """cancel_review对不存在返回False (覆盖lines 223-225)"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        result = scheduler.cancel_review("nonexistent")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
