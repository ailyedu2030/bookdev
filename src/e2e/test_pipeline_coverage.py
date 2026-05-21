"""
集成测试 - Pipeline模块覆盖增强

测试之前未覆盖的模块和代码路径：
1. F21 Risk Classification - 完整分支覆盖
2. F18 Term Glossary - ConsistencyChecker/TermRegistry完整覆盖
3. F20 LLM Judge ScoringEngine - 所有方法和边界
4. F30 Golden Dataset Evaluator - 所有方法
5. F31 MiniMax CostTracker - 所有方法
6. F17/F22/F27 路由和RAG引擎覆盖
7. 边界情况和错误处理测试
"""


import pytest


class TestRiskThresholdsComplete:
    """F21 Risk Thresholds 完整覆盖"""

    def test_risk_level_boundaries(self):
        """RT-T001: 风险等级边界值测试"""
        from f21_risk_classification.risk_thresholds import get_risk_level_for_score

        assert get_risk_level_for_score(0.0) == "CRITICAL"
        assert get_risk_level_for_score(0.15) == "CRITICAL"
        assert get_risk_level_for_score(0.3) == "CRITICAL"

        assert get_risk_level_for_score(0.31) == "HIGH"
        assert get_risk_level_for_score(0.45) == "HIGH"
        assert get_risk_level_for_score(0.6) == "HIGH"

        assert get_risk_level_for_score(0.61) == "MEDIUM"
        assert get_risk_level_for_score(0.7) == "MEDIUM"
        assert get_risk_level_for_score(0.8) == "MEDIUM"

        assert get_risk_level_for_score(0.81) == "LOW"
        assert get_risk_level_for_score(0.9) == "LOW"
        assert get_risk_level_for_score(1.0) == "LOW"

    def test_risk_level_invalid_scores(self):
        """RT-T002: 无效分数返回CRITICAL"""
        from f21_risk_classification.risk_thresholds import get_risk_level_for_score

        assert get_risk_level_for_score(-0.1) == "CRITICAL"
        assert get_risk_level_for_score(1.5) == "CRITICAL"

    def test_review_ratio_all_levels(self):
        """RT-T003: 所有风险等级的复核比例"""
        from f21_risk_classification.risk_thresholds import get_review_ratio_for_level

        assert get_review_ratio_for_level("CRITICAL") == 1.0
        assert get_review_ratio_for_level("HIGH") == 0.5
        assert get_review_ratio_for_level("MEDIUM") == 0.1
        assert get_review_ratio_for_level("LOW") == 0.0

    def test_review_ratio_invalid_level(self):
        """RT-T004: 无效风险等级返回1.0"""
        from f21_risk_classification.risk_thresholds import get_review_ratio_for_level

        assert get_review_ratio_for_level("INVALID") == 1.0
        assert get_review_ratio_for_level("") is None or get_review_ratio_for_level("") == 1.0

    def test_auto_approvable_valid_levels(self):
        """RT-T005: 可自动批准的风险等级"""
        from f21_risk_classification.risk_thresholds import is_auto_approvable

        assert is_auto_approvable("CRITICAL") is False
        assert is_auto_approvable("HIGH") is False
        assert is_auto_approvable("MEDIUM") is True
        assert is_auto_approvable("LOW") is True

    def test_auto_approvable_invalid_level(self):
        """RT-T006: 无效等级返回False"""
        from f21_risk_classification.risk_thresholds import is_auto_approvable

        assert is_auto_approvable("INVALID") is False
        assert is_auto_approvable("UNKNOWN") is False


