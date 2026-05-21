"""
F17: 跨章引用解析器 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。

功能：
- 解析章节间的交叉引用
- 识别引用类型 (定义引用、应用引用、对比引用等)
- 验证引用有效性
- 检测循环引用
"""



class ReferencePattern:
    """引用模式"""
    DEFINITION_REF = "definition_ref"  # 定义引用 [@def:ch01_s01]
    APPLICATION_REF = "application_ref"  # 应用引用 [@app:ch01_s01]
    COMPARISON_REF = "comparison_ref"  # 对比引用 [@cmp:ch01_s01]
    CITATION_REF = "citation_ref"  # 引用 [@cite:DOI]


class ParsedReference:
    """解析后的引用"""
    def __init__(
        self,
        ref_type: str,
        target_id: str,
        source_location: tuple[int, int],  # (line, column)
        context: str,
    ):
        self.ref_type = ref_type
        self.target_id = target_id
        self.source_location = source_location
        self.context = context


class TestReferenceParser:
    """引用解析器测试"""

    def test_parse_definition_reference(self):
        """F17-T001: 解析定义引用"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = "人工智能是指[@def:ch01_s01]...根据定义[@def:ch01_s01]..."

        refs = parser.parse_references(content)

        assert len(refs) == 2
        assert refs[0].ref_type == ReferencePattern.DEFINITION_REF
        assert refs[0].target_id == "ch01_s01"

    def test_parse_application_reference(self):
        """F17-T002: 解析应用引用"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = "这一方法[@app:ch02_s03]已广泛应用于..."

        refs = parser.parse_references(content)

        assert len(refs) == 1
        assert refs[0].ref_type == ReferencePattern.APPLICATION_REF
        assert refs[0].target_id == "ch02_s03"

    def test_parse_comparison_reference(self):
        """F17-T003: 解析对比引用"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = "与[@cmp:ch03_s02]不同，本章采用..."

        refs = parser.parse_references(content)

        assert len(refs) == 1
        assert refs[0].ref_type == ReferencePattern.COMPARISON_REF
        assert refs[0].target_id == "ch03_s02"

    def test_parse_multiple_reference_types(self):
        """F17-T004: 解析多种引用类型"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = """
        人工智能[@def:ch01_s01]是指...
        这一方法[@app:ch02_s03]与[@cmp:ch03_s02]不同...
        详见[@cite:10.1234/example.123]
        """

        refs = parser.parse_references(content)

        assert len(refs) == 4
        ref_types = [r.ref_type for r in refs]
        assert ReferencePattern.DEFINITION_REF in ref_types
        assert ReferencePattern.APPLICATION_REF in ref_types
        assert ReferencePattern.COMPARISON_REF in ref_types

    def test_capture_reference_context(self):
        """F17-T005: 捕获引用上下文"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = "根据[@def:ch01_s01]的定义，人工智能是..."

        refs = parser.parse_references(content)

        assert len(refs) == 1
        assert "定义" in refs[0].context

    def test_capture_source_location(self):
        """F17-T006: 捕获引用位置"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = "第一行内容\n第二行内容\n[@def:ch03_s01]在第三行"

        refs = parser.parse_references(content)

        assert len(refs) == 1
        assert refs[0].source_location[0] == 3  # line 3 (1-indexed)

    def test_detect_circular_reference(self):
        """F17-T007: 检测循环引用"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        references = [
            ("ch01_s01", "ch02_s01"),  # ch01_s01 引用 ch02_s01
            ("ch02_s01", "ch03_s01"),  # ch02_s01 引用 ch03_s01
            ("ch03_s01", "ch01_s01"),  # ch03_s01 引用 ch01_s01 (循环!)
        ]

        has_cycle = parser.detect_circular_reference(references)

        assert has_cycle is True

    def test_no_false_positive_for_non_circular(self):
        """F17-T008: 非循环引用不报错"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        references = [
            ("ch01_s01", "ch02_s01"),
            ("ch01_s02", "ch03_s01"),
            ("ch02_s01", "ch03_s01"),
        ]

        has_cycle = parser.detect_circular_reference(references)

        assert has_cycle is False

    def test_self_reference_detection(self):
        """F17-T009: 检测自我引用"""
        from f17_cross_reference.reference_parser import ReferenceParser

        parser = ReferenceParser()
        content = "本章[@def:ch01_s01]将介绍..."

        refs = parser.parse_references(content)

        assert len(refs) == 1
        assert refs[0].target_id == "ch01_s01"


class TestReferenceResolver:
    """引用解析器测试"""

    def test_resolve_definition_reference(self):
        """F17-T010: 解析定义引用"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "人工智能概述", 1)
        kg.create_section("sec-001", "AI定义", parent_chapter_id="ch-001")

        resolver = ReferenceResolver(kg)
        resolved = resolver.resolve("sec-001", ReferencePattern.DEFINITION_REF)

        assert resolved is not None
        assert "定义" in resolved.title

    def test_resolve_nonexistent_reference(self):
        """F17-T011: 解析不存在的引用"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)

        resolver = ReferenceResolver(kg)
        resolved = resolver.resolve("nonexistent", ReferencePattern.DEFINITION_REF)

        assert resolved is None

    def test_validate_reference_chain(self):
        """F17-T012: 验证引用链完整性"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")

        resolver = ReferenceResolver(kg)
        is_valid = resolver.validate_reference_chain("sec-001")

        assert is_valid is True

    def test_validate_broken_chain(self):
        """F17-T013: 验证断裂的引用链"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        # 没有添加引用边

        resolver = ReferenceResolver(kg)
        # sec-001 引用了一个不存在的目标
        is_valid = resolver.validate_reference_chain("sec-001", referenced_target="nonexistent")

        assert is_valid is False

    def test_get_all_references_from_section(self):
        """F17-T014: 获取章节所有引用"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.create_section("sec-003", "第三节", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")
        kg.add_edge("sec-001", "sec-003", "DEFINES")

        resolver = ReferenceResolver(kg)
        refs = resolver.get_all_references_from_section("sec-001")

        assert len(refs) == 2

    def test_get_all_references_to_section(self):
        """F17-T015: 获取引用到章节的所有来源"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.create_section("sec-003", "第三节", parent_chapter_id="ch-001")
        kg.add_edge("sec-002", "sec-001", "REFERENCES")
        kg.add_edge("sec-003", "sec-001", "DEFINES")

        resolver = ReferenceResolver(kg)
        refs = resolver.get_all_references_to_section("sec-001")

        assert len(refs) == 2

    def test_validate_reference_chain_with_matching_target(self):
        """F17-T022: 验证引用链时找到匹配目标 (覆盖line 53)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")

        resolver = ReferenceResolver(kg)
        is_valid = resolver.validate_reference_chain("sec-001", referenced_target="sec-002")

        assert is_valid is True


