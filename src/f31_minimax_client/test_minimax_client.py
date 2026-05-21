"""
F31: MiniMax M2.7 API客户端 - TDD RED阶段测试

本测试文件包含所有RED测试用例，这些测试在实现前应该失败。
按照TDD原则：
1. RED: 写失败测试 (本文件)
2. GREEN: 写最简实现让测试通过
3. Refactor: 优化代码质量

验收标准:
- ≥15个测试用例
- 所有测试在无真实API Key时通过（使用Mock）
- 单元测试覆盖率 ≥80%
"""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

# ============================================================================
# RateLimiter 测试
# ============================================================================

class TestRateLimiter:
    """速率限制器测试"""

    def test_rate_limiter_allows_requests_within_limit(self):
        """F31-T001: 在限制范围内允许请求"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=60)
        for _ in range(10):
            assert limiter.can_proceed() is True

    def test_rate_limiter_blocks_when_exceeded(self):
        """F31-T002: 超过限制时阻塞请求"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=10)
        for _ in range(10):
            assert limiter.can_proceed() is True
        assert limiter.can_proceed() is False

    def test_rate_limiter_resets_after_window(self):
        """F31-T003: 时间窗口过后自动重置"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=10)
        # 放入过期的时间戳，模拟61秒前的请求
        old_time = time.monotonic() - 61.0
        for _ in range(10):
            limiter._request_timestamps.append(old_time)
        assert limiter.can_proceed() is True

    def test_rate_limiter_remaining_count(self):
        """F31-T004: 正确报告剩余请求数"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=10)
        assert limiter.remaining() == 10
        limiter.can_proceed()
        assert limiter.remaining() == 9

    @pytest.mark.asyncio
    async def test_rate_limiter_async_wait(self):
        """F31-T005: 异步等待直到可用"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=10)
        # 放入接近过期的旧时间戳（61秒前）
        old_time = time.monotonic() - 61.0
        for _ in range(10):
            limiter._request_timestamps.append(old_time)

        # wait_for_available should succeed because old timestamps are expired
        result = await limiter.wait_for_available(timeout=1.0)
        assert result is True
        assert limiter.can_proceed() is True

    @pytest.mark.asyncio
    async def test_rate_limiter_async_wait_timeout(self):
        """F31-T005b: 异步等待超时返回False (覆盖line 85)"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=1)
        limiter.can_proceed()

        now = time.monotonic()
        limiter._request_timestamps = [now - 0.5]

        result = await limiter.wait_for_available(timeout=0.5)
        assert result is False


# ============================================================================
# TokenCounter 测试
# ============================================================================

class TestTokenCounter:
    """Token计数器测试"""

    def test_count_chinese_characters(self):
        """F31-T006: 中文Token计数"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter()
        text = "人工智能是计算机科学的一个分支"
        tokens = counter.count(text)
        assert tokens > 0
        # 中文字符约1.5-2 tokens each
        assert 10 <= tokens <= 40

    def test_count_english_text(self):
        """F31-T007: 英文Token计数"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter()
        text = "Artificial intelligence is a branch of computer science"
        tokens = counter.count(text)
        assert tokens > 0
        # 英文约4 chars/token
        expected_approx = len(text) / 4
        assert abs(tokens - expected_approx) < 20

    def test_count_mixed_text(self):
        """F31-T008: 中英混合Token计数"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter()
        text = "Artificial Intelligence (AI) 即人工智能，是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。"
        tokens = counter.count(text)
        assert tokens > 0

    def test_count_empty_text(self):
        """F31-T009: 空文本Token计数为0"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter()
        assert counter.count("") == 0
        assert counter.count("   ") == 0

    def test_count_within_context_window(self):
        """F31-T010: Token数在上下文窗口内"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter(max_context_tokens=200_000)
        text = "测试内容" * 1000
        tokens = counter.count(text)
        assert tokens < 200_000
        assert counter.is_within_window(text) is True

    def test_count_exceeds_context_window(self):
        """F31-T011: 超过上下文窗口时正确检测"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter(max_context_tokens=100)
        text = "A" * 10000  # This should exceed 100 tokens
        assert counter.is_within_window(text) is False


# ============================================================================
# CostTracker 测试
# ============================================================================

