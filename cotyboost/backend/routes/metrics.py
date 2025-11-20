from flask import Blueprint, jsonify, request
import os
import re
import subprocess
import json
from typing import Optional
from config import TEMP_ROOT

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route("/train_metrics/<project_id>", methods=["GET"])
def get_metrics(project_id):
    """Return training metrics for a given project."""
    metrics = {
        "loss": get_loss_from_log(project_id),
        "vram": get_gpu_memory_used(),
        "gpu_load": get_gpu_utilization()
    }
    return jsonify(metrics)

def get_loss_from_log(project_id: str) -> Optional[float]:
    """Read the latest loss value from ``temp_projects/<project_id>/train.log``
    without loading the entire log file into memory.

    The function scans the log from the end in fixed-size chunks, mimicking the
    behaviour of ``tail`` to find the most recent occurrence of a ``loss`` value.
    """

    log_path = os.path.join(TEMP_ROOT, project_id, "train.log")
    if not os.path.exists(log_path):
        return None

    loss_pattern = re.compile(r"loss[=:]\s*([0-9\.]+)")
    chunk_size = 4096
    with open(log_path, "rb") as f:
        f.seek(0, os.SEEK_END)
        buffer = b""
        position = f.tell()

        while position > 0:
            read_size = min(chunk_size, position)
            position -= read_size
            f.seek(position)
            buffer = f.read(read_size) + buffer

            lines = buffer.split(b"\n")
            buffer = lines[0]  # Preserve potential partial line at the start

            for line in reversed(lines[1:]):
                text = line.decode("utf-8", errors="ignore")
                match = loss_pattern.search(text)
                if match:
                    return round(float(match.group(1)), 4)

        # Check any remaining buffered content
        if buffer:
            text = buffer.decode("utf-8", errors="ignore")
            match = loss_pattern.search(text)
            if match:
                return round(float(match.group(1)), 4)

    return None

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
