from flask import Blueprint, request, jsonify
from encryption import encrypt_all, bytes_to_bitstring
import subprocess
import time
from db_config import get_conn
from datetime import datetime, timezone, timedelta

bp = Blueprint("transmit", __name__)

@bp.route("/", methods=["POST"])
def transmit():
    data = request.get_json()
    fid = int(data.get("fid"))
    mid = int(data.get("mid"))
    pwd = data.get("password")
    print("fid =", fid, "mid =", mid, "pwd =", pwd)
    start_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    try:
        master_key, ciphertext = encrypt_all(fid, mid, pwd)
        master_key_bits = bytes_to_bitstring(master_key)
        ciphertext_bits = bytes_to_bitstring(ciphertext)
        print("Random Key生成成功")
        try:
            cmd1 = [
                "sudo", "/home/pi/IoT/IOT_PROJECT/bit_transmitter", master_key_bits
            ]
            subprocess.run(cmd1, check=True)
            print("Master Key 傳送成功")
            time.sleep(1.25)
            cmd2 = [
                "sudo", "/home/pi/IoT/IOT_PROJECT/bit_transmitter", ciphertext_bits
            ]
            subprocess.run(cmd2, check=True)
            print("Encrypted String傳送成功")
            time.sleep(1)
            conn = get_conn()
            with conn.cursor() as cur:
                # 取得最新的 ErrorLogs 訊息
                cur.execute(
                    "SELECT * FROM ErrorLogs WHERE family_id = %s AND timestamp > %s ORDER BY timestamp DESC LIMIT 1",
                    (fid, start_time)
                )
                err_row = cur.fetchone()
            conn.close()
            if err_row is None:
                return {"message": "歡迎回家"}
            else:
                error_msg = err_row["error_message"] if err_row else "未知錯誤"
                print("Error:", err_row)
                print("start time:", start_time)
                return {"error": error_msg}
        except subprocess.CalledProcessError as e:
            return {"error": "傳送失敗：" + str(e)}
        
    except Exception as e:
        return {"error": "Random Key生成失敗：" + str(e)}
    