"""
F24: 配置中心 - 测试文件

TDD RED阶段：编写失败测试
"""

from datetime import UTC, datetime

import pytest

from f24_config_center import ConfigCenter, ConfigVersion


class TestConfigCenterBasic:
    """测试配置中心基本功能"""

    def test_init_creates_empty_configs(self):
        """F24-UT001: 初始化时配置为空字典"""
        cc = ConfigCenter()
        assert cc.configs == {}

    def test_init_creates_empty_version_history(self):
        """F24-UT002: 初始化时版本历史为空"""
        cc = ConfigCenter()
        assert cc.version_history == []

    def test_get_config_returns_default_for_missing_key(self):
        """F24-UT003: 获取不存在的配置返回默认值"""
        cc = ConfigCenter()
        result = cc.get_config("nonexistent", default="default_value")
        assert result == "default_value"

    def test_get_config_returns_none_when_no_default(self):
        """F24-UT004: 获取不存在的配置且无默认值时返回None"""
        cc = ConfigCenter()
        result = cc.get_config("nonexistent")
        assert result is None


class TestConfigCenterSetConfig:
    """测试设置配置"""

    def test_set_config_creates_entry(self):
        """F24-UT005: 设置配置创建配置项"""
        cc = ConfigCenter()
        cc.set_config("database.host", "localhost")
        assert cc.configs.get("database.host") == "localhost"

    def test_set_config_returns_config_version(self):
        """F24-UT006: 设置配置返回ConfigVersion对象"""
        cc = ConfigCenter()
        version = cc.set_config("app.name", "test_app")
        assert isinstance(version, ConfigVersion)

    def test_set_config_records_version_number(self):
        """F24-UT007: 设置配置记录版本号"""
        cc = ConfigCenter()
        v1 = cc.set_config("key", "value1")
        v2 = cc.set_config("key", "value2")
        assert v1.version == 1
        assert v2.version == 2

    def test_set_config_records_timestamp(self):
        """F24-UT008: 设置配置记录时间戳"""
        cc = ConfigCenter()
        before = datetime.now(UTC)
        version = cc.set_config("key", "value")
        after = datetime.now(UTC)
        assert before <= version.timestamp <= after

    def test_set_config_records_previous_value(self):
        """F24-UT009: 设置配置记录前一个值"""
        cc = ConfigCenter()
        cc.set_config("key", "value1")
        v2 = cc.set_config("key", "value2")
        assert v2.previous_value == "value1"

    def test_set_config_first_version_has_no_previous(self):
        """F24-UT010: 首次设置配置时没有前一个值"""
        cc = ConfigCenter()
        v1 = cc.set_config("key", "value1")
        assert v1.previous_value is None


class TestConfigCenterVersionHistory:
    """测试配置版本历史"""

    def test_get_version_history_returns_list(self):
        """F24-UT011: 获取版本历史返回列表"""
        cc = ConfigCenter()
        cc.set_config("key", "value1")
        cc.set_config("key", "value2")
        history = cc.get_version_history("key")
        assert isinstance(history, list)
        assert len(history) == 2

    def test_get_version_history_returns_empty_for_unknown_key(self):
        """F24-UT012: 获取未知配置的版本历史返回空列表"""
        cc = ConfigCenter()
        history = cc.get_version_history("unknown")
        assert history == []

    def test_version_history_ordered_by_version(self):
        """F24-UT013: 版本历史按版本号排序"""
        cc = ConfigCenter()
        cc.set_config("key", "v1")
        cc.set_config("key", "v2")
        cc.set_config("key", "v3")
        history = cc.get_version_history("key")
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[2].version == 3

    def test_version_history_contains_correct_values(self):
        """F24-UT014: 版本历史包含正确的值"""
        cc = ConfigCenter()
        cc.set_config("key", "value1")
        cc.set_config("key", "value2")
        history = cc.get_version_history("key")
        assert history[0].value == "value1"
        assert history[1].value == "value2"


class TestConfigCenterRollback:
    """测试配置回滚"""

    def test_rollback_to_previous_version(self):
        """F24-UT015: 回滚到前一版本"""
        cc = ConfigCenter()
        cc.set_config("key", "value1")
        cc.set_config("key", "value2")
        result = cc.rollback("key", 1)
        assert result is True
        assert cc.get_config("key") == "value1"

    def test_rollback_returns_true_on_success(self):
        """F24-UT016: 回滚成功返回True"""
        cc = ConfigCenter()
        cc.set_config("key", "value1")
        cc.set_config("key", "value2")
        result = cc.rollback("key", 1)
        assert result is True

    def test_rollback_returns_false_for_unknown_key(self):
        """F24-UT017: 回滚未知配置返回False"""
        cc = ConfigCenter()
        result = cc.rollback("unknown", 1)
        assert result is False

    def test_rollback_returns_false_for_invalid_version(self):
        """F24-UT018: 回滚到无效版本返回False"""
        cc = ConfigCenter()
        cc.set_config("key", "value1")
        result = cc.rollback("key", 999)
        assert result is False

    def test_rollback_current_value_becomes_rollback_version(self):
        """F24-UT019: 回滚后当前值变为回滚版本的值"""
        cc = ConfigCenter()
        cc.set_config("key", "v1")
        cc.set_config("key", "v2")
        cc.set_config("key", "v3")
        cc.rollback("key", 1)
        assert cc.get_config("key") == "v1"

    def test_rollback_creates_new_version(self):
        """F24-UT020: 回滚操作创建新版本"""
        cc = ConfigCenter()
        cc.set_config("key", "v1")
        cc.set_config("key", "v2")
        history_before = len(cc.get_version_history("key"))
        cc.rollback("key", 1)
        history_after = len(cc.get_version_history("key"))
        assert history_after == history_before + 1


class TestConfigCenterComplexTypes:
    """测试复杂类型配置"""

    def test_set_config_supports_dict(self):
        """F24-UT021: 支持字典类型配置"""
        cc = ConfigCenter()
        config = {"host": "localhost", "port": 5432}
        cc.set_config("database", config)
        assert cc.get_config("database") == config

    def test_set_config_supports_list(self):
        """F24-UT022: 支持列表类型配置"""
        cc = ConfigCenter()
        config = ["item1", "item2", "item3"]
        cc.set_config("items", config)
        assert cc.get_config("items") == config

    def test_set_config_supports_nested_objects(self):
        """F24-UT023: 支持嵌套对象配置"""
        cc = ConfigCenter()
        config = {
            "database": {
                "primary": {"host": "db1", "port": 5432},
                "replica": {"host": "db2", "port": 5433}
            }
        }
        cc.set_config("config", config)
        result = cc.get_config("config")
        assert result["database"]["primary"]["host"] == "db1"


class TestConfigCenterMultipleKeys:
    """测试多配置项管理"""

    def test_different_keys_have_independent_histories(self):
        """F24-UT024: 不同配置项有独立的版本历史"""
        cc = ConfigCenter()
        cc.set_config("key1", "value1")
        cc.set_config("key1", "value2")
        cc.set_config("key2", "a1")
        cc.set_config("key2", "a2")
        cc.set_config("key2", "a3")
        assert len(cc.get_version_history("key1")) == 2
        assert len(cc.get_version_history("key2")) == 3

    def test_get_all_keys_returns_all_config_keys(self):
        """F24-UT025: 获取所有配置键"""
        cc = ConfigCenter()
        cc.set_config("key1", "v1")
        cc.set_config("key2", "v2")
        cc.set_config("key3", "v3")
        keys = cc.get_all_keys()
        assert set(keys) == {"key1", "key2", "key3"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
