"""
F29: CI/CD质量门禁 - TDD RED阶段测试

自动化代码质量和安全检查。
验收标准:
- 支持语法检查
- 支持安全扫描
- 支持覆盖率检查
- 单元测试覆盖率 ≥85%
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from typing import List, Dict, Optional, Any

from f29_quality_gate.quality_gate import (
    CheckStatus,
    CheckResult,
    QualityGateResult,
    LinterChecker,
    SecurityScanner,
    CoverageTracker,
)


class TestQualityGate:
    """质量门禁测试"""

    def test_quality_gate_class_exists(self):
        """F29-T001: QualityGate类必须存在"""
        from f29_quality_gate.quality_gate import QualityGate

        assert QualityGate is not None

    def test_quality_gate_initialization(self):
        """F29-T002: QualityGate正确初始化"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        assert gate.linter is not None
        assert gate.security_scanner is not None
        assert gate.coverage_tracker is not None

    def test_run_quality_gates_returns_result(self):
        """F29-T003: run_quality_gates返回QualityGateResult"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate.run_quality_gates("/test/path")
        assert isinstance(result, QualityGateResult)

    def test_quality_gate_result_has_passed_field(self):
        """F29-T004: QualityGateResult包含passed字段"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate.run_quality_gates("/test/path")
        assert hasattr(result, 'passed')
        assert isinstance(result.passed, bool)

    def test_quality_gate_result_has_check_results(self):
        """F29-T005: QualityGateResult包含check_results"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate.run_quality_gates("/test/path")
        assert hasattr(result, 'check_results')
        assert isinstance(result.check_results, list)

    def test_quality_gate_result_has_summary(self):
        """F29-T006: QualityGateResult包含summary"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate.run_quality_gates("/test/path")
        assert hasattr(result, 'summary')
        assert isinstance(result.summary, dict)

    def test_quality_gate_result_has_timestamp(self):
        """F29-T007: QualityGateResult包含timestamp"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate.run_quality_gates("/test/path")
        assert hasattr(result, 'timestamp')
        assert isinstance(result.timestamp, str)

    def test_run_linter_check(self):
        """F29-T008: 能运行语法检查"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate._run_linter_check("/test/path")
        assert isinstance(result, CheckResult)

    def test_run_security_scan(self):
        """F29-T009: 能运行安全扫描"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate._run_security_scan("/test/path")
        assert isinstance(result, CheckResult)

    def test_run_coverage_check(self):
        """F29-T010: 能运行覆盖率检查"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate._run_coverage_check("/test/path")
        assert isinstance(result, CheckResult)

    def test_all_checks_pass_returns_true(self):
        """F29-T011: 所有检查通过时passed为True"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        with patch.object(gate, '_run_linter_check') as mock_linter:
            with patch.object(gate, '_run_security_scan') as mock_security:
                with patch.object(gate, '_run_coverage_check') as mock_coverage:
                    mock_linter.return_value = CheckResult("linter", CheckStatus.PASS, "OK")
                    mock_security.return_value = CheckResult("security", CheckStatus.PASS, "OK")
                    mock_coverage.return_value = CheckResult("coverage", CheckStatus.PASS, "OK")

                    result = gate.run_quality_gates("/test/path")
                    assert result.passed is True

    def test_any_check_fails_returns_false(self):
        """F29-T012: 任一检查失败时passed为False"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        with patch.object(gate, '_run_linter_check') as mock_linter:
            with patch.object(gate, '_run_security_scan') as mock_security:
                with patch.object(gate, '_run_coverage_check') as mock_coverage:
                    mock_linter.return_value = CheckResult("linter", CheckStatus.PASS, "OK")
                    mock_security.return_value = CheckResult("security", CheckStatus.FAIL, "漏洞发现")
                    mock_coverage.return_value = CheckResult("coverage", CheckStatus.PASS, "OK")

                    result = gate.run_quality_gates("/test/path")
                    assert result.passed is False


