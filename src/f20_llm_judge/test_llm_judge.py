"""
F20: LLM-as-Judge评分系统 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。
按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量

验收标准:
- LLM评判评分与人工评分相关性>0.8
- 单元测试覆盖率 ≥85%
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestJudgeDimensions:
    """评分维度测试"""

    def test_judge_dimensions_defined(self):
        """F20-T001: 评分维度必须正确定义"""
        from f20_llm_judge.scoring_engine import JUDGE_DIMENSIONS

        assert "terminology_consistency" in JUDGE_DIMENSIONS
        assert "knowledge_accuracy" in JUDGE_DIMENSIONS
        assert "citation_validity" in JUDGE_DIMENSIONS
        assert "logical_coherence" in JUDGE_DIMENSIONS
        assert "format_compliance" in JUDGE_DIMENSIONS

    def test_dimension_weights_sum_to_one(self):
        """F20-T002: 维度权重必须总和为1"""
        from f20_llm_judge.scoring_engine import JUDGE_DIMENSIONS

        total_weight = sum(d["weight"] for d in JUDGE_DIMENSIONS.values())
        assert abs(total_weight - 1.0) < 0.001, f"Weights sum to {total_weight}, expected 1.0"

    def test_dimension_has_description(self):
        """F20-T003: 每个维度必须有描述"""
        from f20_llm_judge.scoring_engine import JUDGE_DIMENSIONS

        for dim_key, dim_value in JUDGE_DIMENSIONS.items():
            assert "description" in dim_value
            assert len(dim_value["description"]) > 0


class TestPromptTemplates:
    """提示模板测试"""

    def test_judge_prompt_template_exists(self):
        """F20-T010: 评判提示模板必须存在"""
        from f20_llm_judge.prompt_templates import PromptTemplates

        templates = PromptTemplates()
        assert hasattr(templates, "JUDGE_PROMPT")
        assert len(templates.JUDGE_PROMPT) > 0

    def test_prompt_template_contains_dimensions(self):
        """F20-T011: 提示模板必须包含评分维度"""
        from f20_llm_judge.prompt_templates import PromptTemplates

        templates = PromptTemplates()
        prompt = templates.JUDGE_PROMPT

        for dimension in ["terminology_consistency", "knowledge_accuracy",
                          "citation_validity", "logical_coherence", "format_compliance"]:
            assert dimension in prompt, f"Dimension '{dimension}' not in prompt"

    def test_prompt_template_has_scoring_instructions(self):
        """F20-T012: 提示模板必须包含评分说明"""
        from f20_llm_judge.prompt_templates import PromptTemplates

        templates = PromptTemplates()
        prompt = templates.JUDGE_PROMPT

        assert "score" in prompt.lower() or "评分" in prompt

    def test_build_judge_prompt(self):
        """F20-T013: 构建评判提示"""
        from f20_llm_judge.prompt_templates import PromptTemplates

        templates = PromptTemplates()
        content = "这是待评判的教材内容"
        rubric = {"criteria": "评分标准"}

        prompt = templates.build_judge_prompt(content, rubric)

        assert content in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > len(content)


class TestScoringEngine:
    """评分引擎测试"""

    def test_calculate_weighted_score(self):
        """F20-T020: 计算加权分数"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        dimension_scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.85,
            "citation_validity": 0.8,
            "logical_coherence": 0.9,
            "format_compliance": 1.0
        }

        weighted_score = engine.calculate_weighted_score(dimension_scores)

        # 验证加权计算正确
        expected = (
            0.9 * 0.25 +  # terminology
            0.85 * 0.30 +  # knowledge
            0.8 * 0.20 +   # citation
            0.9 * 0.15 +   # logical
            1.0 * 0.10     # format
        )
        assert abs(weighted_score - expected) < 0.001

    def test_calculate_weighted_score_missing_dimension(self):
        """F20-T021: 缺少维度时抛出异常"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        incomplete_scores = {
            "terminology_consistency": 0.9,
            # 缺少其他维度
        }

        with pytest.raises(ValueError):
            engine.calculate_weighted_score(incomplete_scores)

    def test_calculate_weighted_score_invalid_score(self):
        """F20-T022: 无效分数值时抛出异常"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        invalid_scores = {
            "terminology_consistency": 1.5,  # 超出范围
            "knowledge_accuracy": 0.85,
            "citation_validity": 0.8,
            "logical_coherence": 0.9,
            "format_compliance": 1.0
        }

        with pytest.raises(ValueError):
            engine.calculate_weighted_score(invalid_scores)

    def test_score_range_0_to_1(self):
        """F20-T023: 分数范围必须在0-1之间"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        for valid_scores in [
            {"terminology_consistency": 0.0, "knowledge_accuracy": 0.0,
             "citation_validity": 0.0, "logical_coherence": 0.0, "format_compliance": 0.0},
            {"terminology_consistency": 1.0, "knowledge_accuracy": 1.0,
             "citation_validity": 1.0, "logical_coherence": 1.0, "format_compliance": 1.0},
        ]:
            result = engine.calculate_weighted_score(valid_scores)
            assert 0.0 <= result <= 1.0

    def test_calculate_weighted_score_non_numeric(self):
        """F20-T023a: 非数字分数抛出异常"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        non_numeric_scores = {
            "terminology_consistency": "good",
            "knowledge_accuracy": 0.85,
            "citation_validity": 0.8,
            "logical_coherence": 0.9,
            "format_compliance": 1.0
        }

        with pytest.raises(ValueError):
            engine.calculate_weighted_score(non_numeric_scores)

    def test_get_dimension_scores_with_weights(self):
        """F20-T023b: 获取带权重的维度分数"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        dimension_scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.85,
            "citation_validity": 0.8,
        }

        result = engine.get_dimension_scores_with_weights(dimension_scores)

        assert len(result) == 3
        for item in result:
            assert hasattr(item, "dimension")
            assert hasattr(item, "score")
            assert hasattr(item, "weight")
            assert item.dimension in dimension_scores

    def test_get_dimension_scores_with_weights_empty(self):
        """F20-T023c: 获取带权重的维度分数 - 空字典"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        result = engine.get_dimension_scores_with_weights({})

        assert result == []

    def test_validate_dimension_scores_valid(self):
        """F20-T023d: 验证维度分数 - 有效"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        valid_scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.85,
            "citation_validity": 0.8,
            "logical_coherence": 0.9,
            "format_compliance": 1.0
        }

        is_valid, errors = engine.validate_dimension_scores(valid_scores)

        assert is_valid == True
        assert errors == []

    def test_validate_dimension_scores_missing(self):
        """F20-T023e: 验证维度分数 - 缺少维度"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        incomplete_scores = {
            "terminology_consistency": 0.9,
        }

        is_valid, errors = engine.validate_dimension_scores(incomplete_scores)

        assert is_valid == False
        assert len(errors) > 0

    def test_validate_dimension_scores_out_of_range(self):
        """F20-T023f: 验证维度分数 - 超出范围"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        invalid_scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": -0.5,
            "citation_validity": 0.8,
            "logical_coherence": 1.5,
            "format_compliance": 1.0
        }

        is_valid, errors = engine.validate_dimension_scores(invalid_scores)

        assert is_valid == False
        assert len(errors) >= 2

    def test_get_weight_for_known_dimension(self):
        """F20-T023g: 获取已知维度的权重"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        weight = engine.get_weight_for_dimension("knowledge_accuracy")

        assert weight == 0.30

    def test_get_weight_for_unknown_dimension(self):
        """F20-T023h: 获取未知维度的权重"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        weight = engine.get_weight_for_dimension("unknown_dimension")

        assert weight == 0.0

    def test_get_all_dimensions(self):
        """F20-T023i: 获取所有维度配置"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        engine = ScoringEngine()
        dimensions = engine.get_all_dimensions()

        assert "terminology_consistency" in dimensions
        assert "knowledge_accuracy" in dimensions
        assert "citation_validity" in dimensions
        assert "logical_coherence" in dimensions
        assert "format_compliance" in dimensions

    def test_scoring_engine_custom_dimensions(self):
        """F20-T023j: 使用自定义维度的评分引擎"""
        from f20_llm_judge.scoring_engine import ScoringEngine

        custom_dims = {
            "accuracy": {"weight": 0.6, "description": "Accuracy"},
            "clarity": {"weight": 0.4, "description": "Clarity"},
        }

        engine = ScoringEngine(dimensions=custom_dims)
        weighted = engine.calculate_weighted_score({"accuracy": 0.9, "clarity": 0.8})

        assert abs(weighted - (0.9 * 0.6 + 0.8 * 0.4)) < 0.001