class TestCrossReferenceIntegration:
    """跨章引用集成测试"""

    def test_full_reference_lifecycle(self):
        """F17-T016: 完整引用生命周期"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_parser import ReferenceParser
        from f17_cross_reference.reference_resolver import ReferenceResolver

        # 1. 创建图谱
        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "人工智能概述", 1)
        kg.create_section("sec-001", "AI定义", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "AI应用", parent_chapter_id="ch-001")
        kg.add_edge("sec-002", "sec-001", "REFERENCES")

        # 2. 解析引用
        parser = ReferenceParser()
        content = "根据[@def:sec-001]的定义，AI是指..."
        refs = parser.parse_references(content)

        assert len(refs) == 1

        # 3. 解析引用
        resolver = ReferenceResolver(kg)
        resolved = resolver.resolve(refs[0].target_id, refs[0].ref_type)

        assert resolved is not None
        assert resolved.id == "sec-001"

    def test_reference_consistency_check(self):
        """F17-T017: 引用一致性检查"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.create_section("sec-003", "第三节", parent_chapter_id="ch-001")
        kg.add_edge("sec-002", "sec-001", "REFERENCES")
        kg.add_edge("sec-003", "sec-002", "FOLLOWS")

        resolver = ReferenceResolver(kg)

        # sec-001 应该是逻辑起点了
        consistency = resolver.check_reference_consistency(["sec-001", "sec-002", "sec-003"])

        assert consistency["is_consistent"] is True

    def test_validate_reference_chain_nonexistent_target(self):
        """F17-T019: 验证引用链但目标不存在 (覆盖lines 51-55)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")

        resolver = ReferenceResolver(kg)
        is_valid = resolver.validate_reference_chain("sec-001", referenced_target="nonexistent_target")

        assert is_valid is False

    def test_check_reference_consistency_external_reference(self):
        """F17-T020: 检测外部引用问题 (覆盖lines 124-129)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")

        resolver = ReferenceResolver(kg)
        consistency = resolver.check_reference_consistency(["sec-001"])

        assert consistency["is_consistent"] is False
        assert len(consistency["issues"]) > 0
        assert consistency["issues"][0]["type"] == "external_reference"

    def test_check_reference_consistency_duplicate_reference(self):
        """F17-T021: 检测重复引用问题 (覆盖lines 130-137)"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")
        kg.add_edge("sec-001", "sec-002", "REFERENCES")

        resolver = ReferenceResolver(kg)
        consistency = resolver.check_reference_consistency(["sec-001", "sec-002"])

        assert consistency["is_consistent"] is False
        has_duplicate = any(issue["type"] == "duplicate_reference" for issue in consistency["issues"])
        assert has_duplicate is True

    def test_generate_reference_report(self):
        """F17-T018: 生成引用报告"""
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        from f17_cross_reference.reference_resolver import ReferenceResolver

        kg = KnowledgeGraph()
        kg.create_chapter("ch-001", "第一章", 1)
        kg.create_section("sec-001", "第一节", parent_chapter_id="ch-001")
        kg.create_section("sec-002", "第二节", parent_chapter_id="ch-001")
        kg.add_edge("sec-002", "sec-001", "REFERENCES")

        resolver = ReferenceResolver(kg)
        report = resolver.generate_reference_report()

        assert "total_references" in report
        assert "by_type" in report
        assert report["total_references"] == 1
