"""
F31: MiniMax M2.7 API客户端 - 响应解析器

解析MiniMax API的响应数据，包括常规响应和流式响应。
"""

from dataclasses import dataclass


@dataclass
class ParsedResponse:
    """解析后的API响应"""

    content: str
    finish_reason: str | None = None
    usage_total_tokens: int = 0
    usage_prompt_tokens: int = 0
    usage_completion_tokens: int = 0
    model: str | None = None
    is_delta: bool = False
    raw: dict | None = None


class ResponseParser:
    """MiniMax API响应解析器"""

    def parse(self, response_data: dict, is_stream: bool = False) -> ParsedResponse:
        """
        解析API响应

        Args:
            response_data: API返回的JSON数据
            is_stream: 是否为流式响应块

        Returns:
            ParsedResponse对象

        Raises:
            ValueError: 响应包含错误信息时
        """
        # 检查错误
        if "base_resp" in response_data:
            base_resp = response_data["base_resp"]
            if base_resp.get("status_code", 0) != 0:
                raise ValueError(
                    f"API error: {base_resp.get('status_msg', 'unknown error')} "
                    f"(code: {base_resp.get('status_code', 'unknown')})"
                )

        choices = response_data.get("choices", [])
        if not choices:
            return ParsedResponse(content="", finish_reason="empty")

        choice = choices[0]

        if is_stream:
            delta = choice.get("delta", {})
            content = delta.get("content", "")
            return ParsedResponse(
                content=content,
                finish_reason=choice.get("finish_reason"),
                is_delta=True,
                model=response_data.get("model"),
                raw=response_data,
            )
        else:
            message = choice.get("message", {})
            content = message.get("content", "")
            usage = response_data.get("usage", {})

            return ParsedResponse(
                content=content,
                finish_reason=choice.get("finish_reason", "stop"),
                usage_total_tokens=usage.get("total_tokens", 0),
                usage_prompt_tokens=usage.get("prompt_tokens", 0),
                usage_completion_tokens=usage.get("completion_tokens", 0),
                model=response_data.get("model"),
                is_delta=False,
                raw=response_data,
            )

    def validate_structure(self, response_data: dict) -> bool:
        """
        验证响应数据结构

        Args:
            response_data: 待验证的响应数据

        Returns:
            True如果结构有效
        """
        if not response_data:
            return False

        choices = response_data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            return False

        choice = choices[0]
        has_message = "message" in choice and choice["message"] is not None
        has_delta = "delta" in choice and choice["delta"] is not None

        if not has_message and not has_delta:
            return False

        return True

    def extract_error(self, response_data: dict) -> str | None:
        """
        从响应中提取错误信息

        Args:
            response_data: 响应数据

        Returns:
            错误消息字符串，无错误时返回None
        """
        if "base_resp" in response_data:
            base_resp = response_data["base_resp"]
            if base_resp.get("status_code", 0) != 0:
                return base_resp.get("status_msg", "unknown error")

        if "error" in response_data:
            error = response_data["error"]
            if isinstance(error, dict):
                return error.get("message", str(error))
            return str(error)

        return None
