"""
F25: 模型路由引擎 - TDD RED阶段测试

验收标准:
- 根据任务类型正确路由到对应模型
- 支持动态路由规则配置
- 单元测试覆盖率 ≥83%
"""


from f25_model_router.model_router import ModelSelection, Task


class TestModelRouter:
    """模型路由测试"""

    def test_routing_rules_defined(self):
        """F25-T001: 路由规则必须正确定义"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        assert hasattr(router, 'ROUTING_RULES')
        assert isinstance(router.ROUTING_RULES, dict)
        assert len(router.ROUTING_RULES) > 0

    def test_route_factual_verification_to_claude(self):
        """F25-T002: 事实核实任务应路由到Claude"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        task = Task(task_type=TaskType.FACTUAL_VERIFICATION, prompt="验证以下事实")
        result = router.route(task)
        assert result == "claude"

    def test_route_creative_writing_to_minimax(self):
        """F25-T003: 创意写作任务应路由到MiniMax"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        task = Task(task_type=TaskType.CREATIVE_WRITING, prompt="写一首诗")
        result = router.route(task)
        assert result == "minimax"

    def test_route_code_generation_to_gpt4o(self):
        """F25-T004: 代码生成任务应路由到GPT-4o"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        task = Task(task_type=TaskType.CODE_GENERATION, prompt="写一个排序算法")
        result = router.route(task)
        assert result == "gpt4o"

    def test_route_risk_assessment_to_claude(self):
        """F25-T005: 风险评估任务应路由到Claude"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        task = Task(task_type=TaskType.RISK_ASSESSMENT, prompt="评估项目风险")
        result = router.route(task)
        assert result == "claude"

    def test_route_unknown_type_returns_default(self):
        """F25-T006: 未知任务类型应返回默认模型"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        task = Task(task_type=TaskType.GENERAL, prompt="普通任务")
        result = router.route(task)
        assert result == "gpt4o"

    def test_select_model_for_prompt_returns_model_selection(self):
        """F25-T007: select_model_for_prompt应返回ModelSelection"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        result = router.select_model_for_prompt("写一段代码", {})
        assert isinstance(result, ModelSelection)
        assert hasattr(result, 'model_id')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'reason')

    def test_select_model_for_prompt_analyzes_context(self):
        """F25-T008: select_model_for_prompt应分析上下文"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        context = {"complexity": "high", "language": "python"}
        result = router.select_model_for_prompt("写一个web服务器", context)
        assert result.model_id in ["gpt4o", "claude"]
        assert result.confidence > 0.0

    def test_custom_routing_rules(self):
        """F25-T009: 支持自定义路由规则"""
        from f25_model_router.model_router import ModelRouter, TaskType

        custom_rules = {
            "factual_verification": "gpt4o"
        }
        router = ModelRouter(routing_rules=custom_rules)
        task = Task(task_type=TaskType.FACTUAL_VERIFICATION, prompt="验证")
        result = router.route(task)
        assert result == "gpt4o"

    def test_router_has_model_registry(self):
        """F25-T010: 路由器应有模型注册表"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        assert hasattr(router, 'model_registry')
        assert isinstance(router.model_registry, dict)

    def test_get_available_models(self):
        """F25-T011: 能获取可用模型列表"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        models = router.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "claude" in models
        assert "minimax" in models
        assert "gpt4o" in models


class TestModelSelection:
    """模型选择结果测试"""

    def test_model_selection_has_all_fields(self):
        """F25-T012: ModelSelection包含所有必要字段"""
        from f25_model_router.model_router import ModelSelection

        selection = ModelSelection(
            model_id="claude",
            confidence=0.95,
            reason="最佳匹配事实核实任务"
        )
        assert selection.model_id == "claude"
        assert selection.confidence == 0.95
        assert selection.reason == "最佳匹配事实核实任务"

    def test_model_selection_confidence_range(self):
        """F25-T013: 置信度应在0-1之间"""
        from f25_model_router.model_router import ModelSelection

        selection = ModelSelection(
            model_id="claude",
            confidence=1.0,
            reason="test"
        )
        assert 0.0 <= selection.confidence <= 1.0

        selection2 = ModelSelection(
            model_id="claude",
            confidence=0.0,
            reason="test"
        )
        assert 0.0 <= selection2.confidence <= 1.0


class TestTaskTypeRouting:
    """任务类型路由测试"""

    def test_all_task_types_have_routing(self):
        """F25-T014: 所有任务类型都有路由规则"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        for task_type in TaskType:
            task = Task(task_type=task_type, prompt="test")
            result = router.route(task)
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

    def test_routing_preserves_task_object(self):
        """F25-T015: 路由不应修改原始任务对象"""
        from f25_model_router.model_router import ModelRouter, TaskType

        router = ModelRouter()
        original_context = {"key": "value"}
        task = Task(
            task_type=TaskType.FACTUAL_VERIFICATION,
            prompt="验证",
            context=original_context
        )
        router.route(task)
        assert task.context == original_context

    def test_select_model_keyword_code(self):
        """F25-T016: 关键词代码匹配 (覆盖line 89-94)"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        result = router.select_model_for_prompt("写一个python函数", {})

        assert result.model_id == "gpt4o"
        assert result.confidence == 0.9

    def test_select_model_keyword_verification(self):
        """F25-T017: 关键词验证核实匹配 (覆盖line 95-100)"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        result = router.select_model_for_prompt("核实这个事实", {})

        assert result.model_id == "claude"
        assert result.confidence == 0.9

    def test_select_model_keyword_creative(self):
        """F25-T018: 关键词创意写作匹配 (覆盖line 101-106)"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        result = router.select_model_for_prompt("写一个创意故事", {})

        assert result.model_id == "minimax"
        assert result.confidence == 0.85

    def test_select_model_default_fallback(self):
        """F25-T019: 默认模型选择 (覆盖line 107-112)"""
        from f25_model_router.model_router import ModelRouter

        router = ModelRouter()
        result = router.select_model_for_prompt("普通的中文任务", {})

        assert result.model_id == "gpt4o"
        assert result.confidence == 0.7
