"""
F23: 内容安全过滤 - 测试文件
TDD GREEN阶段：实现后测试通过
"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from content_filter import ContentSecurityFilter


class TestContentSecurityFilter(unittest.TestCase):
    """F23内容安全过滤测试套件"""

    def setUp(self):
        """测试前设置"""
        self.filter = ContentSecurityFilter()

    # ========== F23-T001: 脏话检测 ==========
    def test_detects_profanity(self):
        """F23-T001: 检测脏话"""
        profane_content = "这是一个该死的糟糕内容"
        result = self.filter.filter_content(profane_content)

        self.assertFalse(result.is_safe)
        self.assertIn("profanity", result.categories)
        self.assertEqual(result.action, "BLOCK")

    def test_profanity_confidence_score(self):
        """F23-T001: 脏话可信度评分"""
        profane_content = "这个内容包含fuck和shit"
        result = self.filter.filter_content(profane_content)

        self.assertLess(result.confidence_score, 1.0)
        self.assertGreater(result.confidence_score, 0.0)

    def test_multiple_profanity_words(self):
        """F23-T001: 多脏话检测"""
        content = "混合多种脏话：fuck, shit, damn"
        result = self.filter.filter_content(content)

        self.assertFalse(result.is_safe)
        self.assertGreaterEqual(len(result.violations), 1)

    # ========== F23-T002: 仇恨言论过滤 ==========
    def test_filters_hate_speech(self):
        """F23-T002: 过滤仇恨言论"""
        hate_content = "我恨所有某种族的人"
        result = self.filter.filter_content(hate_content)

        self.assertFalse(result.is_safe)
        self.assertIn("hate_speech", result.categories)

    def test_discrimination_content(self):
        """F23-T002: 歧视内容检测"""
        discrimination = "基于宗教的歧视性言论"
        result = self.filter.filter_content(discrimination)

        self.assertFalse(result.is_safe)

    def test_hate_speech_action_block(self):
        """F23-T002: 仇恨言论动作为BLOCK"""
        hate_content = "仇恨言论内容"
        result = self.filter.filter_content(hate_content)

        self.assertEqual(result.action, "BLOCK")

    # ========== F23-T003: PII检测 ==========
    def test_detects_pii_information(self):
        """F23-T003: 检测PII信息"""
        pii_content = "张三的身份证号是110101199001011234，手机是13800138000"
        result = self.filter.filter_content(pii_content)

        self.assertFalse(result.is_safe)
        self.assertIn("pii", result.categories)

    def test_detects_phone_number(self):
        """F23-T003: 检测电话号码"""
        phone_content = "联系电话：139-1234-5678"
        result = self.filter.filter_content(phone_content)

        self.assertFalse(result.is_safe)
        self.assertIn("pii", result.categories)

    def test_detects_email_address(self):
        """F23-T003: 检测邮箱地址"""
        email_content = "请联系 admin@example.com"
        result = self.filter.filter_content(email_content)

        self.assertFalse(result.is_safe)
        self.assertIn("pii", result.categories)

    def test_detects_id_card(self):
        """F23-T003: 检测身份证号"""
        id_content = "身份证号码：110101199001011234"
        result = self.filter.filter_content(id_content)

        self.assertFalse(result.is_safe)
        self.assertIn("pii", result.categories)

    def test_pii_violation_details(self):
        """F23-T003: PII违规详情"""
        pii_content = "李四的身份证110101199001011234"
        result = self.filter.filter_content(pii_content)

        self.assertTrue(len(result.violations) > 0)
        self.assertIn("type", result.violations[0])

    # ========== F23-T004: 政治敏感内容 ==========
    def test_tracks_political_sensitivity(self):
        """F23-T004: 政治敏感追踪"""
        political_content = "包含敏感政治话题"
        result = self.filter.filter_content(political_content)

        self.assertIn("political", result.categories)

    def test_political_sensitivity_level(self):
        """F23-T004: 政治敏感级别"""
        sensitive_content = "敏感政治内容"
        result = self.filter.filter_content(sensitive_content)

        if not result.is_safe:
            self.assertIn("sensitivity_level", result.violations[0])

    def test_political_categories(self):
        """F23-T004: 政治类别"""
        political_content = "台独相关话题"
        result = self.filter.filter_content(political_content)

        self.assertIn("political", result.categories)

    # ========== F23-T005: 批量处理 ==========
    def test_batch_scanning(self):
        """F23-T005: 批量扫描"""
        contents = [
            "正常内容",
            "包含脏话damn",
            "李四手机13912345678"
        ]
        results = self.filter.scan_batch(contents)

        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].is_safe)
        self.assertFalse(results[1].is_safe)
        self.assertFalse(results[2].is_safe)

    def test_batch_result_order(self):
        """F23-T005: 批量结果顺序"""
        contents = ["safe1", "unsafe1", "safe2"]
        results = self.filter.scan_batch(contents)

        self.assertEqual(results[0].action, "PASS")
        self.assertEqual(results[1].action, "BLOCK")
        self.assertEqual(results[2].action, "PASS")

    def test_empty_batch(self):
        """F23-T005: 空批量"""
        results = self.filter.scan_batch([])
        self.assertEqual(len(results), 0)

    def test_large_batch(self):
        """F23-T005: 大批量处理"""
        contents = ["内容" + str(i) for i in range(100)]
        results = self.filter.scan_batch(contents)

        self.assertEqual(len(results), 100)

    # ========== F23-T006: 白名单放行 ==========
    def test_whitelisted_content_passes(self):
        """F23-T006: 白名单内容放行"""
        content = "这是一个特殊白名单内容"
        self.filter.add_to_whitelist(content)

        result = self.filter.filter_content(content)

        self.assertTrue(result.is_safe)
        self.assertEqual(result.action, "WHITELIST")

    def test_whitelist_partial_match(self):
        """F23-T006: 白名单部分匹配"""
        self.filter.add_to_whitelist("白名单关键词")
        content = "这句话包含白名单关键词"

        result = self.filter.filter_content(content)

        self.assertTrue(result.is_safe)

    def test_whitelist_not_affect_other(self):
        """F23-T006: 白名单不影响其他内容"""
        self.filter.add_to_whitelist("safe_keyword")
        unsafe_content = "This is a damn bad content"

        result = self.filter.filter_content(unsafe_content)

        self.assertFalse(result.is_safe)

    # ========== F23-SEC001: 注入攻击防御 ==========
    def test_injection_attack_prevention(self):
        """F23-SEC001: 注入攻击防御"""
        injection_content = "正常内容<script>alert('xss')</script>还有更多"
        result = self.filter.filter_content(injection_content)

        self.assertFalse(result.is_safe)
        self.assertIn("malware", result.categories)

    def test_sql_injection_pattern(self):
        """F23-SEC001: SQL注入模式"""
        sql_content = "'; DROP TABLE users; --"
        result = self.filter.filter_content(sql_content)

        self.assertFalse(result.is_safe)

    def test_xss_injection(self):
        """F23-SEC001: XSS注入"""
        xss_content = "<img src=x onerror=alert(1)>"
        result = self.filter.filter_content(xss_content)

        self.assertFalse(result.is_safe)
        self.assertIn("malware", result.categories)

    def test_path_traversal(self):
        """F23-SEC001: 路径遍历"""
        path_content = "../../../etc/passwd"
        result = self.filter.filter_content(path_content)

        self.assertFalse(result.is_safe)

    def test_command_injection(self):
        """F23-SEC001: 命令注入"""
        cmd_content = "content; rm -rf /"
        result = self.filter.filter_content(cmd_content)

        self.assertFalse(result.is_safe)

    def test_injection_confidence_high(self):
        """F23-SEC001: 注入攻击高置信度"""
        injection_content = "content<script>malicious()</script>"
        result = self.filter.filter_content(injection_content)

        self.assertGreaterEqual(result.confidence_score, 0.9)

    # ========== 安全测试补充 ==========
    def test_safe_content_passes(self):
        """安全内容通过"""
        safe_content = "这是一个完全安全的正常内容"
        result = self.filter.filter_content(safe_content)

        self.assertTrue(result.is_safe)
        self.assertEqual(result.action, "PASS")

    def test_confidence_score_bounds(self):
        """可信度评分边界"""
        content = "任意内容"
        result = self.filter.filter_content(content)

        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)

    def test_mixed_content_flags_all_issues(self):
        """混合内容标记所有问题"""
        mixed = "脏话fuck加PII:张三110101199001011234"
        result = self.filter.filter_content(mixed)

        self.assertFalse(result.is_safe)
        self.assertTrue(len(result.categories) >= 2)

    def test_result_serialization(self):
        """结果可序列化"""
        result = self.filter.filter_content("测试内容")
        result_dict = result.to_dict()

        self.assertIsInstance(result_dict, dict)
        self.assertIn("is_safe", result_dict)
        self.assertIn("confidence_score", result_dict)


class TestAsyncContentFilter(unittest.TestCase):
    """异步过滤测试"""

    def setUp(self):
        self.filter = ContentSecurityFilter()

    def test_async_filter_content(self):
        """异步单条过滤"""
        async def run():
            result = await self.filter.async_filter_content("安全内容")
            self.assertTrue(result.is_safe)

        asyncio.run(run())

    def test_async_batch_scan(self):
        """异步批量扫描"""
        async def run():
            contents = ["内容1", "脏话damn", "安全内容"]
            results = await self.filter.async_scan_batch(contents)
            self.assertEqual(len(results), 3)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
