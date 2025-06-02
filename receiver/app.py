import pymysql
from decryption import decrypt_all
import subprocess
import time
from db_config import get_conn
import hashlib
from door_lock import DoorLock
def sha256(text): return hashlib.sha256(text.encode()).hexdigest()

bonded_fid = 1 # 預設使用者是1

def insert_entry_log(member_id):
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO EntryLogs (member_id) VALUES (%s)", (member_id,))
        conn.commit()
        conn.close()
        print("成功寫入 EntryLogs。")
    except pymysql.MySQLError as err:
        print("MySQL 錯誤：", err)

# 新增錯誤紀錄寫入函式
def insert_err_log(fid: int, error_message: str):
    """
    將錯誤訊息寫入 ErrorLogs 資料表中。
    parameter:
      fid: 家庭 ID
      error_message: 要寫入的錯誤訊息
    """
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ErrorLogs (family_id, error_message) VALUES (%s, %s)",
                (fid, error_message)
            )
        conn.commit()
        conn.close()
        print("成功寫入 ErrorLogs。")
    except pymysql.MySQLError as err:
        print("MySQL 錯誤：", err)

def verify(fid: int, mid: int, password: str):
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            # verify fid 和 password
            password = sha256(password)
            cursor.execute("SELECT * FROM Families WHERE family_id = %s AND password_hash = %s", (fid, password))
            family = cursor.fetchone()
            if not family:
                print(f"❌ 找不到 family_id={fid} 且密碼符合的家庭。")
                conn.close()
                if bonded_fid != None:
                    insert_err_log(bonded_fid, "密碼錯誤"if bonded_fid==fid else "非此家庭成員")
                return False

            # verify mid 和 fid
            cursor.execute("SELECT * FROM Members WHERE member_id = %s AND family_id = %s", (mid, fid))
            member = cursor.fetchone()
            if not member:
                print(f"❌ 找不到 member_id={mid} 與 family_id={fid} 的成員。")
                if bonded_fid!=None:
                    insert_err_log(bonded_fid, "成員不存在")
                conn.close()
                return False
        return True

    except Exception as e:
        print("驗證過程發生錯誤：", e)
        return False

def get_bitstring():
    # 呼叫 C 程式，capture_output=True 會將 stdout/stderr 收到 CompletedProcess 物件裡
    result = subprocess.run(
        ["sudo", "/home/pi/RECEIVER/bits_receiver"], 
        capture_output=True, text=True, check=True
    )
    # 將 stdout 去除前後空白（如換行），就得到純 bit string
    bitstring = result.stdout.strip()

    # 驗證長度是否正確
    if len(bitstring) != 128:
        raise ValueError(f"預期 128 bits，卻收到 {len(bitstring)} bits：{bitstring}")

    return bitstring

if __name__ == "__main__":
    lock= DoorLock()
    while True:
        master_key = get_bitstring()
        # master_key= "10011101010010001001111101100101001101011111011001000000011010101000100000001001100110111001000101010000000111010111010011001110"
        time.sleep(0.1)  # 等待 C 程式啟動穩定
        print("master key received:", master_key)

        ciphertext = get_bitstring()
        # ciphertext= "10010111000111111000010011000001100001010101100001111010101000110100001101010100110001000111111011010110010110100100100111100010"
        print("ciphertext received:", ciphertext)
        try:
            result = decrypt_all(master_key, ciphertext)
            print(result)
            fid = result['fid']
            mid = result['mid']
            password = result['password']
            if verify(fid, mid, password) == True:
                insert_entry_log(mid)
                lock.unlock(5)
                print(f"成員 {mid} 驗證成功，家庭 {fid} 進入。")
            else:
                print(f"成員 {mid} 驗證失敗，家庭 {fid} 進入被拒絕。")

        except Exception as e:
            if bonded_fid!=None:
                insert_err_log(bonded_fid, "LiFi傳輸出錯")
            print("解密失敗:", e)
    lock.cleanup()

