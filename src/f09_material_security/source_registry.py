"""
F09: 素材安全管理 - 来源注册表
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourceInfo:
    name: str
    url: str = ""
    contact: str = ""
    trust_level: str = "UNKNOWN"
    registered_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0


class SourceRegistrationResult:
    def __init__(self, registered: bool, source_id: str = "", reason: str = ""):
        self.registered = registered
        self.source_id = source_id
        self.reason = reason


class MaterialSourceRegistry:
    """素材来源注册表"""

    WHITELIST_SOURCES = {
        "国家统计局",
        "教育部",
        "国务院",
        "中央政府",
        "财政部",
        "中国人民银行",
        "商务部",
        "科技部",
        "国家发改委",
        "国家市场监督管理总局",
    }

    def __init__(self):
        self._registered_sources: dict[str, SourceInfo] = {}

    async def register_source(self, source: SourceInfo) -> SourceRegistrationResult:
        """注册来源"""
        if source.name in self._registered_sources:
            return SourceRegistrationResult(registered=False, reason="Source already registered")

        self._registered_sources[source.name] = source
        return SourceRegistrationResult(registered=True, source_id=source.name)

    async def verify_source(self, source_name: str) -> bool:
        """核实来源"""
        if source_name in self._registered_sources:
            source = self._registered_sources[source_name]
            return source.trust_level in ["WHITELIST", "VERIFIED"]
        return False

    def is_whitelisted(self, source_name: str) -> bool:
        """检查是否在白名单"""
        if source_name in self.WHITELIST_SOURCES:
            return True
        if source_name in self._registered_sources:
            return self._registered_sources[source_name].trust_level == "WHITELIST"
        return False

    def get_source_info(self, source_name: str) -> SourceInfo | None:
        """获取来源信息"""
        if source_name in self._registered_sources:
            return self._registered_sources[source_name]
        if source_name in self.WHITELIST_SOURCES:
            return SourceInfo(name=source_name, trust_level="WHITELIST")
        return None

    def get_all_sources(self) -> list[SourceInfo]:
        """获取所有注册来源"""
        return list(self._registered_sources.values())
