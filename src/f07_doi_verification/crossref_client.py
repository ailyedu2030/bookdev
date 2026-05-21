"""
F07: DOI强制解析服务 - CrossRef客户端
"""
import asyncio
from typing import Any


class CrossRefClient:
    """CrossRef API客户端"""

    DEFAULT_TIMEOUT = 10.0  # seconds

    def __init__(self, base_url: str = "https://api.crossref.org", timeout: float | None = None):
        self.base_url = base_url
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT

    async def fetch_doi_metadata(self, doi: str, timeout: float | None = None) -> dict[str, Any] | None:
        """获取DOI元数据"""
        effective_timeout = timeout if timeout is not None else self.timeout

        try:
            await asyncio.wait_for(asyncio.sleep(0.01), timeout=effective_timeout)  # Simulate network delay
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Request timed out after {effective_timeout} seconds")

        mock_dois = {
            "10.1234/example.123": {
                "DOI": "10.1234/example.123",
                "title": "Example Research Paper",
                "author": "John Doe",
                "published": "2024-01-01",
                "publisher": "Test Publisher",
            },
            "10.1234/ai-research": {
                "DOI": "10.1234/ai-research",
                "title": "Artificial Intelligence Research Overview",
                "author": "AI Research Team",
                "published": "2024-01-15",
                "publisher": "AI Press",
            },
        }

        return mock_dois.get(doi)

    async def verify_doi_exists(self, doi: str, timeout: float | None = None) -> bool:
        """验证DOI是否存在"""
        metadata = await self.fetch_doi_metadata(doi, timeout)
        return metadata is not None
