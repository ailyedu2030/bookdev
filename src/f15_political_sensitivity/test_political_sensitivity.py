"""
F15: 政治敏感分析 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""


class TestPoliticalTracker:
    """政治敏感追踪器测试"""

    def test_track_sensitive_topic(self):
        """F15-T001: 追踪敏感话题"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        result = tracker.track_topic(
            topic="台湾",
            sensitivity_level=SensitivityLevel.HIGH
        )

        assert result is not None

    def test_check_topic_sensitivity(self):
        """F15-T002: 检查话题敏感度"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker.track_topic("台湾", SensitivityLevel.HIGH)

        level = tracker.check_topic_sensitivity("台湾")

        assert level == SensitivityLevel.HIGH

    def test_nonexistent_topic_returns_none(self):
        """F15-T003: 不存在的话题返回无"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        level = tracker.check_topic_sensitivity("完全无害的话题")

        assert level == SensitivityLevel.NONE

    def test_topic_aggregation(self):
        """F15-T004: 话题聚合"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker.track_topic("台湾", SensitivityLevel.HIGH)
        tracker.track_topic("台湾", SensitivityLevel.HIGH)
        tracker.track_topic("台湾", SensitivityLevel.MEDIUM)

        aggregated = tracker.get_topic_aggregation("台湾")

        assert aggregated.count >= 3

    def test_cross_topic_analysis(self):
        """F15-T005: 跨话题分析"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker.track_topic("台湾", SensitivityLevel.HIGH)
        tracker.track_topic("香港", SensitivityLevel.HIGH)

        analysis = tracker.cross_topic_analysis(["台湾", "香港"])

        assert analysis.is_aggregated_risk is True


class TestSentimentAnalyzer:
    """情感分析器测试"""

    def test_analyze_sentiment_positive(self):
        """F15-T006: 正面情感分析"""
        from f15_political_sensitivity.sentiment_analyzer import Sentiment, SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("这个政策非常好，促进了经济发展")

        assert result.sentiment == Sentiment.POSITIVE

    def test_analyze_sentiment_negative(self):
        """F15-T007: 负面情感分析"""
        from f15_political_sensitivity.sentiment_analyzer import Sentiment, SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("这个政策有问题，导致了严重后果")

        assert result.sentiment == Sentiment.NEGATIVE

    def test_analyze_sentiment_neutral(self):
        """F15-T008: 中性情感分析"""
        from f15_political_sensitivity.sentiment_analyzer import Sentiment, SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("今天天气晴朗")

        assert result.sentiment == Sentiment.NEUTRAL

    def test_polarized_content_detection(self):
        """F15-T009: 极化内容检测"""
        from f15_political_sensitivity.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("完全是垃圾政策，愚蠢透顶！")

        assert result.is_polarized is True

    def test_sentiment_intensity_score(self):
        """F15-T010: 情感强度评分"""
        from f15_political_sensitivity.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer.analyze("这个非常好，非常棒，极其出色！")

        assert result.intensity >= 0.7


