"""
F16: 统计抽样验证引擎 - 单元测试
TDD RED阶段：测试必须失败，因为实现不存在
"""
import pytest
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum


class TestSampleSizeCalculation:
    """样本量计算测试"""

    def test_calculate_sample_size_large_population(self):
        """F16-T001: 大总体样本量计算"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.05)

        pop_size = 100000
        sample_size = engine.calculate_sample_size(population_size=pop_size)

        assert sample_size > 0
        assert sample_size < pop_size

    def test_calculate_sample_size_small_population(self):
        """F16-T002: 小总体样本量计算"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.05)

        sample_size = engine.calculate_sample_size(population_size=100)

        assert sample_size > 0
        assert sample_size <= 100

    def test_sample_size_with_99_confidence(self):
        """F16-T003: 99%置信度样本量"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine(confidence_level=0.99, margin_of_error=0.05)

        sample_size_95 = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.05).calculate_sample_size(10000)
        sample_size_99 = engine.calculate_sample_size(population_size=10000)

        assert sample_size_99 > sample_size_95

    def test_sample_size_with_90_confidence(self):
        """F16-T004: 90%置信度样本量"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine(confidence_level=0.90, margin_of_error=0.05)

        sample_size = engine.calculate_sample_size(population_size=10000)

        assert sample_size > 0

    def test_sample_size_with_3_percent_margin(self):
        """F16-T005: 3%误差范围样本量"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.03)

        sample_size_5pct = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.05).calculate_sample_size(10000)
        sample_size_3pct = engine.calculate_sample_size(population_size=10000)

        assert sample_size_3pct > sample_size_5pct


class TestStratifiedSampling:
    """分层抽样测试"""

    def test_stratified_sampling_basic(self):
        """F16-T006: 基本分层抽样"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()

        chapters = [
            Chapter(id="ch1", title="人工智能基础", chapter_type=ChapterType.THEORY, word_count=5000),
            Chapter(id="ch2", title="机器学习", chapter_type=ChapterType.THEORY, word_count=6000),
            Chapter(id="ch3", title="深度学习", chapter_type=ChapterType.PRACTICE, word_count=8000),
            Chapter(id="ch4", title="神经网络", chapter_type=ChapterType.PRACTICE, word_count=7000),
            Chapter(id="ch5", title="自然语言处理", chapter_type=ChapterType.CASE_STUDY, word_count=9000),
        ]

        strata = {
            ChapterType.THEORY: 0.4,
            ChapterType.PRACTICE: 0.4,
            ChapterType.CASE_STUDY: 0.2,
        }

        sample = engine.stratified_sampling(chapters, strata)

        assert len(sample) > 0
        assert len(sample) <= len(chapters)

    def test_stratified_sampling_minimum_per_stratum(self):
        """F16-T007: 每层最小样本量保证"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()

        chapters = [
            Chapter(id="ch1", title="理论1", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch2", title="理论2", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch3", title="实践1", chapter_type=ChapterType.PRACTICE, word_count=1000),
        ]

        strata = {
            ChapterType.THEORY: 0.5,
            ChapterType.PRACTICE: 0.5,
        }

        sample = engine.stratified_sampling(chapters, strata)

        theory_count = sum(1 for c in sample if c.chapter_type == ChapterType.THEORY)
        practice_count = sum(1 for c in sample if c.chapter_type == ChapterType.PRACTICE)

        assert theory_count >= 1
        assert practice_count >= 1

    def test_stratified_sampling_proportional_allocation(self):
        """F16-T008: 按比例分配"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()

        chapters = [
            Chapter(id="ch1", title="理论1", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch2", title="理论2", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch3", title="理论3", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch4", title="理论4", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch5", title="实践1", chapter_type=ChapterType.PRACTICE, word_count=1000),
            Chapter(id="ch6", title="实践2", chapter_type=ChapterType.PRACTICE, word_count=1000),
            Chapter(id="ch7", title="案例1", chapter_type=ChapterType.CASE_STUDY, word_count=1000),
        ]

        strata = {
            ChapterType.THEORY: 0.57,  # 4/7
            ChapterType.PRACTICE: 0.29,  # 2/7
            ChapterType.CASE_STUDY: 0.14,  # 1/7
        }

        sample = engine.stratified_sampling(chapters, strata, proportional=True)

        theory_count = sum(1 for c in sample if c.chapter_type == ChapterType.THEORY)
        practice_count = sum(1 for c in sample if c.chapter_type == ChapterType.PRACTICE)
        case_count = sum(1 for c in sample if c.chapter_type == ChapterType.CASE_STUDY)

        assert theory_count >= practice_count >= case_count


