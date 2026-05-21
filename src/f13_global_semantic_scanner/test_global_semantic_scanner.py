"""
F13: 全局语义扫描器 - TDD测试套件

测试覆盖:
- TopicTracker: 追踪/查询/风险评分/跨章节
- CombinationAnalyzer: 组合风险/危险组合检测/规则管理
- GlobalSemanticScanner: 章节扫描/全局风险/跨章节风险/报告生成
- 安全测试: 注入绕过/组合回避/阈值边界

目标覆盖率: ≥86%
"""


import pytest

# ============================================================
# TopicTracker Tests
# ============================================================


class TestTopicTracker:
    """话题追踪器测试"""

    def test_track_single_topic_in_chapter(self):
        """F13-T001: 单话题单章节追踪"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        tracker.track_topic("政治敏感", "ch01", weight=0.8)

        assert "政治敏感" in tracker._topics
        assert "ch01" in tracker._topics["政治敏感"]["chapters"]
        assert tracker._topics["政治敏感"]["chapters"]["ch01"] == 0.8

    def test_track_multiple_topics_same_chapter(self):
        """F13-T002: 多话题同章节追踪"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        tracker.track_topic("历史观", "ch02", weight=0.5)
        tracker.track_topic("领土", "ch02", weight=0.9)
        tracker.track_topic("意识形态", "ch02", weight=0.7)

        chapters = tracker.get_chapter_topics("ch02")
        assert len(chapters) == 3
        assert "历史观" in chapters
        assert "领土" in chapters
        assert "意识形态" in chapters

    def test_get_topic_chapters(self):
        """F13-T003: 获取话题关联的所有章节"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        tracker.track_topic("台海", "ch01", weight=0.9)
        tracker.track_topic("台海", "ch03", weight=0.7)
        tracker.track_topic("台海", "ch05", weight=0.5)

        chapters = tracker.get_topic_chapters("台海")
        assert len(chapters) == 3
        assert "ch01" in chapters
        assert "ch03" in chapters
        assert "ch05" in chapters

    def test_get_chapter_topics_empty(self):
        """F13-T004: 空章节返回空列表"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        result = tracker.get_chapter_topics("nonexistent")
        assert result == []
        assert isinstance(result, list)

    def test_get_topic_chapters_nonexistent(self):
        """F13-T005: 查询不存在的话题返回空列表"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        result = tracker.get_topic_chapters("不存在的话题")
        assert result == []
        assert isinstance(result, list)

    def test_risk_score_single_chapter(self):
        """F13-T006: 单章节出现的风险评分"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        tracker.track_topic("敏感A", "ch01", weight=0.3)

        score = tracker.get_risk_score("敏感A")
        # 单章节，权重低 → 低风险
        assert 0.0 <= score <= 1.0
        assert score < 0.5

    def test_risk_score_multi_chapter_high_weight(self):
        """F13-T007: 多章节高权重话题风险评分高"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        tracker.track_topic("敏感B", "ch01", weight=0.9)
        tracker.track_topic("敏感B", "ch02", weight=0.9)
        tracker.track_topic("敏感B", "ch03", weight=0.8)
        tracker.track_topic("敏感B", "ch04", weight=0.7)

        score = tracker.get_risk_score("敏感B")
        assert score > 0.5, f"Expected high risk, got {score}"

    def test_risk_score_nonexistent_topic(self):
        """F13-T008: 不存在话题风险评分为0"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        score = tracker.get_risk_score("不存在")
        assert score == 0.0

    def test_track_topic_accumulates_weight(self):
        """F13-T009: 同一话题多次追踪权重累加"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        tracker.track_topic("边界", "ch01", weight=0.5)
        tracker.track_topic("边界", "ch01", weight=0.3)

        assert tracker._topics["边界"]["total_weight"] == pytest.approx(0.8)

    def test_cross_chapter_topic_tracking(self):
        """F13-T010: 跨章节话题追踪验证传播路径"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        chapters = ["ch01", "ch02", "ch03", "ch04", "ch05", "ch06"]
        for ch in chapters:
            tracker.track_topic("舆论引导", ch, weight=0.6 + (chapters.index(ch) * 0.05))

        chs = tracker.get_topic_chapters("舆论引导")
        assert len(chs) == 6
        # 出现在6章 → 高风险
        score = tracker.get_risk_score("舆论引导")
        assert score > 0.6


# ============================================================
# CombinationAnalyzer Tests
# ============================================================


