"""
F18: 术语注册表

追踪术语的首次定义位置和重新定义情况
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TermRegistration:
    """术语注册记录"""
    term: str
    definition: str
    location: str  # 位置标识，如 "ch01_s01"
    timestamp: str  # ISO格式时间戳


class TermRegistry:
    """术语注册表"""

    def __init__(self):
        self._registrations: list[TermRegistration] = []
        self._first_definition: dict[str, TermRegistration] = {}
        self._redefinitions: dict[str, list[TermRegistration]] = {}

    def register(
        self,
        location: str,
        term: str,
        definition: str,
        timestamp: str = None
    ) -> None:
        """注册术语

        Args:
            location: 章节位置，如 "ch01_s01"
            term: 术语名称
            definition: 术语定义
            timestamp: 时间戳 (可选)
        """
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat()

        registration = TermRegistration(
            term=term,
            definition=definition,
            location=location,
            timestamp=timestamp,
        )

        self._registrations.append(registration)

        if term not in self._first_definition:
            self._first_definition[term] = registration
            self._redefinitions[term] = []
        else:
            self._redefinitions[term].append(registration)

    def get_first_definition_location(self, term: str) -> Optional[str]:
        """获取术语首次定义位置

        Args:
            term: 术语名称

        Returns:
            首次定义位置，如果未找到返回None
        """
        reg = self._first_definition.get(term)
        return reg.location if reg else None

    def get_redefinitions(self, term: str) -> list[dict]:
        """获取术语重新定义记录

        Args:
            term: 术语名称

        Returns:
            重新定义记录列表
        """
        redefinitions = self._redefinitions.get(term, [])
        return [
            {
                "location": r.location,
                "definition": r.definition,
                "timestamp": r.timestamp,
            }
            for r in redefinitions
        ]

    def get_definition_history(self, term: str) -> list[dict]:
        """获取术语定义历史

        Args:
            term: 术语名称

        Returns:
            定义历史列表
        """
        history = []

        first = self._first_definition.get(term)
        if first:
            history.append({
                "location": first.location,
                "definition": first.definition,
                "timestamp": first.timestamp,
                "is_first": True,
            })

        for r in self._redefinitions.get(term, []):
            history.append({
                "location": r.location,
                "definition": r.definition,
                "timestamp": r.timestamp,
                "is_first": False,
            })

        return history

    def is_first_definition(self, term: str, location: str) -> bool:
        """检查是否是术语的首次定义

        Args:
            term: 术语名称
            location: 位置

        Returns:
            True如果是首次定义
        """
        first = self._first_definition.get(term)
        return first is not None and first.location == location

    def export(self) -> dict:
        """导出注册表数据

        Returns:
            导出的数据
        """
        return {
            "registrations": [
                {
                    "term": r.term,
                    "definition": r.definition,
                    "location": r.location,
                    "timestamp": r.timestamp,
                }
                for r in self._registrations
            ],
            "first_definitions": {
                term: {
                    "location": r.location,
                    "definition": r.definition,
                    "timestamp": r.timestamp,
                }
                for term, r in self._first_definition.items()
            },
        }

    def import_(self, data: dict) -> None:
        """从数据导入注册表

        Args:
            data: 导入的数据
        """
        self._registrations.clear()
        self._first_definition.clear()
        self._redefinitions.clear()

        for reg_data in data.get("registrations", []):
            self.register(
                location=reg_data["location"],
                term=reg_data["term"],
                definition=reg_data["definition"],
                timestamp=reg_data.get("timestamp"),
            )