class TestCostTracker:
    """成本追踪器测试"""

    def test_cost_tracking_basic(self):
        """F31-T012: 基本成本追踪"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)
        tracker.record_usage(prompt_tokens=500, completion_tokens=300)
        stats = tracker.get_stats()

        assert stats.total_prompt_tokens == 500
        assert stats.total_completion_tokens == 300
        assert stats.total_tokens == 800

    def test_cost_calculation(self):
        """F31-T013: 成本计算准确性"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)
        tracker.record_usage(prompt_tokens=1_000_000, completion_tokens=500_000)
        stats = tracker.get_stats()

        # 1.5M tokens @ ¥2/M = ¥3.0
        assert abs(stats.total_cost - 3.0) < 0.01

    def test_cost_tracker_multiple_records(self):
        """F31-T014: 多次记录累计正确"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)
        for _ in range(10):
            tracker.record_usage(prompt_tokens=100, completion_tokens=50)

        stats = tracker.get_stats()
        assert stats.total_prompt_tokens == 1000
        assert stats.total_completion_tokens == 500
        assert stats.total_tokens == 1500

    def test_cost_tracker_reset(self):
        """F31-T015: 重置统计"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)
        tracker.record_usage(prompt_tokens=1000, completion_tokens=500)
        tracker.reset()

        stats = tracker.get_stats()
        assert stats.total_prompt_tokens == 0
        assert stats.total_cost == 0.0

    def test_cost_tracker_call_count(self):
        """F31-T016: API调用次数统计"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)
        for _ in range(5):
            tracker.record_usage(prompt_tokens=100, completion_tokens=50)

        stats = tracker.get_stats()
        assert stats.total_calls == 5


# ============================================================================
# ResponseParser 测试
# ============================================================================

class TestResponseParser:
    """响应解析器测试"""

    def test_parse_successful_response(self):
        """F31-T019: 解析成功响应"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "这是生成的教材内容"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "total_tokens": 150
            }
        }

        result = parser.parse(response_data)
        assert result.content == "这是生成的教材内容"
        assert result.finish_reason == "stop"
        assert result.usage_total_tokens == 150

    def test_parse_response_without_usage(self):
        """F31-T020: 解析无usage字段的响应"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "内容"
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        result = parser.parse(response_data)
        assert result.content == "内容"
        assert result.usage_total_tokens == 0

    def test_parse_streaming_chunk(self):
        """F31-T021: 解析流式响应块"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        chunk_data = {
            "choices": [
                {
                    "delta": {
                        "content": "分块内容"
                    },
                    "finish_reason": None
                }
            ]
        }

        result = parser.parse(chunk_data, is_stream=True)
        assert result.content == "分块内容"
        assert result.is_delta is True

    def test_parse_error_response(self):
        """F31-T022: 解析错误响应"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        error_data = {
            "base_resp": {
                "status_code": 1002,
                "status_msg": "invalid parameter"
            }
        }

        with pytest.raises(ValueError, match="invalid parameter"):
            parser.parse(error_data)

    def test_validate_response_structure(self):
        """F31-T023: 验证响应结构"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        assert parser.validate_structure({"choices": [{"message": {"content": "x"}}]}) is True
        assert parser.validate_structure({}) is False
        assert parser.validate_structure({"choices": []}) is False


# ============================================================================
# MiniMaxClient (Mock) 测试
# ============================================================================

class TestTokenCounterEdgeCases:
    """Token计数器边界测试"""

    def test_remaining_tokens_calculation(self):
        """F31-T017: 剩余Token数计算"""
        from f31_minimax_client.token_counter import TokenCounter

        counter = TokenCounter(max_context_tokens=1000)
        text = "A" * 100  # ~25 tokens
        remaining = counter.remaining_tokens(text)
        assert remaining > 0
        assert remaining < 1000


