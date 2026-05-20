"""
F06: Tier1数值核实引擎 - Tier1Verifier实现
"""
import asyncio
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class VerificationStatus(Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    TIMEOUT = "TIMEOUT"


@dataclass
class VerificationResult:
    is_verified: bool
    discrepancy: float = 0.0
    reason: str = ""
    status: VerificationStatus = VerificationStatus.PENDING
    source: Optional[str] = None
    external_value: Optional[Any] = None


class Tier1Verifier:
    """Tier1数值核实引擎 - 外部API核实"""

    VALUE_RANGES = {
        "population": {"min": 0, "max": 15000000000},
        "gdp": {"min": 0, "max": 300000000000000},
        "price": {"min": 0, "max": 1000000000000},
    }

    ANOMALY_THRESHOLDS = {
        "population": 10000000000,
        "gdp": 50000000000000,
    }

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self._api_endpoints = {
            "gdp": "https://api.stats.gov.cn/gdp",
            "population": "https://api.stats.gov.cn/population",
        }

    async def verify(
        self,
        data_type: str,
        value: Any,
        year: Optional[int] = None,
        region: Optional[str] = None,
        **context
    ) -> VerificationResult:
        """核实数值数据"""
        if not isinstance(value, (int, float)):
            return VerificationResult(
                is_verified=False,
                reason="INVALID_TYPE",
                status=VerificationStatus.FAILED
            )

        if value < 0:
            return VerificationResult(
                is_verified=False,
                reason="INVALID_RANGE",
                status=VerificationStatus.FAILED
            )

        range_check = self._check_value_range(data_type, value)
        if range_check:
            return range_check

        anomaly_check = self._check_anomaly(data_type, value)
        if anomaly_check:
            return anomaly_check

        try:
            external_data = await self._call_external_api(
                data_type=data_type,
                value=value,
                year=year,
                region=region,
                **context
            )

            if external_data is None:
                return VerificationResult(
                    is_verified=False,
                    reason="EXTERNAL_API_UNAVAILABLE",
                    status=VerificationStatus.FAILED
                )

            discrepancy = self._calculate_discrepancy(value, external_data.get("value", value))
            is_verified = discrepancy < 0.05

            return VerificationResult(
                is_verified=is_verified,
                discrepancy=discrepancy,
                reason="VERIFIED" if is_verified else "DISCREPANCY_TOO_LARGE",
                status=VerificationStatus.VERIFIED if is_verified else VerificationStatus.FAILED,
                source=external_data.get("source", "unknown"),
                external_value=external_data.get("value")
            )

        except asyncio.TimeoutError:
            return VerificationResult(
                is_verified=False,
                reason="TIMEOUT",
                status=VerificationStatus.TIMEOUT
            )
        except Exception as e:
            return VerificationResult(
                is_verified=False,
                reason=f"ERROR: {str(e)}",
                status=VerificationStatus.FAILED
            )

    def _check_value_range(self, data_type: str, value: Any) -> Optional[VerificationResult]:
        """检查数值是否在合理范围内"""
        if data_type not in self.VALUE_RANGES:
            return None

        range_info = self.VALUE_RANGES[data_type]
        if value < range_info["min"] or value > range_info["max"]:
            return VerificationResult(
                is_verified=False,
                reason="INVALID_RANGE",
                status=VerificationStatus.FAILED
            )
        return None

    def _check_anomaly(self, data_type: str, value: Any) -> Optional[VerificationResult]:
        """检测异常值（捏造数值）"""
        if data_type not in self.ANOMALY_THRESHOLDS:
            return None

        threshold = self.ANOMALY_THRESHOLDS[data_type]
        if isinstance(value, (int, float)) and value > threshold:
            return VerificationResult(
                is_verified=False,
                reason="ANOMALY_DETECTED",
                status=VerificationStatus.FAILED
            )
        return None

    async def _call_external_api(
        self,
        data_type: str,
        value: Any,
        year: Optional[int] = None,
        region: Optional[str] = None,
        **context
    ) -> Dict[str, Any]:
        """调用外部API核实数据"""
        api_result = await asyncio.wait_for(
            self._fetch_external_data(data_type, year, region),
            timeout=self.timeout_seconds
        )
        return api_result

    async def _fetch_external_data(
        self,
        data_type: str,
        year: Optional[int],
        region: Optional[str]
    ) -> Dict[str, Any]:
        """获取外部数据 - Mock实现"""
        mock_data = {
            "gdp": {
                "中国": {2023: 12900000000000},
                "美国": {2023: 25460000000000},
            },
            "population": {
                "中国": {2023: 141200000000},
                "美国": {2023: 334000000000},
            }
        }

        if data_type in mock_data and region in mock_data[data_type]:
            year_data = year or 2023
            if year_data in mock_data[data_type][region]:
                return {
                    "verified": True,
                    "value": mock_data[data_type][region][year_data],
                    "source": "国家统计局",
                    "year": year_data,
                    "region": region
                }

        return {"verified": False, "source": "unknown"}

    def _calculate_discrepancy(self, value1: float, value2: float) -> float:
        """计算两个值之间的偏差"""
        if value2 == 0:
            return 1.0 if value1 != 0 else 0.0
        return abs(value1 - value2) / value2


class ExternalDataVerifier:
    """外部数据核实引擎"""

    VERIFICATION_RULES = {
        "gdp": {"source": "国家统计局", "api_endpoint": "https://api.stats.gov.cn/gdp"},
        "population": {"source": "国家统计局", "api_endpoint": "https://api.stats.gov.cn/population"},
        "regulation": {"source": "国家法规数据库", "api_endpoint": "https://law.gov.cn/api"},
        "market_size": {"source": "行业报告", "requires_whitelist": True}
    }

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self._verifier = Tier1Verifier(timeout_seconds=timeout_seconds)

    async def verify(
        self,
        data_type: str,
        value: Any,
        year: Optional[int] = None,
        region: Optional[str] = None,
        **context
    ) -> VerificationResult:
        """调用外部API核实数据"""
        return await self._verifier.verify(
            data_type=data_type,
            value=value,
            year=year,
            region=region,
            **context
        )

    async def _call_national_stats_api(
        self,
        data_type: str,
        year: Optional[int],
        region: Optional[str]
    ) -> Dict[str, Any]:
        """调用国家统计局API"""
        return await self._verifier._fetch_external_data(data_type, year, region)
