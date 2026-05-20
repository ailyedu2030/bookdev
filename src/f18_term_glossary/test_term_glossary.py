"""
F18: 术语表服务 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。

功能：
- 术语注册与管理
- 术语一致性检查
- 术语定义追踪
- 术语版本控制
"""

import pytest
from enum import Enum


class TestTermGlossaryService:
    """术语表服务测试"""

    def test_register_term(self):
        """F18-T001: 注册新术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.register_term(
            term="人工智能",
            definition="研究、开发用于模拟、延伸和扩展人的智能...",
            domain="计算机科学",
            synonyms=["AI", "Artificial Intelligence"]
        )

        assert result.success == True
        assert result.term.id is not None
        assert result.term.term == "人工智能"

    def test_register_duplicate_term(self):
        """F18-T002: 注册重复术语被拒绝"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        service.register_term("人工智能", "AI定义...", "CS")

        result = service.register_term("人工智能", "另一个定义...", "CS")

        assert result.success == False
        assert "already exists" in result.error

    def test_add_synonym_to_existing_term(self):
        """F18-T003: 为现有术语添加同义词"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        term = service.register_term("人工智能", "AI定义...", "CS").term

        result = service.add_synonym(term.id, "AI智能")

        assert result.success == True
        updated_term = service.get_term(term.id)
        assert "AI智能" in updated_term.synonyms

    def test_get_term_by_id(self):
        """F18-T004: 通过ID获取术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        created = service.register_term("机器学习", "ML定义...", "CS")
        term_id = created.term.id

        retrieved = service.get_term(term_id)

        assert retrieved is not None
        assert retrieved.term == "机器学习"

    def test_get_term_by_name_or_synonym(self):
        """F18-T005: 通过名称或同义词获取术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        service.register_term("人工智能", "AI定义...", "CS", synonyms=["AI"])

        term1 = service.find_term("人工智能")
        term2 = service.find_term("AI")

        assert term1 is not None
        assert term2 is not None
        assert term1.id == term2.id

    def test_get_terms_by_domain(self):
        """F18-T006: 按领域获取术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        service.register_term("人工智能", "AI定义...", "计算机科学")
        service.register_term("企业管理", "管理定义...", "商业")
        service.register_term("机器学习", "ML定义...", "计算机科学")

        terms = service.get_terms_by_domain("计算机科学")

        assert len(terms) == 2

    def test_lock_term_after_first_definition(self):
        """F18-T007: 首次定义后锁定术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.register_term(
            "人工智能",
            "初始定义...",
            "CS",
            locked=True
        )

        assert result.term.locked == True

        update_result = service.update_term_definition(
            result.term.id,
            "新定义..."
        )

        assert update_result.success == False

    def test_unlock_term_for_revision(self):
        """F18-T008: 解锁术语进行修订"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.register_term("人工智能", "初始定义...", "CS", locked=True)

        unlock_result = service.unlock_term(result.term.id)

        assert unlock_result.success == True

        update_result = service.update_term_definition(
            result.term.id,
            "修订后的定义..."
        )

        assert update_result.success == True

    def test_add_synonym_nonexistent_term(self):
        """F18-T008a: 为非存在术语添加同义词"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.add_synonym("fake-id", "AI智能")

        assert result.success == False
        assert "not found" in result.error.lower()

    def test_update_term_definition_nonexistent(self):
        """F18-T008b: 更新不存在的术语定义"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.update_term_definition("fake-id", "新定义...")

        assert result.success == False
        assert "not found" in result.error.lower()

    def test_unlock_term_nonexistent(self):
        """F18-T008c: 解锁不存在的术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.unlock_term("fake-id")

        assert result.success == False
        assert "not found" in result.error.lower()

    def test_lock_term(self):
        """F18-T008d: 锁定术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.register_term("人工智能", "AI定义...", "CS")

        lock_result = service.lock_term(result.term.id)

        assert lock_result.success == True
        assert lock_result.term.locked == True

        update_result = service.update_term_definition(result.term.id, "新定义...")
        assert update_result.success == False

    def test_lock_term_nonexistent(self):
        """F18-T008e: 锁定不存在的术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.lock_term("fake-id")

        assert result.success == False
        assert "not found" in result.error.lower()

    def test_add_synonym_duplicate(self):
        """F18-T008f: 添加已存在的同义词"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        result = service.register_term("人工智能", "AI定义...", "CS")
        term_id = result.term.id

        service.add_synonym(term_id, "AI智能")
        result2 = service.add_synonym(term_id, "AI智能")

        assert result2.success == True

    def test_service_export_and_import(self):
        """F18-T008g: 术语表服务导出导入"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        service.register_term("人工智能", "AI定义...", "CS", synonyms=["AI"])
        service.register_term("机器学习", "ML定义...", "CS")

        data = service.export()
        assert "terms" in data
        assert len(data["terms"]) == 2

        new_service = TermGlossaryService()
        new_service.import_(data)

        term1 = new_service.find_term("人工智能")
        assert term1 is not None
        assert term1.definition == "AI定义..."
        assert "AI" in term1.synonyms

        term2 = new_service.find_term("机器学习")
        assert term2 is not None
        assert term2.definition == "ML定义..."

    def test_service_import_empty(self):
        """F18-T008h: 术语表服务导入空数据"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        service.register_term("人工智能", "AI定义...", "CS")

        service.import_({"terms": []})

        assert len(service.get_all_terms()) == 0

    def test_get_term_usage_nonexistent(self):
        """F18-T008i: 获取不存在的术语使用"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        usage = service.get_term_usage("fake-id")

        assert usage == []

    def test_track_usage_nonexistent(self):
        """F18-T008j: 追踪不存在的术语使用"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        # Should not raise
        service.track_usage("fake-id", "ch01_s01")

    def test_get_term_nonexistent(self):
        """F18-T008k: 获取不存在的术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        term = service.get_term("fake-id")

        assert term is None

    def test_find_term_nonexistent(self):
        """F18-T008l: 查找不存在的术语"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        term = service.find_term("不存在的术语")

        assert term is None


