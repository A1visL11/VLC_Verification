from flask import Blueprint, request, jsonify
from db_config import get_conn
import hashlib, random, string, datetime

bp = Blueprint("token", __name__)

def sha256(text): return hashlib.sha256(text.encode()).hexdigest()

def generate_token(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@bp.route("/request", methods=["POST"])
def issue_token():
    data = request.get_json()
    mid = data.get("member_id")
    pwd = data.get("password")

    if not mid or not pwd:
        return jsonify(error="缺少必要參數"), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # 查成員對應的 family_id
            cur.execute("SELECT family_id FROM Members WHERE member_id=%s", (mid,))
            row = cur.fetchone()
            if not row:
                return jsonify(error="成員不存在"), 404
            fid = row["family_id"]

            # 驗證密碼
            cur.execute("SELECT * FROM Families WHERE family_id=%s AND password_hash=%s",
                        (fid, sha256(pwd)))
            if not cur.fetchone():
                return jsonify(error="密碼錯誤"), 403
    finally:
        conn.close()

    # 產生 token
    token = generate_token()
    expire_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat() + "Z"
    print(token)
    return jsonify(token=token, expires=expire_time)