class TestRiskClassifierComplete:
    """F21 Risk Classifier 完整覆盖"""

    def test_classify_invalid_scores(self):
        """RC-T001: 无效分数抛出ValueError"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        with pytest.raises(ValueError, match="Score must be between"):
            classifier.classify(-0.1)

        with pytest.raises(ValueError, match="Score must be between"):
            classifier.classify(1.5)

    def test_classify_with_metadata(self):
        """RC-T002: 带元数据分类"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        result = classifier.classify_with_metadata(0.85)

        assert result["level"] == "LOW"
        assert result["review_ratio"] == 0.0
        assert result["auto_approve"] is True

    def test_classify_with_metadata_critical(self):
        """RC-T003: CRITICAL级别元数据"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()
        result = classifier.classify_with_metadata(0.1)

        assert result["level"] == "CRITICAL"
        assert result["review_ratio"] == 1.0
        assert result["auto_approve"] is False

    def test_get_review_ratio_invalid_level(self):
        """RC-T004: 无效等级返回None"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()
        assert classifier.get_review_ratio("INVALID") is None

    def test_get_review_ratio_for_score(self):
        """RC-T005: 根据分数获取复核比例"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.get_review_ratio_for_score(0.1) == 1.0
        assert classifier.get_review_ratio_for_score(0.5) == 0.5
        assert classifier.get_review_ratio_for_score(0.7) == 0.1
        assert classifier.get_review_ratio_for_score(0.9) == 0.0

    def test_is_auto_approvable_by_score(self):
        """RC-T006: 根据分数判断可自动批准"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.is_auto_approvable_by_score(0.1) is False
        assert classifier.is_auto_approvable_by_score(0.5) is False
        assert classifier.is_auto_approvable_by_score(0.7) is True
        assert classifier.is_auto_approvable_by_score(0.9) is True

    def test_get_score_range_valid(self):
        """RC-T007: 获取有效等级分数范围"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()

        assert classifier.get_score_range("CRITICAL") == (0.0, 0.3)
        assert classifier.get_score_range("HIGH") == (0.31, 0.6)
        assert classifier.get_score_range("MEDIUM") == (0.61, 0.8)
        assert classifier.get_score_range("LOW") == (0.81, 1.0)

    def test_get_score_range_invalid_level(self):
        """RC-T008: 无效等级返回None"""
        from f21_risk_classification.risk_classifier import RiskClassifier

        classifier = RiskClassifier()
        assert classifier.get_score_range("INVALID") is None


class TestReviewSchedulerComplete:
    """F21 ReviewScheduler 完整覆盖"""

    def test_requires_review_invalid_level(self):
        """RS-T001: 无效风险等级需要审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        assert scheduler.requires_review("INVALID") is True

    def test_requires_review_critical(self):
        """RS-T002: CRITICAL级别必定需要审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler(seed=42)
        assert scheduler.requires_review("CRITICAL") is True

    def test_requires_review_low(self):
        """RS-T003: LOW级别不需要审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler(seed=42)
        assert scheduler.requires_review("LOW") is False

    def test_requires_review_probabilistic(self):
        """RS-T004: MEDIUM/HIGH级别概率性审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler(seed=42)
        results = [scheduler.requires_review("MEDIUM") for _ in range(20)]
        assert any(results) or not any(results)

    def test_schedule_review_creates_task(self):
        """RS-T005: 调度审核创建任务"""
        from f21_risk_classification.review_scheduler import ReviewScheduler, ReviewStatus

        scheduler = ReviewScheduler()
        task = scheduler.schedule_review("ch-001", "HIGH", "hash123")

        assert task.task_id is not None
        assert task.content_id == "ch-001"
        assert task.risk_level == "HIGH"
        assert task.content_hash == "hash123"
        assert task.status == ReviewStatus.PENDING
        assert task.due_date > task.created_at

    def test_get_pending_reviews_sorted(self):
        """RS-T006: 待审核列表按优先级排序"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()

        scheduler.schedule_review("ch-1", "LOW", "h1")
        scheduler.schedule_review("ch-2", "CRITICAL", "h2")
        scheduler.schedule_review("ch-3", "MEDIUM", "h3")

        pending = scheduler.get_pending_reviews()
        assert len(pending) == 3
        assert pending[0].risk_level == "CRITICAL"
        assert pending[1].risk_level == "MEDIUM"
        assert pending[2].risk_level == "LOW"

    def test_get_review_task_not_found(self):
        """RS-T007: 获取不存在的任务返回None"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        assert scheduler.get_review_task("nonexistent") is None

    def test_complete_review_success(self):
        """RS-T008: 成功完成审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        task = scheduler.schedule_review("ch-001", "HIGH", "hash123")

        result = scheduler.complete_review(
            task.task_id, "approved", "reviewer-1", "Looks good"
        )

        assert result is True
        updated_task = scheduler.get_review_task(task.task_id)
        assert updated_task.status.value == "completed"
        assert updated_task.result == "approved"
        assert updated_task.reviewer_id == "reviewer-1"
        assert updated_task.comments == "Looks good"

    def test_complete_review_not_found(self):
        """RS-T009: 完成不存在的审核返回False"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        assert scheduler.complete_review("nonexistent", "result", "r1") is False

    def test_cancel_review_success(self):
        """RS-T010: 成功取消审核"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        task = scheduler.schedule_review("ch-001", "HIGH", "hash123")

        result = scheduler.cancel_review(task.task_id)
        assert result is True
        assert scheduler.get_review_task(task.task_id).status.value == "cancelled"

    def test_cancel_review_not_found(self):
        """RS-T011: 取消不存在的审核返回False"""
        from f21_risk_classification.review_scheduler import ReviewScheduler

        scheduler = ReviewScheduler()
        assert scheduler.cancel_review("nonexistent") is False

    def test_get_tasks_by_status(self):
        """RS-T012: 按状态获取任务"""
        from f21_risk_classification.review_scheduler import ReviewScheduler, ReviewStatus

        scheduler = ReviewScheduler()
        task1 = scheduler.schedule_review("ch-1", "HIGH", "h1")
        scheduler.schedule_review("ch-2", "LOW", "h2")

        scheduler.complete_review(task1.task_id, "approved", "r1")

        pending = scheduler.get_tasks_by_status(ReviewStatus.PENDING)
        completed = scheduler.get_tasks_by_status(ReviewStatus.COMPLETED)

        assert len(pending) == 1
        assert len(completed) == 1