class TestInfiltrationDetector:
    """渗透检测器测试"""

    def test_detect_propaganda_pattern(self):
        """F15-T011: 检测宣传模式"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector, ThreatType

        detector = InfiltrationDetector()

        result = detector.detect(
            content="必须支持XX党的决定，这是唯一正确的道路"
        )

        assert result.threat_type == ThreatType.PROPAGANDA

    def test_detect_disinformation(self):
        """F15-T012: 检测虚假信息"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector, ThreatType

        detector = InfiltrationDetector()

        result = detector.detect(
            content="据内幕消息，官方数据都是伪造的"
        )

        assert result.threat_type in [ThreatType.DISINFORMATION, ThreatType.SUBVERSION]

    def test_detect_subversion(self):
        """F15-T013: 检测颠覆内容"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector, ThreatType

        detector = InfiltrationDetector()

        result = detector.detect(
            content="政府腐败无能，必须推翻现有制度"
        )

        assert result.threat_type in [ThreatType.SUBVERSION, ThreatType.HATE_SPEECH]

    def test_safe_content_passes(self):
        """F15-T014: 安全内容通过"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector

        detector = InfiltrationDetector()

        result = detector.detect(
            content="今天学习了人工智能的基础知识"
        )

        assert result.is_safe is True

    def test_detect_coordinated_behavior(self):
        """F15-T015: 检测协调行为"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector

        detector = InfiltrationDetector()

        accounts = [
            "account_1",
            "account_2",
            "account_3",
        ]

        result = detector.detect_coordinated_behavior(accounts)

        assert result is not None


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    def test_propaganda_keyword_injection_prevention(self):
        """F15-S001: 宣传关键词注入防御"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker.track_topic("台湾", SensitivityLevel.HIGH)

        level = tracker.check_topic_sensitivity("台湾 ")

        assert level == SensitivityLevel.HIGH

    def test_bypass_attempt_normalization(self):
        """F15-S002: 绕过尝试规范化"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker.track_topic("台湾", SensitivityLevel.HIGH)

        level1 = tracker.check_topic_sensitivity("台灣")
        level2 = tracker.check_topic_sensitivity("臺灣")

        assert level1 != SensitivityLevel.NONE or level2 != SensitivityLevel.NONE

    def test_adversarial_sentiment_manipulation(self):
        """F15-S003: 对抗性情感操纵"""
        from f15_political_sensitivity.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        content = "好" * 100
        result = analyzer.analyze(content)

        assert result.is_polarized is True

    def test_adversarial_pattern_evasion(self):
        """F15-S004: 对抗模式规避检测"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector

        detector = InfiltrationDetector()

        result = detector.detect("使 用 某 些 手 段 操 纵 舆 论")

        assert result.is_safe is False or result.confidence >= 0.5

    def test_sentiment_analysis_dos_prevention(self):
        """F15-S005: 情感分析DoS预防"""
        from f15_political_sensitivity.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        long_content = "好" * 10000

        result = analyzer.analyze(long_content)

        assert result.processing_time < 5.0

    def test_race_condition_in_tracking(self):
        """F15-S006: 追踪中的竞态条件"""
        import threading

        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()
        results = []

        def track():
            result = tracker.track_topic("台湾", SensitivityLevel.HIGH)
            results.append(result)

        threads = [threading.Thread(target=track) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10


class TestIntegrationTests:
    """集成测试"""

    def test_full_political_analysis_workflow(self):
        """F15-I001: 完整政治分析工作流"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel
        from f15_political_sensitivity.sentiment_analyzer import SentimentAnalyzer

        tracker = PoliticalTracker()
        analyzer = SentimentAnalyzer()
        detector = InfiltrationDetector()

        tracker.track_topic("台湾", SensitivityLevel.HIGH)

        sentiment_result = analyzer.analyze("这个政策影响了台海局势")

        infiltration_result = detector.detect("一些外部势力在干涉")

        assert sentiment_result is not None
        assert infiltration_result is not None

    def test_tracker_analyzer_detector_integration(self):
        """F15-I002: 追踪器-分析器-检测器集成"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel
        from f15_political_sensitivity.sentiment_analyzer import SentimentAnalyzer

        tracker = PoliticalTracker()
        SentimentAnalyzer()
        InfiltrationDetector()

        tracker.track_topic("敏感话题", SensitivityLevel.HIGH)

        combined_result = tracker.cross_topic_analysis(["敏感话题"])

        assert combined_result is not None


class TestPoliticalTrackerUncovered:
    """覆盖PoliticalTracker未测试的分支"""

    def test_normalized_topic_cache_hit(self):
        """lines 67-69: 规范化话题在_normalized_topics中的缓存命中"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker, SensitivityLevel

        tracker = PoliticalTracker()

        tracker._normalized_topics["敏感话题"] = "sensitive_topic"
        tracker._sensitivity_cache["sensitive_topic"] = SensitivityLevel.HIGH

        level = tracker.check_topic_sensitivity("敏感话题")

        assert level == SensitivityLevel.HIGH

    def test_get_topic_aggregation_not_found(self):
        """line 76: 话题不存在时返回空的TopicAggregation"""
        from f15_political_sensitivity.political_tracker import PoliticalTracker

        tracker = PoliticalTracker()

        result = tracker.get_topic_aggregation("完全不存在的topic123")

        assert result.count == 0


class TestInfiltrationDetectorUncovered:
    """覆盖InfiltrationDetector未测试的分支"""

    def test_detect_hate_speech_pattern(self):
        """line 90: 仇恨言论模式匹配返回DetectionResult"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector, ThreatType

        detector = InfiltrationDetector()

        result = detector.detect("包含仇恨言论的内容")

        assert result is not None
        assert result.threat_type == ThreatType.HATE_SPEECH
        assert result.is_safe is False
        assert result.confidence == 0.75
        assert len(result.matched_patterns) > 0

    def test_detect_coordinated_behavior_detected(self):
        """line 117: 检测到协调行为"""
        from f15_political_sensitivity.infiltration_detector import InfiltrationDetector, ThreatType

        detector = InfiltrationDetector()

        accounts = ["user1", "user1", "user1", "user1"]

        result = detector.detect_coordinated_behavior(accounts)

        assert result is not None
        assert result.threat_type == ThreatType.COORDINATED_BEHAVIOR
        assert result.is_safe is False
        assert result.confidence == 0.7
        assert "coordinated_accounts" in result.matched_patterns


class TestSentimentAnalyzerUncovered:
    """覆盖SentimentAnalyzer未测试的分支"""

    def test_is_polarized_short_text(self):
        """line 48: 短文本满足标点条件判定为极化"""
        from f15_political_sensitivity.sentiment_analyzer import Sentiment, SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer._is_polarized("太棒了！", Sentiment.POSITIVE)
        assert result is True

        result = analyzer._is_polarized("真的吗？", Sentiment.NEUTRAL)
        assert result is False

        result = analyzer._is_polarized("震惊！", Sentiment.NEGATIVE)
        assert result is True

    def test_is_polarized_multiple_punctuation(self):
        """line 48: 多感叹号或多问号满足极化条件"""
        from f15_political_sensitivity.sentiment_analyzer import Sentiment, SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        result = analyzer._is_polarized("太棒了！！", Sentiment.POSITIVE)
        assert result is True

        result = analyzer._is_polarized("真的吗？？", Sentiment.NEGATIVE)
        assert result is True
