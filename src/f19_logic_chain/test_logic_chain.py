"""
F19: 逻辑链文档服务 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。

功能：
- 维护章节间的逻辑依赖关系
- 检测逻辑链断裂
- 分析章节连贯性
- 生成逻辑链文档
"""



class TestLogicChainService:
    """逻辑链服务测试"""

    def test_create_dependency(self):
        """F19-T001: 创建依赖关系"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        result = service.add_dependency("ch-001", "ch-002")

        assert result.success is True
        assert result.dependency is not None

    def test_detect_missing_prerequisite(self):
        """F19-T002: 检测缺失的前置章节"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")
        # ch-003 depends on ch-002, but ch-002's dependency (ch-001) is satisfied

        issues = service.detect_issues()

        assert len(issues) == 0

    def test_detect_broken_chain(self):
        """F19-T003: 检测断裂的逻辑链"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")
        service.add_dependency("ch-001", "ch-003")
        # Add self-reference to create issue
        service.add_dependency("ch-001", "ch-001")

        issues = service.detect_issues()

        assert len(issues) > 0
        assert any(i.type == "self_reference" for i in issues)

    def test_get_dependency_chain(self):
        """F19-T004: 获取依赖链"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")
        service.add_dependency("ch-001", "ch-003")

        chain = service.get_dependency_chain("ch-001")

        assert "ch-002" in chain
        assert "ch-003" in chain

    def test_get_all_chapters_ordered(self):
        """F19-T005: 获取拓扑排序后的章节顺序"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")
        service.add_dependency("ch-001", "ch-003")

        ordered = service.get_topological_order()

        assert len(ordered) == 3
        # ch-001 should come before ch-002 and ch-003
        assert ordered.index("ch-001") < ordered.index("ch-002")

    def test_add_prerequisite_dependency(self):
        """F19-T006: 添加前置依赖"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002", dependency_type="prerequisite")

        deps = service.get_dependents("ch-002")  # Get deps of ch-002 (where target=ch-002)
        assert len(deps) == 1
        assert deps[0].dependency_type == "prerequisite"

    def test_validate_no_circular_dependency(self):
        """F19-T007: 验证无循环依赖"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")

        is_valid = service.validate_dependency_graph()

        assert is_valid is True

    def test_detect_circular_dependency(self):
        """F19-T008: 检测循环依赖"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")
        service.add_dependency("ch-003", "ch-001")  # Creates cycle!

        is_valid = service.validate_dependency_graph()

        assert is_valid is False