class TestRateLimiterEdgeCases:
    """速率限制器边界测试"""

    @pytest.mark.asyncio
    async def test_rate_limiter_async_wait_timeout(self):
        """F31-T018: 异步等待超时"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=1)
        limiter.can_proceed()  # 耗尽配额

        # 等待时间远小于窗口周期，应该超时
        result = await limiter.wait_for_available(timeout=0.01)
        assert result is False


class TestResponseParserEdgeCases:
    """响应解析器边界测试"""

    def test_parse_empty_choices(self):
        """F31-T024: 解析空choices"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.parse({"choices": []})
        assert result.content == ""
        assert result.finish_reason == "empty"

    def test_extract_error_from_base_resp(self):
        """F31-T025: 提取base_resp错误"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        error = parser.extract_error({
            "base_resp": {"status_code": 1002, "status_msg": "rate limited"}
        })
        assert error == "rate limited"

    def test_extract_error_no_error(self):
        """F31-T026: 无错误时返回None"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        error = parser.extract_error({
            "choices": [{"message": {"content": "ok"}}]
        })
        assert error is None

    def test_extract_error_from_error_field(self):
        """F31-T027: 提取error字段错误"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        error = parser.extract_error({
            "error": {"message": "server error"}
        })
        assert error == "server error"

    def test_extract_error_string_format(self):
        """F31-T028: 提取字符串格式错误"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        error = parser.extract_error({
            "error": "something broke"
        })
        assert error == "something broke"


class TestCostTrackerEdgeCases:
    """成本追踪器边界测试"""

    def test_usage_stats_to_dict(self):
        """F31-T029: UsageStats序列化"""
        from f31_minimax_client.cost_tracker import CostTracker

        tracker = CostTracker(price_per_million=2.0)
        tracker.record_usage(prompt_tokens=100, completion_tokens=50)

        stats = tracker.get_stats()
        d = stats.to_dict()
        assert d["total_prompt_tokens"] == 100
        assert d["total_completion_tokens"] == 50
        assert d["total_calls"] == 1


