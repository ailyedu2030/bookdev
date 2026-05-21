"""
F09: 素材安全管理 - 素材安全管理器
"""
import asyncio
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from f09_material_security.source_registry import MaterialSourceRegistry, SourceInfo


class MaterialStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TrustLevel(Enum):
    WHITELIST = "WHITELIST"
    VERIFIED = "VERIFIED"
    UNKNOWN = "UNKNOWN"
    UNTRUSTED = "UNTRUSTED"


class ScanStatus(Enum):
    CLEAN = "CLEAN"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


@dataclass
class Material:
    material_id: str = ""
    content: str = ""
    source: Optional[SourceInfo] = None
    trust_score: float = 0.0
    security_status: str = "PENDING"


@dataclass
class SecurityScanResult:
    scan_status: ScanStatus
    sensitive_word_count: int = 0
    malicious_pattern_count: int = 0
    tampering_detected: bool = False
    details: List[str] = field(default_factory=list)


@dataclass
class RegistrationResult:
    status: str
    material_id: str = ""
    trust_score: float = 0.0
    reason: str = ""


class MaterialValidationError(Exception):
    """素材验证错误"""
    pass


class MaterialSecurityManager:
    """素材安全管理器"""

    TRUST_SCORE_THRESHOLDS = {
        "WHITELIST": 1.0,
        "VERIFIED": 0.8,
        "UNKNOWN": 0.5,
        "UNTRUSTED": 0.0
    }

    BLOCK_THRESHOLDS = {
        "min_trust_score": 0.7,
        "min_scan_score": 0.9
    }

    # F09-001 FIX: 使用正则模式而不是简单字符串，并添加编码变体检测
    SENSITIVE_PATTERNS = [
        r"恶意", r"可疑链接", r"钓鱼", r"诈骗", r"病毒", r"木马",
        r"黑客", r"攻击", r"漏洞", r"后门", r"间谍", r"监控",
        r"窃取", r"非法", r"赌博", r"色情", r"暴力",
    ]

    # URL检测正则
    URL_PATTERN = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
        re.IGNORECASE
    )

    # 可能的编码绕过变体（预编译）
    ENCODING_VARIANTS = {
        # 零宽度字符
        '\u200b': '',  # Zero Width Space
        '\u200c': '',  # Zero Width Non-Joiner
        '\u200d': '',  # Zero Width Joiner
        '\ufeff': '',  # BOM
    }

    RETRIEVAL_WEIGHTS = {
        "WHITELIST": 1.0,
        "VERIFIED": 0.8,
        "UNKNOWN": 0.3,
        "UNTRUSTED": 0.0
    }

    def __init__(self, source_registry: Optional[MaterialSourceRegistry] = None):
        self.source_registry = source_registry or MaterialSourceRegistry()
        self._registered_materials: Dict[str, Material] = {}
        self._material_weights: Dict[str, float] = {}

    def _normalize_content(self, content: str) -> str:
        """F09-001 FIX: 规范化内容以防止编码绕过
        
        1. Unicode NFKC规范化
        2. 移除零宽度字符
        3. 全角转半角
        """
        # 移除零宽度字符
        for zwc, replacement in self.ENCODING_VARIANTS.items():
            content = content.replace(zwc, replacement)
        
        # Unicode NFKC规范化
        content = unicodedata.normalize('NFKC', content)
        
        # 全角转半角
        content = self._fullwidth_to_halfwidth(content)
        
        return content

    def _fullwidth_to_halfwidth(self, text: str) -> str:
        """全角转半角"""
        result = []
        for char in text:
            # 全角空格 (U+3000) -> 半角空格
            if char == '\u3000':
                result.append(' ')
            # 全角数字、字母、符号 -> 半角
            elif '\uff01' <= char <= '\uff5e':
                result.append(chr(ord(char) - 0xfee0))
            else:
                result.append(char)
        return ''.join(result)

    async def register_material(self, material: Material) -> RegistrationResult:
        """注册素材（需审核）"""
        if material.source is None:
            raise MaterialValidationError("Material must have a source")

        if material.material_id:
            existing = self._registered_materials.get(material.material_id)
            if existing:
                return RegistrationResult(
                    status="REJECTED",
                    material_id=material.material_id,
                    reason="Material already registered"
                )

        trust_score = self.calculate_trust_score(material)

        scan_result = await self.security_scan(material.content)

        if scan_result.scan_status == ScanStatus.BLOCKED:
            return RegistrationResult(
                status="REJECTED",
                material_id=material.material_id,
                trust_score=trust_score,
                reason="Content blocked by security scan"
            )

        if trust_score < self.BLOCK_THRESHOLDS["min_trust_score"]:
            return RegistrationResult(
                status="REJECTED",
                material_id=material.material_id,
                trust_score=trust_score,
                reason=f"Trust score {trust_score} below threshold"
            )

        if material.source.trust_level == "WHITELIST":
            status = "APPROVED"
        elif material.source.trust_level == "VERIFIED":
            status = "APPROVED" if trust_score >= 0.8 else "PENDING"
        else:
            status = "PENDING"

        material.trust_score = trust_score
        material.security_status = status

        if not material.material_id:
            material.material_id = hashlib.sha256(
                material.content.encode()
            ).hexdigest()[:16]

        self._registered_materials[material.material_id] = material
        self._material_weights[material.material_id] = self.get_retrieval_weight(material.material_id)

        return RegistrationResult(
            status=status,
            material_id=material.material_id,
            trust_score=trust_score
        )

    async def security_scan(self, content: str) -> SecurityScanResult:
        """安全扫描
        
        F09-001 FIX: 使用正则和Unicode规范化防止编码绕过
        """
        sensitive_count = 0
        malicious_count = 0
        details = []

        # 规范化内容
        normalized = self._normalize_content(content.lower())

        # 使用正则模式检测
        for pattern in self.SENSITIVE_PATTERNS:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = regex.findall(normalized)
                if matches:
                    sensitive_count += len(matches)
                    details.append(f"Found sensitive pattern: {pattern}")
            except re.error:
                # 跳过无效的正则
                continue

        # F09-001 FIX: 使用正则检测URL，而不是简单字符串匹配
        url_matches = self.URL_PATTERN.findall(content)
        if url_matches:
            malicious_count += 1
            details.append(f"Found {len(url_matches)} URL(s) in content")

        if sensitive_count > 0 or malicious_count > 0:
            scan_status = ScanStatus.WARNING if malicious_count == 0 else ScanStatus.BLOCKED
        else:
            scan_status = ScanStatus.CLEAN

        return SecurityScanResult(
            scan_status=scan_status,
            sensitive_word_count=sensitive_count,
            malicious_pattern_count=malicious_count,
            details=details
        )

    def calculate_trust_score(self, material: Material) -> float:
        """计算可信度评分"""
        if material.source is None:
            return 0.0

        base_score = self.TRUST_SCORE_THRESHOLDS.get(
            material.source.trust_level, 0.0
        )

        return base_score

    def get_retrieval_weight(self, material_id: str) -> float:
        """获取检索权重"""
        if material_id in self._material_weights:
            return self._material_weights[material_id]

        material = self._registered_materials.get(material_id)
        if material and material.source:
            return self.RETRIEVAL_WEIGHTS.get(
                material.source.trust_level, 0.3
            )

        return 0.3

    def detect_tampering(
        self,
        original_content: str,
        current_content: str
    ) -> Dict[str, Any]:
        """检测篡改"""
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()

        return {
            "tampering_detected": original_hash != current_hash,
            "original_hash": original_hash,
            "current_hash": current_hash
        }
