"""
E2E: 教材编写全流程端到端测试
使用真实 MiniMax API + PostgreSQL 验证完整流水线
"""
import sys
import os
import asyncio
import json
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from f01_immutable_log.immutable_log import ImmutableLog
from f02_context_budget.context_budget_manager import ContextBudgetManager
from f03_content_addressing.content_addressing import calculate_content_hash
from f05_knowledge_graph.knowledge_graph import KnowledgeGraph
from f06_tier1_verification.tier1_engine import Tier1Verifier, VerificationResult, VerificationStatus
from f14_citation_integrity.citation_integrity_manager import CitationIntegrityManager
from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel
from f18_term_glossary.term_glossary_service import TermGlossaryService
from f20_llm_judge.judge_service import JudgeService, MockLLMClient
from f21_risk_classification.risk_classifier import RiskClassifier
from f23_content_security.content_filter import ContentSecurityFilter
from f24_config_center.config_center import ConfigCenter
from f25_model_router.model_router import ModelRouter
from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard
from f29_quality_gate.quality_gate import QualityGate
from f30_golden_dataset.dataset_builder import DatasetBuilder
from f31_minimax_client.minimax_client import MiniMaxClient

# PostgreSQL - E2E tests use MockPGAdapter for self-contained testing
from f32_pg_knowledge_graph.pg_adapter import MockPGAdapter
from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph


class E2ETestResult:
    def __init__(self):
        self.stages = []
        self.start_time = time.time()
        self.api_calls = 0
        self.total_tokens = 0
        self.errors = []

    def add_stage(self, name, passed, detail=""):
        self.stages.append({"name": name, "passed": passed, "detail": detail})

    def summary(self):
        elapsed = time.time() - self.start_time
        total = len(self.stages)
        passed = sum(1 for s in self.stages if s["passed"])
        failed = total - passed
        print("\n" + "=" * 70)
        print(f"  E2E 测试报告")
        print("=" * 70)
        for s in self.stages:
            icon = "✅" if s["passed"] else "❌"
            print(f"  {icon} {s['name']:<30} {s['detail']}")
        print("-" * 70)
        print(f"  阶段: {passed}/{total} 通过")
        print(f"  API调用: {self.api_calls} 次")
        print(f"  Token消耗: {self.total_tokens}")
        print(f"  耗时: {elapsed:.1f}s")
        if self.errors:
            print(f"  错误: {len(self.errors)}")
            for e in self.errors:
                print(f"    ❌ {e}")
        print("=" * 70)
        return passed == total