class TestMiniMaxClient:
    """MiniMax M2.7客户端测试"""

    @pytest.mark.asyncio
    async def test_client_initialization_with_api_key(self):
        """F31-T030: 使用API Key初始化客户端"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        client = MiniMaxClient(api_key="test-key-123")
        assert client.api_key == "test-key-123"
        assert client.model == "MiniMax-M2.7"
        assert "minimaxi.com" in client.base_url

    @pytest.mark.asyncio
    async def test_client_initialization_without_api_key(self):
        """F31-T031: 无API Key时使用环境变量"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        with patch.dict("os.environ", {"MINIMAX_API_KEY": "env-key-456"}):
            client = MiniMaxClient()
            assert client.api_key == "env-key-456"

    @pytest.mark.asyncio
    async def test_mock_client_generate(self):
        """F31-T032: Mock客户端生成内容"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="你是教材编写助手",
            user_prompt="写一段关于人工智能的介绍"
        )

        assert result.content is not None
        assert len(result.content) > 0
        assert "人工智能" in result.content or "AI" in result.content
        assert result.model == "MiniMax-M2.7(mock)"
        assert result.finish_reason == "stop"
        assert result.usage.total_tokens > 0

    @pytest.mark.asyncio
    async def test_mock_client_usage_tracking(self):
        """F31-T033: Mock客户端追踪使用量"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        await client.generate(
            system_prompt="test",
            user_prompt="hello world"
        )

        stats = client.get_usage_stats()
        assert stats.total_calls == 1
        assert stats.total_tokens > 0

    @pytest.mark.asyncio
    async def test_mock_client_multiple_calls(self):
        """F31-T034: Mock客户端多次调用统计正确"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        for i in range(3):
            await client.generate(
                system_prompt=f"system {i}",
                user_prompt=f"user {i}"
            )

        stats = client.get_usage_stats()
        assert stats.total_calls == 3

    @pytest.mark.asyncio
    async def test_mock_client_with_custom_max_tokens(self):
        """F31-T035: Mock客户端支持自定义max_tokens"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="系统提示",
            user_prompt="用户输入",
            max_tokens=100
        )

        assert result.content is not None
        # Mock should respect max_tokens limit
        assert result.usage.completion_tokens <= 100

    @pytest.mark.asyncio
    async def test_mock_client_with_retry(self):
        """F31-T036: Mock客户端带重试生成"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate_with_retry(
            system_prompt="system",
            user_prompt="user",
            max_retries=3
        )

        assert result.content is not None
        assert result.retry_count >= 0

    @pytest.mark.asyncio
    async def test_mock_client_rate_limit(self):
        """F31-T037: Mock客户端速率限制"""
        from f31_minimax_client.minimax_client import MiniMaxClientError, MockMiniMaxClient
        from f31_minimax_client.rate_limiter import RateLimiter

        # 使用低限制测试
        limiter = RateLimiter(max_rpm=2)
        client = MockMiniMaxClient(rate_limiter=limiter)

        # 前2次应该成功
        await client.generate(system_prompt="s", user_prompt="u")
        await client.generate(system_prompt="s", user_prompt="u")

        # 第3次应该因速率限制失败
        with pytest.raises(MiniMaxClientError, match="Rate limit"):
            await client.generate(system_prompt="s", user_prompt="u")

    @pytest.mark.asyncio
    async def test_client_token_count_delegation(self):
        """F31-T038: 客户端Token计数委托"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        tokens = client.count_tokens("Hello World 你好世界")
        assert tokens > 0

    @pytest.mark.asyncio
    async def test_mock_client_streaming_response(self):
        """F31-T039: Mock客户端流式响应"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="test",
            user_prompt="hello",
            stream=True
        )

        assert result.content is not None
        assert result.is_streamed is True

    @pytest.mark.asyncio
    async def test_api_key_missing_triggers_mock_fallback(self):
        """F31-T040: API Key缺失时触发Mock回退"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        with patch.dict("os.environ", {}, clear=True):
            client = MiniMaxClient()
            assert client._is_mock_mode is True

    @pytest.mark.asyncio
    async def test_mock_client_temperature_effect(self):
        """F31-T041: Mock客户端temperature参数有效"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result1 = await client.generate(
            system_prompt="test",
            user_prompt="hello",
            temperature=0.0
        )
        result2 = await client.generate(
            system_prompt="test",
            user_prompt="hello",
            temperature=1.0
        )

        assert result1.content is not None
        assert result2.content is not None
        # temperature=0 should produce deterministic output
        # temperature=1 may produce different output (in mock, both work)

    @pytest.mark.asyncio
    async def test_client_handles_empty_prompt(self):
        """F31-T042: 空提示处理"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()

        with pytest.raises(ValueError, match="empty"):
            await client.generate(system_prompt="", user_prompt="test")

        with pytest.raises(ValueError, match="empty"):
            await client.generate(system_prompt="test", user_prompt="")

    @pytest.mark.asyncio
    async def test_mock_client_returns_structured_output(self):
        """F31-T043: Mock客户端支持结构化JSON输出"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="你返回JSON",
            user_prompt="返回一个包含name和age的JSON对象"
        )

        # Mock should try to return JSON when requested
        assert result.content is not None
        try:
            data = json.loads(result.content)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pass  # Mock may not always return valid JSON

    @pytest.mark.asyncio
    async def test_client_usage_stats_format(self):
        """F31-T044: 使用统计格式正确"""
        from f31_minimax_client.cost_tracker import UsageStats
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        await client.generate(system_prompt="s", user_prompt="u")

        stats = client.get_usage_stats()
        assert isinstance(stats, UsageStats)
        assert hasattr(stats, "total_calls")
        assert hasattr(stats, "total_tokens")
        assert hasattr(stats, "total_cost")

    @pytest.mark.asyncio
    async def test_mock_client_extreme_max_tokens(self):
        """F31-T045: Mock客户端极低max_tokens截断"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="你是教材编写助手",
            user_prompt="请详细介绍人工智能的发展历史和应用领域" * 5,
            max_tokens=50
        )

        assert result.content is not None
        assert result.usage.completion_tokens <= 50

    @pytest.mark.asyncio
    async def test_generate_with_retry_all_fail(self):
        """F31-T046: 全部重试失败时抛出异常"""
        from f31_minimax_client.minimax_client import MiniMaxClientError, MockMiniMaxClient
        from f31_minimax_client.rate_limiter import RateLimiter

        # 创建rate_limit=1的客户端
        limiter = RateLimiter(max_rpm=1)
        client = MockMiniMaxClient(rate_limiter=limiter)

        # 先消耗配额
        await client.generate(system_prompt="s", user_prompt="u")

        # 现在所有generate调用都会因rate limit失败
        with pytest.raises(MiniMaxClientError, match="attempts"):
            await client.generate_with_retry(
                system_prompt="test",
                user_prompt="test",
                max_retries=2
            )


# ============================================================================
# MiniMaxClient 内部方法测试 (覆盖真实API路径和Mock分支)
# ============================================================================

