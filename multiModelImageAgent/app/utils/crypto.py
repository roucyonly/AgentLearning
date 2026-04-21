from cryptography.fernet import Fernet
import base64
import hashlib
import time


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


def generate_kling_token(access_key: str, secret_key: str) -> str:
    """生成 Kling API 的 JWT token"""
    import jwt

    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": access_key,
        "exp": int(time.time()) + 1800,  # 30 minutes
        "nbf": int(time.time()) - 5  # 5 seconds ago
    }
    token = jwt.encode(payload, secret_key, headers=headers)
    return token