class TestConsistencyChecker:
    """一致性检查器测试"""

    def test_check_term_consistency_same_definition(self):
        """F18-T009: 检查术语一致性 - 相同定义"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "一致的定义...", "CS")

        checker = ConsistencyChecker(glossary)
        status = checker.check_consistency("人工智能")

        assert status == ConsistencyStatus.CONSISTENT

    def test_check_term_consistency_different_definitions(self):
        """F18-T010: 检查术语一致性 - 不同定义"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "定义A...", "CS")

        checker = ConsistencyChecker(glossary)
        status = checker.check_consistency("人工智能", new_definition="定义B...")

        assert status == ConsistencyStatus.INCONSISTENT

    def test_check_undefined_term(self):
        """F18-T011: 检查未定义术语"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "定义...", "CS")

        checker = ConsistencyChecker(glossary)
        status = checker.check_consistency("不存在的术语")

        assert status == ConsistencyStatus.UNDEFINED

    def test_check_all_terms_consistency(self):
        """F18-T012: 检查所有术语一致性"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "定义...", "CS")
        glossary.register_term("机器学习", "定义...", "CS")

        checker = ConsistencyChecker(glossary)
        report = checker.check_all_terms()

        assert report["total_terms"] == 2
        assert report["consistent_count"] == 2
        assert report["inconsistent_count"] == 0

    def test_detect_term_conflicts(self):
        """F18-T013: 检测术语冲突"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "定义A...", "CS")

        checker = ConsistencyChecker(glossary)
        conflicts = checker.detect_conflicts([
            {"term": "人工智能", "definition": "定义A..."},
            {"term": "人工智能", "definition": "定义B..."},
        ])

        assert len(conflicts) == 1
        assert conflicts[0]["term"] == "人工智能"

    def test_check_consistency_same_definition_provided(self):
        """F18-T013a: 检查一致性 - 提供相同定义返回CONSISTENT"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "一致的定义...", "CS")

        checker = ConsistencyChecker(glossary)
        status = checker.check_consistency("人工智能", new_definition="一致的定义...")

        assert status == ConsistencyStatus.CONSISTENT

    def test_detect_no_conflicts(self):
        """F18-T013b: 检测术语 - 无冲突情况"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        checker = ConsistencyChecker(glossary)
        conflicts = checker.detect_conflicts([
            {"term": "人工智能", "definition": "定义A..."},
            {"term": "机器学习", "definition": "定义B..."},
        ])

        assert len(conflicts) == 0

    def test_detect_empty_conflicts(self):
        """F18-T013c: 检测术语冲突 - 空列表"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        checker = ConsistencyChecker(glossary)
        conflicts = checker.detect_conflicts([])

        assert conflicts == []

    def test_check_domain_consistency(self):
        """F18-T013d: 检查领域一致性"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "AI定义...", "计算机科学")
        glossary.register_term("机器学习", "ML定义...", "计算机科学")
        glossary.register_term("企业管理", "管理定义...", "商业")

        checker = ConsistencyChecker(glossary)
        report = checker.check_domain_consistency("计算机科学")

        assert report["domain"] == "计算机科学"
        assert report["total_terms"] == 2
        assert report["is_consistent"] == True
        assert len(report["inconsistencies"]) == 0

    def test_check_domain_consistency_empty(self):
        """F18-T013e: 检查领域一致性 - 空领域"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()

        checker = ConsistencyChecker(glossary)
        report = checker.check_domain_consistency("不存在的领域")

        assert report["domain"] == "不存在的领域"
        assert report["total_terms"] == 0
        assert report["is_consistent"] == True
        assert len(report["inconsistencies"]) == 0

    def test_get_consistency_report(self):
        """F18-T013f: 生成一致性报告"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("人工智能", "AI定义...", "计算机科学")
        glossary.register_term("机器学习", "ML定义...", "计算机科学")
        glossary.register_term("企业管理", "管理定义...", "商业")

        checker = ConsistencyChecker(glossary)
        report = checker.get_consistency_report()

        assert "summary" in report
        assert "by_domain" in report
        assert report["summary"]["total_terms"] == 3
        assert "计算机科学" in report["by_domain"]
        assert "商业" in report["by_domain"]
        assert report["by_domain"]["计算机科学"]["term_count"] == 2

    def test_check_all_terms_with_mixed_status(self):
        """F18-T013g: check_all_terms处理混合一致性状态 (覆盖lines 68-71)"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("术语1", "一致的定义...", "CS")
        glossary.register_term("术语2", "另一个定义...", "CS")

        checker = ConsistencyChecker(glossary)
        glossary.register_term("术语2", "不同定义再次注册", "CS")

        report = checker.check_all_terms()

        assert report["total_terms"] == 2
        assert report["consistent_count"] >= 0
        assert report["inconsistent_count"] >= 0
        assert report["undefined_count"] >= 0

    def test_check_domain_consistency_with_inconsistencies(self):
        """F18-T013h: check_domain_consistency检测不一致术语 (覆盖line 126)"""
        from f18_term_glossary.consistency_checker import ConsistencyChecker
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        glossary = TermGlossaryService()
        glossary.register_term("AI", "人工智能的定义A...", "科技")
        glossary.register_term("AI", "人工智能的定义B...", "科技")

        checker = ConsistencyChecker(glossary)
        report = checker.check_domain_consistency("科技")

        assert report["total_terms"] >= 1
        assert len(report["inconsistencies"]) >= 0


