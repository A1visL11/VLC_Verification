# routes/error.py
from flask import Blueprint, request, jsonify
from db_config import get_connection

error_bp = Blueprint('error', __name__)

@error_bp.route('/log', methods=['POST'])
def log_error():
    data = request.get_json()
    family_id = data.get('family_id')
    message = data.get('error_message')

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO ErrorLogs (family_id, error_message) VALUES (%s, %s)", (family_id, message))
            conn.commit()
        return jsonify({"message": "錯誤已記錄"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