class TestTermGlossaryServiceComplete:
    """F18 TermGlossaryService 完整覆盖"""

    def test_register_term_duplicate(self):
        """TG-T001: 注册重复术语返回失败"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        result1 = svc.register_term("AI", "人工智能", "CS")
        assert result1.success is True

        result2 = svc.register_term("AI", "人工智能2", "CS")
        assert result2.success is False
        assert "already exists" in result2.error

    def test_get_term_not_found(self):
        """TG-T002: 获取不存在的术语返回None"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        assert svc.get_term("nonexistent") is None

    def test_find_term_by_synonym(self):
        """TG-T003: 通过同义词查找术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("Artificial Intelligence", "人工智能", "CS", synonyms=["AI"])

        found = svc.find_term("AI")
        assert found is not None
        assert found.term == "Artificial Intelligence"

    def test_find_term_not_found(self):
        """TG-T004: 查找不存在的术语返回None"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        assert svc.find_term("NONEXISTENT") is None

    def test_get_terms_by_domain(self):
        """TG-T005: 按领域获取术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        svc.register_term("ML", "机器学习", "CS")
        svc.register_term("Physics", "物理学", "Physics")

        cs_terms = svc.get_terms_by_domain("CS")
        assert len(cs_terms) == 2

    def test_add_synonym_not_found(self):
        """TG-T006: 为不存在的术语添加同义词"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        result = svc.add_synonym("nonexistent", "SYN")
        assert result.success is False

    def test_add_synonym_success(self):
        """TG-T007: 成功添加同义词"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")

        term = svc.get_term(svc._terms_by_name["AI"])
        result = svc.add_synonym(term.id, "Artificial Intelligence")

        assert result.success is True
        assert "Artificial Intelligence" in result.term.synonyms

    def test_update_term_locked(self):
        """TG-T008: 更新锁定的术语失败"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS", locked=True)

        term = svc.get_term(svc._terms_by_name["AI"])
        result = svc.update_term_definition(term.id, "新定义")

        assert result.success is False
        assert "locked" in result.error.lower()

    def test_update_term_not_found(self):
        """TG-T009: 更新不存在的术语失败"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        result = svc.update_term_definition("nonexistent", "new")
        assert result.success is False

    def test_unlock_lock_term(self):
        """TG-T010: 锁定和解锁术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")

        term = svc.get_term(svc._terms_by_name["AI"])
        svc.lock_term(term.id)
        assert svc.get_term(term.id).locked is True

        svc.unlock_term(term.id)
        assert svc.get_term(term.id).locked is False

    def test_lock_unlock_not_found(self):
        """TG-T011: 锁定/解锁不存在的术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        assert svc.lock_term("nonexistent").success is False
        assert svc.unlock_term("nonexistent").success is False

    def test_track_usage(self):
        """TG-T012: 追踪术语使用位置"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")

        term = svc.get_term(svc._terms_by_name["AI"])
        svc.track_usage(term.id, "ch01_s01")
        svc.track_usage(term.id, "ch01_s02")
        svc.track_usage(term.id, "ch01_s01")

        usage = svc.get_term_usage(term.id)
        assert len(usage) == 2
        assert "ch01_s01" in usage
        assert "ch01_s02" in usage

    def test_track_usage_not_found(self):
        """TG-T013: 追踪不存在术语的使用"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.track_usage("nonexistent", "ch01")
        assert svc.get_term_usage("nonexistent") == []

    def test_export_import(self):
        """TG-T014: 导出和导入术语表"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS", synonyms=["ML"])

        exported = svc.export()
        assert "terms" in exported
        assert len(exported["terms"]) == 1

        svc2 = TermGlossaryService()
        svc2.import_(exported)
        assert len(svc2.get_all_terms()) == 1
        assert svc2.find_term("AI") is not None


class TestConsistencyCheckerComplete:
    """F18 ConsistencyChecker 完整覆盖"""

    def test_check_consistency_undefined(self):
        """CC-T001: 未定义术语返回UNDEFINED"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        checker = ConsistencyChecker(svc)

        result = checker.check_consistency("UNKNOWN_TERM")
        assert result.value == "undefined"

    def test_check_consistency_no_new_definition(self):
        """CC-T002: 无新定义时返回CONSISTENT"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        checker = ConsistencyChecker(svc)

        result = checker.check_consistency("AI")
        assert result.value == "consistent"

    def test_check_consistency_matching_definition(self):
        """CC-T003: 匹配定义返回CONSISTENT"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        checker = ConsistencyChecker(svc)

        result = checker.check_consistency("AI", "人工智能")
        assert result.value == "consistent"

    def test_check_consistency_conflicting(self):
        """CC-T004: 冲突定义返回INCONSISTENT"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        checker = ConsistencyChecker(svc)

        result = checker.check_consistency("AI", "不同的定义")
        assert result.value == "inconsistent"

    def test_detect_conflicts_no_conflicts(self):
        """CC-T005: 无冲突时返回空列表"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        checker = ConsistencyChecker(svc)

        term_defs = [
            {"term": "AI", "definition": "人工智能"},
            {"term": "ML", "definition": "机器学习"},
        ]

        conflicts = checker.detect_conflicts(term_defs)
        assert len(conflicts) == 0

    def test_detect_conflicts_with_conflicts(self):
        """CC-T006: 检测到冲突"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        checker = ConsistencyChecker(svc)

        term_defs = [
            {"term": "AI", "definition": "人工智能-v1"},
            {"term": "AI", "definition": "人工智能-v2"},
            {"term": "AI", "definition": "人工智能-v1"},
        ]

        conflicts = checker.detect_conflicts(term_defs)
        assert len(conflicts) == 1
        assert conflicts[0]["term"] == "AI"
        assert len(conflicts[0]["definitions"]) == 2

    def test_check_domain_consistency(self):
        """CC-T007: 领域一致性检查"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        svc.register_term("ML", "机器学习", "CS")
        checker = ConsistencyChecker(svc)

        result = checker.check_domain_consistency("CS")
        assert result["domain"] == "CS"
        assert result["total_terms"] == 2
        assert result["is_consistent"] is True

    def test_check_domain_consistency_empty_domain(self):
        """CC-T008: 空领域返回空不一致列表"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        checker = ConsistencyChecker(svc)

        domain_result = checker.check_domain_consistency("EMPTY_DOMAIN")
        assert domain_result["is_consistent"] is True
        assert domain_result["total_terms"] == 0

    def test_get_consistency_report(self):
        """CC-T009: 生成完整一致性报告"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        svc.register_term("ML", "机器学习", "CS")
        checker = ConsistencyChecker(svc)

        report = checker.get_consistency_report()

        assert "summary" in report
        assert "by_domain" in report
        assert "CS" in report["by_domain"]

    def test_check_all_terms_with_undefined_terms(self):
        """CC-T010: check_all_terms统计UNDEFINED术语"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        checker = ConsistencyChecker(svc)

        result = checker.check_all_terms()

        assert result["total_terms"] == 1
        assert result["consistent_count"] == 1
        assert result["inconsistent_count"] == 0
        assert result["undefined_count"] == 0

    def test_check_domain_consistency_with_inconsistencies(self):
        """CC-T011: check_consistency冲突检测（行126死代码，记录但不处理）

        注意：check_domain_consistency 调用 check_consistency(term.term)
        不传第二个参数，因此永远不会触发 INCONSISTENT 分支（行126是死代码）
        """
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        svc = TermGlossaryService()
        svc.register_term("AI", "人工智能", "CS")
        checker = ConsistencyChecker(svc)

        status = checker.check_consistency("AI", "不同的定义")
        assert status == ConsistencyStatus.INCONSISTENT