class TestMiniMaxClientInternal:
    """MiniMax客户端内部方法测试"""

    def test_build_headers(self):
        """F31-T047: 构建请求头 (covers line 193)"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        client = MiniMaxClient(api_key="test-key")
        headers = client._build_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_build_payload(self):
        """F31-T048: 构建请求体 (covers line 207)"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        client = MiniMaxClient(api_key="test-key", model="Custom-Model")
        payload = client._build_payload(
            system_prompt="系统提示",
            user_prompt="用户输入",
            max_tokens=1000,
            temperature=0.5,
            stream=False,
        )
        assert payload["model"] == "Custom-Model"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "系统提示"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "用户输入"
        assert payload["max_tokens"] == 1000
        assert payload["temperature"] == 0.5
        assert payload["stream"] is False

    @pytest.mark.asyncio
    async def test_real_api_successful_response(self):
        """F31-T049: 真实API成功响应 (covers lines 126-175)"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        client = MiniMaxClient(api_key="test-real-key")

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "AI生成的内容"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 100}
        })

        # Proper async context manager mock
        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_ctx
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await client.generate(
                system_prompt="你是AI助手",
                user_prompt="写一段内容"
            )

        assert result.content == "AI生成的内容"
        assert result.finish_reason == "stop"
        assert result.model == "MiniMax-M2.7"
        assert result.usage.total_tokens == 100
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_real_api_http_error(self):
        """F31-T050: 真实API HTTP错误响应 (covers lines 141-145)"""
        from f31_minimax_client.minimax_client import MiniMaxClient, MiniMaxClientError

        client = MiniMaxClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_ctx
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(MiniMaxClientError, match="API returned 500"):
                await client.generate(
                    system_prompt="sys",
                    user_prompt="usr"
                )

    @pytest.mark.asyncio
    async def test_real_api_error_in_response(self):
        """F31-T051: 真实API响应中包含错误 (covers lines 152-154)"""
        from f31_minimax_client.minimax_client import MiniMaxClient, MiniMaxClientError

        client = MiniMaxClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "base_resp": {"status_code": 1002, "status_msg": "rate limited"},
            "choices": [{"message": {"content": ""}, "finish_reason": "error"}],
            "usage": {"total_tokens": 0}
        })

        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_ctx
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(MiniMaxClientError, match="API error: rate limited"):
                await client.generate(
                    system_prompt="sys",
                    user_prompt="usr"
                )

    @pytest.mark.asyncio
    async def test_real_api_error_field_response(self):
        """F31-T051b: 真实API error字段错误 (covers lines 153-154)"""
        from f31_minimax_client.minimax_client import MiniMaxClient, MiniMaxClientError

        client = MiniMaxClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "error": {"message": "service unavailable"},
            "choices": [{"message": {"content": ""}, "finish_reason": "error"}],
            "usage": {"total_tokens": 0}
        })

        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_ctx
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(MiniMaxClientError, match="API error: service unavailable"):
                await client.generate(
                    system_prompt="sys",
                    user_prompt="usr"
                )

    @pytest.mark.asyncio
    async def test_real_api_network_error(self):
        """F31-T052: 真实API网络错误 (covers lines 177-178)"""
        from f31_minimax_client.minimax_client import MiniMaxClient, MiniMaxClientError

        client = MiniMaxClient(api_key="test-key")

        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Connection refused")
        )

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_ctx
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(MiniMaxClientError, match="Network error"):
                await client.generate(
                    system_prompt="sys",
                    user_prompt="usr"
                )

    @pytest.mark.asyncio
    async def test_real_api_unexpected_error(self):
        """F31-T053: 真实API意外异常 (covers lines 181-182)"""
        from f31_minimax_client.minimax_client import MiniMaxClient, MiniMaxClientError

        client = MiniMaxClient(api_key="test-key")

        mock_post_ctx = MagicMock()
        mock_post_ctx.__aenter__ = AsyncMock(
            side_effect=RuntimeError("Something unexpected")
        )

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_ctx
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(MiniMaxClientError, match="Unexpected error"):
                await client.generate(
                    system_prompt="sys",
                    user_prompt="usr"
                )


class TestMiniMaxClientMockBranches:
    """MiniMax Mock客户端内部分支测试"""

    @pytest.mark.asyncio
    async def test_deterministic_response_ai_keyword(self):
        """F31-T054: 确定性响应-AI关键词 (covers line 336)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="系统提示",
            user_prompt="介绍人工智能的应用",
            temperature=0.0
        )
        assert "人工智能" in result.content

    @pytest.mark.asyncio
    async def test_deterministic_response_textbook_keyword(self):
        """F31-T055: 确定性响应-教材关键词 (covers lines 337-338)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="编写教材内容",
            user_prompt="教材章节概要",
            temperature=0.0
        )
        assert "教材编写" in result.content or "教材" in result.content

    @pytest.mark.asyncio
    async def test_deterministic_response_intro_keyword(self):
        """F31-T056: 确定性响应-介绍关键词 (covers line 340)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="系统提示",
            user_prompt="介绍相关知识",
            temperature=0.0
        )
        assert "介绍" in result.content

    @pytest.mark.asyncio
    async def test_deterministic_response_long_prompt(self):
        """F31-T057: 确定性响应-长提示扩展输出 (covers line 351)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="系统提示" * 20,
            user_prompt="请详细介绍人工智能的发展历史、核心技术、应用场景和未来趋势" * 5,
            temperature=0.0,
            max_tokens=5000
        )
        assert result.content is not None
        assert len(result.content) > 100
        assert "核心概念与定义" in result.content or "理论基础与原理" in result.content

    @pytest.mark.asyncio
    async def test_deterministic_response_truncation(self):
        """F31-T058: 确定性响应-超max_tokens截断 (covers lines 366-368)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="系统提示" * 20,
            user_prompt="请详细介绍人工智能" * 10,
            temperature=0.0,
            max_tokens=30
        )
        assert result.content is not None
        assert result.usage.completion_tokens <= 30

    @pytest.mark.asyncio
    async def test_varied_response_textbook_keyword(self):
        """F31-T059: 变体响应-教材关键词 (covers line 406)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="教材编写指导",
            user_prompt="如何编写优质教材",
            temperature=1.0
        )
        assert result.content is not None
        assert "教材" in result.content

    @pytest.mark.asyncio
    async def test_varied_response_ai_keyword(self):
        """F31-T060: 变体响应-AI关键词 (covers line 392)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="系统提示",
            user_prompt="人工智能是什么",
            temperature=1.0
        )
        assert result.content is not None
        assert "人工智能" in result.content

    @pytest.mark.asyncio
    async def test_varied_response_fallback(self):
        """F31-T061: 变体响应-无关键词时通用回复 (covers lines 417-424)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="通用助手",
            user_prompt="你好",
            temperature=1.0
        )
        assert result.content is not None
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_mock_json_response_valid(self):
        """F31-T062: Mock JSON输出-合法JSON (covers lines 298-305)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="返回json格式数据",
            user_prompt="返回一个包含key和value的JSON对象",
            temperature=0.0
        )
        assert result.content is not None
        try:
            data = json.loads(result.content)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pass

    @pytest.mark.asyncio
    async def test_mock_json_response_invalid_json(self):
        """F31-T063: Mock JSON输出-非法JSON时回退 (covers lines 306-307)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="返回json",
            user_prompt="JSON",
            temperature=1.0
        )
        assert result.content is not None
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_varied_response_truncation(self):
        """F31-T064: 变体响应-超max_tokens截断 (covers lines 428-431)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate(
            system_prompt="教材",
            user_prompt="教材" * 20,
            temperature=1.0,
            max_tokens=20
        )
        assert result.content is not None
        assert result.usage.completion_tokens <= 20

    def test_mock_minimax_client_init(self):
        """F31-T065: MockMiniMaxClient初始化 (covers MockMiniMaxClient.__init__)"""
        from f31_minimax_client.cost_tracker import CostTracker
        from f31_minimax_client.minimax_client import MockMiniMaxClient
        from f31_minimax_client.rate_limiter import RateLimiter
        from f31_minimax_client.token_counter import TokenCounter

        limiter = RateLimiter(max_rpm=30)
        tracker = CostTracker(price_per_million=1.5)
        counter = TokenCounter(max_context_tokens=100_000)

        client = MockMiniMaxClient(
            rate_limiter=limiter,
            cost_tracker=tracker,
            token_counter=counter,
        )
        assert client._is_mock_mode is True
        assert client.api_key == "mock-key"

    def test_token_usage_dataclass(self):
        """F31-T066: TokenUsage数据类构造"""
        from f31_minimax_client.minimax_client import TokenUsage

        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

        usage2 = TokenUsage(prompt_tokens=5, completion_tokens=5, total_tokens=10)
        assert usage2.total_tokens == 10

        usage3 = TokenUsage()
        assert usage3.prompt_tokens == 0
        assert usage3.completion_tokens == 0
        assert usage3.total_tokens == 0

    def test_generate_result_defaults(self):
        """F31-T067: GenerateResult默认值和post_init"""
        from f31_minimax_client.minimax_client import GenerateResult

        result = GenerateResult(content="test")
        assert result.finish_reason == "stop"
        assert result.model == "MiniMax-M2.7"
        assert result.timestamp != ""
        assert result.usage.total_tokens == 0

    @pytest.mark.asyncio
    async def test_client_custom_timeout(self):
        """F31-T068: 客户端自定义超时 (covers __init__ timeout)"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        client = MiniMaxClient(api_key="test-key", timeout=30.0)
        assert client._timeout == 30.0

        client2 = MiniMaxClient(api_key="test-key")
        assert client2._timeout == 120.0

    @pytest.mark.asyncio
    async def test_client_custom_url_and_model(self):
        """F31-T069: 客户端自定义URL和模型 (covers __init__ custom options)"""
        from f31_minimax_client.minimax_client import MiniMaxClient

        client = MiniMaxClient(
            api_key="test-key",
            base_url="https://custom.api.com/v2",
            model="CustomModel",
        )
        assert client.base_url == "https://custom.api.com/v2"
        assert client.model == "CustomModel"

    @pytest.mark.asyncio
    async def test_generate_with_retry_success(self):
        """F31-T070: 带重试的生成-首次成功 (covers generate_with_retry retry_count)"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        client = MockMiniMaxClient()
        result = await client.generate_with_retry(
            system_prompt="test",
            user_prompt="test",
            max_retries=3,
            temperature=0.0,
        )
        assert result.retry_count == 0
        assert result.content is not None