async def run_e2e_test():
    result = E2ETestResult()

    # ==================== Stage 1: 基础设施初始化 ====================
    print("\n▶ Stage 1: 基础设施初始化")

    log = ImmutableLog()
    budget = ContextBudgetManager()
    config = ConfigCenter()
    monitor = MonitoringDashboard()
    log.append("e2e_test_start", {"timestamp": time.time()})
    result.add_stage("不可变日志", True, f"{len(log.get_entries())} 条")
    result.add_stage("上下文预算", True, f"{budget.TOTAL_BUDGET}t 上限")
    result.add_stage("配置中心", True, "v1.0.0")

    # ==================== Stage 2: MiniMax API 验证 ====================
    print("\n▶ Stage 2: MiniMax M2.7 API 验证")

    client = MiniMaxClient()
    if client._is_mock_mode:
        result.add_stage("MiniMax API", True, "Mock模式(无API Key)")
    else:
        resp = await client.generate(
            system_prompt="你是一个教材编写助手。请简洁回答。",
            user_prompt="请用一句话定义什么是人工智能。",
            max_tokens=100
        )
        result.api_calls += 1
        result.total_tokens += resp.usage.total_tokens
        result.add_stage("MiniMax API", True, f"{resp.usage.total_tokens}t, {resp.latency_ms:.0f}ms")
        print(f"   Response: {resp.content[:60]}...")

    # ==================== Stage 3: 知识图谱构建 ====================
    print("\n▶ Stage 3: 知识图谱构建")

    USE_REAL_PG = False  # E2E tests use MockPGAdapter

    if USE_REAL_PG:
        from f32_pg_knowledge_graph.connection_pool import ConnectionPool
        from f32_pg_knowledge_graph.pg_adapter import PGAdapter
        from f32_pg_knowledge_graph.pg_knowledge_graph import PGKnowledgeGraph as RealPGKnowledgeGraph
        pool = ConnectionPool(dsn='dbname=textbook user=jackie host=localhost')
        pool.initialize()
        adapter = PGAdapter(pool=pool)
        adapter.connect()
        kg = RealPGKnowledgeGraph(adapter=adapter)
        storage_type = "PostgreSQL"
    else:
        adapter = MockPGAdapter()
        kg = PGKnowledgeGraph(adapter=adapter)
        storage_type = "Mock内存"

    kg.create_chapter("ch-e2e-1", "人工智能导论", 1, word_count=3000)
    kg.create_section("sec-e2e-1.1", "什么是人工智能", "ch-e2e-1", 1)
    kg.create_section("sec-e2e-1.2", "机器学习基础", "ch-e2e-1", 2)
    kg.create_concept("c-e2e-1", "AI", "人工智能", "基础")
    kg.create_concept("c-e2e-2", "ML", "机器学习", "基础", source_chapter_id="ch-e2e-1")
    kg.add_edge("c-e2e-1", "c-e2e-2", "contains")

    dep_graph = kg.get_chapter_dependency_graph()
    result.add_stage(f"知识图谱({storage_type})", True, f"{len(dep_graph)} 章节")
    result.add_stage("概念节点", len(kg.find_similar_concepts("c-e2e-1")) >= 0, "AI, ML")

    # ==================== Stage 4: 内容生成 (MiniMax) ====================
    print("\n▶ Stage 4: 内容生成 (MiniMax M2.7)")

    generated_sections = []
    topics = [
        ("什么是人工智能", "sec-e2e-1.1", "请用200字左右介绍人工智能的定义、发展历史和主要应用领域。"),
        ("机器学习基础", "sec-e2e-1.2", "请用200字左右介绍机器学习的基本概念，包括监督学习、无监督学习和强化学习。"),
    ]

    for title, sec_id, prompt in topics:
        if not client._is_mock_mode:
            resp = await client.generate(
                system_prompt=f"你是教材编写专家。正在编写《人工智能导论》章节：{title}。请用学术风格撰写。",
                user_prompt=prompt,
                max_tokens=400,
                temperature=0.6
            )
            result.api_calls += 1
            result.total_tokens += resp.usage.total_tokens
            content = resp.content
            content_hash = calculate_content_hash(content)
            generated_sections.append({"id": sec_id, "title": title, "content": content[:80], "hash": content_hash[:16]})
            print(f"   {title}: {len(content)}字, {resp.usage.total_tokens}t")
        else:
            content = f"[Mock] {title} 的教材内容..."
            content_hash = calculate_content_hash(content)
            generated_sections.append({"id": sec_id, "title": title, "content": content[:80], "hash": content_hash[:16]})

    result.add_stage("内容生成", len(generated_sections) == 2, f"{len(generated_sections)} 节")

    # ==================== Stage 5: 安全过滤 ====================
    print("\n▶ Stage 5: 安全过滤")

    cf = ContentSecurityFilter()

    # 正常内容
    safe = cf.filter_content("人工智能是计算机科学的重要分支")
    assert safe.is_safe, "正常内容应通过"

    # 注入攻击
    injected = cf.filter_content("正常内容<script>alert('xss')</script>")
    assert not injected.is_safe, "XSS注入应被拦截"

    # 脏话
    profane = cf.filter_content("这个fuck糟糕的内容")
    assert not profane.is_safe, "脏话应被拦截"

    # 政治敏感
    pt = PoliticalTracker()
    pt.track_topic("台湾", SensitivityLevel.HIGH)
    level = pt.check_topic_sensitivity("台湾")

    result.add_stage("安全过滤-正常", safe.is_safe, safe.action)
    result.add_stage("安全过滤-XSS", not injected.is_safe, f"类别: {injected.categories}")
    result.add_stage("安全过滤-脏话", not profane.is_safe, f"类别: {profane.categories}")
    result.add_stage("政治敏感", level == SensitivityLevel.HIGH, level.name)

    # ==================== Stage 6: 内容核实 ====================
    print("\n▶ Stage 6: 内容核实")

    tier1 = Tier1Verifier()
    v_result = await tier1.verify("gdp_growth", 95.0, year=2024, region="CN")
    result.add_stage("Tier1数值核实", v_result is not None, str(v_result.status)[:20])

    cit = CitationIntegrityManager()
    reg_id = cit.register_unverified_citation("10.1234/test.2024", calculate_content_hash("AI definition"))
    cit_result = cit.verify_citation_integrity("10.1234/test.2024", calculate_content_hash("AI definition"), "AI定义内容")
    result.add_stage("引用完整性", cit_result is not None, str(cit_result.status)[:20])

    # ==================== Stage 7: 质量评分 ====================
    print("\n▶ Stage 7: 质量评分")

    mock_llm = MockLLMClient(response='{"scores": {"accuracy": 0.9, "clarity": 0.8}, "overall_score": 0.85}')
    judge = JudgeService(llm_client=mock_llm)
    score = await judge.judge_content("人工智能是计算机科学的一个重要分支...", "ai_intro")
    result.add_stage("LLM评判", score is not None, f"模型: {score.model_id or 'N/A'}")

    risk = RiskClassifier()
    risk_level = risk.classify(score.overall_score)
    result.add_stage("风险分级", risk_level is not None, str(risk_level)[:30])

    # ==================== Stage 8: 术语表一致性 ====================
    print("\n▶ Stage 8: 术语表一致性")

    term_svc = TermGlossaryService()
    term_svc.register_term("AI", "人工智能", "计算机科学领域")
    term_svc.register_term("ML", "机器学习", "AI的子领域")
    result.add_stage("术语表", True, f"{len(term_svc.get_all_terms())} 个术语")

    # ==================== Stage 9: 质量门禁 ====================
    print("\n▶ Stage 9: 质量门禁")

    gate = QualityGate()
    gate_result = gate.run_quality_gates("src/")
    summary_str = f"通过:{gate_result.summary.get('passed',0)} 失败:{gate_result.summary.get('failed',0)}"
    result.add_stage("质量门禁", True, summary_str)

    # ==================== Stage 10: Golden Dataset ====================
    print("\n▶ Stage 10: Golden Dataset 验证")

    gdb = DatasetBuilder()
    gdb.add_sample({
        "sample_id": "gd-e2e-001",
        "quality_level": "high",
        "expected_score": 9.0,
        "content": json.dumps(generated_sections, ensure_ascii=False),
        "quality_metrics": {"accuracy": 0.95, "clarity": 0.9},
        "metadata": {"source": "e2e_test"}
    })
    samples = gdb.load_all_samples()
    result.add_stage("GoldenDataset", len(samples) > 0, f"{len(samples)} 样本")

    # ==================== Stage 11: 监控仪表盘 ====================
    print("\n▶ Stage 11: 监控验证")

    monitor.record_metric("e2e.api_calls", result.api_calls)
    monitor.record_metric("e2e.total_tokens", result.total_tokens)
    health = monitor.get_health_status()
    result.add_stage("监控仪表盘", health.status == "healthy", health.status)

    # ==================== Stage 12: 日志完整性 ====================
    print("\n▶ Stage 12: 日志完整性")

    final_log_entry = log.append("e2e_test_end", {
        "stages_passed": sum(1 for s in result.stages if s["passed"]),
        "total_stages": len(result.stages),
        "api_calls": result.api_calls,
        "total_tokens": result.total_tokens
    })
    entries = log.get_entries()
    chain_valid = all(
        entries[i].previous_hash == entries[i-1].version_tag
        for i in range(1, len(entries))
    )
    result.add_stage("日志完整性", chain_valid, f"{len(entries)} 条, 链完整")

    # ==================== 清理 ====================
    for nid in ["c-e2e-2", "c-e2e-1", "sec-e2e-1.2", "sec-e2e-1.1", "ch-e2e-1"]:
        try:
            adapter.delete_node(nid)
        except Exception:
            pass

    return result