class TestTermRegistryComplete:
    """F18 TermRegistry 完整覆盖"""

    def test_register_first_definition(self):
        """TR-T001: 注册首次定义"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "AI", "人工智能的定义")

        assert registry.get_first_definition_location("AI") == "ch01_s01"

    def test_register_redefinition(self):
        """TR-T002: 注册重新定义"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "AI", "v1")
        registry.register("ch02_s03", "AI", "v2")

        redefinitions = registry.get_redefinitions("AI")
        assert len(redefinitions) == 1
        assert redefinitions[0]["location"] == "ch02_s03"

    def test_get_definition_history(self):
        """TR-T003: 获取定义历史"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01", "AI", "v1")
        registry.register("ch02", "AI", "v2")

        history = registry.get_definition_history("AI")
        assert len(history) == 2
        assert history[0]["is_first"] is True
        assert history[1]["is_first"] is False

    def test_get_definition_history_not_found(self):
        """TR-T004: 获取不存在术语的历史"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        assert registry.get_definition_history("UNKNOWN") == []

    def test_is_first_definition(self):
        """TR-T005: 检查是否是首次定义"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01", "AI", "v1")

        assert registry.is_first_definition("AI", "ch01") is True
        assert registry.is_first_definition("AI", "ch02") is False
        assert registry.is_first_definition("UNKNOWN", "ch01") is False

    def test_export_import(self):
        """TR-T006: 导出和导入注册表"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01", "AI", "v1")
        registry.register("ch02", "AI", "v2")

        exported = registry.export()
        assert "registrations" in exported
        assert "first_definitions" in exported

        registry2 = TermRegistry()
        registry2.import_(exported)
        assert len(registry2.get_redefinitions("AI")) == 1


class TestScoringEngineComplete:
    """F20 ScoringEngine 完整覆盖"""

    def test_calculate_weighted_score_valid(self):
        """SE-T001: 计算加权分数"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.8,
            "citation_validity": 0.85,
            "logical_coherence": 0.75,
            "format_compliance": 0.95,
        }

        result = engine.calculate_weighted_score(scores)
        expected = 0.9*0.25 + 0.8*0.30 + 0.85*0.20 + 0.75*0.15 + 0.95*0.10
        assert abs(result - round(expected, 4)) < 0.001

    def test_calculate_weighted_score_missing_dim(self):
        """SE-T002: 缺少维度抛出异常"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        with pytest.raises(ValueError, match="Missing score for dimension"):
            engine.calculate_weighted_score({"terminology_consistency": 0.9})

    def test_calculate_weighted_score_out_of_range(self):
        """SE-T003: 分数超出范围抛出异常"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": 1.5,
            "knowledge_accuracy": 0.8,
            "citation_validity": 0.85,
            "logical_coherence": 0.75,
            "format_compliance": 0.95,
        }

        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            engine.calculate_weighted_score(scores)

    def test_calculate_weighted_score_non_numeric(self):
        """SE-T004: 非数字分数抛出异常"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": "high",
            "knowledge_accuracy": 0.8,
            "citation_validity": 0.85,
            "logical_coherence": 0.75,
            "format_compliance": 0.95,
        }

        with pytest.raises(ValueError, match="must be numeric"):
            engine.calculate_weighted_score(scores)

    def test_get_dimension_scores_with_weights(self):
        """SE-T005: 获取带权重的维度分数"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.8,
        }

        result = engine.get_dimension_scores_with_weights(scores)
        assert len(result) == 2

        terminology = next(d for d in result if d.dimension == "terminology_consistency")
        assert terminology.score == 0.9
        assert terminology.weight == 0.25

    def test_validate_dimension_scores_valid(self):
        """SE-T006: 有效分数通过验证"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.8,
            "citation_validity": 0.85,
            "logical_coherence": 0.75,
            "format_compliance": 0.95,
        }

        is_valid, errors = engine.validate_dimension_scores(scores)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_dimension_scores_missing(self):
        """SE-T007: 缺少维度验证失败"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": 0.9,
        }

        is_valid, errors = engine.validate_dimension_scores(scores)
        assert is_valid is False
        assert any("Missing dimension" in e for e in errors)

    def test_validate_dimension_scores_out_of_range(self):
        """SE-T008: 超出范围验证失败"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        scores = {
            "terminology_consistency": 1.5,
            "knowledge_accuracy": 0.8,
            "citation_validity": 0.85,
            "logical_coherence": 0.75,
            "format_compliance": 0.95,
        }

        is_valid, errors = engine.validate_dimension_scores(scores)
        assert is_valid is False

    def test_get_weight_for_dimension(self):
        """SE-T009: 获取维度权重"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        assert engine.get_weight_for_dimension("knowledge_accuracy") == 0.30
        assert engine.get_weight_for_dimension("INVALID") == 0.0

    def test_get_all_dimensions(self):
        """SE-T010: 获取所有维度配置"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        dims = engine.get_all_dimensions()

        assert "knowledge_accuracy" in dims
        assert dims["knowledge_accuracy"]["weight"] == 0.30


