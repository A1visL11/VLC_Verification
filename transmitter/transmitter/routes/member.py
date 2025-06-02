from flask import Blueprint, request, session, jsonify, send_file
from db_config import get_conn
from io import BytesIO

bp = Blueprint("member", __name__)

def _require_login():
    if "family_id" not in session:
        return jsonify(error="未登入"), 401

@bp.route("/list", methods=["GET"])
def list_members():
    if (err := _require_login()):
        return err
    fid = session.get("family_id")
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT member_id, name FROM Members WHERE family_id = %s", (fid,))
        members = cur.fetchall()
    conn.close()
    return {"members": members}

@bp.route("/add", methods=["POST"])
def add_member():
    if (err := _require_login()):
        return err
    fid = session["family_id"]
    name = request.form.get("name")
    file = request.files.get("avatar")
    avatar_data = file.read() if file else None

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO Members (name, family_id, avatar_data) VALUES (%s, %s, %s)",
            (name, fid, avatar_data)
        )
        conn.commit()
    conn.close()
    return {"message": "新增成員成功"}

@bp.route("/avatar/<int:member_id>")
def get_avatar(member_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT avatar_data FROM Members WHERE member_id = %s", (member_id,))
        row = cur.fetchone()
    conn.close()
    if row and row["avatar_data"]:
        return send_file(BytesIO(row["avatar_data"]), mimetype='image/jpeg')
    else:
        return send_file("static/default.png", mimetype="image/png")

@bp.route("/delete/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    if "family_id" not in session:
        return {"error": "未登入"}, 401

    fid = session["family_id"]
    conn = get_conn()
    with conn.cursor() as cur:
        # 1. 刪除此成員的 EntryLogs
        cur.execute("DELETE FROM EntryLogs WHERE member_id = %s", (member_id,))

        # 2. 再刪除 Members 表中的該成員
        cur.execute(
            "DELETE FROM Members WHERE member_id = %s AND family_id = %s",
            (member_id, fid)
        )
        conn.commit()
    conn.close()
    return {"message": "成員已刪除"}