class TestDependencyGraph:
    """依赖图测试"""

    def test_build_graph(self):
        """F19-T009: 构建依赖图"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_node("ch-001")
        graph.add_node("ch-002")
        graph.add_edge("ch-001", "ch-002")

        assert graph.has_node("ch-001")
        assert graph.has_node("ch-002")
        assert graph.has_edge("ch-001", "ch-002")

    def test_get_dependencies(self):
        """F19-T010: 获取节点的所有依赖"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")  # ch-001 depends on ch-002
        graph.add_edge("ch-001", "ch-003")  # ch-001 depends on ch-003

        deps = graph.get_dependencies("ch-001")

        assert len(deps) == 2

    def test_get_dependents(self):
        """F19-T011: 获取依赖该节点的所有节点"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-002", "ch-001")  # ch-002 depends on ch-001
        graph.add_edge("ch-003", "ch-001")  # ch-003 depends on ch-001

        dependents = graph.get_dependents("ch-001")

        assert "ch-002" in dependents
        assert "ch-003" in dependents

    def test_detect_independent_nodes(self):
        """F19-T012: 检测独立节点"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_node("ch-001")
        graph.add_node("ch-002")
        graph.add_edge("ch-001", "ch-003")

        independent = graph.get_independent_nodes()

        assert "ch-002" in independent

    def test_find_dependency_path(self):
        """F19-T013: 查找依赖路径"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        path = graph.find_path("ch-001", "ch-003")

        assert path is not None
        assert len(path) == 3

    def test_find_path_nonexistent_start(self):
        """F19-T013a: 查找路径 - 起始节点不存在"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")

        path = graph.find_path("nonexistent", "ch-002")

        assert path is None

    def test_find_path_nonexistent_end(self):
        """F19-T013b: 查找路径 - 目标节点不存在"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")

        path = graph.find_path("ch-001", "nonexistent")

        assert path is None

    def test_find_path_start_equals_end(self):
        """F19-T013c: 查找路径 - 起点等于终点"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")

        path = graph.find_path("ch-001", "ch-001")

        assert path == ["ch-001"]

    def test_find_path_no_path(self):
        """F19-T013d: 查找路径 - 无路径"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-003", "ch-004")

        path = graph.find_path("ch-001", "ch-004")

        assert path is None

    def test_get_all_paths(self):
        """F19-T013e: 获取所有路径"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        paths = graph.get_all_paths("ch-001", "ch-003")

        assert len(paths) == 1
        assert paths[0] == ["ch-001", "ch-002", "ch-003"]

    def test_get_all_paths_multiple(self):
        """F19-T013f: 获取所有路径 - 多条路径"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-001", "ch-003")

        paths = graph.get_all_paths("ch-001", "ch-003")

        assert len(paths) == 2

    def test_get_all_paths_nonexistent(self):
        """F19-T013g: 获取所有路径 - 节点不存在"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")

        paths = graph.get_all_paths("nonexistent", "ch-002")
        assert paths == []

    def test_get_all_paths_no_path(self):
        """F19-T013h: 获取所有路径 - 无路径"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-003", "ch-004")

        paths = graph.get_all_paths("ch-001", "ch-004")
        assert paths == []

    def test_has_cycle_directly(self):
        """F19-T013i: 直接测试循环检测"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-003", "ch-001")

        assert graph.has_cycle() is True

    def test_has_no_cycle_directly(self):
        """F19-T013j: 直接测试无循环"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        assert graph.has_cycle() is False

    def test_has_cycle_self_loop(self):
        """F19-T013k: 自循环检测"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-001")

        assert graph.has_cycle() is True

    def test_get_all_edges(self):
        """F19-T013l: 获取所有边"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        edges = graph.get_all_edges()

        assert len(edges) == 2
        assert ("ch-001", "ch-002") in edges

    def test_add_duplicate_edge(self):
        """F19-T013m: 添加重复边"""
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-001", "ch-002")

        assert graph.has_edge("ch-001", "ch-002") is True
        assert len(graph.get_dependencies("ch-001")) == 1


class TestCoherenceAnalyzer:
    """连贯性分析器测试"""

    def test_analyze_prerequisite_chain(self):
        """F19-T014: 分析前置依赖链"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-001", "ch-003")

        analyzer = CoherenceAnalyzer(graph)
        analysis = analyzer.analyze_prerequisite_chain("ch-001")

        assert analysis["complete"] is True
        assert len(analysis["chain"]) == 3

    def test_analyze_prerequisite_chain_nonexistent(self):
        """F19-T014a: 分析前置依赖链 - 不存在的节点"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")

        analyzer = CoherenceAnalyzer(graph)
        analysis = analyzer.analyze_prerequisite_chain("nonexistent")

        assert analysis["complete"] is False
        assert analysis["chain"] == []
        assert analysis["missing"] == []

    def test_analyze_prerequisite_chain_no_deps(self):
        """F19-T014b: 分析前置依赖链 - 无依赖的节点"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_node("ch-004")

        analyzer = CoherenceAnalyzer(graph)
        analysis = analyzer.analyze_prerequisite_chain("ch-004")

        assert analysis["complete"] is False
        assert analysis["chain"] == ["ch-004"]

    def test_detect_logical_gaps(self):
        """F19-T015: 检测逻辑缺口"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-001", "ch-003")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-003", "ch-004")

        analyzer = CoherenceAnalyzer(graph)
        gaps = analyzer.detect_logical_gaps()

        assert len(gaps) == 1
        assert gaps[0]["node"] == "ch-004"
        assert gaps[0]["type"] == "orphan_node"

    def test_analyze_concept_progression(self):
        """F19-T016: 分析概念递进"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        analyzer = CoherenceAnalyzer(graph)
        progression = analyzer.analyze_concept_progression()

        assert progression["is_logical"] is True
        assert "sorted_nodes" in progression
        assert progression["depth"] == 3

    def test_analyze_concept_progression_with_cycle(self):
        """F19-T016a: 分析概念递进 - 存在循环依赖"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-003", "ch-001")

        analyzer = CoherenceAnalyzer(graph)
        progression = analyzer.analyze_concept_progression()

        assert progression["is_logical"] is False
        assert progression["reason"] == "检测到循环依赖"

    def test_find_missing_concept_prerequisites(self):
        """F19-T017: 查找缺失的概念前提"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        analyzer = CoherenceAnalyzer(graph)
        missing = analyzer.find_missing_prerequisites("ch-003")

        assert len(missing) == 0

    def test_find_missing_prerequisites_nonexistent(self):
        """F19-T017a: 查找缺失前提 - 不存在的节点"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")

        analyzer = CoherenceAnalyzer(graph)
        missing = analyzer.find_missing_prerequisites("nonexistent")

        assert missing == []

    def test_find_missing_prerequisites_transitive(self):
        """F19-T017b: 查找缺失前提 - 传递性依赖"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-002", "ch-004")

        analyzer = CoherenceAnalyzer(graph)
        missing = analyzer.find_missing_prerequisites("ch-001")

        assert "ch-002" in missing
        assert "ch-003" in missing
        assert "ch-004" in missing

    def test_calculate_coherence_score_empty_nodes(self):
        """F19-T017c: 计算连贯性评分 - 空节点"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        analyzer = CoherenceAnalyzer(graph)
        score = analyzer.calculate_coherence_score()

        assert score == 1.0

    def test_calculate_coherence_score_no_edges(self):
        """F19-T017d: 计算连贯性评分 - 无边的节点"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_node("ch-001")
        graph.add_node("ch-002")

        analyzer = CoherenceAnalyzer(graph)
        score = analyzer.calculate_coherence_score()

        assert score == 0.5

    def test_calculate_coherence_score_with_cycle(self):
        """F19-T017e: 计算连贯性评分 - 存在循环依赖"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-003", "ch-001")

        analyzer = CoherenceAnalyzer(graph)
        score = analyzer.calculate_coherence_score()

        assert 0.0 <= score <= 1.0

    def test_generate_coherence_report(self):
        """F19-T018: 生成连贯性报告"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        analyzer = CoherenceAnalyzer(graph)
        report = analyzer.generate_coherence_report()

        assert "overall_score" in report
        assert "issues" in report
        assert report["overall_score"] >= 0.0

    def test_generate_coherence_report_with_cycle(self):
        """F19-T018a: 生成连贯性报告 - 存在循环依赖"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")
        graph.add_edge("ch-003", "ch-001")

        analyzer = CoherenceAnalyzer(graph)
        report = analyzer.generate_coherence_report()

        assert report["is_coherent"] is False
        circular_issues = [i for i in report["issues"] if i["type"] == "circular_dependency"]
        assert len(circular_issues) == 1

    def test_compare_chapters(self):
        """F19-T018b: 比较章节逻辑关系"""
        from f19_logic_chain.coherence_analyzer import CoherenceAnalyzer
        from f19_logic_chain.dependency_graph import DependencyGraph

        graph = DependencyGraph()
        graph.add_edge("ch-001", "ch-002")
        graph.add_edge("ch-002", "ch-003")

        analyzer = CoherenceAnalyzer(graph)
        result = analyzer.compare_chapters("ch-001", "ch-003")

        assert "chapter1_before_chapter2" in result
        assert "chapter2_before_chapter1" in result
        assert "direct_path_1_to_2" in result
        assert "direct_path_2_to_1" in result
        assert result["direct_path_1_to_2"] is not None
        assert result["direct_path_2_to_1"] is None


class TestLogicChainIntegration:
    """逻辑链集成测试"""

    def test_full_logic_chain_lifecycle(self):
        """F19-T019: 完整逻辑链生命周期"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()

        # 1. 添加依赖
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")

        # 2. 验证图
        assert service.validate_dependency_graph() is True

        # 3. 获取顺序
        ordered = service.get_topological_order()
        assert ordered.index("ch-001") < ordered.index("ch-002")
        assert ordered.index("ch-002") < ordered.index("ch-003")

        # 4. 检测问题
        issues = service.detect_issues()
        assert len(issues) == 0

    def test_logic_chain_export_import(self):
        """F19-T020: 逻辑链导出导入"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")

        data = service.export()
        new_service = LogicChainService()
        new_service.import_(data)

        ordered = new_service.get_topological_order()
        assert len(ordered) == 3

    def test_generate_logic_chain_document(self):
        """F19-T021: 生成逻辑链文档"""
        from f19_logic_chain.logic_chain_service import LogicChainService

        service = LogicChainService()
        service.add_dependency("ch-001", "ch-002")
        service.add_dependency("ch-002", "ch-003")
        service.add_dependency("ch-001", "ch-003")

        document = service.generate_logic_chain_document()

        assert "ch-001" in document
        assert "ch-002" in document
        assert "ch-003" in document
        assert document.count("依赖") >= 2