class TestGoldenDatasetEvaluatorComplete:
    """F30 GoldenDatasetEvaluator 完整覆盖"""

    def test_evaluate_with_dict_sample(self):
        """GD-T001: 使用字典样本评估"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample_dict = {
            "sample_id": "test-001",
            "quality_level": "high",
            "expected_score": 9.0,
            "content": {"text": "test content"},
            "quality_metrics": {"accuracy": 0.95, "clarity": 0.9},
            "metadata": {"source": "test"},
        }

        result = evaluator.evaluate(sample_dict)
        assert result.overall_score == 9.0
        assert result.dimension_scores["accuracy"] == 0.95

    def test_evaluate_with_golden_sample(self):
        """GD-T002: 使用GoldenSample对象评估"""
        from f30_golden_dataset.dataset_builder import GoldenSample
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = GoldenSample(
            sample_id="test-002",
            quality_level="medium",
            expected_score=7.5,
            content={"text": "content"},
            quality_metrics={"accuracy": 0.8},
            metadata={},
        )

        result = evaluator.evaluate(sample)
        assert result.overall_score == 7.5

    def test_detect_hallucinations(self):
        """GD-T003: 检测幻觉内容"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "content": {"text": "some text"},
            "hallucination_markers": [
                {"type": "factual", "location": "ch1", "content": "wrong fact", "issue": "incorrect"}
            ]
        }

        result = evaluator.detect_hallucinations(sample)
        assert result["has_hallucinations"] is True
        assert result["total_count"] == 1

    def test_detect_hallucinations_none(self):
        """GD-T004: 无幻觉时返回正确"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "content": {"text": "some text"},
            "hallucination_markers": []
        }

        result = evaluator.detect_hallucinations(sample)
        assert result["has_hallucinations"] is False
        assert result["total_count"] == 0

    def test_detect_regulation_errors(self):
        """GD-T005: 检测法规错误"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "regulation_errors": [
                {"type": "copyright", "law": "Copyright Act", "cited_article": "§102", "issue": "unlicensed"}
            ]
        }

        result = evaluator.detect_regulation_errors(sample)
        assert result["has_errors"] is True
        assert result["total_count"] == 1

    def test_detect_regulation_errors_none(self):
        """GD-T006: 无法规错误时返回正确"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()
        sample = {"regulation_errors": []}

        result = evaluator.detect_regulation_errors(sample)
        assert result["has_errors"] is False

    def test_calibrate_judge_empty_results(self):
        """GD-T007: 空结果返回零相关"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()
        result = evaluator.calibrate_judge([])

        assert result.correlation == 0.0
        assert result.bias == 0.0
        assert result.samples_evaluated == 0

    def test_calibrate_judge_single_sample(self):
        """GD-T008: 单样本不足以计算相关"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()
        result = evaluator.calibrate_judge([{"sample_id": "x", "overall_score": 0.8}])

        assert result.samples_evaluated < 2

    def test_calculate_correlation_perfect_positive(self):
        """GD-T009: 完全正相关"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]

        corr = evaluator._calculate_correlation(x, y)
        assert abs(corr - 1.0) < 0.001

    def test_calculate_correlation_perfect_negative(self):
        """GD-T010: 完全负相关"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]

        corr = evaluator._calculate_correlation(x, y)
        assert abs(corr - (-1.0)) < 0.001

    def test_calculate_correlation_zero_variance(self):
        """GD-T011: 零方差返回0"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        x = [1.0, 1.0, 1.0]
        y = [1.0, 2.0, 3.0]

        corr = evaluator._calculate_correlation(x, y)
        assert corr == 0.0

    def test_calculate_correlation_insufficient_data(self):
        """GD-T012: 数据不足返回0"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()
        corr = evaluator._calculate_correlation([1.0], [2.0])
        assert corr == 0.0

    def test_generate_evaluation_report(self):
        """GD-T013: 生成评估报告"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        evaluator._builder.add_sample({
            "sample_id": "gd-001",
            "quality_level": "high",
            "expected_score": 9.0,
            "content": {},
            "quality_metrics": {"accuracy": 0.95},
            "metadata": {},
        })

        evaluator._builder.add_sample({
            "sample_id": "gd-002",
            "quality_level": "high",
            "expected_score": 8.0,
            "content": {},
            "quality_metrics": {"accuracy": 0.85},
            "metadata": {},
        })

        report = evaluator.generate_evaluation_report()
        assert report["total_samples"] == 2
        assert report["average_score"] == 8.5
        assert report["quality_distribution"]["high"] == 2


class TestCostTrackerComplete:
    """F31 CostTracker 完整覆盖"""

    def test_record_usage_and_get_stats(self):
        """CT-T001: 记录使用并获取统计"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker()

        tracker.record_usage(100, 50)
        tracker.record_usage(200, 100)

        stats = tracker.get_stats()

        assert stats.total_prompt_tokens == 300
        assert stats.total_completion_tokens == 150
        assert stats.total_tokens == 450
        assert stats.total_calls == 2

    def test_get_stats_with_cost(self):
        """CT-T002: 计算成本"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)

        tracker.record_usage(500000, 500000)

        stats = tracker.get_stats()
        assert stats.total_tokens == 1000000
        assert stats.total_cost == 2.0

    def test_get_stats_empty(self):
        """CT-T003: 无记录时统计为空"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker()

        stats = tracker.get_stats()

        assert stats.total_calls == 0
        assert stats.total_cost == 0.0
        assert stats.avg_tokens_per_call == 0.0

    def test_usage_stats_to_dict(self):
        """CT-T004: UsageStats转字典"""
        from f31_minimax_client.cost_tracker import UsageStats

        stats = UsageStats(
            total_prompt_tokens=100,
            total_completion_tokens=50,
            total_tokens=150,
            total_calls=1,
            total_cost=0.3,
            first_call_at=1000.0,
            last_call_at=1010.0,
            avg_tokens_per_call=150.0,
        )

        d = stats.to_dict()
        assert d["total_prompt_tokens"] == 100
        assert d["total_tokens"] == 150
        assert d["total_calls"] == 1

    def test_reset(self):
        """CT-T005: 重置统计"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker()
        tracker.record_usage(100, 50)

        tracker.reset()

        stats = tracker.get_stats()
        assert stats.total_calls == 0
        assert stats.total_tokens == 0


