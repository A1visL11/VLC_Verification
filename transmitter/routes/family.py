from flask import Blueprint, request, session, jsonify
from db_config import get_conn
import hashlib

bp = Blueprint("family", __name__)

def sha256(text): return hashlib.sha256(text.encode()).hexdigest()

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name, pw = data["family_name"], sha256(data["password"])
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO Families (family_name,password_hash) VALUES(%s,%s)", (name, pw))
            conn.commit()
        return {"message": "註冊成功"}
    except Exception as e:
        return {"error": str(e)}, 400
    finally:
        conn.close()

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    name, pw = data["family_name"], sha256(data["password"])
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT family_id FROM Families WHERE family_name=%s AND password_hash=%s", (name, pw))
            row = cur.fetchone()
            if not row:
                return {"error": "帳號或密碼錯誤"}, 401
            session["family_id"] = row["family_id"]  # 記到 cookie
            return {"message": "登入成功", "family_id": row["family_id"]}
    finally:
        conn.close()

@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return {"message": "已登出"}