class TestConfidenceCalculator:
    """置信度计算器测试"""

    def test_calculate_confidence_interval(self):
        """F16-T009: 计算置信区间"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()

        sample_mean = 0.85
        sample_std = 0.1
        sample_size = 100
        confidence_level = 0.95

        result = calculator.calculate_confidence_interval(
            sample_mean, sample_std, sample_size, confidence_level
        )

        assert result.lower_bound < sample_mean < result.upper_bound
        assert result.confidence_level == 0.95

    def test_confidence_interval_wider_for_lower_confidence(self):
        """F16-T010: 低置信度对应更宽区间"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()

        result_95 = calculator.calculate_confidence_interval(0.85, 0.1, 100, 0.95)
        result_90 = calculator.calculate_confidence_interval(0.85, 0.1, 100, 0.90)

        interval_95 = result_95.upper_bound - result_95.lower_bound
        interval_90 = result_90.upper_bound - result_90.lower_bound

        assert interval_95 > interval_90

    def test_calculate_margin_of_error(self):
        """F16-T011: 计算误差范围"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()

        margin = calculator.calculate_margin_of_error(
            sample_proportion=0.5,
            sample_size=400,
            confidence_level=0.95
        )

        assert margin > 0
        assert margin < 0.5

    def test_sample_size_from_margin_of_error(self):
        """F16-T012: 从误差范围反推样本量"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()

        n = calculator.sample_size_from_margin_of_error(
            margin_of_error=0.05,
            population_proportion=0.5,
            confidence_level=0.95
        )

        assert n > 0


class TestSampleValidator:
    """样本验证器测试"""

    def test_validate_sample_representativeness(self):
        """F16-T013: 验证样本代表性"""
        from f16_statistical_sampling.sample_validator import SampleValidator, ValidationResult

        validator = SampleValidator()

        population = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        sample = [0.2, 0.4, 0.6, 0.8]

        result = validator.validate_representativeness(population, sample)

        assert result.is_valid == True
        assert result.score >= 0

    def test_validate_sample_too_small(self):
        """F16-T014: 样本量过小验证"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        population = list(range(100))
        sample = [1, 2]

        result = validator.validate_minimum_size(population, sample)

        assert result.is_valid == False
        assert "size" in result.message.lower() or "too small" in result.message.lower()

    def test_validate_stratification_balance(self):
        """F16-T015: 验证分层平衡"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        population_strata = {
            "A": list(range(50)),
            "B": list(range(50, 100)),
        }
        sample_strata = {
            "A": [1, 2, 3],
            "B": [51, 52, 53],
        }

        result = validator.validate_stratification_balance(population_strata, sample_strata)

        assert result.is_valid == True

    def test_detect_sampling_bias(self):
        """F16-T016: 检测抽样偏差"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        population = list(range(1, 101))
        biased_sample = list(range(1, 21))

        result = validator.detect_bias(population, biased_sample)

        assert result.is_biased == True
        assert result.bias_score > 0


class TestEdgeCases:
    """边界情况测试"""

    def test_single_element_population(self):
        """F16-T017: 单元素总体"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()

        sample_size = engine.calculate_sample_size(population_size=1)

        assert sample_size == 1

    def test_empty_sample_request(self):
        """F16-T018: 请求空样本"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()

        sample_size = engine.calculate_sample_size(population_size=0)

        assert sample_size == 0

    def test_sample_larger_than_population(self):
        """F16-T019: 样本量大于总体"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()

        sample_size = engine.calculate_sample_size(population_size=10)

        assert sample_size <= 10


