from flask import Blueprint, request, jsonify, Response, stream_with_context
import subprocess
import os
import time
from app import training_processes

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_ROOT = os.path.join(BASE_DIR, "temp_projects")

train_bp = Blueprint('train', __name__)

@train_bp.route('/train', methods=['POST'])
def launch_training():
    data = request.get_json()
    project_id = data.get('project_id')
    model_name = data.get('model_name')
    mode = data.get('mode')

    if not all([project_id, model_name, mode]):
        return jsonify({"error": "Missing parameters"}), 400

    dataset_path = os.path.join(TEMP_ROOT, project_id, "dataset.json")
    output_dir = os.path.join(TEMP_ROOT, project_id, "adapter")
    log_file = os.path.join(TEMP_ROOT, project_id, "train.log")

    command = [
        "accelerate", "launch", "train_qlora.py",
        "--model_name", model_name,
        "--mode", mode,
        "--dataset_path", dataset_path,
        "--output_dir", output_dir
    ]

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with open(log_file, "a") as log:
        process = subprocess.Popen(
            command,
            stdout=log,
            stderr=log,
            env=env,
            preexec_fn=os.setsid,
        )

    training_processes[project_id] = process

    return jsonify({"status": "Training started", "log_file": log_file})

@train_bp.route('/train_stream/<project_id>')
def train_stream_route(project_id):
    log_file_path = os.path.join(TEMP_ROOT, project_id, "train.log")

    def generate_log_updates(log_file_path):
        try:
            with open(log_file_path, 'r') as f:
                # Move to the end of the file
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)  # Wait for new lines
                        # Optional: Add a condition to stop if the training is done
                        # For example, check for a specific message or if the file hasn't changed
                        continue
                    yield f"data: {line}\n\n"
        except FileNotFoundError:
            yield f"data: Error: Log file not found at {log_file_path}\n\n"
            return
        except Exception as e:
            yield f"data: Error reading log file: {str(e)}\n\n"
            return

    return Response(stream_with_context(generate_log_updates(log_file_path)), mimetype='text/event-stream')
