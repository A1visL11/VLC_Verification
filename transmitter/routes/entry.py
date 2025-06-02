from flask import Blueprint, session, jsonify, request
from db_config import get_conn

bp = Blueprint("entry", __name__)

@bp.route("/list", methods=["GET"])
def list_logs():
    if "family_id" not in session:
        return {"error": "未登入"}, 401
    fid = session["family_id"]
    conn = get_conn()
    with conn.cursor() as cur:
        # 1. 先抓所有 member_id 與對應的 name
        cur.execute("SELECT member_id, name FROM Members WHERE family_id=%s", (fid,))
        members = {m["member_id"]: m["name"] for m in cur.fetchall()}
        # 2. 抓 EntryLogs
        if members:
            cur.execute("""
                SELECT log_id AS id, member_id, entry_time AS time, NULL AS error_message, 'entry' AS log_type
                FROM EntryLogs
                WHERE member_id IN %s
            """, (tuple(members.keys()),))
            entry_rows = list(cur.fetchall())
        else:
            entry_rows = []
        # 3. 抓 ErrorLogs
        cur.execute("""
            SELECT error_id AS id, NULL AS member_id, timestamp AS time, error_message, 'error' AS log_type
            FROM ErrorLogs
            WHERE family_id=%s
        """, (fid,))
        error_rows = list(cur.fetchall())
    conn.close()
    # 4. 合併並排序
    combined = entry_rows + error_rows
    combined.sort(key=lambda x: x["time"], reverse=True)
    # 5. 將成員名稱填入 entry logs
    logs = []
    for r in combined:
        if r["log_type"] == "entry":
            logs.append({
                "type": "entry",
                "id": r["id"],
                "name": members.get(r["member_id"], ""),
                "time": r["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "message": ""
            })
        else:  # error
            logs.append({
                "type": "error",
                "id": r["id"],
                "name": "",
                "time": r["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "message": r["error_message"]
            })
    return {"logs": logs}

@bp.route("/delete", methods=["POST"])
def delete_log():
    if "family_id" not in session:
        return {"error": "未登入"}, 401
    fid = session["family_id"]
    data = request.get_json()
    log_type = data.get("type")
    log_id = data.get("id")
    conn = get_conn()
    with conn.cursor() as cur:
        if log_type == "entry":
            # 確認該 entry log 屬於此家庭
            cur.execute("""
                DELETE EL
                FROM EntryLogs EL
                JOIN Members M ON EL.member_id = M.member_id
                WHERE EL.log_id = %s AND M.family_id = %s
            """, (log_id, fid))
        elif log_type == "error":
            # 確認該 error log 屬於此家庭
            cur.execute("DELETE FROM ErrorLogs WHERE error_id = %s AND family_id = %s", (log_id, fid))
        else:
            return {"error": "參數錯誤"}, 400
        conn.commit()
    conn.close()
    return {"success": True}