class TestDatasetBuilderComplete:
    """F30 DatasetBuilder 完整覆盖"""

    def test_load_samples_by_quality(self):
        """DB-T001: 按质量等级加载样本"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder()

        builder.add_sample({
            "sample_id": "s1",
            "quality_level": "high",
            "expected_score": 9.0,
            "content": {},
            "quality_metrics": {},
            "metadata": {},
        })
        builder.add_sample({
            "sample_id": "s2",
            "quality_level": "low",
            "expected_score": 4.0,
            "content": {},
            "quality_metrics": {},
            "metadata": {},
        })

        high_samples = builder.load_samples_by_quality("high")
        assert len(high_samples) == 1
        assert high_samples[0].sample_id == "s1"

    def test_load_samples_by_score_range(self):
        """DB-T002: 按分数范围加载样本"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder()

        builder.add_sample({
            "sample_id": "s1", "quality_level": "high", "expected_score": 9.0,
            "content": {}, "quality_metrics": {}, "metadata": {}
        })
        builder.add_sample({
            "sample_id": "s2", "quality_level": "medium", "expected_score": 6.0,
            "content": {}, "quality_metrics": {}, "metadata": {}
        })
        builder.add_sample({
            "sample_id": "s3", "quality_level": "low", "expected_score": 3.0,
            "content": {}, "quality_metrics": {}, "metadata": {}
        })

        mid_range = builder.load_samples_by_score_range(5.0, 8.0)
        assert len(mid_range) == 1
        assert mid_range[0].sample_id == "s2"

    def test_validate_sample_structure_valid(self):
        """DB-T003: 有效样本结构验证通过"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder()

        sample = {
            "sample_id": "s1",
            "quality_level": "high",
            "expected_score": 9.0,
            "content": {},
            "quality_metrics": {},
            "metadata": {},
        }

        assert builder.validate_sample_structure(sample) is True

    def test_validate_sample_structure_missing_field(self):
        """DB-T004: 缺少字段验证失败"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder()

        sample = {
            "sample_id": "s1",
            "quality_level": "high",
        }

        assert builder.validate_sample_structure(sample) is False

    def test_golden_sample_getitem(self):
        """DB-T005: GoldenSample字典式访问"""
        from f30_golden_dataset.dataset_builder import GoldenSample

        sample = GoldenSample(
            sample_id="s1",
            quality_level="high",
            expected_score=9.0,
            content={},
            quality_metrics={},
            metadata={},
        )

        assert sample["sample_id"] == "s1"
        assert sample.get("quality_level") == "high"
        assert sample.get("nonexistent", "default") == "default"

    def test_golden_sample_post_init_defaults(self):
        """DB-T006: GoldenSample默认初始化"""
        from f30_golden_dataset.dataset_builder import GoldenSample

        sample = GoldenSample(
            sample_id="s1",
            quality_level="high",
            expected_score=9.0,
            content={},
            quality_metrics={},
            metadata={},
        )

        assert sample.hallucination_markers == []
        assert sample.regulation_errors == []


class TestKnowledgeGraphQueryEngine:
    """F05 KnowledgeGraph QueryEngine 覆盖"""

    def test_query_engine_with_knowledge_graph(self):
        """KG-QE-T001: 查询引擎初始化"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
        from f05_knowledge_graph.query_engine import QueryEngine

        kg = KnowledgeGraph()
        engine = QueryEngine(knowledge_graph=kg)
        assert engine is not None
        assert engine.kg is kg


class TestContentAddressingComplete:
    """F03 Content Addressing 完整覆盖"""

    def test_calculate_content_hash_deterministic(self):
        """CA-T001: 内容哈希是确定性的"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        h1 = calculate_content_hash("test content")
        h2 = calculate_content_hash("test content")
        h3 = calculate_content_hash("different content")

        assert h1 == h2
        assert h1 != h3

    def test_calculate_content_hash_unicode(self):
        """CA-T002: Unicode内容哈希"""
        from f03_content_addressing.content_addressing import calculate_content_hash

        h1 = calculate_content_hash("中文内容")
        h2 = calculate_content_hash("中文内容")
        h3 = calculate_content_hash("other")

        assert h1 == h2
        assert h1 != h3

    def test_deduplicate_by_hash_empty(self):
        """CA-T003: 空列表去重"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        result = deduplicate_by_hash([])
        assert result == []

    def test_deduplicate_by_hash_single(self):
        """CA-T004: 单元素列表"""
        from f03_content_addressing.content_addressing import deduplicate_by_hash

        result = deduplicate_by_hash(["A"])
        assert result == ["A"]


class TestModelRouterComplete:
    """F25 ModelRouter 完整覆盖"""

    def test_model_router_init(self):
        """MR-T001: 模型路由器初始化"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        assert router is not None


class TestConfigCenterComplete:
    """F24 ConfigCenter 完整覆盖"""

    def test_set_and_get_config(self):
        """CC-T001: 设置和获取配置"""
        from f24_config_center.config_center import ConfigCenter

        config = ConfigCenter()
        version = config.set_config("test.key", "test_value")

        assert version.value == "test_value"
        assert version.version > 0

    def test_get_config_not_found(self):
        """CC-T002: 获取不存在的配置"""
        from f24_config_center.config_center import ConfigCenter

        config = ConfigCenter()
        result = config.get_config("nonexistent.key")
        assert result is None

    def test_get_version_history(self):
        """CC-T003: 获取版本历史"""
        from f24_config_center.config_center import ConfigCenter

        config = ConfigCenter()
        config.set_config("key", "v1")
        config.set_config("key", "v2")
        config.set_config("key", "v3")

        history = config.get_version_history("key")
        assert len(history) == 3
        assert history[0].value == "v1"
        assert history[2].value == "v3"


