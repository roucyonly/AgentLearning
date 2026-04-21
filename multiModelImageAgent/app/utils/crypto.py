from cryptography.fernet import Fernet
import base64
import hashlib


def get_encryption_key(secret: str) -> bytes:
    """生成加密密钥"""
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())


def encrypt_api_key(api_key: str, secret: str) -> str:
    """加密 API Key"""
    key = get_encryption_key(secret)
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted: str, secret: str) -> str:
    """解密 API Key"""
    key = get_encryption_key(secret)
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()


def hash_api_key(api_key: str) -> str:
    """哈希 API Key 用于验证"""
    return hashlib.sha256(api_key.encode()).hexdigest()