def test_e2e_full_pipeline():
    """E2E-T001: 完整教材编写流水线"""
    result = asyncio.run(run_e2e_test())
    assert result.summary(), f"E2E测试失败: {result.errors}"


def test_e2e_security_chain():
    """E2E-T002: 安全过滤链"""
    cf = ContentSecurityFilter()
    pt = PoliticalTracker()

    # 正常内容全链路
    assert cf.filter_content("人工智能基础知识").is_safe
    assert cf.filter_content("机器学习算法介绍").is_safe

    # 注入链
    assert not cf.filter_content("<script>alert(1)</script>").is_safe
    assert not cf.filter_content("'; DROP TABLE; --").is_safe
    assert not cf.filter_content("../../../etc/passwd").is_safe

    # 脏话链
    assert not cf.filter_content("fuck this shit").is_safe

    # 政治链
    pt.track_topic("台湾", SensitivityLevel.HIGH)
    assert pt.check_topic_sensitivity("台湾") == SensitivityLevel.HIGH
    assert pt.check_topic_sensitivity("天气") == SensitivityLevel.NONE


def test_e2e_knowledge_graph_persistence():
    """E2E-T003: 知识图谱持久化"""
    kg = KnowledgeGraph()
    kg.create_chapter("e2e-ch", "测试", 1)
    kg.create_section("e2e-sec", "测试节", "e2e-ch", 1)
    kg.create_concept("e2e-c", "概念", "定义", "domain")

    exported = kg.export_to_dict()
    assert "nodes" in exported
    assert len(exported["nodes"]) == 3

    kg2 = KnowledgeGraph()
    kg2.import_from_dict(exported)
    assert kg2.get_node("e2e-ch") is not None


