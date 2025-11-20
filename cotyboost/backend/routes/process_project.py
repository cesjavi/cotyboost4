from flask import Blueprint, request, jsonify, send_file
import os, zipfile, shutil
import subprocess
import re
from utils.analyzer import analyze_project
import json
import glob
from config import TEMP_ROOT

project_bp = Blueprint('project', __name__)

@project_bp.route('/process_project/', methods=['POST'])
def process_project():
    try:
        project_name = None
        extract_path = None

        # ZIP upload
        if 'file' in request.files:
            zip_file = request.files['file']
            project_name = os.path.splitext(zip_file.filename)[0].replace(" ", "_")
        elif request.json and 'github_url' in request.json:
            github_url = request.json['github_url']
            pattern = re.compile(r"^https://github\.com/([^/]+)/([^/]+)(\.git)?$")
            match = pattern.match(github_url)
            if not match:
                return jsonify({"error": "Invalid GitHub URL"}), 400
            project_name = match.group(2).replace(" ", "_")
        else:
            return jsonify({"error": "No se recibió ZIP ni GitHub URL"}), 400
        project_id = project_name
        extract_path = os.path.join(TEMP_ROOT, project_id)

        # Ensure a clean extraction directory
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        os.makedirs(extract_path, exist_ok=True)

        if 'file' in request.files:
            zip_path = os.path.join(extract_path, 'source.zip')
            zip_file.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        else:  # GitHub URL
            if os.path.exists(os.path.join(extract_path, '.git')):
                try:
                    subprocess.run(['git', '-C', extract_path, 'pull'], check=True)
                except Exception:
                    shutil.rmtree(extract_path)
                    subprocess.run(['git', 'clone', github_url, extract_path], check=True)
            else:
                subprocess.run(['git', 'clone', github_url, extract_path], check=True)


        analysis = analyze_project(extract_path)
        analysis['project_id'] = project_id
        analysis['project_name'] = project_name

        # Guardar análisis para referencia posterior
        with open(os.path.join(extract_path, 'analysis.json'), 'w') as f:
            json.dump(analysis, f)

        # Construir dataset básico desde los archivos .py encontrados
        dataset = []
        for ext in ['*.py', '*.cs']:
            for filepath in glob.glob(os.path.join(extract_path, '**', ext), recursive=True):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    chunks = [''.join(lines[i:i+20]) for i in range(0, len(lines), 20)]
                    for chunk in chunks:
                        dataset.append({
                            "instruction": "Explica qué hace este código.",
                            "input": chunk.strip(),
                            "output": ""
                        })

        dataset_path = os.path.join(extract_path, 'dataset.json')
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)

        with open(dataset_path, 'r') as f:
            preview_samples = json.load(f)[:3]
        analysis['dataset_preview'] = preview_samples

        # Adjuntar contenido del log si existe
        log_path = os.path.join(extract_path, "train.log")
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                analysis['log_preview'] = f.read()[-3000:]

        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@project_bp.route('/download_dataset/<project_id>', methods=['GET'])
def download_dataset(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    dataset_path = os.path.join(folder_path, "dataset.json")
    analysis_path = os.path.join(folder_path, "analysis.json")
    if os.path.exists(dataset_path):
        filename = "dataset.json"
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                if "project_name" in analysis:
                    filename = f"dataset_{analysis['project_name']}.json"
        return send_file(dataset_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Dataset no encontrado."}), 404

@project_bp.route('/download_adapter/<project_id>', methods=['GET'])
def download_adapter(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    adapter_path = os.path.join(folder_path, "adapter", "adapter_model.bin")
    analysis_path = os.path.join(folder_path, "analysis.json")
    if os.path.exists(adapter_path):
        filename = "adapter.bin"
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                if "project_name" in analysis:
                    filename = f"adapter_{analysis['project_name']}.bin"
        return send_file(adapter_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Adaptador no encontrado."}), 404

@project_bp.route('/download_log/<project_id>', methods=['GET'])
def download_log(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    log_path = os.path.join(folder_path, "train.log")
    analysis_path = os.path.join(folder_path, "analysis.json")
    if os.path.exists(log_path):
        filename = "train.log"
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                if "project_name" in analysis:
                    filename = f"train_{analysis['project_name']}.log"
        return send_file(log_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Log de entrenamiento no encontrado."}), 404