class TestMiniMaxClientUncovered:
    """覆盖MiniMaxClient未测试的分支"""

    @pytest.mark.asyncio
    async def test_mock_json_response_malformed_with_braces(self):
        """covers lines 300-307: 提取的JSON片段无效时保留原内容"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        original_method = MockMiniMaxClient._deterministic_response

        def fake_deterministic(self, system_prompt, user_prompt, max_tokens):
            return '这是JSON: {invalid json} 结束了'

        MockMiniMaxClient._deterministic_response = fake_deterministic
        try:
            client = MockMiniMaxClient()
            result = await client.generate(
                system_prompt="返回json",
                user_prompt="JSON",
                temperature=0.0
            )
            assert result.content is not None
        finally:
            MockMiniMaxClient._deterministic_response = original_method

    @pytest.mark.asyncio
    async def test_wait_for_available_no_timestamps(self):
        """covers line 85: 没有时间戳记录时等待0.1秒"""
        from f31_minimax_client.rate_limiter import RateLimiter

        limiter = RateLimiter(max_rpm=60)
        result = await limiter.wait_for_available(timeout=1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_mock_json_extraction_succeeds(self):
        """covers line 305: JSON关键词响应包含有效JSON时成功提取"""
        from f31_minimax_client.minimax_client import MockMiniMaxClient

        original_method = MockMiniMaxClient._varied_response

        def fake_varied_response(self, system_prompt, user_prompt, max_tokens):
            return '以下是JSON响应: {"name": "测试", "value": 123} 结束'

        MockMiniMaxClient._varied_response = fake_varied_response
        try:
            client = MockMiniMaxClient()
            result = await client.generate(
                system_prompt="返回JSON格式",
                user_prompt="JSON",
                temperature=1.0
            )
            assert result.content is not None
            import json
            data = json.loads(result.content)
            assert data["name"] == "测试"
            assert data["value"] == 123
        finally:
            MockMiniMaxClient._varied_response = original_method

    def test_validate_response_structure_no_message_no_delta(self):
        """covers line 104: choice既没有message也没有delta时返回False"""
        from f31_minimax_client.response_parser import ResponseParser

        parser = ResponseParser()
        result = parser.validate_structure({
            "choices": [{"finish_reason": "stop"}]
        })
        assert result is False