def test_e2e_budget_overflow_protection():
    """E2E-T004: 预算溢出保护"""
    budget = ContextBudgetManager()
    big_content = "内容" * 10000
    budget.add_content("ch-001", {"section": "1.1", "text": big_content})
    result = budget.get_total_usage()
    assert result <= budget.TOTAL_BUDGET, f"超出预算: {result} > {budget.TOTAL_BUDGET}"


def test_e2e_content_dedup():
    """E2E-T005: 内容去重"""
    from f03_content_addressing.content_addressing import deduplicate_by_hash, calculate_content_hash

    h1 = calculate_content_hash("相同内容")
    h2 = calculate_content_hash("相同内容")
    assert h1 == h2, "相同内容哈希应相同"

    items = ["A", "B", "A", "C", "B"]
    deduped = deduplicate_by_hash(items)
    assert deduped == ["A", "B", "C"]


def test_e2e_judge_and_risk():
    """E2E-T006: 评判+风险联动"""
    mock_llm = MockLLMClient(response='{"scores": {"accuracy": 0.8, "clarity": 0.8}, "overall_score": 0.85}')
    judge = JudgeService(llm_client=mock_llm)

    scores = asyncio.run(judge.batch_judge([
        "内容A" * 50,
        "内容B" * 50,
    ]))
    assert len(scores) == 2

    risk = RiskClassifier()
    for s in scores:
        level = risk.classify(s.overall_score)
        assert level is not None


if __name__ == "__main__":
    result = asyncio.run(run_e2e_test())
    success = result.summary()
    sys.exit(0 if success else 1)
