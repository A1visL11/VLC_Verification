#!/usr/bin/env python3
# decryption.py - 接收 master_key 和 ciphertext，並完成 fid, mid, password 解密

import sys
from Crypto.Cipher import AES

def bitstring_to_bytes(s: str) -> bytes:
    """將 '0'/'1' bitstring 轉為 bytes。"""
    return int(s, 2).to_bytes(len(s) // 8, byteorder='big')

def split_masks(master_key: bytes):
    """從 master_key 切分出 fid_mask, mid_mask, password_mask"""
    fid_mask = master_key[0:4]
    mid_mask = master_key[4:8]
    password_mask = master_key[8:16]
    return fid_mask, mid_mask, password_mask

def xor_bytes(data: bytes, mask: bytes) -> bytes:
    """對應位元做 XOR。"""
    return bytes(d ^ m for d, m in zip(data, mask))

def decrypt_fid(enc: bytes, fid_mask: bytes) -> int:
    """XOR 後轉回 int"""
    raw = xor_bytes(enc, fid_mask)
    return int.from_bytes(raw, byteorder='big')

def decrypt_mid(enc: bytes, mid_mask: bytes) -> int:
    """XOR 後轉回 int"""
    raw = xor_bytes(enc, mid_mask)
    return int.from_bytes(raw, byteorder='big')

def decrypt_password(enc: bytes, password_mask: bytes) -> str:
    """XOR 還原後去除 padding，並解碼為字串"""
    raw = xor_bytes(enc, password_mask)
    raw = raw.rstrip(b'\x00')
    return raw.decode('utf-8')

def aes_decrypt(cipher_bytes: bytes, key: bytes) -> bytes:
    """使用 AES-128-ECB 解密"""
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(cipher_bytes)


def decrypt_all(master_key_str: str, ciphertext_str: str) -> dict:
    """
    類似 encrypt_all 的接口。輸入 master_key 和 ciphertext bytes，
    Return 'fid', 'mid', 'password' 的 dictionary。
    """
    # 將 bitstring 轉為 bytes
    master_key = bitstring_to_bytes(master_key_str)
    ciphertext = bitstring_to_bytes(ciphertext_str)

    # 切分出各自的 mask
    fid_mask, mid_mask, password_mask = split_masks(master_key)

    # AES-128-ECB 解密取得原始 block
    block = aes_decrypt(ciphertext, master_key)

    # 拆分三段
    fid_enc = block[0:4]
    mid_enc = block[4:8]
    pwd_enc = block[8:16]

    # 各自 XOR 還原並轉型
    fid = decrypt_fid(fid_enc, fid_mask)
    mid = decrypt_mid(mid_enc, mid_mask)
    password = decrypt_password(pwd_enc, password_mask)

    return {"fid": fid, "mid": mid, "password": password}

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <MASTER_KEY_bitstring> <CIPHERTEXT_bitstring>")
        sys.exit(1)

    mk_bits = sys.argv[1]
    ct_bits = sys.argv[2]

    res = decrypt_all(mk_bits, ct_bits)

    print(f"fid = {res['fid']}")
    print(f"mid = {res['mid']}")
    print(f"password = {res['password']}")

if __name__ == "__main__":
    main()