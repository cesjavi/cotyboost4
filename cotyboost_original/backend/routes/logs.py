# backend/routes/logs.py
from flask import Blueprint, request, jsonify
import os

logs_bp = Blueprint('logs', __name__)

@logs_bp.route("/logs/", methods=["GET"])
def get_logs():
    path = request.args.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "Log file not found"}), 400
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    return jsonify({
        "logs": lines[-100:],  # última parte del log
        "finished": any("Training completed" in line for line in lines)
    })