class TestSecurityTests:
    """安全测试 - P0漏洞覆盖"""

    def test_zero_confidence_level_rejection(self):
        """F16-S001: 零置信度拒绝"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        with pytest.raises(ValueError):
            StatisticalSamplingEngine(confidence_level=0, margin_of_error=0.05)

    def test_negative_margin_of_error_rejection(self):
        """F16-S002: 负误差范围拒绝"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        with pytest.raises(ValueError):
            StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=-0.01)

    def test_confidence_level_above_one_rejection(self):
        """F16-S003: 超过1的置信度拒绝"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        with pytest.raises(ValueError):
            StatisticalSamplingEngine(confidence_level=1.5, margin_of_error=0.05)

    def test_manipulated_sample_bias_detection(self):
        """F16-S004: 操作样本偏差检测"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        population = list(range(1, 101))
        manipulated_sample = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        result = validator.detect_bias(population, manipulated_sample)

        assert result.is_biased == True
        assert result.bias_score > 0.5

    def test_sampling_without_stratification_danger_warning(self):
        """F16-S005: 未分层抽样危险警告"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()

        chapters = [
            Chapter(id="ch1", title="第一章", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch2", title="第二章", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch3", title="第三章", chapter_type=ChapterType.PRACTICE, word_count=1000),
            Chapter(id="ch4", title="第四章", chapter_type=ChapterType.PRACTICE, word_count=1000),
            Chapter(id="ch5", title="第五章", chapter_type=ChapterType.CASE_STUDY, word_count=1000),
        ]

        strata = {
            ChapterType.THEORY: 0.4,
            ChapterType.PRACTICE: 0.4,
            ChapterType.CASE_STUDY: 0.2,
        }

        sample = engine.stratified_sampling(chapters, strata)

        has_all_types = len(set(c.chapter_type for c in sample)) >= 2

        assert has_all_types == True


class TestCoverageGapSamplingEngine:
    """覆盖率补齐：sampling_engine.py 未覆盖路径"""

    def test_stratified_sampling_empty_chapters(self):
        """F16-CG001: 分层抽样-空章节列表"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()
        result = engine.stratified_sampling([], {})
        assert result == []

    def test_stratified_sampling_auto_generate_strata(self):
        """F16-CG002: 分层抽样-自动生成分层比例(无strata/空strata)"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id="ch1", title="理论1", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch2", title="理论2", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch3", title="实践1", chapter_type=ChapterType.PRACTICE, word_count=1000),
        ]
        sample = engine.stratified_sampling(chapters, {})
        assert len(sample) > 0
        has_theory = any(c.chapter_type == ChapterType.THEORY for c in sample)
        has_practice = any(c.chapter_type == ChapterType.PRACTICE for c in sample)
        assert has_theory or has_practice

    def test_stratified_sampling_none_strata(self):
        """F16-CG003: 分层抽样-None strata自动生成"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id="ch1", title="理论1", chapter_type=ChapterType.THEORY, word_count=1000),
            Chapter(id="ch2", title="实践1", chapter_type=ChapterType.PRACTICE, word_count=1000),
        ]
        sample = engine.stratified_sampling(chapters, None)
        assert len(sample) > 0

    def test_systematic_sampling_basic(self):
        """F16-CG004: 系统抽样-基本功能"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.05)
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(1, 31)
        ]
        sample = engine.systematic_sampling(chapters)
        assert len(sample) > 0
        assert len(sample) <= 30

    def test_systematic_sampling_empty(self):
        """F16-CG005: 系统抽样-空列表"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()
        sample = engine.systematic_sampling([])
        assert sample == []

    def test_systematic_sampling_explicit_size(self):
        """F16-CG006: 系统抽样-指定样本量"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(1, 21)
        ]
        sample = engine.systematic_sampling(chapters, sample_size=5)
        assert len(sample) == 5

    def test_systematic_sampling_small_population(self):
        """F16-CG007: 系统抽样-总体小于样本量"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(1, 4)
        ]
        sample = engine.systematic_sampling(chapters, sample_size=10)
        assert len(sample) == 3

    def test_systematic_sampling_zero_interval(self):
        """F16-CG008: 系统抽样-间隔为0(小总体大样本)"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(1, 4)
        ]
        sample = engine.systematic_sampling(chapters, sample_size=10)
        assert len(sample) == 3  # Interval=0, returns chapters[:sample_size] which is all 3

    def test_cluster_sampling_basic(self):
        """F16-CG009: 整群抽样-基本功能"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(1, 21)
        ]
        sample = engine.cluster_sampling(chapters, cluster_size=5)
        assert len(sample) > 0
        assert len(sample) <= 20

    def test_cluster_sampling_empty(self):
        """F16-CG010: 整群抽样-空列表"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()
        sample = engine.cluster_sampling([])
        assert sample == []

    def test_cluster_sampling_invalid_size(self):
        """F16-CG011: 整群抽样-无效集群大小"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [Chapter(id="ch1", title="章节1", chapter_type=ChapterType.THEORY, word_count=1000)]
        sample = engine.cluster_sampling(chapters, cluster_size=0)
        assert sample == []

    def test_cluster_sampling_small_population(self):
        """F16-CG012: 整群抽样-小型总体"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(1, 3)
        ]
        sample = engine.cluster_sampling(chapters, cluster_size=10)
        assert len(sample) > 0


class TestCoverageGapConfidenceCalculator:
    """覆盖率补齐：confidence_calculator.py 未覆盖路径"""

    def test_confidence_interval_zero_sample_size(self):
        """F16-CG013: 置信区间-零样本量报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Sample size must be positive"):
            ConfidenceCalculator().calculate_confidence_interval(0.85, 0.1, 0)

    def test_confidence_interval_negative_std(self):
        """F16-CG014: 置信区间-负标准差报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Standard deviation cannot be negative"):
            ConfidenceCalculator().calculate_confidence_interval(0.85, -0.1, 100)

    def test_margin_of_error_zero_sample_size(self):
        """F16-CG015: 误差范围-零样本量报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Sample size must be positive"):
            ConfidenceCalculator().calculate_margin_of_error(0.5, 0)

    def test_margin_of_error_invalid_proportion_low(self):
        """F16-CG016: 误差范围-负比例报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Sample proportion must be between 0 and 1"):
            ConfidenceCalculator().calculate_margin_of_error(-0.1, 100)

    def test_margin_of_error_invalid_proportion_high(self):
        """F16-CG017: 误差范围-超1比例报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Sample proportion must be between 0 and 1"):
            ConfidenceCalculator().calculate_margin_of_error(1.5, 100)

    def test_sample_size_from_margin_invalid_margin(self):
        """F16-CG018: 反推样本量-无效误差范围报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Margin of error must be between 0 and 1"):
            ConfidenceCalculator().sample_size_from_margin_of_error(0.0)

    def test_sample_size_from_margin_invalid_proportion(self):
        """F16-CG019: 反推样本量-无效比例报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Population proportion must be between 0 and 1"):
            ConfidenceCalculator().sample_size_from_margin_of_error(0.05, population_proportion=2.0)

    def test_calculate_required_sample_size(self):
        """F16-CG020: 计算有限总体所需样本量"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()
        n = calculator.calculate_required_sample_size(
            population_size=1000,
            confidence_level=0.95,
            margin_of_error=0.05,
            population_proportion=0.5
        )
        assert n > 0
        assert n <= 1000

    def test_calculate_required_sample_size_zero_pop(self):
        """F16-CG021: 有限总体样本量-零总体报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Population size must be positive"):
            ConfidenceCalculator().calculate_required_sample_size(0)

    def test_calculate_required_sample_size_small_pop(self):
        """F16-CG022: 有限总体样本量-小总体"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()
        n = calculator.calculate_required_sample_size(population_size=10)
        assert n > 0

    def test_calculate_required_sample_size_99_confidence(self):
        """F16-CG023: 有限总体样本量-99%置信度"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()
        n = calculator.calculate_required_sample_size(
            population_size=5000,
            confidence_level=0.99
        )
        assert n > 0

    def test_calculate_standard_error(self):
        """F16-CG024: 计算标准误差"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()
        se = calculator.calculate_standard_error(sample_std=10.0, sample_size=100)
        assert se == 1.0

    def test_calculate_standard_error_zero_sample(self):
        """F16-CG025: 标准误差-零样本报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Sample size must be positive"):
            ConfidenceCalculator().calculate_standard_error(10.0, 0)

    def test_calculate_standard_error_negative_std(self):
        """F16-CG026: 标准误差-负标准差报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Standard deviation cannot be negative"):
            ConfidenceCalculator().calculate_standard_error(-1.0, 100)

    def test_calculate_z_score(self):
        """F16-CG027: Z分数获取"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()
        assert calculator.calculate_z_score(0.95) == 1.96
        assert calculator.calculate_z_score(0.90) == 1.645
        assert calculator.calculate_z_score(0.99) == 2.576

    def test_calculate_z_score_unsupported(self):
        """F16-CG028: Z分数-不支持的置信度报错"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        with pytest.raises(ValueError, match="Confidence level"):
            ConfidenceCalculator().calculate_z_score(0.80)

    def test_confidence_interval_extreme_values(self):
        """F16-CG029: 置信区间-边界值(proportion=0和proportion=1)"""
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator

        calculator = ConfidenceCalculator()
        margin_0 = calculator.calculate_margin_of_error(0.0, 100, 0.95)
        assert margin_0 == 0.0
        margin_1 = calculator.calculate_margin_of_error(1.0, 100, 0.95)
        assert margin_1 == 0.0


class TestCoverageGapSampleValidator:
    """覆盖率补齐：sample_validator.py 未覆盖路径"""

    def test_validate_representativeness_empty_both(self):
        """F16-CG030: 代表性验证-空总体和空样本"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        result = validator.validate_representativeness([], [])
        assert result.is_valid is False
        assert result.score == 0.0

    def test_validate_representativeness_pop_mean_zero(self):
        """F16-CG031: 代表性验证-总体均值为零"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        result = validator.validate_representativeness([0.0, 0.0, 0.0], [1.0, 2.0])
        assert result.is_valid is False
        assert result.score == 0.0

    def test_validate_minimum_size_below_recommended(self):
        """F16-CG032: 最小样本量验证-低于推荐量"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator(minimum_sample_size=3)
        population = list(range(120))
        sample = [1, 2, 3, 4, 5]  # >3 but < recommended for 120 (~max(10, 120/10)=12)
        result = validator.validate_minimum_size(population, sample)
        assert result.is_valid is True
        assert result.score < 1.0

    def test_validate_minimum_size_below_recommended_large(self):
        """F16-CG033: 最小样本量验证-大总体低于推荐量"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator(minimum_sample_size=3)
        population = list(range(2000))
        sample = [1, 2, 3, 4]  # 4 > 3 but below recommended for 2000 (~44)
        result = validator.validate_minimum_size(population, sample)
        assert result.is_valid is True
        assert 0 < result.score < 1.0

    def test_validate_stratification_balance_mismatch(self):
        """F16-CG034: 分层平衡验证-分层不匹配"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        pop_strata = {"A": [1, 2], "B": [3, 4]}
        sample_strata = {"A": [1], "C": [5]}  # C not in population
        result = validator.validate_stratification_balance(pop_strata, sample_strata)
        assert result.is_valid is False
        assert result.score == 0.0

    def test_validate_stratification_balance_zero_pop_stratum(self):
        """F16-CG035: 分层平衡验证-总体层为空(stratum有零总体, A为空被跳过)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        pop_strata = {"A": [], "B": [1, 2, 3]}
        sample_strata = {"A": [1], "B": [1, 2]}
        result = validator.validate_stratification_balance(pop_strata, sample_strata)
        assert result.score >= 0

    def test_validate_stratification_balance_all_zero(self):
        """F16-CG036: 分层平衡验证-全部层为空"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        pop_strata = {"A": [], "B": []}
        sample_strata = {"A": [], "B": []}
        result = validator.validate_stratification_balance(pop_strata, sample_strata)
        assert result.is_valid is False
        assert result.score == 0.0

    def test_detect_bias_empty(self):
        """F16-CG037: 偏差检测-空总体和空样本"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        result = validator.detect_bias([], [])
        assert result.is_biased is True
        assert result.bias_type == "empty"

    def test_detect_bias_high_variance(self):
        """F16-CG038: 偏差检测-高方差(触发high_variance类型)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = [5.0, 5.1, 4.9, 5.0, 5.1, 4.9, 5.0, 5.1, 5.0, 5.1]
        sample = [1.0, 100.0, 1.0, 100.0]  # variance ratio >> 2.0
        result = validator.detect_bias(population, sample)
        assert result.is_biased is True
        assert result.bias_score > 0.3

    def test_detect_bias_low_variance(self):
        """F16-CG039: 偏差检测-低方差(触发low_variance类型)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = [1.0, 10.0, 20.0, 30.0, 40.0, 50.0]
        sample = [5.0, 5.0, 5.0, 5.0]  # nearly zero variance
        result = validator.detect_bias(population, sample)
        assert result.is_biased is True

    def test_detect_bias_range_restriction(self):
        """F16-CG040: 偏差检测-范围限制"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = list(range(1, 101))
        sample = [45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55]  # narrow range
        result = validator.detect_bias(population, sample)
        assert result.is_biased is True

    def test_validate_sample_quality(self):
        """F16-CG041: 综合样本质量验证"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        sample = [0.2, 0.4, 0.6, 0.8]
        results = validator.validate_sample_quality(population, sample)
        assert "representativeness" in results
        assert "minimum_size" in results
        assert "stratification" not in results

    def test_validate_sample_quality_with_strata(self):
        """F16-CG042: 综合质量验证-含分层"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = list(range(1, 101))
        sample = list(range(10, 21))
        strata = {"low": list(range(1, 50)), "high": list(range(50, 101))}
        results = validator.validate_sample_quality(population, sample, strata)
        assert "representativeness" in results
        assert "minimum_size" in results
        assert "stratification" in results

    def test_validate_minimum_size_edge_100_pop(self):
        """F16-CG043: 最小样本量-恰好100(触发<=100分支)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator(minimum_sample_size=3)
        population = list(range(100))
        sample = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = validator.validate_minimum_size(population, sample)
        assert result.is_valid is True
        assert result.score == 1.0  # 10 >= max(10, 100//10)=10

    def test_validate_minimum_size_edge_1000_pop(self):
        """F16-CG044: 最小样本量-恰好1000(触发<=1000分支)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator(minimum_sample_size=3)
        population = list(range(1000))
        sample = list(range(30))  # 30 < max(30, 1000//20)=50
        result = validator.validate_minimum_size(population, sample)
        assert result.is_valid is True
        assert 0 < result.score < 1.0

    def test_validate_minimum_size_large_pop(self):
        """F16-CG045: 最小样本量-大总体(>1000) 最小量检查"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator(minimum_sample_size=3)
        population = list(range(10000))
        sample = list(range(3))  # 3 exactly at minimum but below recommended
        result = validator.validate_minimum_size(population, sample)
        assert result.is_valid is True
        assert result.score < 1.0

    def test_detect_bias_mixed_median_and_coverage(self):
        """F16-CG046: 偏差检测-同时触发中位数和覆盖率偏差"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = list(range(1, 101))
        sample = [1, 2, 3, 4, 5]  # median diff big, narrow coverage
        result = validator.detect_bias(population, sample)
        assert result.is_biased is True
        assert result.bias_score >= 0.7

    def test_detect_bias_low_variance_type(self):
        """F16-CG047: 偏差检测-低方差类型(low_variance)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = list(range(1, 101))
        sample = [47, 48, 49, 50, 51, 52, 53, 54]  # median centered, low std
        result = validator.detect_bias(population, sample)
        assert result.is_biased is True
        assert result.bias_type == "low_variance"

    def test_detect_bias_range_restriction_type(self):
        """F16-CG048: 偏差检测-范围限制类型(range_restriction)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()
        population = list(range(1, 101))
        sample = [28, 29, 30, 31, 32, 33, 68, 69, 70, 71, 72, 73]
        result = validator.detect_bias(population, sample)
        assert result.is_biased is True
        assert result.bias_type == "range_restriction"