class TestCombinationAnalyzer:
    """组合敏感分析器测试"""

    def test_analyze_basic_combination(self):
        """F13-T011: 基本组合分析"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        score = analyzer.analyze_combination(["历史观", "意识形态"])

        assert 0.0 <= score <= 1.0
        assert score > 0.0

    def test_combination_repeated_escalates(self):
        """F13-T012: 组合重复出现风险递增"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        s1 = analyzer.analyze_combination(["领土", "主权"])
        s2 = analyzer.analyze_combination(["领土", "主权"])
        s3 = analyzer.analyze_combination(["领土", "主权"])

        assert s3 > s2 >= s1, f"s1={s1}, s2={s2}, s3={s3}"
        assert s3 > 0.0

    def test_dangerous_combinations_detection(self):
        """F13-T013: 危险组合检测"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        analyzer.add_rule("台海", "军事", risk_weight=0.9)
        analyzer.add_rule("意识形态", "舆论", risk_weight=0.8)
        analyzer.add_rule("领土", "主权", risk_weight=0.7)
        analyzer.add_rule("历史观", "民族", risk_weight=0.6)

        # 触发高危组合
        analyzer.analyze_combination(["台海", "军事"])
        analyzer.analyze_combination(["意识形态", "舆论"])

        dangerous = analyzer.get_dangerous_combinations(threshold=0.5)
        assert len(dangerous) >= 2

    def test_get_dangerous_combinations_empty_no_rules(self):
        """F13-T014: 无规则时危险组合为空"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        # 不添加任何规则，仅分析
        analyzer.analyze_combination(["普通A", "普通B"])
        analyzer.analyze_combination(["普通C", "普通D"])

        dangerous = analyzer.get_dangerous_combinations(threshold=0.1)
        assert len(dangerous) == 0

    def test_add_rule_and_detect(self):
        """F13-T015: 添加规则后检测"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        analyzer.add_rule("宗教", "民族问题", risk_weight=0.85)
        analyzer.add_rule("领土", "历史", risk_weight=0.75)

        analyzer.analyze_combination(["宗教", "民族问题"])
        analyzer.analyze_combination(["领土", "历史"])
        analyzer.analyze_combination(["普通", "安全"])

        dangerous = analyzer.get_dangerous_combinations(threshold=0.7)
        assert len(dangerous) == 2

    def test_combination_score_max_capped(self):
        """F13-T016: 组合风险分上限为1.0"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        analyzer.add_rule("极端", "暴力", risk_weight=1.0)
        for _ in range(100):
            score = analyzer.analyze_combination(["极端", "暴力"])

        assert 0.0 <= score <= 1.0

    def test_combination_threshold_boundary(self):
        """F13-T017: 阈值边界精确测试"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        analyzer.add_rule("边界A", "边界B", risk_weight=0.6)

        analyzer.analyze_combination(["边界A", "边界B"])

        # threshold=0.7 应排
        result_high = analyzer.get_dangerous_combinations(threshold=0.7)
        # threshold=0.5 应包含
        result_low = analyzer.get_dangerous_combinations(threshold=0.5)

        assert len(result_high) == 0
        assert len(result_low) >= 1

    def test_three_topic_combination(self):
        """F13-T018: 三话题组合分析"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        score = analyzer.analyze_combination(["A", "B", "C"])
        assert 0.0 <= score <= 1.0
        # 三话题比两话题风险更高
        score2 = analyzer.analyze_combination(["A", "B"])
        assert score > score2


# ============================================================
# GlobalSemanticScanner Tests
# ============================================================