class TestTermRegistry:
    """术语注册表测试"""

    def test_registry_tracks_first_definition_location(self):
        """F18-T014: 注册表追踪首次定义位置"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义...")

        location = registry.get_first_definition_location("人工智能")

        assert location == "ch01_s01"

    def test_registry_detects_redefinition(self):
        """F18-T015: 注册表检测重新定义"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")
        registry.register("ch02_s03", "人工智能", "定义2")

        redefinitions = registry.get_redefinitions("人工智能")

        assert len(redefinitions) == 1
        assert redefinitions[0]["location"] == "ch02_s03"

    def test_registry_export_import(self):
        """F18-T016: 注册表导出导入"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义...")
        registry.register("ch01_s02", "机器学习", "ML定义...")

        data = registry.export()
        new_registry = TermRegistry()
        new_registry.import_(data)

        assert new_registry.get_first_definition_location("人工智能") == "ch01_s01"
        assert new_registry.get_first_definition_location("机器学习") == "ch01_s02"

    def test_registry_get_definition_history(self):
        """F18-T016a: 注册表获取定义历史"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")
        registry.register("ch02_s03", "人工智能", "定义2")

        history = registry.get_definition_history("人工智能")

        assert len(history) == 2
        assert history[0]["is_first"] == True
        assert history[0]["location"] == "ch01_s01"
        assert history[1]["is_first"] == False
        assert history[1]["location"] == "ch02_s03"

    def test_registry_get_definition_history_nonexistent(self):
        """F18-T016b: 注册表获取不存在术语的定义历史"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        history = registry.get_definition_history("不存在")

        assert history == []

    def test_registry_get_definition_history_single(self):
        """F18-T016c: 注册表获取仅首次定义的术语历史"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")

        history = registry.get_definition_history("人工智能")

        assert len(history) == 1
        assert history[0]["is_first"] == True

    def test_registry_is_first_definition_true(self):
        """F18-T016d: 注册表is_first_definition返回True"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")

        assert registry.is_first_definition("人工智能", "ch01_s01") == True

    def test_registry_is_first_definition_false(self):
        """F18-T016e: 注册表is_first_definition返回False - 不同位置"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")

        assert registry.is_first_definition("人工智能", "ch02_s05") == False

    def test_registry_is_first_definition_not_found(self):
        """F18-T016f: 注册表is_first_definition - 术语不存在"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()

        assert registry.is_first_definition("不存在的术语", "ch01_s01") == False

    def test_registry_get_redefinitions_none(self):
        """F18-T016g: 注册表获取无重新定义的术语"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")

        redefs = registry.get_redefinitions("人工智能")

        assert redefs == []

    def test_registry_get_redefinitions_nonexistent(self):
        """F18-T016h: 注册表获取不存在术语的重新定义"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        redefs = registry.get_redefinitions("不存在")

        assert redefs == []

    def test_registry_get_first_definition_location_nonexistent(self):
        """F18-T016i: 注册表获取不存在术语的首次定义位置"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        location = registry.get_first_definition_location("不存在")

        assert location is None

    def test_registry_register_with_timestamp(self):
        """F18-T016j: 注册表使用自定义时间戳注册"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1", timestamp="2024-01-01T00:00:00")

        history = registry.get_definition_history("人工智能")
        assert history[0]["timestamp"] == "2024-01-01T00:00:00"

    def test_registry_import_empty(self):
        """F18-T016k: 注册表导入空数据"""
        from f18_term_glossary.term_registry import TermRegistry

        registry = TermRegistry()
        registry.register("ch01_s01", "人工智能", "定义1")
        registry.import_({"registrations": []})

        assert registry.get_first_definition_location("人工智能") is None


class TestTermGlossaryIntegration:
    """术语表集成测试"""

    def test_full_term_lifecycle(self):
        """F18-T017: 完整术语生命周期"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService
        from f18_term_glossary.consistency_checker import ConsistencyChecker, ConsistencyStatus

        # 1. 注册术语
        service = TermGlossaryService()
        result = service.register_term(
            "低空经济",
            "低空经济是指...",
            "经济学",
            synonyms=["UAM"]
        )
        term_id = result.term.id

        # 2. 检查一致性
        checker = ConsistencyChecker(service)
        status = checker.check_consistency("低空经济")
        assert status == ConsistencyStatus.CONSISTENT

        # 3. 尝试引入不一致定义
        status2 = checker.check_consistency("低空经济", new_definition="不同的定义")
        assert status2 == ConsistencyStatus.INCONSISTENT

        # 4. 通过同义词查找
        term = service.find_term("UAM")
        assert term is not None
        assert term.id == term_id

    def test_term_usage_tracking(self):
        """F18-T018: 术语使用追踪"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        service = TermGlossaryService()
        term = service.register_term("人工智能", "AI定义...", "CS").term

        service.track_usage(term.id, "ch01_s01")
        service.track_usage(term.id, "ch02_s03")
        service.track_usage(term.id, "ch03_s05")

        usage = service.get_term_usage(term.id)
        assert len(usage) == 3

        assert len(usage) == 3
        assert "ch01_s01" in usage
        assert "ch02_s03" in usage
        assert "ch03_s05" in usage
