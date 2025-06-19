from flask import Blueprint, request, jsonify
import subprocess
import os

train_bp = Blueprint('train', __name__)

@train_bp.route('/train', methods=['POST'])
def launch_training():
    data = request.get_json()
    project_id = data.get('project_id')
    model_name = data.get('model_name')
    mode = data.get('mode')

    if not all([project_id, model_name, mode]):
        return jsonify({"error": "Missing parameters"}), 400

    dataset_path = f"temp_projects/{project_id}/dataset.json"
    output_dir = f"temp_projects/{project_id}/adapter"
    log_file = f"temp_projects/{project_id}/train.log"

    command = [
        "accelerate", "launch", "train_qlora.py",
        "--model_name", model_name,
        "--mode", mode,
        "--dataset_path", dataset_path,
        "--output_dir", output_dir
    ]

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "w") as log:
        subprocess.Popen(command, stdout=log, stderr=log)

    return jsonify({"status": "Training started", "log_file": log_file})
