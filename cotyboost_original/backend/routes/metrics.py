from flask import Blueprint, jsonify, request
import os
import re
import subprocess
import json

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route("/train_metrics/<project_id>", methods=["GET"])
def get_metrics(project_id):
    # Leer nombre del proyecto desde archivo de análisis generado
    metadata_path = f"temp_projects/{project_id}/analysis.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            data = json.load(f)
            project_name = data.get("project_name", "project")
    else:
        project_name = "project"

    full_id = f"{project_id}_{project_name}"
    metrics = {
        "loss": get_loss_from_log(full_id),
        "vram": get_gpu_memory_used(),
        "gpu_load": get_gpu_utilization()
    }
    return jsonify(metrics)

def get_loss_from_log(project_dir):
    log_path = f"temp_projects/{project_dir}/train.log"
    if not os.path.exists(log_path):
        return None
    loss = None
    with open(log_path, "r") as f:
        for line in reversed(f.readlines()):
            match = re.search(r"loss[=:]\s*([0-9\.]+)", line)
            if match:
                loss = float(match.group(1))
                break
    return round(loss, 4) if loss else None

def get_gpu_memory_used():
    try:
        output = subprocess.check_output([
            "nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"
        ]).decode("utf-8")
        return int(output.strip().split("\n")[0])
    except:
        return None

def get_gpu_utilization():
    try:
        output = subprocess.check_output([
            "nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,nounits,noheader"
        ]).decode("utf-8")
        return int(output.strip().split("\n")[0])
    except:
        return None