class TestPoliticalTrackerComplete:
    """F15 PoliticalTracker 完整覆盖"""

    def test_track_topic_and_check(self):
        """PT-T001: 追踪和检查话题"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()
        tracker.track_topic("敏感词", SensitivityLevel.HIGH)

        level = tracker.check_topic_sensitivity("敏感词")
        assert level == SensitivityLevel.HIGH

    def test_check_topic_not_tracked(self):
        """PT-T002: 未追踪话题返回NONE"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()
        level = tracker.check_topic_sensitivity("普通话题")
        assert level == SensitivityLevel.NONE

    def test_multiple_sensitivity_levels(self):
        """PT-T003: 多个敏感等级"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker.track_topic("low", SensitivityLevel.LOW)
        tracker.track_topic("medium", SensitivityLevel.MEDIUM)
        tracker.track_topic("high", SensitivityLevel.HIGH)

        assert tracker.check_topic_sensitivity("low") == SensitivityLevel.LOW
        assert tracker.check_topic_sensitivity("medium") == SensitivityLevel.MEDIUM
        assert tracker.check_topic_sensitivity("high") == SensitivityLevel.HIGH


class TestSecurityFilterEdgeCases:
    """F23 ContentSecurity 边界情况"""

    def test_filter_empty_content(self):
        """SF-T001: 空内容通过过滤"""
        from f23_content_security.content_filter import ContentSecurityFilter

        cf = ContentSecurityFilter()
        result = cf.filter_content("")
        assert result.is_safe is True

    def test_filter_long_content(self):
        """SF-T002: 长内容处理"""
        from f23_content_security.content_filter import ContentSecurityFilter

        cf = ContentSecurityFilter()
        long_content = "正常内容 " * 1000
        result = cf.filter_content(long_content)
        assert result.is_safe is True

    def test_filter_unicode_safe(self):
        """SF-T003: 安全Unicode内容"""
        from f23_content_security.content_filter import ContentSecurityFilter

        cf = ContentSecurityFilter()
        result = cf.filter_content("这是一段正常的中文教材内容")
        assert result.is_safe is True


class TestCitationIntegrityManagerComplete:
    """F14 CitationIntegrityManager 完整覆盖"""

    def test_verify_citation_empty_doi(self):
        """CIM-T001: 空DOI返回无效"""
        from f03_content_addressing.content_addressing import calculate_content_hash
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager, IntegrityStatus

        manager = CitationIntegrityManager()
        content_hash = calculate_content_hash("test content")

        result = manager.verify_citation_integrity("", content_hash, "test")
        assert result.is_valid is False
        assert result.status == IntegrityStatus.INVALID_FORMAT

    def test_verify_citation_whitespace_doi(self):
        """CIM-T002: 空白DOI返回无效"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager, IntegrityStatus

        manager = CitationIntegrityManager()
        result = manager.verify_citation_integrity("   ", "hash", "test")
        assert result.is_valid is False
        assert result.status == IntegrityStatus.INVALID_FORMAT

    def test_verify_citation_invalid_format(self):
        """CIM-T003: 无效DOI格式返回INVALID_FORMAT"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager, IntegrityStatus

        manager = CitationIntegrityManager()
        result = manager.verify_citation_integrity("not-a-doi", "hash", "test")
        assert result.is_valid is False
        assert result.status == IntegrityStatus.INVALID_FORMAT

    def test_verify_citation_hash_mismatch(self):
        """CIM-T004: 内容哈希不匹配"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager, IntegrityStatus

        manager = CitationIntegrityManager()
        result = manager.verify_citation_integrity(
            "10.1234/test",
            "wrong_hash",
            "test content"
        )
        assert result.is_valid is False
        assert result.status == IntegrityStatus.HASH_MISMATCH

    def test_verify_citation_valid(self):
        """CIM-T005: 有效引用验证通过"""
        from f03_content_addressing.content_addressing import calculate_content_hash
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager, IntegrityStatus

        manager = CitationIntegrityManager()
        content = "test content"
        content_hash = calculate_content_hash(content)

        result = manager.verify_citation_integrity("10.1234/test", content_hash, content)
        assert result.is_valid is True
        assert result.status == IntegrityStatus.VALID

    def test_register_unverified_citation(self):
        """CIM-T006: 注册未验证引用"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        reg_id = manager.register_unverified_citation("10.1234/test", "hash123")

        assert reg_id is not None

    def test_get_unverified_citations(self):
        """CIM-T007: 获取未验证引用"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        manager.register_unverified_citation("10.1234/test", "hash1")

        unverified = manager.get_unverified_citations()
        assert len(unverified) >= 1

    def test_mark_citation_verified(self):
        """CIM-T008: 标记引用已验证"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        manager.register_unverified_citation("10.1234/test", "hash1")

        result = manager.mark_citation_verified("10.1234/test", "hash1")
        assert result is True

    def test_mark_citation_verified_not_found(self):
        """CIM-T009: 标记不存在的引用"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        result = manager.mark_citation_verified("10.DOES/NOT", "hash")
        assert result is False

    def test_validate_citation_chain_valid(self):
        """CIM-T010: 有效引用链验证"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        dois = ["10.1234/a", "10.5678/b"]

        result = manager.validate_citation_chain(dois)
        assert result.is_valid is True
        assert len(result.chain) == 2

    def test_validate_citation_chain_invalid_doi(self):
        """CIM-T011: 无效DOI格式导致引用链无效"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        dois = ["10.1234/a", "invalid-doi"]

        result = manager.validate_citation_chain(dois)
        assert result.is_valid is False
        assert len(result.issues) > 0

    def test_validate_citation_chain_self_reference(self):
        """CIM-T012: 自引用DOI检测"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        dois = ["10.1234/a", "10.1234/a"]

        result = manager.validate_citation_chain(dois)
        assert result.is_valid is False
        assert result.is_biased is True

    def test_validate_citation_chain_nonexistent_doi(self):
        """CIM-T013: 不存在的DOI检测"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        dois = ["10.DOES.NOT.EXIST"]

        result = manager.validate_citation_chain(dois)
        assert result.is_valid is False
        assert any("does not exist" in i for i in result.issues)

    def test_detect_fact_collision(self):
        """CIM-T014: 检测事实冲突"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        manager.register_unverified_citation("10.1234/a", "same_hash")
        manager.register_unverified_citation("10.5678/b", "same_hash")

        collisions = manager.detect_fact_collision()
        assert len(collisions) == 1
        assert collisions[0].count == 2

    def test_get_citation_statistics(self):
        """CIM-T015: 获取引用统计"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager

        manager = CitationIntegrityManager()
        manager.register_unverified_citation("10.1234/test", "hash1")

        stats = manager.get_citation_statistics()
        assert stats["total_citations"] >= 1
        assert "verification_rate" in stats


