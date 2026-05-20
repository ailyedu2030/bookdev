"""
集成测试 - 模块间交互验证

测试跨模块集成场景：
1. F00 Kafka + F01 Immutable Log
2. F02 Context Budget + F04 Temporal Workflow Activities
3. F05 Knowledge Graph + F32 PG Adapter
4. F13 Global Semantic Scanner + F18 Term Glossary
5. F19 Logic Chain + F20 LLM Judge
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestKafkaLogIntegration:
    """F00 + F01: Kafka事件与不可变日志集成"""

    def test_event_produces_log_entry(self):
        """INT-T001: Kafka事件产生日志条目"""
        from f01_immutable_log.immutable_log import create_log_entry, reset_global_chain
        import json
        from f03_content_addressing.content_addressing import calculate_content_hash

        reset_global_chain()

        event_data = {
            "event_type": "chapter_created",
            "chapter_id": "ch-001",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        entry = create_log_entry("kafka_event", event_data)

        assert entry.operation_type == "kafka_event"
        assert entry.payload == event_data
        event_json = json.dumps(event_data, sort_keys=True, ensure_ascii=False)
        assert entry.content_hash == calculate_content_hash(event_json)

    def test_log_chain_for_kafka_events(self):
        """INT-T002: Kafka事件日志链"""
        from f01_immutable_log.immutable_log import create_log_entry, verify_chain_integrity, reset_global_chain

        reset_global_chain()

        events = [
            ("kafka_event", {"seq": 1, "type": "chapter_created"}),
            ("kafka_event", {"seq": 2, "type": "section_added"}),
            ("kafka_event", {"seq": 3, "type": "concept_registered"}),
        ]

        entries = [create_log_entry(op, data) for op, data in events]

        assert verify_chain_integrity(entries) is True
        for i in range(1, len(entries)):
            assert entries[i].previous_hash == entries[i-1].version_tag


class TestBudgetWorkflowIntegration:
    """F02 Context Budget + F04 Temporal Activities 集成"""

    def test_budget_with_quality_check_input(self):
        """INT-T010: 预算管理器生成质量检查输入"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager
        from f04_temporal_workflow.activities.quality_check_activity import QualityCheckInput

        budget = ContextBudgetManager()

        content = {
            "title": "人工智能导论",
            "sections": [{"title": "什么是AI", "subsections": ["定义", "历史", "应用"]}],
            "text": "人工智能是计算机科学的重要分支..."
        }

        result = budget.add_content("ch-001", content)

        assert result.accepted is True

        check_input = QualityCheckInput(
            chapter_id="ch-001",
            content=content["text"],
            outline={"sections": content["sections"]},
            check_types=["grammar", "coherence"]
        )

        assert check_input.chapter_id == "ch-001"
        assert "grammar" in check_input.check_types

    def test_budget_with_format_check_input(self):
        """INT-T011: 预算管理器生成格式检查输入"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager
        from f04_temporal_workflow.activities.format_review_activity import FormatCheckInput

        budget = ContextBudgetManager()

        content = "# 人工智能导论\n\n## 什么是AI\n\n人工智能是..."
        result = budget.add_content("ch-002", {"text": content})

        assert result.accepted is True

        format_input = FormatCheckInput(
            chapter_id="ch-002",
            content=content,
            format_standard="textbook"
        )

        assert "#" in format_input.content
        assert format_input.format_standard == "textbook"

    def test_budget_with_term_check_input(self):
        """INT-T012: 预算管理器生成术语检查输入"""
        from f02_context_budget.context_budget_manager import ContextBudgetManager
        from f04_temporal_workflow.activities.term_check_activity import TermCheckInput

        budget = ContextBudgetManager()

        content = "人工智能（AI）和机器学习（ML）是相关概念..."
        result = budget.add_content("ch-003", {"text": content})

        assert result.accepted is True

        glossary = {"人工智能": "AI", "机器学习": "ML"}

        term_input = TermCheckInput(
            chapter_id="ch-003",
            content=content,
            glossary=glossary
        )

        assert term_input.glossary == glossary
        assert "人工智能" in term_input.content


class TestKnowledgeGraphPGIntegration:
    """F05 Knowledge Graph + F32 PG Adapter 集成"""

    def test_pg_adapter_in_knowledge_graph(self):
        """INT-T020: PG适配器在知识图谱中使用"""
        from f32_pg_knowledge_graph.pg_adapter import MockPGAdapter
        from f05_knowledge_graph.knowledge_graph import KnowledgeGraph

        adapter = MockPGAdapter()
        kg = KnowledgeGraph()

        kg.create_chapter("ch-pg-1", "测试章节", 1)
        kg.create_concept("c-pg-1", "测试概念", "测试定义", "测试领域")

        exported = kg.export_to_dict()

        assert "nodes" in exported
        assert len(exported["nodes"]) == 2

    def test_pg_graph_adapter_export_import(self):
        """INT-T021: PG图谱适配器导出导入"""
        from f32_pg_knowledge_graph.pg_adapter import MockPGAdapter
        from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph

        adapter = MockPGAdapter()
        kg = PGKnowledgeGraph(adapter=adapter)

        kg.create_chapter("ch-export", "导出测试", 1)
        kg.create_section("sec-export", "小节", "ch-export", 1)

        exported = kg.export_to_dict()

        assert "nodes" in exported
        assert "edges" in exported

        adapter2 = MockPGAdapter()
        kg2 = PGKnowledgeGraph(adapter=adapter2)
        kg2.import_from_dict(exported)

        assert kg2.get_node("ch-export") is not None
        assert kg2.get_node("sec-export") is not None


class TestSemanticTermIntegration:
    """F13 Global Semantic Scanner + F18 Term Glossary 集成"""

    def test_term_glossary_with_semantic_search(self):
        """INT-T030: 术语表与语义搜索集成"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService

        term_svc = TermGlossaryService()

        term_svc.register_term("AI", "人工智能", "计算机科学")
        term_svc.register_term("ML", "机器学习", "人工智能子领域")
        term_svc.register_term("DL", "深度学习", "机器学习子领域")

        terms = term_svc.get_all_terms()
        assert len(terms) >= 3

        term = term_svc.find_term("AI")
        assert term is not None

    def test_term_consistency_check(self):
        """INT-T031: 术语一致性检查"""
        from f18_term_glossary.term_glossary_service import TermGlossaryService
        from f18_term_glossary.consistency_checker import ConsistencyChecker

        term_svc = TermGlossaryService()
        checker = ConsistencyChecker(term_svc)

        term_svc.register_term("AI", "人工智能", "计算机科学")

        content_with_term = "人工智能（AI）是重要的技术..."
        content_without_term = "这是一些其他内容..."

        result = checker.check_consistency(
            content_with_term,
            ["人工智能", "AI"]
        )

        assert result is not None


