#!/usr/bin/env python3
# encryption.py — 產生隨機 master_key、分割為 masks，並完成 fid、mid、password 加密

import os
import sys
from Crypto.Cipher import AES

def generate_master_key() -> bytes:
    """Linux entropy pool 隨機生成 16 bytes 作為 master_key。"""
    return os.urandom(16)

def split_masks(master_key: bytes):
    """
    將 16 bytes master_key 切分為：
      - fid_mask (4 bytes)
      - mid_mask (4 bytes)
      - password_mask (8 bytes)
    """
    fid_mask      = master_key[0:4]
    mid_mask      = master_key[4:8]
    password_mask = master_key[8:16]
    return fid_mask, mid_mask, password_mask

def xor_bytes(data: bytes, mask: bytes) -> bytes:
    """對應位元做 XOR，回傳與 mask 同樣長度的 bytes。"""
    return bytes(d ^ m for d, m in zip(data, mask))

def encrypt_fid(fid: int, fid_mask: bytes) -> bytes:
    """將 fid 轉為 4 bytes 大端整數，並與 fid_mask XOR。"""
    raw = fid.to_bytes(4, byteorder='big')
    return xor_bytes(raw, fid_mask)

def encrypt_mid(mid: int, mid_mask: bytes) -> bytes:
    """將 mid 轉為 4 bytes 大端整數，並與 mid_mask XOR。"""
    raw = mid.to_bytes(4, byteorder='big')
    return xor_bytes(raw, mid_mask)

def encrypt_password(password: str, password_mask: bytes) -> bytes:
    """
    將 password UTF-8 編碼後截／補至 8 bytes，並與 password_mask XOR。
    """
    raw = password.encode('utf-8')
    if len(raw) > len(password_mask):
        raw = raw[:len(password_mask)]
    else:
        raw = raw.ljust(len(password_mask), b'\x00')
    return xor_bytes(raw, password_mask)

def merge_fields(fid_enc: bytes, mid_enc: bytes, pwd_enc: bytes) -> bytes:
    """將三段加密後的 bytes 串接，得到 16 bytes 的 block。"""
    return fid_enc + mid_enc + pwd_enc  # 總長度 4+4+8 = 16 bytes

def aes_encrypt(block: bytes, key: bytes) -> bytes:
    """使用 AES-128-ECB（key = master_key）加密 16 bytes block。"""
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(block)

def bytes_to_bitstring(data: bytes) -> str:
    """將 bytes 轉為長度 = len(data)*8 的 '0'/'1' bitstring。"""
    return ''.join(f'{b:08b}' for b in data)

def encrypt_all(fid: int, mid: int, password: str):
    """
    完整加密流程：
      1. generate_master_key
      2. split_masks
      3. 各欄位 XOR 加密
      4. merge_fields
      5. aes_encrypt
    回傳 (master_key, ciphertext_bytes)
    """
    master_key = generate_master_key()
    fid_mask, mid_mask, pwd_mask = split_masks(master_key)

    fid_enc = encrypt_fid(fid, fid_mask)
    mid_enc = encrypt_mid(mid, mid_mask)
    pwd_enc = encrypt_password(password, pwd_mask)

    block        = merge_fields(fid_enc, mid_enc, pwd_enc)
    cipher_bytes = aes_encrypt(block, master_key)

    return master_key, cipher_bytes

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <fid> <mid> <password>")
        sys.exit(1)

    fid      = int(sys.argv[1])
    mid      = int(sys.argv[2])
    password = sys.argv[3]

    master_key, cipher_bytes = encrypt_all(fid, mid, password)

    print("MASTER_KEY (128-bit):", bytes_to_bitstring(master_key))
    print("CIPHERTEXT  (128-bit):", bytes_to_bitstring(cipher_bytes))

if __name__ == "__main__":
    main()