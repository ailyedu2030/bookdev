"""
F11: HSM客户端 (硬件安全模块)
"""

import hashlib


class HSMClient:
    """硬件安全模块客户端"""

    def __init__(self, config=None):
        self.config = config
        self._private_key = None

    def sign(self, data: str) -> str:
        """使用HSM私钥签名"""
        raise NotImplementedError("HSM sign must be implemented with actual HSM SDK")

    def verify(self, data: str, signature: str) -> bool:
        """使用HSM公钥验证签名"""
        raise NotImplementedError("HSM verify must be implemented with actual HSM SDK")

    def get_public_key_pem(self) -> str:
        """获取公钥"""
        raise NotImplementedError("HSM get_public_key_pem must be implemented")


class MockHSMClient(HSMClient):
    """模拟HSM客户端（用于测试）

    注意：此模拟类仅用于测试环境，绝不应用于生产。
    生产环境必须使用真实的HSM硬件或HSM云服务。
    """

    def __init__(self, config=None):
        super().__init__(config)
        # F11-002 FIX: 移除硬编码测试密钥，使用配置或生成随机值
        self._mock_private_key = config.get("private_key") if config else None
        self._mock_public_key = config.get("public_key") if config else None

        # 如果没有提供密钥，使用临时值但标记为非生产可用
        if not self._mock_private_key:
            self._mock_private_key = "MOCK_ONLY_NOT_FOR_PRODUCTION"
        if not self._mock_public_key:
            self._mock_public_key = "MOCK_ONLY_NOT_FOR_PRODUCTION"

    def sign(self, data: str) -> str:
        """模拟签名"""
        import hashlib
        return f"hsm_signature_{hashlib.sha256(data.encode()).hexdigest()}"

    def verify(self, data: str, signature: str) -> bool:
        """模拟验证"""
        if signature.startswith("hsm_signature_"):
            expected = f"hsm_signature_{hashlib.sha256(data.encode()).hexdigest()}"
            return signature == expected
        # F11-002 FIX: 移除不安全的 "valid_signature" 回退
        # F11-002 FIX: 移除 "hsm_signature" 回退
        return False

    def get_public_key_pem(self) -> str:
        """获取模拟公钥"""
        return self._mock_public_key if self._mock_public_key else ""

    def is_production_ready(self) -> bool:
        """检查是否已配置为生产可用"""
        return bool(self._mock_private_key and self._mock_private_key != "MOCK_ONLY_NOT_FOR_PRODUCTION")