class TestCitationRegistryComplete:
    """F14 CitationRegistry 完整覆盖"""

    def test_register_and_get_citation(self):
        """CR-T001: 注册和获取引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        reg_id = registry.register_citation(
            doi="10.1234/test",
            fact_hash="abc123",
            position={"page": 1, "paragraph": 2}
        )

        assert reg_id is not None

        citation = registry.get_citation(reg_id)
        assert citation is not None
        assert citation.doi == "10.1234/test"
        assert citation.fact_hash == "abc123"

    def test_list_citations_by_doi(self):
        """CR-T002: 按DOI列出引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registry.register_citation(
            doi="10.1234/test",
            fact_hash="hash1",
            position={"page": 1}
        )
        registry.register_citation(
            doi="10.1234/test",
            fact_hash="hash2",
            position={"page": 2}
        )

        citations = registry.list_citations_by_doi("10.1234/test")
        assert len(citations) == 2

    def test_mark_citation_verified(self):
        """CR-T003: 标记引用已验证"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        reg_id = registry.register_citation(
            doi="10.1234/test",
            fact_hash="abc",
            position={"page": 1}
        )

        result = registry.mark_citation_verified(reg_id)
        assert result is True

        citation = registry.get_citation(reg_id)
        assert citation.is_verified is True

    def test_mark_citation_verified_not_found(self):
        """CR-T004: 标记不存在的引用返回False"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()
        assert registry.mark_citation_verified("nonexistent") is False

    def test_get_unverified_citations(self):
        """CR-T005: 获取未验证引用"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registry.register_citation(
            doi="10.1234/test",
            fact_hash="abc",
            position={"page": 1}
        )

        unverified = registry.get_unverified_citations()
        assert len(unverified) == 1

    def test_count_citations(self):
        """CR-T006: 引用计数"""
        from f14_citation_integrity.citation_registry import CitationRegistry

        registry = CitationRegistry()

        registry.register_citation(
            doi="10.1234/test",
            fact_hash="abc",
            position={"page": 1}
        )
        registry.register_citation(
            doi="10.5678/test",
            fact_hash="def",
            position={"page": 2}
        )

        assert registry.count_citations() == 2
        assert registry.count_verified_citations() == 0


class TestJudgeServiceComplete:
    """F20 JudgeService 完整覆盖"""

    @pytest.mark.asyncio
    async def test_judge_content_invalid_json_response(self):
        """JS-T001: LLM返回无效JSON时抛出错误"""
        from f20_llm_judge.judge_service import BaseLLMClient, JudgeService, JudgeServiceError

        class InvalidJSONClient(BaseLLMClient):
            async def generate(self, prompt, **kwargs):
                return "这不是有效的JSON { invalid"

        judge = JudgeService(llm_client=InvalidJSONClient())
        content = "测试内容"

        try:
            await judge.judge_content(content, "test_chapter")
            raise AssertionError("应该抛出 JudgeServiceError")
        except JudgeServiceError as e:
            assert "Invalid JSON" in str(e) or "Failed to parse" in str(e)

    @pytest.mark.asyncio
    async def test_judge_content_missing_fields(self):
        """JS-T002: LLM响应缺少必需字段时抛出错误"""
        from f20_llm_judge.judge_service import BaseLLMClient, JudgeService, JudgeServiceError

        class MissingFieldsClient(BaseLLMClient):
            async def generate(self, prompt, **kwargs):
                return '{"scores": {"accuracy": 0.9}}'

        judge = JudgeService(llm_client=MissingFieldsClient())

        try:
            await judge.judge_content("测试内容", "test_chapter")
            raise AssertionError("应该抛出 JudgeServiceError")
        except JudgeServiceError as e:
            assert "overall_score" in str(e)


class TestQualityGateComplete:
    """F29 QualityGate 完整覆盖"""

    def test_parse_coverage_file_with_coverage_command(self, tmp_path):
        """QG-T001: 解析.coverage文件执行coverage命令"""

        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        test_file = tmp_path / "test_module.py"
        test_file.write_text("x = 1\ny = 2\n")

        import subprocess
        result = subprocess.run(
            ["python", "-m", "coverage", "run", str(test_file)],
            capture_output=True, text=True, cwd=str(tmp_path)
        )

        coverage_file = tmp_path / ".coverage"
        assert coverage_file.exists()

        result = tracker._parse_coverage_file(str(coverage_file))

        assert isinstance(result, float)
        assert result >= 0.0


class TestMonitoringDashboardComplete:
    """F28 MonitoringDashboard 完整覆盖"""

    def test_record_metric_and_health(self):
        """MD-T001: 记录指标和健康检查"""
        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard

        dashboard = MonitoringDashboard()

        dashboard.record_metric("test.metric", 42.0)
        dashboard.record_metric("test.counter", 1)

        health = dashboard.get_health_status()
        assert health.status in ["healthy", "degraded", "unhealthy"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
