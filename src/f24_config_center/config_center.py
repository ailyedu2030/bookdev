"""
F24: 配置中心 - GREEN阶段实现

按照TDD原则，此实现仅包含让测试通过的最简代码。
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class ConfigVersion:
    """配置版本"""

    version: int
    key: str
    value: Any
    previous_value: Any
    timestamp: datetime


class ConfigCenter:
    """配置中心"""

    def __init__(self):
        self.configs: dict[str, Any] = {}
        self.version_history: list[ConfigVersion] = []
        self._version_counters: dict[str, int] = {}
        self._key_histories: dict[str, list[ConfigVersion]] = {}

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return self.configs.get(key, default)

    def set_config(self, key: str, value: Any) -> ConfigVersion:
        """设置配置（记录版本）"""
        previous_value = self.configs.get(key)
        self._version_counters[key] = self._version_counters.get(key, 0) + 1
        version = self._version_counters[key]

        config_version = ConfigVersion(
            version=version, key=key, value=value, previous_value=previous_value, timestamp=datetime.now(UTC)
        )

        if key not in self._key_histories:
            self._key_histories[key] = []
        self._key_histories[key].append(config_version)
        self.version_history.append(config_version)

        self.configs[key] = value
        return config_version

    def get_version_history(self, key: str) -> list[ConfigVersion]:
        """获取配置版本历史"""
        return self._key_histories.get(key, [])

    def rollback(self, key: str, version: int) -> bool:
        """回滚到指定版本"""
        if key not in self._key_histories:
            return False

        history = self._key_histories[key]
        target_version = None
        for v in history:
            if v.version == version:
                target_version = v
                break

        if target_version is None:
            return False

        self.set_config(key, target_version.value)
        return True

    def get_all_keys(self) -> list[str]:
        """获取所有配置键"""
        return list(self.configs.keys())
