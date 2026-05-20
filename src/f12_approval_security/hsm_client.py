"""
F12: HSM客户端 (硬件安全模块)
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
    """模拟HSM客户端（用于测试）"""

    def __init__(self, config=None):
        super().__init__(config)
        self._mock_private_key = "mock_private_key_for_testing"
        self._mock_public_key = "mock_public_key_for_testing"

    def sign(self, data: str) -> str:
        """模拟签名"""
        return f"hsm_signature_{hashlib.sha256(data.encode()).hexdigest()}"

    def verify(self, data: str, signature: str) -> bool:
        """模拟验证"""
        if signature.startswith("hsm_signature_"):
            expected = f"hsm_signature_{hashlib.sha256(data.encode()).hexdigest()}"
            return signature == expected
        if signature == "valid_signature":
            return True
        if signature == "software_signature":
            return False
        return False

    def get_public_key_pem(self) -> str:
        """获取模拟公钥"""
        return self._mock_public_key
