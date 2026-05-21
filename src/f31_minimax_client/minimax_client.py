"""
F31: MiniMax M2.7 API客户端

提供MiniMax M2.7模型的真实API客户端和Mock实现。
Mock实现用于无API Key时的开发和测试。
"""

import os
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Optional, AsyncIterator, Dict, Any

import aiohttp

from f31_minimax_client.token_counter import TokenCounter
from f31_minimax_client.response_parser import ResponseParser, ParsedResponse
from f31_minimax_client.rate_limiter import RateLimiter
from f31_minimax_client.cost_tracker import CostTracker, UsageStats


@dataclass
class TokenUsage:
    """Token使用详情"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class GenerateResult:
    """生成结果"""
    content: str
    finish_reason: str = "stop"
    model: str = "MiniMax-M2.7"
    usage: TokenUsage = field(default_factory=TokenUsage)
    is_streamed: bool = False
    retry_count: int = 0
    latency_ms: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")


class MiniMaxClientError(Exception):
    """MiniMax客户端异常"""
    pass


class MiniMaxClient:
    """MiniMax M2.7 API客户端"""

    BASE_URL = "https://api.minimaxi.com/v1"
    CHAT_ENDPOINT = "/text/chatcompletion_v2"
    MODEL = "MiniMax-M2.7"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None,
        cost_tracker: Optional[CostTracker] = None,
        token_counter: Optional[TokenCounter] = None,
        timeout: float = 120.0,
    ):
        """
        初始化MiniMax客户端

        Args:
            api_key: API密钥，默认从环境变量MINIMAX_API_KEY获取
            base_url: API基础URL
            model: 模型名称
            rate_limiter: 速率限制器
            cost_tracker: 成本追踪器
            token_counter: Token计数器
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY")
        self.base_url = base_url or os.environ.get("MINIMAX_API_BASE") or self.BASE_URL
        self.model = model or os.environ.get("MINIMAX_MODEL") or self.MODEL
        self._timeout = timeout

        self._is_mock_mode = not self.api_key

        self.rate_limiter = rate_limiter or RateLimiter(max_rpm=60)
        self.cost_tracker = cost_tracker or CostTracker(price_per_million=2.0)
        self.token_counter = token_counter or TokenCounter(max_context_tokens=200_000)
        self.response_parser = ResponseParser()

        # INF-012: Create session once and reuse instead of creating per-call
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_created_at: Optional[float] = None
        self._session_timeout = aiohttp.ClientTimeout(total=self._timeout)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a reusable session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._session_timeout)
            self._session_created_at = time.monotonic()
        return self._session

    async def close(self) -> None:
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ) -> GenerateResult:
        """
        生成内容

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            max_tokens: 最大生成Token数
            temperature: 温度参数 (0.0-1.0)
            stream: 是否使用流式响应

        Returns:
            GenerateResult对象

        Raises:
            ValueError: 输入验证失败
            MiniMaxClientError: API调用失败
        """
        self._validate_input(system_prompt, user_prompt)

        if self._is_mock_mode:
            return self._mock_generate(system_prompt, user_prompt, max_tokens, temperature, stream)

        # 等待速率限制 - INF-013: check_and_record properly records the request
        await self.rate_limiter.wait_for_available()

        start_time = time.monotonic()

        try:
            # INF-012: Reuse session instead of creating new one per call
            session = await self._get_session()
            headers = self._build_headers()
            payload = self._build_payload(system_prompt, user_prompt, max_tokens, temperature, stream)

            async with session.post(
                f"{self.base_url}{self.CHAT_ENDPOINT}",
                json=payload,
                headers=headers,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MiniMaxClientError(
                        f"API returned {response.status}: {error_text[:500]}"
                    )

                response_data = await response.json()

            # 解析响应
            parsed = self.response_parser.parse(response_data, is_stream=stream)

            # INF-014: Check for error only once, not twice
            error_msg = self.response_parser.extract_error(response_data)
            if error_msg:
                raise MiniMaxClientError(f"API error: {error_msg}")

            # 记录使用量
            self.cost_tracker.record_usage(
                prompt_tokens=parsed.usage_prompt_tokens,
                completion_tokens=parsed.usage_completion_tokens,
            )

            latency_ms = (time.monotonic() - start_time) * 1000

            return GenerateResult(
                content=parsed.content,
                finish_reason=parsed.finish_reason or "stop",
                model=self.model,
                usage=TokenUsage(
                    prompt_tokens=parsed.usage_prompt_tokens,
                    completion_tokens=parsed.usage_completion_tokens,
                    total_tokens=parsed.usage_total_tokens,
                ),
                is_streamed=stream,
                latency_ms=latency_ms,
            )

        except aiohttp.ClientError as e:
            raise MiniMaxClientError(f"Network error: {e}")
        except MiniMaxClientError:
            raise
        except Exception as e:
            raise MiniMaxClientError(f"Unexpected error: {e}")

    def _validate_input(self, system_prompt: str, user_prompt: str):
        """验证输入参数"""
        if not system_prompt or not system_prompt.strip():
            raise ValueError("system_prompt cannot be empty")
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt cannot be empty")

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        stream: bool,
    ) -> Dict[str, Any]:
        """构建请求体"""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

    async def generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> GenerateResult:
        """
        带重试的生成

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            max_retries: 最大重试次数

        Returns:
            GenerateResult对象

        Raises:
            MiniMaxClientError: 所有重试都失败时
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = await self.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    **kwargs,
                )
                result.retry_count = attempt
                return result
            except (MiniMaxClientError, aiohttp.ClientError) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = min(2 ** attempt, 30)
                    await asyncio.sleep(wait_time)

        raise MiniMaxClientError(
            f"All {max_retries + 1} attempts failed. Last error: {last_error}"
        )

    def count_tokens(self, text: str) -> int:
        """计算Token数"""
        return self.token_counter.count(text)

    def get_usage_stats(self) -> UsageStats:
        """获取使用统计"""
        return self.cost_tracker.get_stats()

    def _mock_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> GenerateResult:
        """
        Mock生成（无API Key时使用）

        行为尽可能接近真实API。

        INF-011: Use check_and_record to properly track mock requests
        in the rate limiter. This ensures mock mode behaves like real mode.
        """
        # INF-011: Use check_and_record instead of can_proceed so the
        # timestamp is properly recorded in the rate limiter
        if not self.rate_limiter.check_and_record():
            raise MiniMaxClientError("Rate limit exceeded")

        prompt_tokens = self.token_counter.count(system_prompt + user_prompt)

        # 根据温度调整响应确定性
        if temperature < 0.1:
            # 确定性响应
            completion = self._deterministic_response(system_prompt, user_prompt, max_tokens)
        else:
            completion = self._varied_response(system_prompt, user_prompt, max_tokens)

        completion_tokens = self.token_counter.count(completion)
        completion_tokens = min(completion_tokens, max_tokens)

        # 如果有JSON关键词，尝试返回JSON
        if ("json" in system_prompt.lower() or "json" in user_prompt.lower()):
            try:
                json_match_start = completion.find("{")
                json_match_end = completion.rfind("}")
                if json_match_start >= 0 and json_match_end > json_match_start:
                    json_str = completion[json_match_start:json_match_end + 1]
                    json.loads(json_str)
                    completion = json_str
            except (json.JSONDecodeError, ValueError):
                pass

        self.cost_tracker.record_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        return GenerateResult(
            content=completion,
            finish_reason="stop",
            model=f"{self.MODEL}(mock)",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            is_streamed=stream,
            latency_ms=50.0,
        )

    def _deterministic_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> str:
        """确定性响应 (temperature≈0)"""
        key_words = []
        if "人工智能" in user_prompt or "AI" in user_prompt:
            key_words.append("人工智能")
        if "教材" in user_prompt or "教材" in system_prompt:
            key_words.append("教材编写")
        if "介绍" in user_prompt:
            key_words.append("介绍")

        topic = "、".join(key_words) if key_words else "相关主题"

        response = (
            f"关于{topic}的内容如下：\n\n"
            f"这是基于MiniMax M2.7模型生成的教材内容。"
        )

        # 如果用户提示较长，生成更长响应
        if len(user_prompt) > 100:
            response += (
                f"\n\n系统提示: {system_prompt[:100]}...\n"
                f"用户需求: {user_prompt[:200]}...\n\n"
                f"根据您的需求，以下是教材内容的详细展开：\n"
                f"1. 核心概念与定义\n"
                f"2. 理论基础与原理\n"
                f"3. 应用场景与案例分析\n"
                f"4. 实践操作与注意事项\n"
                f"5. 总结与思考题\n\n"
                f"以上内容基于MiniMax M2.7模型生成，建议结合实际情况进行调整。"
            )

        # 确保不超过max_tokens
        completion_tokens = self.token_counter.count(response)
        if completion_tokens > max_tokens:
            ratio = max_tokens / completion_tokens
            cutoff = int(len(response) * ratio * 0.9)
            response = response[:cutoff] + "..."

        return response

    def _varied_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> str:
        """变体响应 (temperature>0)"""
        # 模拟一些变化
        variants = [
            "以下是关于该主题的详细内容：\n\n",
            "根据您的要求，答案如下：\n\n",
            "这是生成的内容：\n\n",
        ]

        import hashlib
        seed = int(hashlib.md5(user_prompt.encode()).hexdigest()[:8], 16)
        idx = seed % len(variants)

        response = variants[idx]

        if "人工智能" in user_prompt or "AI" in user_prompt:
            response += (
                f"人工智能（Artificial Intelligence，简称AI）是计算机科学的一个重要分支，"
                f"旨在研究和开发能够模拟、延伸和扩展人类智能的理论、方法、技术及应用系统。\n\n"
                f"人工智能的核心领域包括：\n"
                f"1. 机器学习（Machine Learning）\n"
                f"2. 深度学习（Deep Learning）\n"
                f"3. 自然语言处理（Natural Language Processing）\n"
                f"4. 计算机视觉（Computer Vision）\n"
                f"5. 知识表示与推理（Knowledge Representation）\n\n"
                f"近年来，随着大语言模型（LLM）的快速发展，"
                f"人工智能在教材编写、教育辅助等领域的应用越来越广泛。"
            )
        elif "教材" in user_prompt or "教材" in system_prompt:
            response += (
                f"教材是教学活动的基本工具，是知识传递的重要载体。\n\n"
                f"一本优秀的教材应当具备以下特征：\n"
                f"1. 知识体系的完整性与系统性\n"
                f"2. 内容组织的逻辑性与层次性\n"
                f"3. 语言表达的准确性与清晰性\n"
                f"4. 案例选择的典型性与时代性\n"
                f"5. 习题设计的层次性与启发性\n\n"
                f"在AI辅助教材编写的背景下，"
                f"我们需要在效率提升和质量保障之间找到平衡。"
            )
        else:
            response += (
                f"关于您的问题，以下是相关回答：\n\n"
                f"根据系统提示的要求，我们针对该主题进行了分析和整理。"
                f"该内容基于MiniMax M2.7大语言模型生成，"
                f"模型拥有200K tokens的上下文窗口，"
                f"能够处理长文本的生成和理解任务。"
            )

        # 确保不超过max_tokens
        completion_tokens = self.token_counter.count(response)
        if completion_tokens > max_tokens:
            ratio = max_tokens / completion_tokens
            cutoff = int(len(response) * ratio * 0.9)
            response = response[:cutoff] + "..."

        return response


class MockMiniMaxClient(MiniMaxClient):
    """Mock MiniMax客户端 - 无API Key时的替代实现

    行为接近真实API，用于开发和测试。
    """

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        cost_tracker: Optional[CostTracker] = None,
        token_counter: Optional[TokenCounter] = None,
    ):
        """
        初始化Mock客户端

        Args:
            rate_limiter: 速率限制器
            cost_tracker: 成本追踪器
            token_counter: Token计数器
        """
        super().__init__(
            api_key="mock-key",
            rate_limiter=rate_limiter,
            cost_tracker=cost_tracker,
            token_counter=token_counter,
        )
        self._is_mock_mode = True