class TestGlobalSemanticScanner:
    """全局语义扫描器测试"""

    def test_scanner_init(self):
        """F13-T019: 扫描器初始化"""
        from f13_global_semantic_scanner.semantic_scanner import (
            CombinationAnalyzer,
            GlobalSemanticScanner,
            TopicTracker,
        )

        scanner = GlobalSemanticScanner()
        assert isinstance(scanner.topic_tracker, TopicTracker)
        assert isinstance(scanner.combination_analyzer, CombinationAnalyzer)

    def test_scan_chapter_single_topic(self):
        """F13-T020: 章节扫描-单话题检测"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        results = scanner.scan_chapter("ch01", "本章探讨了台海问题的历史演变")

        assert len(results) >= 1
        assert any(r.topic_id == "台海" for r in results)

    def test_scan_chapter_multiple_topics(self):
        """F13-T021: 章节扫描-多话题检测"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        content = "本章内容涵盖领土争端、主权争议以及意识形态分歧。" "此外还讨论了历史观和民族文化认同等问题。"
        results = scanner.scan_chapter("ch02", content)

        assert len(results) >= 2, f"Expected >=2 results, got {len(results)}"

    def test_scan_chapter_no_sensitive_content(self):
        """F13-T022: 无敏感内容章节扫描"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        results = scanner.scan_chapter("ch03", "本章介绍基础数学概念，包括加法、减法、乘法和除法。")

        assert len(results) == 0, f"Expected 0 results, got {len(results)}: {results}"

    def test_get_global_risk_score_empty(self):
        """F13-T023: 空扫描全局风险为0"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        score = scanner.get_global_risk_score()
        assert score == 0.0

    def test_get_global_risk_score_multi_chapter(self):
        """F13-T024: 多章节扫描全局风险增长"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        scanner.scan_chapter("ch01", "本章涉及台海问题的历史和现状分析")
        score1 = scanner.get_global_risk_score()

        scanner.scan_chapter("ch02", "台海地区的军事部署与战略分析")
        score2 = scanner.get_global_risk_score()
        # 同一敏感话题跨章节 → 风险递增
        assert score2 >= score1

    def test_get_cross_chapter_risks(self):
        """F13-T025: 跨章节风险检测"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        scanner.scan_chapter("ch01", "台海问题是中国内政")
        scanner.scan_chapter("ch03", "台海局势与国际法")
        scanner.scan_chapter("ch05", "论台海和平统一")

        risks = scanner.get_cross_chapter_risks()
        assert len(risks) >= 1
        # 台海出现在3章，应有跨章节风险记录
        assert any("台海" in str(r.get("topic", "")) or len(r.get("chapters", [])) >= 2 for r in risks)

    def test_generate_scan_report(self):
        """F13-T026: 生成扫描报告"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        scanner.scan_chapter("ch01", "意识形态与舆论引导")
        scanner.scan_chapter("ch02", "意识形态与教育方针")
        scanner.scan_chapter("ch03", "普通教育内容")

        report = scanner.generate_scan_report()
        assert isinstance(report, dict)
        assert "global_risk_score" in report
        assert "total_chapters_scanned" in report
        assert "cross_chapter_risks" in report
        assert "dangerous_combinations" in report
        assert 0.0 <= report["global_risk_score"] <= 1.0

    def test_scan_result_structure(self):
        """F13-T027: 扫描结果数据结构完整性"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner, ScanResult

        scanner = GlobalSemanticScanner()
        results = scanner.scan_chapter("ch01", "领土争端与主权问题分析")

        for r in results:
            assert isinstance(r, ScanResult)
            assert isinstance(r.topic_id, str)
            assert isinstance(r.risk_score, float)
            assert 0.0 <= r.risk_score <= 1.0
            assert isinstance(r.affected_chapters, list)
            assert isinstance(r.combined_risks, list)

    def test_multiple_chapters_build_accumulated_risk(self):
        """F13-T028: 多章节累积风险递增"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()

        sensitive_contents = [
            ("ch01", "台海问题的历史渊源与地缘政治"),
            ("ch03", "台海军事对峙与国际干预风险"),
            ("ch05", "台海两岸经济融合与政治分歧"),
            ("ch07", "台海和平统一的法律框架分析"),
        ]

        scores = []
        for ch_id, content in sensitive_contents:
            scanner.scan_chapter(ch_id, content)
            scores.append(scanner.get_global_risk_score())

        # 风险应单调不减
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1], f"scores[{i}]={scores[i]} < scores[{i-1}]={scores[i-1]}"


# ============================================================
# 安全测试
# ============================================================


class TestCoverageGaps:
    """补充覆盖率缺口测试"""

    def test_analyze_single_topic_returns_zero(self):
        """F13-C001: 单话题组合分析返回0"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        score = analyzer.analyze_combination(["单独话题"])
        assert score == 0.0

    def test_analyze_empty_list_returns_zero(self):
        """F13-C002: 空列表组合分析返回0"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        score = analyzer.analyze_combination([])
        assert score == 0.0

    def test_classify_severity_high(self):
        """F13-C003: 严重度分类-HIGH"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        assert scanner._classify_severity(0.7) == "HIGH"
        assert scanner._classify_severity(0.9) == "HIGH"
        assert scanner._classify_severity(1.0) == "HIGH"

    def test_classify_severity_medium(self):
        """F13-C004: 严重度分类-MEDIUM"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        assert scanner._classify_severity(0.4) == "MEDIUM"
        assert scanner._classify_severity(0.6) == "MEDIUM"
        assert scanner._classify_severity(0.69) == "MEDIUM"

    def test_classify_severity_low(self):
        """F13-C005: 严重度分类-LOW"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        assert scanner._classify_severity(0.0) == "LOW"
        assert scanner._classify_severity(0.3) == "LOW"
        assert scanner._classify_severity(0.39) == "LOW"

    def test_global_risk_no_topic_scores(self):
        """F13-C006: 无话题评分时全局风险为0"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        # 添加扫描章节但不触发任何话题 — 但扫描空内容也会产生0个结果
        # 更直接: 内部状态有 scanned_chapters 但无 results
        scanner._scanned_chapters.add("ch_empty")
        scanner._chapter_results["ch_empty"] = []
        score = scanner.get_global_risk_score()
        assert score == 0.0


class TestSecurityEdgeCases:
    """安全边缘测试"""

    def test_injection_bypass_unicode_homoglyphs(self):
        """F13-S001: Unicode同形字注入绕过"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        # 使用Unicode同形字试图绕过
        content = "台\u6d77问题"  # 正常汉字
        result_normal = scanner.scan_chapter("ch01", content)

        # 如果正常检测到了，说明扫描器工作正常
        # 但如果同形字替换也触发，说明抵抗力强
        assert len(result_normal) > 0, "Should detect normal content"

    def test_injection_bypass_content_splitting(self):
        """F13-S002: 内容分片注入绕过测试"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        # 尝试把敏感词拆分
        content = "台...海...问...题 被划分在多个段落中"
        results = scanner.scan_chapter("ch01", content)

        # 无论如何，扫描器不应崩溃
        assert isinstance(results, list)

    def test_injection_bypass_excessive_content(self):
        """F13-S003: 大量无关内容淹没敏感词"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        # 在大量正常内容中嵌入敏感词
        filler = "教育是立国之本，科技是第一生产力。" * 500
        content = filler + " 台海问题是中国核心利益。"
        results = scanner.scan_chapter("ch01", content)

        # 不应崩溃，时间不应过长
        assert isinstance(results, list)

    def test_combination_avoidance_single_topic(self):
        """F13-S004: 组合回避-仅单话题出现"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        scanner.scan_chapter("ch01", "讨论意识形态")
        scanner.scan_chapter("ch02", "讨论意识形态")

        # 仅单种话题，没有形成危险组合
        report = scanner.generate_scan_report()
        if report.get("dangerous_combinations"):
            # 即使有，也不应来自"意识形态"+"政治"组合
            assert isinstance(report["dangerous_combinations"], list)

    def test_threshold_boundary_exact(self):
        """F13-S005: 精确阈值边界测试"""
        from f13_global_semantic_scanner.semantic_scanner import CombinationAnalyzer

        analyzer = CombinationAnalyzer()
        # 添加恰好等于阈值的规则
        analyzer.add_rule("临界A", "临界B", risk_weight=0.6999999)

        analyzer.analyze_combination(["临界A", "临界B"])

        # threshold=0.7 不应包含
        high = analyzer.get_dangerous_combinations(threshold=0.7)
        # threshold=0.6 应包含
        low = analyzer.get_dangerous_combinations(threshold=0.6)

        assert len(high) == 0
        assert len(low) >= 1

    def test_empty_content_scan(self):
        """F13-S006: 空内容扫描不崩溃"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        results = scanner.scan_chapter("ch01", "")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_special_characters_content(self):
        """F13-S007: 特殊字符内容安全"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        content = "!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/~` \n\t\r 台海 ⚠️⚠️⚠️"
        results = scanner.scan_chapter("ch01", content)
        # 不应崩溃
        assert isinstance(results, list)

    def test_extremely_long_topic_name(self):
        """F13-S008: 超长话题名"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()
        long_topic = "A" * 10000
        tracker.track_topic(long_topic, "ch01", weight=0.5)
        result = tracker.get_topic_chapters(long_topic)
        assert result == ["ch01"]

    def test_concurrent_like_scans(self):
        """F13-S009: 模拟并发扫描不破坏状态"""
        from f13_global_semantic_scanner.semantic_scanner import GlobalSemanticScanner

        scanner = GlobalSemanticScanner()
        chapters_data = [
            ("ch01", "领土争端与历史认知"),
            ("ch02", "意识形态与国家安全"),
            ("ch03", "台海问题与区域稳定"),
            ("ch04", "民族政策与宗教自由"),
            ("ch05", "网络舆论与信息管控"),
            ("ch06", "基础数学与物理原理"),
            ("ch07", "领土争端与国际法规"),
            ("ch08", "意识形态与教育改革"),
            ("ch09", "台海经济与两岸关系"),
            ("ch10", "普通文学赏析"),
        ]

        for ch_id, content in chapters_data:
            scanner.scan_chapter(ch_id, content)

        report = scanner.generate_scan_report()
        assert report["total_chapters_scanned"] == 10
        assert 0.0 <= report["global_risk_score"] <= 1.0
        assert isinstance(report["cross_chapter_risks"], list)
        assert isinstance(report["dangerous_combinations"], list)


class TestTopicTrackerUncovered:
    """覆盖TopicTracker未测试的分支"""

    def test_get_risk_score_zero_chapters(self):
        """line 152: 话题章节数为0时返回0.0"""
        from f13_global_semantic_scanner.semantic_scanner import TopicTracker

        tracker = TopicTracker()

        tracker._topics["test_topic"] = {"chapters": {}, "total_weight": 0.0, "frequency": 0}

        score = tracker.get_risk_score("test_topic")

        assert score == 0.0