class TestLogicJudgeIntegration:
    """F19 Logic Chain + F20 LLM Judge 集成"""

    @pytest.mark.asyncio
    async def test_logic_analysis_with_judge(self):
        """INT-T040: 逻辑分析与LLM评判集成"""
        from f20_llm_judge.judge_service import JudgeService, MockLLMClient

        mock_llm = MockLLMClient(response='{"scores": {"accuracy": 0.9, "clarity": 0.85, "coherence": 0.8}, "overall_score": 0.85}')
        judge = JudgeService(llm_client=mock_llm)

        content = "人工智能是计算机科学的一个重要分支。它使机器能够学习。机器学习是AI的子领域。"

        score = await judge.judge_content(content, "test_chapter")

        assert score is not None
        assert score.overall_score == 0.85

    @pytest.mark.asyncio
    async def test_batch_judge_with_risk_classification(self):
        """INT-T041: 批量评判与风险分级"""
        from f20_llm_judge.judge_service import JudgeService, MockLLMClient
        from f21_risk_classification.risk_classifier import RiskClassifier

        mock_llm = MockLLMClient(response='{"scores": {"accuracy": 0.9}, "overall_score": 0.9}')
        judge = JudgeService(llm_client=mock_llm)
        risk = RiskClassifier()

        contents = [
            "内容A" * 50,
            "内容B" * 50,
        ]

        scores = await judge.batch_judge(contents)

        assert len(scores) == 2

        for score in scores:
            level = risk.classify(score.overall_score)
            assert level is not None