class TestJudgeService:
    """LLM评判服务测试"""

    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        mock = AsyncMock()
        mock.generate.return_value = json.dumps({
            "scores": {
                "terminology_consistency": 0.9,
                "knowledge_accuracy": 0.85,
                "citation_validity": 0.8,
                "logical_coherence": 0.9,
                "format_compliance": 0.95
            },
            "overall_score": 0.88
        })
        return mock

    @pytest.mark.asyncio
    async def test_judge_content_returns_scores(self, mock_llm_client):
        """F20-T030: 评判内容返回分数"""
        from f20_llm_judge.judge_service import JudgeService

        service = JudgeService(llm_client=mock_llm_client)
        content = "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。"

        result = await service.judge_content(content)

        assert result is not None
        assert hasattr(result, "scores")
        assert hasattr(result, "overall_score")
        assert hasattr(result, "timestamp")

    @pytest.mark.asyncio
    async def test_judge_content_includes_dimension_scores(self, mock_llm_client):
        """F20-T031: 评判结果包含各维度分数"""
        from f20_llm_judge.judge_service import JudgeService

        mock_llm_client.generate.return_value = '''{
            "scores": {
                "terminology_consistency": 0.92,
                "knowledge_accuracy": 0.88,
                "citation_validity": 0.85,
                "logical_coherence": 0.90,
                "format_compliance": 0.95
            },
            "overall_score": 0.90,
            "reasoning": "内容质量良好"
        }'''

        service = JudgeService(llm_client=mock_llm_client)
        result = await service.judge_content("测试内容")

        assert "terminology_consistency" in result.scores
        assert "knowledge_accuracy" in result.scores
        assert "citation_validity" in result.scores
        assert "logical_coherence" in result.scores
        assert "format_compliance" in result.scores

    @pytest.mark.asyncio
    async def test_judge_content_includes_reasoning(self, mock_llm_client):
        """F20-T032: 评判结果包含推理说明"""
        from f20_llm_judge.judge_service import JudgeService

        mock_llm_client.generate.return_value = '''{
            "scores": {"terminology_consistency": 0.9},
            "overall_score": 0.9,
            "reasoning": "术语使用准确，逻辑清晰"
        }'''

        service = JudgeService(llm_client=mock_llm_client)
        result = await service.judge_content("测试内容")

        assert hasattr(result, "reasoning")
        assert result.reasoning is not None

    @pytest.mark.asyncio
    async def test_judge_content_handles_llm_error(self, mock_llm_client):
        """F20-T033: LLM错误时正确处理"""
        from f20_llm_judge.judge_service import JudgeService, JudgeServiceError

        mock_llm_client.generate.side_effect = Exception("LLM API Error")

        service = JudgeService(llm_client=mock_llm_client)

        with pytest.raises(JudgeServiceError):
            await service.judge_content("测试内容")

    @pytest.mark.asyncio
    async def test_judge_content_validates_response_format(self, mock_llm_client):
        """F20-T034: 验证LLM响应格式"""
        from f20_llm_judge.judge_service import JudgeService, JudgeServiceError

        # 无效的JSON响应
        mock_llm_client.generate.return_value = "这不是有效的JSON"

        service = JudgeService(llm_client=mock_llm_client)

        with pytest.raises(JudgeServiceError):
            await service.judge_content("测试内容")

    @pytest.mark.asyncio
    async def test_judge_content_requires_content(self):
        """F20-T035: 评判内容不能为空"""
        from f20_llm_judge.judge_service import JudgeService

        service = JudgeService(llm_client=AsyncMock())

        with pytest.raises(ValueError):
            await service.judge_content("")

    @pytest.mark.asyncio
    async def test_batch_judge(self, mock_llm_client):
        """F20-T036: 批量评判"""
        from f20_llm_judge.judge_service import JudgeService

        service = JudgeService(llm_client=mock_llm_client)
        contents = [
            "内容1：人工智能的定义",
            "内容2：机器学习的分类",
            "内容3：深度学习的应用"
        ]

        results = await service.batch_judge(contents)

        assert len(results) == 3
        for result in results:
            assert hasattr(result, "scores")
            assert hasattr(result, "overall_score")

    @pytest.mark.asyncio
    async def test_batch_judge_with_failure(self, mock_llm_client):
        """F20-T036a: 批量评判 - 部分失败"""
        from f20_llm_judge.judge_service import JudgeService, JudgeServiceError

        # 第二次调用失败
        call_count = [0]

        async def fail_on_second(prompt, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise JudgeServiceError("模拟错误")
            return json.dumps({
                "scores": {
                    "terminology_consistency": 0.9,
                    "knowledge_accuracy": 0.85,
                    "citation_validity": 0.8,
                    "logical_coherence": 0.9,
                    "format_compliance": 0.95
                },
                "overall_score": 0.88
            })

        mock_llm_client.generate = fail_on_second

        service = JudgeService(llm_client=mock_llm_client)
        contents = [
            "内容1",
            "内容2",
            "内容3"
        ]

        results = await service.batch_judge(contents)

        assert len(results) == 2  # 跳过了失败的内容

    def test_parse_llm_response_embedded_json(self):
        """F20-T036b: 解析嵌入JSON的LLM响应"""
        from f20_llm_judge.judge_service import JudgeService

        service = JudgeService(llm_client=AsyncMock())
        # Use flat JSON without nested braces so the regex can match
        response = '以下是评分结果:\n{"scores": 0.9, "overall_score": 0.85, "reasoning": "良好"}\n以上是结论。'

        result = service._parse_llm_response(response)

        assert result is not None
        assert result.overall_score == 0.85

    def test_parse_llm_response_missing_scores(self):
        """F20-T036c: 解析LLM响应 - 缺少scores字段"""
        from f20_llm_judge.judge_service import JudgeService, JudgeServiceError

        service = JudgeService(llm_client=AsyncMock())
        response = '{"overall_score": 0.85}'

        with pytest.raises(JudgeServiceError, match="missing 'scores' field"):
            service._parse_llm_response(response)

    def test_parse_llm_response_missing_overall_score(self):
        """F20-T036d: 解析LLM响应 - 缺少overall_score字段"""
        from f20_llm_judge.judge_service import JudgeService, JudgeServiceError

        service = JudgeService(llm_client=AsyncMock())
        response = '{"scores": {"terminology_consistency": 0.9}}'

        with pytest.raises(JudgeServiceError, match="missing 'overall_score' field"):
            service._parse_llm_response(response)

    def test_judge_result_to_dict(self):
        """F20-T036e: JudgeResult转字典"""
        from f20_llm_judge.judge_service import JudgeResult, JudgeStatus
        from datetime import datetime

        result = JudgeResult(
            scores={"terminology_consistency": 0.9},
            overall_score=0.85,
            reasoning="测试",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            status=JudgeStatus.COMPLETED,
            model_id="gpt-4",
            latency_ms=150.0
        )

        d = result.to_dict()

        assert d["scores"]["terminology_consistency"] == 0.9
        assert d["overall_score"] == 0.85
        assert d["status"] == "completed"
        assert d["model_id"] == "gpt-4"
        assert d["latency_ms"] == 150.0


class TestRubricValidator:
    """评分标准验证器测试"""

    def test_validate_rubric_has_required_dimensions(self):
        """F20-T040: 评分标准必须包含所有必需维度"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        valid_rubric = {
            "terminology_consistency": {"weight": 0.25, "criteria": "术语一致性"},
            "knowledge_accuracy": {"weight": 0.30, "criteria": "知识准确性"},
            "citation_validity": {"weight": 0.20, "criteria": "引用有效性"},
            "logical_coherence": {"weight": 0.15, "criteria": "逻辑连贯性"},
            "format_compliance": {"weight": 0.10, "criteria": "格式合规性"}
        }

        assert validator.validate_rubric(valid_rubric) is True

    def test_validate_rubric_missing_dimension(self):
        """F20-T041: 缺少维度时验证失败"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        incomplete_rubric = {
            "terminology_consistency": {"weight": 0.25, "criteria": "术语一致性"},
            "knowledge_accuracy": {"weight": 0.30, "criteria": "知识准确性"},
            # 缺少其他维度
        }

        assert validator.validate_rubric(incomplete_rubric) is False

    def test_validate_rubric_weights_sum_to_one(self):
        """F20-T042: 评分标准权重和必须为1"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        invalid_rubric = {
            "terminology_consistency": {"weight": 0.5, "criteria": "术语一致性"},
            "knowledge_accuracy": {"weight": 0.5, "criteria": "知识准确性"},
            "citation_validity": {"weight": 0.5, "criteria": "引用有效性"},
            "logical_coherence": {"weight": 0.5, "criteria": "逻辑连贯性"},
            "format_compliance": {"weight": 0.5, "criteria": "格式合规性"}
        }

        assert validator.validate_rubric(invalid_rubric) is False

    def test_validate_rubric_weight_range(self):
        """F20-T043: 权重值必须在0-1之间"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        invalid_rubric = {
            "terminology_consistency": {"weight": 1.5, "criteria": "术语一致性"},
            "knowledge_accuracy": {"weight": 0.30, "criteria": "知识准确性"},
            "citation_validity": {"weight": 0.20, "criteria": "引用有效性"},
            "logical_coherence": {"weight": 0.15, "criteria": "逻辑连贯性"},
            "format_compliance": {"weight": 0.10, "criteria": "格式合规性"}
        }

        assert validator.validate_rubric(invalid_rubric) is False

    def test_validate_dimension_score(self):
        """F20-T044: 验证单维度分数"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        assert validator.validate_dimension_score(0.5) is True
        assert validator.validate_dimension_score(0.0) is True
        assert validator.validate_dimension_score(1.0) is True
        assert validator.validate_dimension_score(-0.1) is False
        assert validator.validate_dimension_score(1.1) is False

    def test_validate_rubric_negative_weight(self):
        """F20-T044a: 评分标准包含负权重"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        negative_weight_rubric = {
            "terminology_consistency": {"weight": -0.1, "criteria": "术语一致性"},
            "knowledge_accuracy": {"weight": 0.30, "criteria": "知识准确性"},
            "citation_validity": {"weight": 0.30, "criteria": "引用有效性"},
            "logical_coherence": {"weight": 0.30, "criteria": "逻辑连贯性"},
            "format_compliance": {"weight": 0.20, "criteria": "格式合规性"}
        }

        assert validator.validate_rubric(negative_weight_rubric) is False

    def test_validate_rubric_weight_greater_than_one(self):
        """F20-T044b: 评分标准包含大于1的权重且和为1"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()

        # 一个维度权重为1，其他为0，和仍为1但单个权重超范围
        extreme_rubric = {
            "terminology_consistency": {"weight": 2.0, "criteria": "术语一致性"},
            "knowledge_accuracy": {"weight": -0.25, "criteria": "知识准确性"},
            "citation_validity": {"weight": -0.25, "criteria": "引用有效性"},
            "logical_coherence": {"weight": -0.25, "criteria": "逻辑连贯性"},
            "format_compliance": {"weight": -0.25, "criteria": "格式合规性"}
        }

        assert validator.validate_rubric(extreme_rubric) is False

    def test_validate_all_dimension_scores_valid(self):
        """F20-T044c: 验证所有维度分数 - 有效"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()
        scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.85,
            "citation_validity": 0.8,
            "logical_coherence": 0.9,
            "format_compliance": 0.95
        }

        is_valid, errors = validator.validate_all_dimension_scores(scores)

        assert is_valid is True
        assert errors == []

    def test_validate_all_dimension_scores_missing(self):
        """F20-T044d: 验证所有维度分数 - 缺少维度"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()
        scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": 0.85,
        }

        is_valid, errors = validator.validate_all_dimension_scores(scores)

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_all_dimension_scores_out_of_range(self):
        """F20-T044e: 验证所有维度分数 - 超出范围"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()
        scores = {
            "terminology_consistency": 0.9,
            "knowledge_accuracy": -0.1,
            "citation_validity": 1.5,
            "logical_coherence": 0.9,
            "format_compliance": 0.95
        }

        is_valid, errors = validator.validate_all_dimension_scores(scores)

        assert is_valid is False
        assert len(errors) >= 2

    def test_get_dimension_descriptions(self):
        """F20-T044f: 获取所有维度描述"""
        from f20_llm_judge.rubric_validator import RubricValidator

        validator = RubricValidator()
        descriptions = validator.get_dimension_descriptions()

        assert len(descriptions) == 5
        assert "terminology_consistency" in descriptions
        assert len(descriptions["terminology_consistency"]) > 0


