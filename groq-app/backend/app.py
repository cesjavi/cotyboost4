from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq_api import send_prompt
from analyzer import analyze_project
from datetime import datetime
import shutil
import os
import zipfile
import subprocess
import re
import json
import glob

print("Iniciando app...")
print("GROQ_API_KEY:", os.environ.get("GROQ_API_KEY"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_ROOT = os.path.join(BASE_DIR, "temp_projects")

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.json.get("prompt", "")
    response = send_prompt(prompt)
    return jsonify(response)

@app.route("/process_project/", methods=["POST"]) 
@app.route("/process_project", methods=["POST"]) 
def process_project():
    try:
        project_name = None

        if 'file' in request.files:
            zip_file = request.files['file']
            project_name = os.path.splitext(zip_file.filename)[0].replace(' ', '_')
        elif request.json and 'github_url' in request.json:
            github_url = request.json['github_url']
            pattern = re.compile(r'^https://github\.com/([^/]+)/([^/]+)(\.git)?$')
            match = pattern.match(github_url)
            if not match:
                return jsonify({'error': 'Invalid GitHub URL'}), 400
            project_name = match.group(2).replace(' ', '_')
        else:
            return jsonify({'error': 'No se recibió ZIP ni GitHub URL'}), 400

        project_id = project_name
        extract_path = os.path.join(TEMP_ROOT, project_id)
        os.makedirs(extract_path, exist_ok=True)

        if 'file' in request.files:
            zip_path = os.path.join(extract_path, 'source.zip')
            zip_file.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        else:
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

        with open(os.path.join(extract_path, 'analysis.json'), 'w') as f:
            json.dump(analysis, f)

        dataset = []
        for ext in ['*.py', '*.cs']:
            for filepath in glob.glob(os.path.join(extract_path, '**', ext), recursive=True):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    chunks = [''.join(lines[i:i+20]) for i in range(0, len(lines), 20)]
                    for chunk in chunks:
                        dataset.append({
                            'instruction': 'Explica qué hace este código.',
                            'input': chunk.strip(),
                            'output': ''
                        })

        dataset_path = os.path.join(extract_path, 'dataset.json')
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)

        with open(dataset_path, 'r') as f:
            preview_samples = json.load(f)[:3]
        analysis['dataset_preview'] = preview_samples

        log_path = os.path.join(extract_path, 'train.log')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                analysis['log_preview'] = f.read()[-3000:]

        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download_dataset/<project_id>', methods=['GET'])
def download_dataset(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    dataset_path = os.path.join(folder_path, 'dataset.json')
    analysis_path = os.path.join(folder_path, 'analysis.json')
    if os.path.exists(dataset_path):
        filename = 'dataset.json'
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                if 'project_name' in analysis:
                    filename = f"dataset_{analysis['project_name']}.json"
        return send_file(dataset_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': 'Dataset no encontrado.'}), 404


@app.route('/download_adapter/<project_id>', methods=['GET'])
def download_adapter(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    adapter_path = os.path.join(folder_path, 'adapter', 'adapter_model.bin')
    analysis_path = os.path.join(folder_path, 'analysis.json')
    if os.path.exists(adapter_path):
        filename = 'adapter.bin'
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                if 'project_name' in analysis:
                    filename = f"adapter_{analysis['project_name']}.bin"
        return send_file(adapter_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': 'Adaptador no encontrado.'}), 404


@app.route('/download_log/<project_id>', methods=['GET'])
def download_log(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    log_path = os.path.join(folder_path, 'train.log')
    analysis_path = os.path.join(folder_path, 'analysis.json')
    if os.path.exists(log_path):
        filename = 'train.log'
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                if 'project_name' in analysis:
                    filename = f"train_{analysis['project_name']}.log"
        return send_file(log_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': 'Log de entrenamiento no encontrado.'}), 404


@app.route('/complete_dataset/<project_id>', methods=['POST'])
def complete_dataset(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    dataset_path = os.path.join(folder_path, 'dataset.json')

    if not os.path.exists(dataset_path):
        return jsonify({'error': 'Dataset no encontrado.'}), 404

    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    completados = 0
    for item in dataset:
        if not item.get("output"):
            prompt = f"{item['instruction']}\n\n{item['input']}"
            response = send_prompt(prompt)
            try:
                item["output"] = response["choices"][0]["message"]["content"]
            except Exception as e:
                print("⚠️ Respuesta inesperada de Groq:", response)
                item["output"] = f"❌ Error en respuesta de Groq: {str(response)}"
            completados += 1

    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    return jsonify({"status": "ok", "completados": completados})


def train_project(project_id):
    """Launch training process for a given project."""
    folder_path = os.path.join(TEMP_ROOT, project_id)
    dataset_path = os.path.join(folder_path, 'dataset.json')
    log_path = os.path.join(folder_path, "train.log")

    with open(log_path, "a", encoding="utf-8") as log:
        if not os.path.exists(dataset_path):
            return jsonify({'error': 'Dataset no encontrado.'}), 404

        mode = request.json.get("mode", "lora")
        model_name = request.json.get("model_name", "codellama/CodeLlama-7b-hf")

        command = [
            "accelerate", "launch", "groq-app/backend/utils/lora_trainer.py",
            "--model_name", model_name,
            "--mode", mode,
            "--dataset_path", dataset_path,
            "--output_dir", os.path.join(folder_path, "adapter")
        ]

        log.write("🚀 Iniciando entrenamiento...\n")
        log.flush()
        try:
            subprocess.Popen(command, stdout=log, stderr=log)
            log.write("✅ Popen lanzado correctamente.\n")
        except Exception as e:
            log.write(f"❌ Error lanzando subprocess: {str(e)}\n")

    return jsonify({
        "status": "ok",
        "message": f"Entrenamiento iniciado con modelo {model_name} en modo {mode}"
    })


@app.route('/train/<project_id>', methods=['POST'])
def train_project_route(project_id):
    return train_project(project_id)

@app.route('/auto_train/<project_id>', methods=['POST'])
def auto_train(project_id):
    folder_path = os.path.join(TEMP_ROOT, project_id)
    dataset_path = os.path.join(folder_path, 'dataset.json')
    log_path = os.path.join(folder_path, "train.log")
    with open(log_path, "a", encoding="utf-8") as log:
        if not os.path.exists(dataset_path):
            return jsonify({'error': 'Dataset no encontrado.'}), 404

        # 1. Cargar y completar dataset con Groq
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        completados = 0
        for item in dataset:
            if not item.get("output"):
                prompt = f"{item['instruction']}\n\n{item['input']}"
                response = send_prompt(prompt)
                if response.get("error"):
                    item["output"] = f"❌ Error en respuesta de Groq: {response.get('error')} - Raw: {response.get('raw')}"
                else:
                    try:
                        item["output"] = response["choices"][0]["message"]["content"]
                        print(f"✅ Respuesta procesada: {item['output'][:50]}...\n")  
                        log.write(f"✅ Respuesta procesada: {item['output'][:50]}...\n")  
                    except (KeyError, IndexError) as e:
                        print(f"⚠️ Respuesta inesperada de Groq (auto_train): {response}, error: {e}")
                        log.write(f"⚠️ Respuesta inesperada de Groq (auto_train): {response}, error: {e}")
                        item["output"] = f"❌ Error procesando respuesta de Groq: {str(response)}"
                completados += 1

        with open(dataset_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

    response = train_project(project_id)
    data = response.get_json()
    data["completados"] = completados
    return jsonify(data), response.status_code


@app.route('/log/<project_id>', methods=['GET'])
def get_log(project_id):
    log_path = os.path.join(TEMP_ROOT, project_id, 'train.log')
    if not os.path.exists(log_path):
        return jsonify({
            "log": "⏳ Entrenamiento aún no comenzó...",
            "last_modified": None
        })
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()[-5000:]
        last_modified = datetime.fromtimestamp(os.path.getmtime(log_path)).strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            "log": contenido,
            "last_modified": last_modified
        })
    except Exception as e:
        return jsonify({
            "log": f"⚠️ Error leyendo log: {str(e)}",
            "last_modified": None
        })

if __name__ == "__main__":
    app.run(debug=True)
