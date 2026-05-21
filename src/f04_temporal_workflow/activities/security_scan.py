"""
安全扫描活动 - 对教材内容进行安全合规检查。

检查维度:
- 敏感内容检测 (Sensitive Content): 政治/宗教/色情/暴力
- 数据隐私 (Data Privacy): 个人信息泄露风险
- 版权合规 (Copyright): 引用内容的版权检查
- 事实核查 (Fact Check): 基本事实准确性
- 多样性包容性 (DEI): 多样性和包容性审查

幂等: 相同 content_hash 返回相同结果
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from ..workflows.mock_client import TemporalActivity

logger = logging.getLogger(__name__)


# 敏感词库 (模拟)
_SENSITIVE_PATTERNS = {
    "political": ["敏感政治词汇1", "敏感政治词汇2"],
    "religious": ["宗教敏感词1", "宗教敏感词2"],
    "violent": ["暴力内容关键词"],
    "adult": ["不适宜内容关键词"],
}

# 合规检查器
_COMPLIANCE_RULES = [
    {"id": "C001", "name": "不得包含违法违规内容", "severity": "CRITICAL"},
    {"id": "C002", "name": "不得泄露个人信息", "severity": "HIGH"},
    {"id": "C003", "name": "引用内容需注明来源", "severity": "MEDIUM"},
    {"id": "C004", "name": "图表需标注数据来源", "severity": "MEDIUM"},
    {"id": "C005", "name": "公式和定理标注原始出处", "severity": "LOW"},
    {"id": "C006", "name": "案例数据须脱敏处理", "severity": "HIGH"},
    {"id": "C007", "name": "确保内容多样性和包容性", "severity": "MEDIUM"},
]


@TemporalActivity.defn(
    name="ScanChapter",
    idempotent=True,
)
async def scan_chapter(
    chapter_id: str,
    content: str,
    scan_level: str = "STANDARD",
) -> Dict[str, Any]:
    """扫描单个章节的安全合规性 (幂等)"""
    logger.info(f"[SecurityScan] Scanning chapter '{chapter_id}' (level={scan_level})")

    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    results = {
        "sensitive_content": _scan_sensitive_content(content),
        "privacy_check": _scan_privacy(content),
        "copyright_check": _scan_copyright(content),
        "compliance_check": _scan_compliance(content, scan_level),
    }

    # 汇总
    total_checks = sum(len(v.get("findings", v if isinstance(v, list) else [])) for v in results.values() if isinstance(v, (dict, list)))
    violations = [
        finding
        for category in results.values()
        for finding in (category.get("findings", category if isinstance(category, list) else []))
        if isinstance(finding, dict) and finding.get("severity") in ("CRITICAL", "HIGH")
    ]

    overall_status = "PASS" if not violations else "FAIL" if any(
        v.get("severity") == "CRITICAL" for v in violations
    ) else "WARNING"

    result = {
        "chapter_id": chapter_id,
        "content_hash": content_hash,
        "scan_level": scan_level,
        "status": overall_status,
        "results": results,
        "violations": violations,
        "violation_count": len(violations),
        "total_checks": total_checks,
        "recommendation": _get_scan_recommendation(overall_status, violations),
    }

    logger.info(
        f"[SecurityScan] Chapter '{chapter_id}' scan: {overall_status} ({len(violations)} violations)"
    )
    return result


@TemporalActivity.defn(
    name="BatchScanChapters",
    idempotent=True,
)
async def batch_scan_chapters(
    chapters: List[Dict[str, Any]],
    scan_level: str = "STANDARD",
) -> Dict[str, Any]:
    """
    批量安全扫描 (幂等)
    TEMP-014: 添加了幂等性保护
    """
    logger.info(f"[SecurityScan] Batch scanning {len(chapters)} chapters")

    # TEMP-014: 生成批次唯一键
    chapter_ids = [ch.get("chapter_id", "unknown") for ch in chapters]
    batch_key = hashlib.sha256(f"batch-scan:{','.join(chapter_ids)}:{scan_level}".encode()).hexdigest()[:16]

    scan_results = []
    all_violations = []

    for ch in chapters:
        result = await scan_chapter(
            chapter_id=ch.get("chapter_id", "unknown"),
            content=ch.get("content", ""),
            scan_level=scan_level,
        )
        # TEMP-014: 标记批次
        result["batch_id"] = batch_key
        scan_results.append(result)
        all_violations.extend(result.get("violations", []))

    overall = "PASS"
    if any(r.get("status") == "FAIL" for r in scan_results):
        overall = "FAIL"
    elif any(r.get("status") == "WARNING" for r in scan_results):
        overall = "WARNING"

    logger.info(
        f"[SecurityScan] Batch complete: {overall} ({len(all_violations)} total violations), batch_key={batch_key[:16]}"
    )

    return {
        "status": overall,
        "scan_level": scan_level,
        "total_chapters": len(chapters),
        "passed": sum(1 for r in scan_results if r.get("status") == "PASS"),
        "warnings": sum(1 for r in scan_results if r.get("status") == "WARNING"),
        "failed": sum(1 for r in scan_results if r.get("status") == "FAIL"),
        "violations": all_violations,
        "chapter_results": scan_results,
        "batch_id": batch_key,  # TEMP-014: 用于追踪
    }


def _scan_sensitive_content(content: str) -> Dict[str, Any]:
    """敏感内容检测"""
    findings = []
    content_lower = content.lower()

    for category, patterns in _SENSITIVE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in content_lower:
                findings.append({
                    "category": category,
                    "pattern": pattern,
                    "severity": "HIGH" if category in ("political", "adult") else "MEDIUM",
                    "recommendation": f"请审核 '{pattern}' 相关内容是否适合教材使用",
                })

    return {
        "status": "PASS" if not findings else "WARNING",
        "findings": findings,
        "count": len(findings),
    }


def _scan_privacy(content: str) -> Dict[str, Any]:
    """隐私检查 - 检测潜在的个人信息泄露"""
    import re

    findings = []

    # 模拟检测模式
    patterns = {
        "email": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "检测到邮箱地址"),
        "phone_cn": (r"1[3-9]\d{9}", "检测到中国手机号"),
        "id_card": (r"\d{17}[\dXx]", "检测到身份证号格式"),
    }

    for name, (pattern, message) in patterns.items():
        if re.search(pattern, content):
            findings.append({
                "type": name,
                "message": message,
                "severity": "HIGH",
                "recommendation": f"请移除或脱敏{message.split('检测到')[1] if '检测到' in message else message}",
            })

    return {
        "status": "PASS" if not findings else "WARNING",
        "findings": findings,
        "count": len(findings),
    }


def _scan_copyright(content: str) -> Dict[str, Any]:
    """版权合规检查"""
    findings = []

    # 检查引用标注
    has_references = "参考文献" in content or "参考" in content or "引用" in content
    if len(content) > 500 and not has_references:
        findings.append({
            "type": "missing_references",
            "message": "较长内容未发现参考文献标注",
            "severity": "MEDIUM",
            "recommendation": "建议在章节末尾添加参考文献",
        })

    return {
        "status": "PASS" if not findings else "WARNING",
        "findings": findings,
        "count": len(findings),
    }


def _scan_compliance(content: str, scan_level: str) -> Dict[str, Any]:
    """合规检查"""
    findings = []

    for rule in _COMPLIANCE_RULES:
        # 模拟合规检查 - 在实际系统中会调用专门的检查服务
        if scan_level == "DEEP" or rule["severity"] in ("CRITICAL", "HIGH"):
            # 简单模拟：长内容可能有更多问题
            import random
            seed = int(hashlib.sha256((content[:100] + rule["id"]).encode()).hexdigest()[:8], 16)
            random.seed(seed)

            # 95% 概率通过
            if random.random() > 0.95:
                findings.append({
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "status": "VIOLATED",
                    "recommendation": f"规则 {rule['id']}: {rule['name']} 需要人工审核",
                })

            random.seed(None)

    return {
        "status": "PASS" if not findings else "WARNING",
        "findings": findings,
        "rules_checked": len(_COMPLIANCE_RULES),
        "violations": len(findings),
    }


def _get_scan_recommendation(status: str, violations: List[Dict]) -> str:
    if status == "PASS":
        return "SCAN_PASS - 安全扫描通过，内容可进入下一阶段"
    elif status == "WARNING":
        return "MANUAL_REVIEW_RECOMMENDED - 存在低风险项，建议人工审核后发布"
    else:
        critical_count = sum(1 for v in violations if v.get("severity") == "CRITICAL")
        return f"SCAN_FAILED - 发现 {critical_count} 个严重问题，必须修改后重新扫描"


class SecurityScan:
    """安全扫描活动集合"""

    @staticmethod
    async def scan(chapter_id: str, content: str, scan_level: str = "STANDARD") -> Dict[str, Any]:
        return await scan_chapter(chapter_id, content, scan_level)

    @staticmethod
    async def batch_scan(chapters: List[Dict[str, Any]], scan_level: str = "STANDARD") -> Dict[str, Any]:
        return await batch_scan_chapters(chapters, scan_level)