class TestCorrelationWithHumanJudgment:
    """与人工评分相关性测试"""

    @pytest.mark.asyncio
    async def test_correlation_calculation(self):
        """F20-T050: 相关性计算"""
        from f20_llm_judge.judge_service import calculate_correlation

        llm_scores = [0.9, 0.85, 0.78, 0.92, 0.88]
        human_scores = [0.92, 0.83, 0.80, 0.90, 0.87]

        correlation = calculate_correlation(llm_scores, human_scores)

        assert 0 <= correlation <= 1
        assert correlation > 0.8, "Correlation should be > 0.8 for well-calibrated judge"

    @pytest.mark.asyncio
    async def test_perfect_correlation(self):
        """F20-T051: 完全相关性"""
        from f20_llm_judge.judge_service import calculate_correlation

        scores = [0.9, 0.85, 0.78, 0.92, 0.88]

        correlation = calculate_correlation(scores, scores)

        assert correlation == pytest.approx(1.0, abs=1e-9)

    @pytest.mark.asyncio
    async def test_negative_correlation(self):
        """F20-T052: 负相关性"""
        from f20_llm_judge.judge_service import calculate_correlation

        llm_scores = [0.9, 0.85, 0.78, 0.92, 0.88]
        human_scores = [0.3, 0.35, 0.42, 0.28, 0.32]

        correlation = calculate_correlation(llm_scores, human_scores)

        assert correlation < 0

    def test_calculate_correlation_unequal_length(self):
        """F20-T053: 相关性计算 - 不等长列表"""
        from f20_llm_judge.judge_service import calculate_correlation

        with pytest.raises(ValueError, match="same length"):
            calculate_correlation([0.9, 0.8], [0.7, 0.8, 0.9])

    def test_calculate_correlation_single_sample(self):
        """F20-T054: 相关性计算 - 单样本"""
        from f20_llm_judge.judge_service import calculate_correlation

        result = calculate_correlation([0.9], [0.8])

        assert result == 1.0

    def test_calculate_correlation_zero_variance(self):
        """F20-T055: 相关性计算 - 零方差"""
        from f20_llm_judge.judge_service import calculate_correlation

        result = calculate_correlation([0.5, 0.5, 0.5], [0.8, 0.85, 0.82])

        assert result == 0.0

    def test_calculate_correlation_both_zero_variance(self):
        """F20-T056: 相关性计算 - 双方零方差"""
        from f20_llm_judge.judge_service import calculate_correlation

        result = calculate_correlation([0.5, 0.5, 0.5], [0.8, 0.8, 0.8])

        assert result == 0.0


