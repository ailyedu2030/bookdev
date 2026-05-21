"""
F31: MiniMax M2.7 API客户端 - Token计数器

支持中英文混合文本的Token估算。
"""

import re


class TokenCounter:
    """Token计数器 - 基于启发式规则估算Token数"""

    # 近似换算系数
    CHINESE_CHAR_TOKENS = 1.5  # 每个中文字符 ≈ 1.5 tokens
    ENGLISH_CHARS_PER_TOKEN = 4  # 每4个英文字符 ≈ 1 token
    CODE_CHARS_PER_TOKEN = 3.5  # 代码每3.5字符 ≈ 1 token

    def __init__(self, max_context_tokens: int = 200_000):
        """
        初始化Token计数器

        Args:
            max_context_tokens: 上下文窗口大小
        """
        self.max_context_tokens = max_context_tokens

    def count(self, text: str) -> int:
        """
        计算文本的Token数

        使用启发式规则分别计算中英文Token数。

        Args:
            text: 输入文本

        Returns:
            估算的Token数
        """
        if not text or not text.strip():
            return 0

        text = text.strip()

        # 分离中文和非中文字符
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
        non_chinese = re.sub(r"[\u4e00-\u9fff\u3400-\u4dbf]", "", text)

        # 非中文部分按英文规则计数
        non_chinese_stripped = re.sub(r"\s+", " ", non_chinese).strip()
        non_chinese_chars = len(non_chinese_stripped)

        # 计算Token数
        chinese_tokens = chinese_chars * self.CHINESE_CHAR_TOKENS
        english_tokens = non_chinese_chars / self.ENGLISH_CHARS_PER_TOKEN

        # 标点符号和空格按0.25 token计
        punctuation = len(re.findall(r'[，。！？；：""\'\'（）\s,.!?;:"\'()\\s]', text))
        punct_tokens = punctuation * 0.25

        total = int(chinese_tokens + english_tokens + punct_tokens)
        return max(1, total)

    def is_within_window(self, text: str) -> bool:
        """
        检查文本是否在上下文窗口内

        Args:
            text: 输入文本

        Returns:
            True如果在窗口内，否则False
        """
        return self.count(text) <= self.max_context_tokens

    def remaining_tokens(self, text: str) -> int:
        """
        计算剩余可用Token数

        Args:
            text: 当前已使用的文本

        Returns:
            剩余可用Token数
        """
        used = self.count(text)
        return max(0, self.max_context_tokens - used)