class TestIntegrationTests:
    """集成测试"""

    def test_full_sampling_workflow(self):
        """F16-I001: 完整抽样工作流"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType
        from f16_statistical_sampling.confidence_calculator import ConfidenceCalculator
        from f16_statistical_sampling.sample_validator import SampleValidator

        engine = StatisticalSamplingEngine(confidence_level=0.95, margin_of_error=0.05)
        calculator = ConfidenceCalculator()
        validator = SampleValidator()

        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY if i % 2 == 0 else ChapterType.PRACTICE, word_count=2000)
            for i in range(1, 21)
        ]

        strata = {ChapterType.THEORY: 0.5, ChapterType.PRACTICE: 0.5}

        sample_size = engine.calculate_sample_size(population_size=len(chapters))

        sample = engine.stratified_sampling(chapters, strata)

        assert len(sample) <= len(chapters)

        sample_means = [c.word_count for c in sample]
        result = validator.validate_representativeness(
            [c.word_count for c in chapters],
            sample_means
        )

        assert result.score >= 0

    def test_sampling_with_population_parameters(self):
        """F16-I002: 带总体参数的抽样"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()

        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000 * i)
            for i in range(1, 11)
        ]

        strata = {ChapterType.THEORY: 1.0}

        sample = engine.stratified_sampling(chapters, strata)

        assert len(sample) > 0
        assert all(c.word_count > 0 for c in sample)


