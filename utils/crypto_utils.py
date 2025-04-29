import os
import hmac
import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# 生成对称密钥（AES-128）
def generate_key():
    return get_random_bytes(16)

# 伪随机函数 PRF: HMAC-SHA256(key, data)
def prf(key: bytes, data: str) -> bytes:
    return hmac.new(key, data.encode(), hashlib.sha256).digest()

# 对称加密 (AES-GCM)
def encrypt(key: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce + tag + ciphertext

# 对称解密 (AES-GCM)
def decrypt(key: bytes, blob: bytes) -> bytes:
    nonce = blob[:16]
    tag   = blob[16:32]
    ct    = blob[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)
