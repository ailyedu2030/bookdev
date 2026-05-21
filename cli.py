"""AI多Agent教材编写系统 - 主CLI入口"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def cmd_test(args):
    import subprocess
    cmd = ["python", "-m", "pytest", "src/", "-v", "--tb=short"]
    if args.quiet:
        cmd[4] = "-q"
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    env = os.environ.copy()
    env["MOCK_TEMPORAL"] = "true"
    subprocess.run(cmd, env=env)


def cmd_status(args):
    import importlib
    modules = [
        ("F01", "不可变日志", "f01_immutable_log.immutable_log"),
        ("F02", "上下文预算", "f02_context_budget.context_budget_manager"),
        ("F03", "内容寻址", "f03_content_addressing.content_addressing"),
        ("F04", "Temporal工作流", "f04_temporal_workflow.workflows.textbook_chapter"),
        ("F05", "知识图谱", "f05_knowledge_graph.knowledge_graph"),
        ("F06", "数值核实", "f06_tier1_verification.tier1_engine"),
        ("F07", "DOI验证", "f07_doi_verification.doi_verifier"),
        ("F08", "法规核实", "f08_regulation_verification.regulation_verifier"),
        ("F09", "素材安全", "f09_material_security.material_security_manager"),
        ("F10", "概念安全", "f10_concept_security.concept_security"),
        ("F11", "工作流安全", "f11_workflow_security.workflow_security_manager"),
        ("F12", "审批安全", "f12_approval_security.approval_security_manager"),
        ("F13", "语义扫描", "f13_global_semantic_scanner.semantic_scanner"),
        ("F14", "引用完整性", "f14_citation_integrity.citation_integrity_manager"),
        ("F15", "政治敏感", "f15_political_sensitivity.political_tracker"),
        ("F16", "统计抽样", "f16_statistical_sampling.sampling_engine"),
        ("F17", "跨章引用", "f17_cross_reference.reference_resolver"),
        ("F18", "术语表", "f18_term_glossary.term_glossary_service"),
        ("F19", "逻辑链", "f19_logic_chain.logic_chain_service"),
        ("F20", "LLM评判", "f20_llm_judge.judge_service"),
        ("F21", "风险分级", "f21_risk_classification.risk_classifier"),
        ("F22", "素材RAG", "f22_material_rag.rag_engine"),
        ("F23", "内容安全过滤", "f23_content_security.content_filter"),
        ("F24", "配置中心", "f24_config_center.config_center"),
        ("F25", "模型路由", "f25_model_router.model_router"),
        ("F26", "血缘追踪", "f26_lineage_tracker.lineage_tracker"),
        ("F27", "GraphRAG", "f27_graph_rag.graph_rag_query"),
        ("F28", "监控仪表盘", "f28_monitoring_dashboard.monitoring_dashboard"),
        ("F29", "质量门禁", "f29_quality_gate.quality_gate"),
        ("F30", "Golden Dataset", "f30_golden_dataset.dataset_builder"),
    ]

    print("=" * 70)
    print("  AI多Agent教材编写系统 v1.0 - 模块状态")
    print("=" * 70)
    print(f"{'节点':<6} {'模块':<24} {'状态'}")
    print("-" * 70)

    ok = 0
    fail = 0
    for node_id, name, path in modules:
        try:
            importlib.import_module(path)
            print(f"  {node_id:<4} {name:<24} {'✅'}")
            ok += 1
        except Exception as e:
            print(f"  {node_id:<4} {name:<24} {'❌ ' + str(e)[:40]}")
            fail += 1

    print("-" * 70)
    print(f"  总计: {ok+fail} | 就绪: {ok} | 不可用: {fail}")
    print("=" * 70)


def cmd_check(args):
    """快速系统检查"""
    try:
        from f01_immutable_log.immutable_log import ImmutableLog
        log = ImmutableLog()
        log.append("system_check", {"status": "online"})
        print(f"✅ 不可变日志: {len(log.get_entries())} 条")

        from f02_context_budget.context_budget_manager import ContextBudgetManager
        budget = ContextBudgetManager()
        u = budget.get_total_usage()
        print(f"✅ 上下文预算: {u if isinstance(u, int | float) else u.get('total', 0)} tokens")

        from f03_content_addressing.content_addressing import calculate_content_hash
        h = calculate_content_hash("hello world")
        print(f"✅ 内容寻址: SHA256={h[:16]}...")

        from f23_content_security.content_filter import ContentSecurityFilter
        cf = ContentSecurityFilter()
        r = cf.filter_content("正常内容")
        print(f"✅ 安全过滤: {'safe' if r.is_safe else 'blocked'}")

        from f24_config_center.config_center import ConfigCenter
        c = ConfigCenter()
        c.set_config("version", "1.0.0")
        print(f"✅ 配置中心: v{c.get_config('version')}")

        from f28_monitoring_dashboard.monitoring_dashboard import MonitoringDashboard
        d = MonitoringDashboard()
        s = d.get_health_status()
        print(f"✅ 监控: {s.status}")

        print("\n🎉 核心系统检查通过！")
    except Exception as e:
        print(f"❌ 检查失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="AI多Agent教材编写系统 v1.0")
    sub = parser.add_subparsers(dest="command")

    tp = sub.add_parser("test", help="运行测试")
    tp.add_argument("-q", "--quiet", action="store_true")
    tp.add_argument("-c", "--coverage", action="store_true")
    tp.add_argument("--xfail", action="store_true")

    sub.add_parser("status", help="模块状态")
    sub.add_parser("check", help="快速检查")

    args = parser.parse_args()
    if args.command == "test":
        cmd_test(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "check":
        cmd_check(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
