import glob
import json
import os
import shutil
import subprocess
import uuid
import zipfile
from flask import Blueprint, jsonify, request

from utils.analyzer import analyze_project
project_bp = Blueprint('project_bp', __name__)

@project_bp.route('/process_project/', methods=['POST'])
def process_project():
    try:
        print("request.files:", request.files)
        print("request.json:", request.json)
        print("request.form:", request.form)
        
        project_id = f"{uuid.uuid4().hex[:8]}"
        suggested_model = None
        project_name = None
        extract_path = None

        # --- ZIP upload ---
        if 'file' in request.files:
            project_name = os.path.splitext(request.files['file'].filename)[0].lower().replace(' ', '_')
            combined_name = f"{project_name}_{project_id}"
            extract_path = os.path.join("temp_projects", combined_name)
            os.makedirs(extract_path, exist_ok=True)
            zip_file = request.files['file']
            zip_path = os.path.join(extract_path, 'source.zip')
            zip_file.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            suggested_model = request.form.get('suggested_model', "codellama/CodeLlama-7b-hf")

        # --- GitHub URL ---
        elif request.json and 'github_url' in request.json:
            github_url = request.json['github_url']
            project_name = github_url.strip('/').split('/')[-1].lower().replace(' ', '_')
            combined_name = f"{project_name}_{project_id}"
            extract_path = os.path.join("temp_projects", combined_name)
            os.makedirs(extract_path, exist_ok=True)
            command = f"git clone {github_url} {extract_path}"
            subprocess.run(command, shell=True)
            suggested_model = request.json.get('suggested_model', "codellama/CodeLlama-7b-hf")

        # --- Local Folder Path ---
        elif request.json and 'local_path' in request.json:
            local_path = request.json['local_path']
            if not os.path.exists(local_path):
                return jsonify({"error": f"El path {local_path} no existe"}), 400
            project_name = os.path.basename(local_path).replace(" ", "_")
            combined_name = f"{project_name}_{project_id}"
            extract_path = os.path.join("temp_projects", combined_name)
            os.makedirs(extract_path, exist_ok=True)
            # Copiar todo el contenido de la carpeta local
            for filename in os.listdir(local_path):
                src_path = os.path.join(local_path, filename)
                dest_path = os.path.join(extract_path, filename)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
            suggested_model = request.json.get('suggested_model', "codellama/CodeLlama-7b-hf")

        # --- Nada válido recibido ---
        else:
            return jsonify({"error": "No se recibió ZIP, GitHub URL ni carpeta local"}), 400

        # --- Análisis del proyecto ---
        analysis = analyze_project(extract_path)
        analysis['project_id'] = combined_name
        analysis['project_name'] = project_name
        analysis['suggested_model'] = suggested_model

        # Guardar análisis
        with open(os.path.join(extract_path, 'analysis.json'), 'w') as f:
            json.dump(analysis, f)

        # Dataset básico
        dataset = []
        for ext in ['*.py', '*.cs']:
            for filepath in glob.glob(os.path.join(extract_path, '**', ext), recursive=True):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    chunks = [''.join(lines[i:i + 20]) for i in range(0, len(lines), 20)]
                    for chunk in chunks:
                        dataset.append({
                            "instruction": "Explain what this code does.",
                            "input": chunk.strip(),
                            "output": ""
                        })

        # Guardar dataset
        dataset_path = os.path.join(extract_path, 'dataset.json')
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)

        # Vista previa de los datos
        with open(dataset_path, 'r') as f:
            preview_samples = json.load(f)[:3]
        analysis['dataset_preview'] = preview_samples

        return jsonify(analysis)
    except Exception as e:
        print(f"❌ Error en process_project: {str(e)}")
        return jsonify({"error": str(e)}), 500