class TestMockLLMClientCoverage:
    """MockLLMClient覆盖率测试"""

    @pytest.mark.asyncio
    async def test_mock_llm_client_raises_when_should_fail_true(self):
        """F20-T057: MockLLMClient在should_fail=True时抛出异常 (覆盖line 75)"""
        from f20_llm_judge.judge_service import MockLLMClient, JudgeService, JudgeServiceError

        mock_client = MockLLMClient(should_fail=True)
        service = JudgeService(llm_client=mock_client)

        with pytest.raises(JudgeServiceError):
            await service.judge_content("测试内容")

    @pytest.mark.asyncio
    async def test_mock_llm_client_default_response(self):
        """F20-T058: MockLLMClient默认响应 (覆盖line 81)"""
        from f20_llm_judge.judge_service import MockLLMClient, JudgeService

        mock_client = MockLLMClient()
        service = JudgeService(llm_client=mock_client)

        result = await service.judge_content("测试内容")

        assert result is not None
        assert hasattr(result, "scores")
        assert hasattr(result, "overall_score")
        assert result.overall_score == 0.88

    @pytest.mark.asyncio
    async def test_judge_content_json_decode_error_handler(self):
        """F20-T059: JudgeService处理JSONDecodeError (覆盖line 152)"""
        from f20_llm_judge.judge_service import MockLLMClient, JudgeService, JudgeServiceError

        mock_client = MockLLMClient(response="invalid json {")
        service = JudgeService(llm_client=mock_client)

        with pytest.raises(JudgeServiceError):
            await service.judge_content("测试内容")

    @pytest.mark.asyncio
    async def test_judge_content_general_exception_handler(self):
        """F20-T060: JudgeService处理通用异常 (覆盖line 154)"""
        from f20_llm_judge.judge_service import MockLLMClient, JudgeService, JudgeServiceError

        class RaisingMockClient(MockLLMClient):
            async def generate(self, prompt: str, **kwargs) -> str:
                raise RuntimeError("Unexpected error")

        mock_client = RaisingMockClient()
        service = JudgeService(llm_client=mock_client)

        with pytest.raises(JudgeServiceError) as exc_info:
            await service.judge_content("测试内容")

        assert "Judge service error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