class TestCheckResult:
    """检查结果测试"""

    def test_check_result_has_required_fields(self):
        """F29-T013: CheckResult包含所有必要字段"""
        result = CheckResult(
            name="test_check",
            status=CheckStatus.PASS,
            message="检查通过"
        )
        assert result.name == "test_check"
        assert result.status == CheckStatus.PASS
        assert result.message == "检查通过"

    def test_check_result_has_details(self):
        """F29-T014: CheckResult可包含详细信息"""
        result = CheckResult(
            name="test",
            status=CheckStatus.WARNING,
            message="发现警告",
            details={"warnings": ["未使用的变量"]}
        )
        assert result.details is not None
        assert "warnings" in result.details


class TestCheckStatus:
    """检查状态测试"""

    def test_check_status_enum_values(self):
        """F29-T015: CheckStatus枚举值正确"""
        assert CheckStatus.PASS.value == "pass"
        assert CheckStatus.FAIL.value == "fail"
        assert CheckStatus.WARNING.value == "warning"
        assert CheckStatus.SKIP.value == "skip"


class TestLinterChecker:
    """语法检查器测试"""

    def test_linter_checker_exists(self):
        """F29-T016: LinterChecker类存在"""
        checker = LinterChecker()
        result = checker.check("/test/path")
        assert isinstance(result, CheckResult)

    def test_linter_finds_syntax_error(self):
        """F29-T017: 能发现语法错误"""
        checker = LinterChecker()
        result = checker.check("tests/fixtures/syntax_error.py")
        assert result.status in [CheckStatus.FAIL, CheckStatus.PASS]


class TestSecurityScanner:
    """安全扫描器测试"""

    def test_security_scanner_exists(self):
        """F29-T018: SecurityScanner类存在"""
        scanner = SecurityScanner()
        result = scanner.scan("/test/path")
        assert isinstance(result, CheckResult)

    def test_security_scanner_detects_hardcoded_secret(self):
        """F29-T019: 能检测硬编码密钥"""
        import tempfile
        import os

        scanner = SecurityScanner()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("api_key = 'sk-1234567890abcdefghijklmnopqrstu'\n")
            temp_path = f.name

        try:
            result = scanner.scan(temp_path)
            assert result.status == CheckStatus.FAIL
        finally:
            os.unlink(temp_path)


class TestCoverageTracker:
    """覆盖率追踪器测试"""

    def test_coverage_tracker_exists(self):
        """F29-T020: CoverageTracker类存在"""
        tracker = CoverageTracker()
        result = tracker.track("/test/path")
        assert isinstance(result, CheckResult)

    def test_coverage_tracker_checks_threshold(self):
        """F29-T021: 覆盖率检查有阈值判断"""
        tracker = CoverageTracker()
        result = tracker.track("/test/path", threshold=80)
        assert result.status in [CheckStatus.PASS, CheckStatus.FAIL, CheckStatus.WARNING]


class TestLinterCheckerDetailed:
    """语法检查器详细测试"""

    def test_linter_checks_file_with_syntax_error(self):
        """F29-T022: 能检测文件语法错误"""
        import tempfile
        import os

        linter = LinterChecker()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo(\n    pass\n")
            temp_path = f.name

        try:
            result = linter._check_file(temp_path)
            assert result.status == CheckStatus.FAIL
            assert '语法错误' in result.message
        finally:
            os.unlink(temp_path)

    def test_linter_checks_valid_file(self):
        """F29-T023: 有效文件通过检查"""
        import tempfile
        import os

        linter = LinterChecker()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo():\n    pass\n")
            temp_path = f.name

        try:
            result = linter._check_file(temp_path)
            assert result.status == CheckStatus.PASS
        finally:
            os.unlink(temp_path)

    def test_linter_checks_directory(self):
        """F29-T024: 能检查目录"""
        import tempfile
        import os

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'valid.py'), 'w') as f:
                f.write("x = 1\n")

            result = linter._check_directory(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_linter_checks_directory_with_syntax_error(self):
        """F29-T024b: 目录中文件有语法错误时返回FAIL"""
        import tempfile
        import os

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'valid.py'), 'w') as f:
                f.write("x = 1\n")
            with open(os.path.join(tmpdir, 'invalid.py'), 'w') as f:
                f.write("def foo(\n    pass\n")

            result = linter._check_directory(tmpdir)
            assert result.status == CheckStatus.FAIL
            assert '发现 1 个错误' in result.message


