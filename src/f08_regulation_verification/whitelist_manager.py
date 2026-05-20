"""
F08: 法规引用核实系统 - 白名单管理器
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class LawInfo:
    name: str
    issuing_body: str
    effective_date: str
    total_articles: int
    source: str = "国家法规数据库"
    last_updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


class WhitelistManager:
    """法规白名单管理器"""

    WHITELISTED_LAWS: Dict[str, LawInfo] = {
        "人工智能法": LawInfo(
            name="人工智能法",
            issuing_body="全国人民代表大会",
            effective_date="2026-01-01",
            total_articles=72,
            source="国家法规数据库"
        ),
        "数据安全法": LawInfo(
            name="数据安全法",
            issuing_body="全国人民代表大会",
            effective_date="2021-09-01",
            total_articles=55,
            source="国家法规数据库"
        ),
        "个人信息保护法": LawInfo(
            name="个人信息保护法",
            issuing_body="全国人民代表大会",
            effective_date="2021-11-01",
            total_articles=74,
            source="国家法规数据库"
        ),
        "网络安全法": LawInfo(
            name="网络安全法",
            issuing_body="全国人民代表大会",
            effective_date="2017-06-01",
            total_articles=70,
            source="国家法规数据库"
        ),
        "电子商务法": LawInfo(
            name="电子商务法",
            issuing_body="全国人民代表大会",
            effective_date="2019-01-01",
            total_articles=89,
            source="国家法规数据库"
        )
    }

    def __init__(self):
        self._custom_laws: Dict[str, LawInfo] = {}

    def is_whitelisted(self, law_name: str) -> bool:
        """检查法规是否在白名单中"""
        return law_name in self.WHITELISTED_LAWS or law_name in self._custom_laws

    def get_law_info(self, law_name: str) -> Optional[LawInfo]:
        """获取法规信息"""
        if law_name in self.WHITELISTED_LAWS:
            return self.WHITELISTED_LAWS[law_name]
        return self._custom_laws.get(law_name)

    def get_whitelisted_laws(self) -> List[str]:
        """获取白名单法规列表"""
        return list(self.WHITELISTED_LAWS.keys()) + list(self._custom_laws.keys())

    def add_law(self, name: str, total_articles: int, issuing_body: str, effective_date: str = None) -> bool:
        """添加法规到白名单"""
        if name in self.WHITELISTED_LAWS:
            return False

        self._custom_laws[name] = LawInfo(
            name=name,
            issuing_body=issuing_body,
            effective_date=effective_date or datetime.now().strftime("%Y-%m-%d"),
            total_articles=total_articles,
            source="Custom"
        )
        return True

    def remove_law(self, name: str) -> bool:
        """从白名单移除法规"""
        if name in self._custom_laws:
            del self._custom_laws[name]
            return True
        return False

    def validate_article_number(self, law_name: str, article_num: int) -> bool:
        """验证条款号是否在有效范围内"""
        info = self.get_law_info(law_name)
        if info is None:
            return False
        return 1 <= article_num <= info.total_articles
