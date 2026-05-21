"""
F30: Golden Dataset系统 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。
按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量

验收标准:
- Golden Dataset样本可用于校准
- 单元测试覆盖率 ≥88%
"""

import json
import os

import pytest

# 样本文件路径
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")


class TestGoldenDatasetSamples:
    """Golden Dataset样本测试"""

    def test_sample_files_exist(self):
        """F30-T001: 所有样本文件必须存在"""
        expected_samples = [
            "gd001_high_quality.json",
            "gd002_medium_quality.json",
            "gd003_low_quality.json",
            "gd004_hallucination.json",
            "gd005_regulation_error.json"
        ]

        for sample_file in expected_samples:
            sample_path = os.path.join(SAMPLES_DIR, sample_file)
            assert os.path.exists(sample_path), f"Sample file {sample_file} not found"

    def test_high_quality_sample_structure(self):
        """F30-T002: 高质量样本结构验证"""
        sample_path = os.path.join(SAMPLES_DIR, "gd001_high_quality.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        # 必需字段
        assert "sample_id" in sample
        assert "quality_level" in sample
        assert "expected_score" in sample
        assert "content" in sample
        assert "quality_metrics" in sample

        # 值验证
        assert sample["sample_id"] == "GD-001"
        assert sample["quality_level"] == "high"
        assert 9.0 <= sample["expected_score"] <= 10.0

    def test_medium_quality_sample_structure(self):
        """F30-T003: 中等质量样本结构验证"""
        sample_path = os.path.join(SAMPLES_DIR, "gd002_medium_quality.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        assert sample["quality_level"] == "medium"
        assert 7.0 <= sample["expected_score"] <= 8.0

    def test_low_quality_sample_structure(self):
        """F30-T004: 低质量样本结构验证"""
        sample_path = os.path.join(SAMPLES_DIR, "gd003_low_quality.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        assert sample["quality_level"] == "low"
        assert 3.0 <= sample["expected_score"] <= 4.0

    def test_hallucination_sample_has_markers(self):
        """F30-T005: 幻觉样本必须标记幻觉位置"""
        sample_path = os.path.join(SAMPLES_DIR, "gd004_hallucination.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        assert "hallucination_markers" in sample
        assert len(sample["hallucination_markers"]) > 0

        # 检查标记结构
        for marker in sample["hallucination_markers"]:
            assert "type" in marker
            assert "location" in marker
            assert "content" in marker
            assert "issue" in marker

    def test_hallucination_sample_has_numerical_hallucinations(self):
        """F30-T006: 幻觉样本包含数值幻觉"""
        sample_path = os.path.join(SAMPLES_DIR, "gd004_hallucination.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        markers = sample["hallucination_markers"]
        numerical_markers = [m for m in markers if m["type"] == "numerical_hallucination"]

        assert len(numerical_markers) > 0
        # 检查包含明显的虚假数值
        content_text = json.dumps(sample["content"])
        assert "30%" in content_text or "250万" in content_text

    def test_hallucination_sample_has_citation_hallucinations(self):
        """F30-T007: 幻觉样本包含引用幻觉"""
        sample_path = os.path.join(SAMPLES_DIR, "gd004_hallucination.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        markers = sample["hallucination_markers"]
        citation_markers = [m for m in markers if m["type"] == "citation_hallucination"]

        assert len(citation_markers) > 0

    def test_regulation_error_sample_structure(self):
        """F30-T008: 法规错误样本结构验证"""
        sample_path = os.path.join(SAMPLES_DIR, "gd005_regulation_error.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        assert "regulation_errors" in sample
        assert len(sample["regulation_errors"]) > 0

        # 检查错误结构
        for error in sample["regulation_errors"]:
            assert "type" in error
            assert "law" in error
            assert "cited_article" in error
            assert "issue" in error

    def test_regulation_error_sample_has_nonexistent_articles(self):
        """F30-T009: 法规错误样本包含不存在条款"""
        sample_path = os.path.join(SAMPLES_DIR, "gd005_regulation_error.json")

        with open(sample_path, encoding="utf-8") as f:
            sample = json.load(f)

        errors = sample["regulation_errors"]
        nonexistent_errors = [e for e in errors if e["type"] == "nonexistent_article"]

        assert len(nonexistent_errors) > 0

    def test_all_samples_have_metadata(self):
        """F30-T010: 所有样本必须有元数据"""
        sample_files = [
            "gd001_high_quality.json",
            "gd002_medium_quality.json",
            "gd003_low_quality.json",
            "gd004_hallucination.json",
            "gd005_regulation_error.json"
        ]

        for sample_file in sample_files:
            sample_path = os.path.join(SAMPLES_DIR, sample_file)
            with open(sample_path, encoding="utf-8") as f:
                sample = json.load(f)

            assert "metadata" in sample
            metadata = sample["metadata"]
            assert "created_at" in metadata
            assert "author" in metadata
            assert "domain" in metadata


class TestDatasetBuilder:
    """Dataset构建器测试"""

    def test_load_all_samples(self):
        """F30-T020: 加载所有样本"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)
        dataset = builder.load_all_samples()

        assert len(dataset) == 5
        assert "GD-001" in dataset
        assert "GD-002" in dataset
        assert "GD-003" in dataset
        assert "GD-004" in dataset
        assert "GD-005" in dataset

    def test_load_samples_by_quality_level(self):
        """F30-T021: 按质量等级加载样本"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)

        high_samples = builder.load_samples_by_quality("high")
        assert len(high_samples) == 1
        assert high_samples[0]["sample_id"] == "GD-001"

        hallucination_samples = builder.load_samples_by_quality("hallucination")
        assert len(hallucination_samples) == 1
        assert hallucination_samples[0]["sample_id"] == "GD-004"

    def test_load_samples_by_score_range(self):
        """F30-T022: 按分数范围加载样本"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)

        high_score_samples = builder.load_samples_by_score_range(min_score=9.0)
        assert len(high_score_samples) == 1

        low_score_samples = builder.load_samples_by_score_range(max_score=4.0)
        assert len(low_score_samples) == 3

    def test_get_calibration_samples(self):
        """F30-T023: 获取校准用样本"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)
        calibration_set = builder.get_calibration_samples()

        assert len(calibration_set) > 0
        # 校准集应该包含不同质量等级的样本
        quality_levels = {s["quality_level"] for s in calibration_set}
        assert len(quality_levels) >= 2

    def test_add_sample(self):
        """F30-T024: 添加样本到数据集"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)
        initial_count = len(builder.load_all_samples())

        new_sample = {
            "sample_id": "GD-006",
            "quality_level": "high",
            "expected_score": 9.0,
            "content": {"title": "测试样本"},
            "quality_metrics": {},
            "metadata": {}
        }

        builder.add_sample(new_sample)
        dataset = builder.load_all_samples()

        assert len(dataset) == initial_count + 1

    def test_validate_sample_structure(self):
        """F30-T025: 验证样本结构"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder()

        valid_sample = {
            "sample_id": "TEST-001",
            "quality_level": "high",
            "expected_score": 9.0,
            "content": {"title": "测试"},
            "quality_metrics": {},
            "metadata": {}
        }

        assert builder.validate_sample_structure(valid_sample) is True

    def test_validate_sample_structure_missing_fields(self):
        """F30-T026: 缺少字段时验证失败"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder()

        invalid_sample = {
            "sample_id": "TEST-001",
            # 缺少其他必需字段
        }

        assert builder.validate_sample_structure(invalid_sample) is False


class TestSampleManager:
    """样本管理器测试"""

    def test_get_sample_by_id(self):
        """F30-T030: 通过ID获取样本"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)

        sample = manager.get_sample_by_id("GD-001")
        assert sample is not None
        assert sample["sample_id"] == "GD-001"

    def test_get_sample_not_found(self):
        """F30-T031: 样本不存在返回None"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)

        sample = manager.get_sample_by_id("NONEXISTENT")
        assert sample is None

    def test_list_all_sample_ids(self):
        """F30-T032: 列出所有样本ID"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)

        sample_ids = manager.list_all_sample_ids()

        assert len(sample_ids) == 5
        assert "GD-001" in sample_ids
        assert "GD-005" in sample_ids

    def test_get_hallucination_samples(self):
        """F30-T033: 获取幻觉样本"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)
        hallucination_samples = manager.get_hallucination_samples()

        assert len(hallucination_samples) == 1
        assert hallucination_samples[0]["sample_id"] == "GD-004"

    def test_get_regulation_error_samples(self):
        """F30-T034: 获取法规错误样本"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)
        error_samples = manager.get_regulation_error_samples()

        assert len(error_samples) == 1
        assert error_samples[0]["sample_id"] == "GD-005"

    def test_update_sample(self):
        """F30-T035: 更新样本"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)

        original_sample = manager.get_sample_by_id("GD-001")
        original_sample["expected_score"]

        updated_sample = manager.update_sample("GD-001", {"expected_score": 9.8})

        assert updated_sample["expected_score"] == 9.8

    def test_delete_sample(self):
        """F30-T036: 删除样本"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir=SAMPLES_DIR)
        initial_count = len(manager.list_all_sample_ids())

        result = manager.delete_sample("GD-003")
        assert result is True

        final_count = len(manager.list_all_sample_ids())
        assert final_count == initial_count - 1

    def test_golden_sample_default_markers(self):
        """F30-T037: GoldenSample默认初始化 (覆盖lines 27, 29)"""
        from f30_golden_dataset.sample_manager import GoldenSample

        sample = GoldenSample(
            sample_id="test-001",
            quality_level="high",
            expected_score=9.0,
            content={"text": "test"},
            quality_metrics={},
            metadata={}
        )

        assert sample.hallucination_markers == []
        assert sample.regulation_errors == []

    def test_update_nonexistent_sample_returns_none(self):
        """F30-T038: 更新不存在的样本返回None (覆盖line 143)"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager()
        result = manager.update_sample("nonexistent", {"expected_score": 5.0})

        assert result is None

    def test_update_sample_partial_fields(self):
        """F30-T039: 部分更新样本字段 (覆盖lines 148, 150)"""
        from f30_golden_dataset.sample_manager import GoldenSample, SampleManager

        manager = SampleManager()
        manager._samples["test-001"] = GoldenSample(
            sample_id="test-001",
            quality_level="high",
            expected_score=9.0,
            content={"text": "original"},
            quality_metrics={"accuracy": 0.9},
            metadata={}
        )

        result = manager.update_sample("test-001", {
            "quality_metrics": {"accuracy": 0.95},
            "content": {"text": "updated"}
        })

        assert result is not None
        assert result.quality_metrics["accuracy"] == 0.95
        assert result.content["text"] == "updated"
        assert result.expected_score == 9.0

    def test_delete_nonexistent_sample_returns_false(self):
        """F30-T040: 删除不存在的样本返回False (覆盖line 167)"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager()
        result = manager.delete_sample("nonexistent")

        assert result is False


class TestGoldenDatasetEvaluator:
    """Golden Dataset评估器测试"""

    def test_evaluate_with_high_quality_sample(self):
        """F30-T040: 高质量样本评估"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "sample_id": "GD-001",
            "quality_level": "high",
            "expected_score": 9.5,
            "quality_metrics": {
                "terminology_consistency": 0.98,
                "knowledge_accuracy": 0.99,
                "citation_validity": 1.0,
                "logical_coherence": 0.95,
                "format_compliance": 1.0
            }
        }

        evaluation = evaluator.evaluate(sample)

        assert evaluation is not None
        assert hasattr(evaluation, "overall_score")
        assert hasattr(evaluation, "dimension_scores")

    def test_evaluate_detects_hallucination(self):
        """F30-T041: 评估检测幻觉内容"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "sample_id": "GD-004",
            "quality_level": "hallucination",
            "expected_score": 2.0,
            "content": {
                "title": "测试",
                "sections": [
                    {
                        "paragraphs": [
                            "2024年，中国GDP增长率为30%",  # 明显幻觉
                            "[@ref:inexistent_source]"  # 虚假引用
                        ]
                    }
                ]
            },
            "hallucination_markers": [
                {"type": "numerical_hallucination", "content": "30%"}
            ]
        }

        result = evaluator.detect_hallucinations(sample)

        assert result["has_hallucinations"] is True
        assert len(result["detected_hallucinations"]) > 0

    def test_evaluate_detects_regulation_errors(self):
        """F30-T042: 评估检测法规错误"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "sample_id": "GD-005",
            "quality_level": "regulation_error",
            "regulation_errors": [
                {"type": "nonexistent_article", "cited_article": "第九十九条"}
            ]
        }

        result = evaluator.detect_regulation_errors(sample)

        assert result["has_errors"] is True
        assert len(result["detected_errors"]) > 0

    def test_calibrate_judge_with_samples(self):
        """F30-T043: 使用样本校准评判器"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator(samples_dir=SAMPLES_DIR)

        # 模拟LLM评判结果
        llm_results = [
            {"sample_id": "GD-001", "overall_score": 0.92},
            {"sample_id": "GD-002", "overall_score": 0.78},
            {"sample_id": "GD-003", "overall_score": 0.38},
        ]

        calibration_result = evaluator.calibrate_judge(llm_results)

        assert hasattr(calibration_result, "correlation")
        assert hasattr(calibration_result, "bias")
        assert 0 <= calibration_result.correlation <= 1

    def test_evaluate_dimension_score_accuracy(self):
        """F30-T044: 评估维度分数准确性"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator()

        sample = {
            "sample_id": "GD-001",
            "quality_level": "high",
            "expected_score": 9.5,
            "quality_metrics": {
                "terminology_consistency": 0.98,
                "knowledge_accuracy": 0.99,
                "citation_validity": 1.0,
                "logical_coherence": 0.95,
                "format_compliance": 1.0
            },
            "content": {},
            "metadata": {}
        }

        evaluation = evaluator.evaluate(sample)

        for dimension, expected_score in sample["quality_metrics"].items():
            actual_score = evaluation.dimension_scores.get(dimension)
            assert actual_score is not None
            # 分数应该接近期望值（允许小误差）
            assert abs(actual_score - expected_score) < 0.05

    def test_generate_evaluation_report(self):
        """F30-T045: 生成评估报告"""
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator

        evaluator = GoldenDatasetEvaluator(samples_dir=SAMPLES_DIR)

        report = evaluator.generate_evaluation_report()

        assert report is not None
        assert "total_samples" in report
        assert "average_score" in report
        assert "quality_distribution" in report


class TestGoldenDatasetIntegration:
    """Golden Dataset集成测试"""

    def test_full_calibration_workflow(self):
        """F30-T050: 完整校准工作流"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder
        from f30_golden_dataset.evaluator import GoldenDatasetEvaluator
        from f30_golden_dataset.sample_manager import SampleManager

        # 加载数据集
        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)
        builder.load_all_samples()

        # 获取样本管理器
        manager = SampleManager(samples_dir=SAMPLES_DIR)

        # 获取评估器
        evaluator = GoldenDatasetEvaluator(samples_dir=SAMPLES_DIR)

        # 评估高质量样本
        high_sample = manager.get_sample_by_id("GD-001")
        eval_result = evaluator.evaluate(high_sample)

        assert eval_result.overall_score > 0.9

        # 评估幻觉样本
        halluc_sample = manager.get_sample_by_id("GD-004")
        halluc_result = evaluator.detect_hallucinations(halluc_sample)

        assert halluc_result["has_hallucinations"] is True

    def test_dataset_coverage(self):
        """F30-T051: 数据集覆盖各种质量等级"""
        from f30_golden_dataset.dataset_builder import DatasetBuilder

        builder = DatasetBuilder(samples_dir=SAMPLES_DIR)
        dataset = builder.load_all_samples()

        quality_levels = {sample["quality_level"] for sample in dataset.values()}

        assert "high" in quality_levels
        assert "medium" in quality_levels
        assert "low" in quality_levels
        assert "hallucination" in quality_levels
        assert "regulation_error" in quality_levels


class TestF30CoverageGapsRemaining:
    """F30: 剩余覆盖缺口测试 - 覆盖sample_manager.py剩余未覆盖行"""

    def test_load_all_nonexistent_directory(self):
        """F30-T045: _load_all处理不存在的目录 (覆盖line 58)"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager(samples_dir="/nonexistent/directory")

        assert len(manager.list_all_sample_ids()) == 0

    def test_add_sample_with_complete_data(self):
        """F30-T046: add_sample完整数据 (覆盖lines 179-181)"""
        from f30_golden_dataset.sample_manager import SampleManager

        manager = SampleManager()

        sample_data = {
            "sample_id": "test_sample_001",
            "quality_level": "high",
            "expected_score": 0.95,
            "content": {"text": "测试内容"},
            "quality_metrics": {"accuracy": 0.9},
            "metadata": {"source": "test"},
            "hallucination_markers": [],
            "regulation_errors": []
        }

        result = manager.add_sample(sample_data)

        assert result.sample_id == "test_sample_001"
        assert result.quality_level == "high"
        assert result.expected_score == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