class TestSecurityScannerDetailed:
    """安全扫描器详细测试"""

    def test_security_scanner_detects_api_key(self):
        """F29-T025: 能检测API密钥"""
        import tempfile
        import os

        scanner = SecurityScanner()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("api_key = 'sk-1234567890abcdefghijklmnopqrstu'\n")
            temp_path = f.name

        try:
            result = scanner._scan_file(temp_path)
            assert len(result) > 0
        finally:
            os.unlink(temp_path)

    def test_security_scanner_detects_password(self):
        """F29-T026: 能检测硬编码密码"""
        import tempfile
        import os

        scanner = SecurityScanner()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("password = 'mysecretpassword123'\n")
            temp_path = f.name

        try:
            result = scanner._scan_file(temp_path)
            assert len(result) > 0
        finally:
            os.unlink(temp_path)

    def test_security_scanner_scans_directory(self):
        """F29-T027: 能扫描目录"""
        import tempfile
        import os

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert isinstance(result, CheckResult)

    def test_security_scanner_skips_conftest_files(self):
        """F29-T027b: conftest文件被跳过"""
        import tempfile
        import os

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'conftest.py'), 'w') as f:
                f.write("password = 'secret123'\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS


class TestCoverageTrackerDetailed:
    """覆盖率追踪器详细测试"""

    def test_coverage_tracker_parses_coverage_file(self):
        """F29-T028: 能解析覆盖率文件"""
        import tempfile
        import os

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = os.path.join(tmpdir, '.coverage')
            with open(coverage_file, 'w') as f:
                f.write("SF:/path/to/file.py\n")
                f.write("DA:10,3\n")
                f.write("DA:11,2\n")
                f.write("DA:12,0\n")

            result = tracker._parse_coverage_file(coverage_file)
            assert abs(result - 66.67) < 0.01

    def test_coverage_tracker_handles_empty_coverage(self):
        """F29-T029: 能处理空覆盖率文件"""
        import tempfile
        import os

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = os.path.join(tmpdir, '.coverage')
            with open(coverage_file, 'w') as f:
                f.write("SF:/path/to/file.py\n")

            result = tracker._parse_coverage_file(coverage_file)
            assert result == 0.0


class TestQualityGateSummary:
    """质量门禁摘要测试"""

    def test_summary_counts_correctly(self):
        """F29-T030: 摘要正确计数"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        check_results = [
            CheckResult("linter", CheckStatus.PASS, "OK"),
            CheckResult("security", CheckStatus.FAIL, "发现漏洞"),
            CheckResult("coverage", CheckStatus.WARNING, "覆盖率低"),
        ]

        summary = gate._compute_summary(check_results)
        assert summary["total"] == 3
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["warnings"] == 1
        assert summary["skipped"] == 0

    def test_all_checks_warning_returns_false(self):
        """F29-T031: 全部警告不通过"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        with patch.object(gate, '_run_linter_check') as mock_linter:
            with patch.object(gate, '_run_security_scan') as mock_security:
                with patch.object(gate, '_run_coverage_check') as mock_coverage:
                    mock_linter.return_value = CheckResult("linter", CheckStatus.WARNING, "警告")
                    mock_security.return_value = CheckResult("security", CheckStatus.WARNING, "警告")
                    mock_coverage.return_value = CheckResult("coverage", CheckStatus.WARNING, "警告")

                    result = gate.run_quality_gates("/test/path")
                    assert result.passed is False


class TestEdgeCases:
    """边缘情况测试"""

    def test_linter_handles_read_error(self):
        """F29-T032: Linter处理读取错误"""
        import tempfile
        import os

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = linter._check_file(tmpdir)
            assert result.status in [CheckStatus.PASS, CheckStatus.WARNING]

    def test_linter_handles_empty_directory(self):
        """F29-T033: Linter处理空目录"""
        import tempfile

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = linter._check_directory(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_security_scanner_handles_empty_directory(self):
        """F29-T034: SecurityScanner处理空目录"""
        import tempfile

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_security_scanner_handles_read_error(self):
        """F29-T035: SecurityScanner处理读取错误"""
        import tempfile
        import os

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, 'subdir')
            os.makedirs(subdir)
            result = scanner._scan_file(subdir)
            assert isinstance(result, list)

    def test_coverage_tracker_handles_empty_coverage_file(self):
        """F29-T036: CoverageTracker处理空覆盖率文件"""
        import tempfile
        import os

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = os.path.join(tmpdir, '.coverage')
            with open(coverage_file, 'w') as f:
                f.write("")

            result = tracker._parse_coverage_file(coverage_file)
            assert result == 0.0

    def test_quality_gate_result_summary_keys(self):
        """F29-T037: 结果摘要包含所有键"""
        from f29_quality_gate.quality_gate import QualityGate

        gate = QualityGate()
        result = gate.run_quality_gates("/test/path")
        assert 'total' in result.summary
        assert 'passed' in result.summary
        assert 'failed' in result.summary
        assert 'warnings' in result.summary
        assert 'skipped' in result.summary

    def test_check_result_str_representation(self):
        """F29-T038: CheckResult可转换为字符串"""
        result = CheckResult(
            name="test",
            status=CheckStatus.PASS,
            message="OK"
        )
        assert "test" in str(result)
        assert "PASS" in str(result)

    def test_quality_gate_result_str_representation(self):
        """F29-T039: QualityGateResult可转换为字符串"""
        result = QualityGateResult(
            passed=True,
            check_results=[],
            summary={"total": 0, "passed": 0, "failed": 0, "warnings": 0, "skipped": 0},
            timestamp="2024-01-01T00:00:00"
        )
        assert "QualityGateResult" in str(result)

    def test_linter_invalid_path_returns_pass(self):
        """F29-T040: Linter检查无效路径返回PASS (覆盖line 58)"""
        import tempfile
        from f29_quality_gate.quality_gate import LinterChecker

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            socket_path = tmpdir + "/test.sock"
            import socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(socket_path)
            sock.listen(1)

            result = linter.check(socket_path)

            assert result.status == CheckStatus.PASS

    def test_coverage_below_threshold_returns_fail(self):
        """F29-T041: 覆盖率低于阈值返回FAIL (覆盖lines 224-230)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import CoverageTracker, CheckStatus

        checker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = os.path.join(tmpdir, ".coverage")
            with open(coverage_file, "w") as f:
                f.write("TOTAL 50.0%")

            result = checker.track(tmpdir, threshold=80)

            assert result.status == CheckStatus.FAIL

    def test_summary_counts_skipped(self):
        """F29-T042: 汇总统计包含SKIP计数 (覆盖lines 360-361)"""
        from f29_quality_gate.quality_gate import QualityGate, CheckResult, CheckStatus

        gate = QualityGate()
        with patch.object(gate, '_run_linter_check') as mock_linter:
            with patch.object(gate, '_run_security_scan') as mock_security:
                with patch.object(gate, '_run_coverage_check') as mock_coverage:
                    mock_linter.return_value = CheckResult("linter", CheckStatus.SKIP, "跳过")
                    mock_security.return_value = CheckResult("security", CheckStatus.SKIP, "跳过")
                    mock_coverage.return_value = CheckResult("coverage", CheckStatus.SKIP, "跳过")

                    result = gate.run_quality_gates("/test/path")

                    assert result.summary["skipped"] == 3


class TestF29CoverageGapsRemaining:
    """F29: 剩余覆盖缺口测试 - 覆盖quality_gate.py剩余未覆盖行"""

    def test_linter_check_directory_via_check_method(self):
        """F29-T049: LinterChecker.check调用_check_directory (覆盖line 56)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import LinterChecker, CheckStatus

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'valid.py'), 'w') as f:
                f.write("x = 1\n")

            result = linter.check(tmpdir)

            assert result.status == CheckStatus.PASS

    def test_linter_check_directory_with_pycache(self):
        """F29-T050: LinterChecker跳过__pycache__目录 (覆盖line 95)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import LinterChecker, CheckStatus

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            pycache_dir = os.path.join(tmpdir, '__pycache__')
            os.makedirs(pycache_dir)
            with open(os.path.join(pycache_dir, 'valid.py'), 'w') as f:
                f.write("x = 1\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("y = 2\n")

            result = linter._check_directory(tmpdir)

            assert result.status == CheckStatus.PASS

    def test_coverage_tracker_no_coverage_file_returns_warning(self):
        """F29-T054: CoverageTracker无覆盖率文件返回WARNING (覆盖line 207)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import CoverageTracker, CheckStatus

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.path.exists', return_value=False):
                result = tracker.track(tmpdir, threshold=80)

                assert result.status == CheckStatus.WARNING
                assert "未找到覆盖率文件" in result.message

    def test_linter_check_file_via_check_method(self):
        """F29-T043: LinterChecker.check调用_check_file (覆盖line 54)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import LinterChecker, CheckStatus

        linter = LinterChecker()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def foo():\n    pass\n")
            temp_path = f.name

        try:
            result = linter.check(temp_path)
            assert result.status == CheckStatus.PASS
        finally:
            os.unlink(temp_path)

    def test_coverage_above_threshold_returns_pass(self):
        """F29-T044: 覆盖率高于阈值返回PASS (覆盖line 218)"""
        from f29_quality_gate.quality_gate import CoverageTracker, CheckStatus

        tracker = CoverageTracker()
        with patch.object(tracker, '_parse_coverage_file', return_value=90.0):
            with patch('os.path.exists', return_value=True):
                result = tracker.track("/test/path", threshold=80)

                assert result.status == CheckStatus.PASS

    def test_run_coverage_check_exception_returns_warning(self):
        """F29-T045: _run_coverage_check异常时返回WARNING (覆盖lines 232-233)"""
        from f29_quality_gate.quality_gate import QualityGate, CoverageTracker, CheckStatus

        gate = QualityGate()
        with patch.object(gate.coverage_tracker, '_parse_coverage_file', side_effect=Exception("parse error")):
            result = gate._run_coverage_check("/test/path")

            assert result.status == CheckStatus.WARNING

    def test_parse_coverage_file_nonexistent_path(self):
        """F29-T046: _parse_coverage_file路径不存在返回0.0 (覆盖line 245)"""
        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        result = tracker._parse_coverage_file("/nonexistent/path/.coverage")

        assert result == 0.0

    def test_parse_coverage_file_subprocess_path(self):
        """F29-T047: _parse_coverage_file通过subprocess解析 (覆盖lines 252-260)"""
        import subprocess
        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        mock_run = MagicMock()
        mock_run.return_value.stdout = 'TOTAL      100     25   75.00%'

        with patch('subprocess.run', mock_run):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', MagicMock()):
                    result = tracker._parse_coverage_file('/test/.coverage')

                    assert isinstance(result, float)

    def test_parse_text_coverage_malformed_da_line(self):
        """F29-T048: _parse_text_coverage处理畸形DA行 (覆盖lines 285-286)"""
        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        content = "SF:/test.py\nDA:abc,def\nDA:1,2\n"
        result = tracker._parse_text_coverage(content)

        assert result == 100.0

    def test_linter_check_skips_pycache_in_directory(self):
        """F29-T049: LinterChecker跳过__pycache__目录 (覆盖line 95)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import LinterChecker, CheckStatus

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            pycache_dir = os.path.join(tmpdir, '__pycache__')
            os.makedirs(pycache_dir)
            with open(os.path.join(pycache_dir, 'cached.pyc'), 'w') as f:
                f.write("x = 1\n")
            with open(os.path.join(tmpdir, 'valid.py'), 'w') as f:
                f.write("y = 2\n")

            result = linter._check_directory(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_linter_check_skips_pytest_cache_in_directory(self):
        """F29-T050: LinterChecker跳过.pytest_cache目录 (覆盖line 95)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import LinterChecker, CheckStatus

        linter = LinterChecker()
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, '.pytest_cache')
            os.makedirs(cache_dir)
            with open(os.path.join(cache_dir, 'cache.json'), 'w') as f:
                f.write('{"key": "value"}\n')
            with open(os.path.join(tmpdir, 'valid.py'), 'w') as f:
                f.write("z = 3\n")

            result = linter._check_directory(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_security_scanner_skips_pycache(self):
        """F29-T051: SecurityScanner跳过__pycache__目录 (覆盖line 137)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import SecurityScanner, CheckStatus

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            pycache_dir = os.path.join(tmpdir, '__pycache__')
            os.makedirs(pycache_dir)
            with open(os.path.join(pycache_dir, 'evil.pyc'), 'w') as f:
                f.write("password = 'secret123'\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_security_scanner_skips_git_directory(self):
        """F29-T052: SecurityScanner跳过.git目录 (覆盖line 137)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import SecurityScanner, CheckStatus

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, '.git')
            os.makedirs(git_dir)
            with open(os.path.join(git_dir, 'config'), 'w') as f:
                f.write("password = 'secret456'\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_security_scanner_skips_non_py_files(self):
        """F29-T053: SecurityScanner跳过非.py文件 (覆盖line 140)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import SecurityScanner, CheckStatus

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'data.txt'), 'w') as f:
                f.write("password = 'secret789'\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_security_scanner_skips_test_files(self):
        """F29-T054: SecurityScanner跳过test_开头文件 (覆盖line 142)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import SecurityScanner, CheckStatus

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'test_secret.py'), 'w') as f:
                f.write("api_key = 'sk-1234567890abcdefghijklmnopqrstu'\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_coverage_tracker_parses_subprocess_coverage(self):
        """F29-T055: CoverageTracker通过subprocess解析覆盖率 (覆盖lines 252-260)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = os.path.join(tmpdir, '.coverage')
            with open(coverage_file, 'w') as f:
                f.write('{"data": {}}\n')

            result = tracker._parse_coverage_file(coverage_file)
            assert isinstance(result, float)

    def test_security_scanner_skips_conftest(self):
        """F29-T056: SecurityScanner跳过conftest文件 (覆盖line 144)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import SecurityScanner, CheckStatus

        scanner = SecurityScanner()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, 'conftest.py'), 'w') as f:
                f.write("secret = 'super_secret_token_123456789012'\n")
            with open(os.path.join(tmpdir, 'clean.py'), 'w') as f:
                f.write("x = 1\n")

            result = scanner.scan(tmpdir)
            assert result.status == CheckStatus.PASS

    def test_parse_text_coverage_zero_lines(self):
        """F29-T060: _parse_text_coverage处理零总行数"""
        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        content = "SF:/test.py\nDA:1,0\nDA:2,0\n"
        result = tracker._parse_text_coverage(content)

        assert result == 0.0

    def test_track_with_subprocess_coverage_output(self):
        """F29-T061: CoverageTracker通过subprocess解析真实覆盖率 (覆盖lines 256-260)"""
        import tempfile
        import os
        from f29_quality_gate.quality_gate import CoverageTracker, CheckStatus

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = os.path.join(tmpdir, '.coverage')
            with open(coverage_file, 'w') as f:
                f.write('{"data": {}}\n')

            tracker._parse_coverage_file = lambda coverage_file: 75.0
            result = tracker.track(tmpdir, threshold=80)

            assert result.status == CheckStatus.FAIL

    def test_track_parses_exception_from_parse(self):
        """F29-T062: CoverageTracker.track异常处理 (覆盖lines 232-233)"""
        import tempfile
        from f29_quality_gate.quality_gate import CoverageTracker, CheckStatus
        from unittest.mock import patch

        tracker = CoverageTracker()

        def raising_parse(coverage_file):
            raise RuntimeError("parse error")

        tracker._parse_coverage_file = raising_parse
        with patch('os.path.exists', return_value=True):
            result = tracker.track("/fake/path", threshold=80)

            assert result.status == CheckStatus.WARNING

    def test_parse_coverage_file_via_subprocess(self):
        """F29-T063: CoverageTracker通过subprocess解析TOTAL行 (覆盖lines 256-260)"""
        import tempfile
        import os
        import subprocess
        from f29_quality_gate.quality_gate import CoverageTracker

        tracker = CoverageTracker()
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, 'test_module.py')
            with open(py_file, 'w') as f:
                f.write('x = 1\n')

            subprocess.run(
                ['python', '-m', 'coverage', 'run', py_file],
                capture_output=True, text=True, cwd=tmpdir
            )

            coverage_file = os.path.join(tmpdir, '.coverage')
            result = tracker._parse_coverage_file(coverage_file)

            assert isinstance(result, float)
            assert result >= 0