class TestF16CoverageGapsRemaining:
    """F16: 剩余覆盖缺口测试 - 覆盖sample_validator和sampling_engine剩余未覆盖行"""

    def test_detect_bias_high_variance_type(self):
        """F16-T046: detect_bias高方差类型覆盖 (line 190: variance_ratio > 2.0)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        population = [9.0] * 50 + [11.0] * 50
        sample = [10.0] * 9 + [40.0]

        result = validator.detect_bias(population, sample)

        assert result.bias_type == "high_variance"

    def test_median_empty_list_returns_zero(self):
        """F16-T047: _median空列表返回0 (line 230)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        result = validator._median([])

        assert result == 0

    def test_std_empty_data_returns_zero(self):
        """F16-T048: _std空数据返回0 (line 238)"""
        from f16_statistical_sampling.sample_validator import SampleValidator

        validator = SampleValidator()

        result = validator._std([])

        assert result == 0

    def test_default_strata_empty_chapters(self):
        """F16-T049: _default_strata空章节返回空字典 (line 109)"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine

        engine = StatisticalSamplingEngine()

        result = engine._default_strata([])

        assert result == {}

    def test_systematic_sampling_zero_sample_size(self):
        """F16-T050: systematic_sampling的sample_size为0时返回空列表 (line 131)"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(10)
        ]

        result = engine.systematic_sampling(chapters, sample_size=0)

        assert result == []

    def test_systematic_sampling_zero_interval(self):
        """F16-T051: systematic_sampling的interval为0时返回chapters[:sample_size] (line 136)"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = [
            Chapter(id=f"ch{i}", title=f"章节{i}", chapter_type=ChapterType.THEORY, word_count=1000)
            for i in range(3)
        ]

        result = engine.systematic_sampling(chapters, sample_size=10)

        assert len(result) == 3

    def test_cluster_sampling_no_clusters(self):
        """F16-T052: cluster_sampling无有效集群时返回空列表 (line 162)"""
        from f16_statistical_sampling.sampling_engine import StatisticalSamplingEngine, Chapter, ChapterType

        engine = StatisticalSamplingEngine()
        chapters = []

        result = engine.cluster_sampling(chapters, cluster_size=10)

        assert result == []