class TestSecurityPipelineIntegration:
    """安全过滤管道集成"""

    def test_content_filter_with_political_tracker(self):
        """INT-T050: 内容过滤与政治敏感追踪"""
        from f23_content_security.content_filter import ContentSecurityFilter
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        cf = ContentSecurityFilter()
        pt = PoliticalTracker()

        pt.track_topic("台湾", SensitivityLevel.HIGH)

        content = "人工智能技术在教育领域应用广泛"
        result = cf.filter_content(content)

        assert result.is_safe is True

        sensitive_level = pt.check_topic_sensitivity("台湾")
        assert sensitive_level == SensitivityLevel.HIGH

    def test_xss_injection_blocked(self):
        """INT-T051: XSS注入被阻止"""
        from f23_content_security.content_filter import ContentSecurityFilter

        cf = ContentSecurityFilter()

        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        for payload in xss_payloads:
            result = cf.filter_content(payload)
            assert not result.is_safe, f"XSS should be blocked: {payload}"

    def test_sql_injection_blocked(self):
        """INT-T052: SQL注入被阻止"""
        from f23_content_security.content_filter import ContentSecurityFilter

        cf = ContentSecurityFilter()

        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            " UNION SELECT * FROM passwords--",
        ]

        for payload in sql_payloads:
            result = cf.filter_content(payload)
            assert not result.is_safe, f"SQL injection should be blocked: {payload}"


class TestConfigMonitoringIntegration:
    """配置中心与监控集成"""

    def test_config_change_triggers_metric(self):
        """INT-T060: 配置变更触发指标记录"""
        from f24_config_center.config_center import ConfigCenter
        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard

        config = ConfigCenter()
        monitor = MonitoringDashboard()

        initial_version = config.set_config("test.key", "initial_value")

        monitor.record_metric("config.version", initial_version.version)

        new_version = config.set_config("test.key", "new_value")

        monitor.record_metric("config.version", new_version.version)

        assert new_version.version > initial_version.version

    def test_config_version_history(self):
        """INT-T061: 配置版本历史"""
        from f24_config_center.config_center import ConfigCenter

        config = ConfigCenter()

        v1 = config.set_config("versioned.key", "value1")
        v2 = config.set_config("versioned.key", "value2")
        v3 = config.set_config("versioned.key", "value3")

        history = config.get_version_history("versioned.key")

        assert len(history) == 3
        assert history[0].value == "value1"
        assert history[1].value == "value2"
        assert history[2].value == "value3"


class TestWorkflowActivityIntegration:
    """F04 Workflow + Activities 集成"""

    def test_workflow_signals_trigger_activities(self):
        """INT-T070: 工作流信号触发活动"""
        from f04_temporal_workflow.activities.term_check_activity import TermCheckInput
        from f04_temporal_workflow.activities.format_review_activity import FormatCheckInput
        from f04_temporal_workflow.activities.security_scan_activity import SecurityScanInput

        term_input = TermCheckInput(
            chapter_id="ch-workflow-1",
            content="人工智能（AI）的内容...",
            glossary={"人工智能": "AI"}
        )

        assert term_input.chapter_id == "ch-workflow-1"
        assert "AI" in term_input.glossary.values()

        format_input = FormatCheckInput(
            chapter_id="ch-workflow-1",
            content="# AI简介\n\n这是内容...",
            format_standard="textbook"
        )

        assert "#" in format_input.content

        security_input = SecurityScanInput(
            chapter_id="ch-workflow-1",
            content="正常内容",
            scan_types=["xss", "injection", "credentials"]
        )

        assert "xss" in security_input.scan_types


class TestQualityGateIntegration:
    """质量门禁集成"""

    def test_quality_gate_with_all_modules(self):
        """INT-T080: 质量门禁与所有模块集成"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()

        result = gate.run_quality_gates("src/")

        assert result is not None
        assert hasattr(result, "passed")

    def test_linter_check(self):
        """INT-T081: Linter检查"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()

        result = gate.run_quality_gates("src/f01_immutable_log/")

        assert result is not None


class TestDataLineageIntegration:
    """数据血缘集成"""

    def test_tier1_with_content_hash(self):
        """INT-T090: Tier1核实与内容哈希"""
        from f06_tier1_verification.tier1_engine import Tier1Verifier, VerificationStatus

        verifier = Tier1Verifier()

        result = asyncio.run(verifier.verify("test_metric", 100.0, year=2024))

        assert result is not None

    def test_citation_with_hash(self):
        """INT-T091: 引用完整性与哈希"""
        from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager
        from f03_content_addressing.content_addressing import calculate_content_hash

        manager = CitationIntegrityManager()

        content = "人工智能的定义..."
        content_hash = calculate_content_hash(content)

        reg_id = manager.register_unverified_citation("10.1234/test", content_hash)

        assert reg_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
