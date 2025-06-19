from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from routes.process_project import project_bp
from routes.train import train_bp
from routes.metrics import metrics_bp
from routes.logs import logs_bp
import subprocess
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import glob
import json

app = Flask(__name__)
CORS(app)
# Registrar Blueprints
#app.register_blueprint(project_bp, url_prefix='/project')
app.register_blueprint(train_bp, url_prefix='/train')
app.register_blueprint(metrics_bp, url_prefix='/metrics')
app.register_blueprint(logs_bp, url_prefix='/logs')
app.register_blueprint(project_bp)

training_processes = {}
inference_sessions = {}

@app.route('/list_projects', methods=['GET'])
def list_projects():
    base_path = "temp_projects"
    projects = []
    for d in os.listdir(base_path):
        folder = os.path.join(base_path, d)
        if os.path.isdir(folder):
            # Podés cargar el analysis.json para más datos:
            analysis_path = os.path.join(folder, "analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r") as f:
                    analysis = json.load(f)
                projects.append({
                    "id": d,
                    "name": analysis.get("project_name", d),
                    "model": analysis.get("suggested_model", ""),
                    "recommendation": analysis.get("recommendation", ""),
                })
            else:
                projects.append({"id": d, "name": d, "model": "", "recommendation": ""})
    return jsonify({"projects": projects})


## ===========================
# Entrenamiento en tiempo real
# ===========================
@app.route('/train_stream/<project_id>', methods=['POST'])
def train_stream(project_id):
    model_name = request.json.get("model_name")
    mode = request.json.get("mode")

    command = [
        "accelerate", "launch", "./train_qlora.py",
        "--model_name", model_name,
        "--mode", mode,
        "--dataset_path", f"temp_projects/{project_id}/dataset.json",
        "--output_dir", f"temp_projects/{project_id}/adapter"
    ]

    print(f"🚀 Ejecutando comando: {' '.join(command)}")

    # Lanzar el proceso en segundo plano
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    training_processes[project_id] = process

    def generate():
        for line in process.stdout:
            print(f"[LOG]: {line.strip()}")
            yield f"data: {line.strip()}\n\n"
        for line in process.stderr:
            print(f"[ERROR]: {line.strip()}")
            yield f"data: {line.strip()}\n\n"

    return Response(generate(), content_type='text/event-stream')

# ===========================
# Detener Entrenamiento
# ===========================
@app.route('/stop_train', methods=['POST'])
def stop_train():
    project_id = request.json.get("project_id")
    process = training_processes.get(project_id)

    if process and process.poll() is None:
        process.terminate()
        process.wait()
        del training_processes[project_id]
        return jsonify({"message": f"Entrenamiento para el proyecto {project_id} detenido exitosamente."}), 200
    else:
        return jsonify({"error": "No se encontró un proceso en ejecución para este proyecto."}), 404

# ===========================
# Descargar el Adaptador
# ===========================
@app.route('/download_adapter/<project_id>', methods=['HEAD', 'GET'])
def download_adapter(project_id):
    adapter_path = f"temp_projects/{project_id}/adapter"
    
    # Verificamos si el adaptador existe en la carpeta correcta
    if os.path.exists(adapter_path):
        return send_from_directory(adapter_path, "adapter_model.safetensors", as_attachment=True)
    else:
        print(f"🔴 Adaptador no encontrado en: {adapter_path}")
        return jsonify({"error": "Adaptador no encontrado"}), 404

# ===========================
# Cargar Modelo y Tokenizer para Inferencia
# ===========================
def load_inference_model(project_id):
    if project_id not in inference_sessions:
        adapter_path = f"temp_projects/{project_id}/adapter"
        #model_name = "Salesforce/codegen-2B-mono"
        model_name = "Salesforce/codegen-6B-mono"
        
        print(f"🔍 Cargando modelo desde: {adapter_path}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
        
        # Cargar el modelo adaptado con LoRA
        model = PeftModel.from_pretrained(model, adapter_path)
        model.eval()
        
        inference_sessions[project_id] = {
            "tokenizer": tokenizer,
            "model": model
        }
    return inference_sessions[project_id]

# ===========================
# Inferencia
# ===========================
@app.route('/inference', methods=['POST'])
def inference():
    project_id = request.json.get("project_id")
    prompt = request.json.get("prompt")

    if not project_id or not prompt:
        return jsonify({"error": "Faltan parámetros para realizar la inferencia"}), 400

    try:
        session = load_inference_model(project_id)
        tokenizer = session["tokenizer"]
        model = session["model"]

        # Tokenización y generación
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).to(model.device)
        outputs = model.generate(inputs.input_ids, max_new_tokens=256, do_sample=True, top_p=0.95, temperature=0.7)
        
        # Decodificar respuesta
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"📝 Respuesta generada: {response_text}")

        return jsonify({"result": response_text}), 200

    except Exception as e:
        print(f"❌ Error durante la inferencia: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ===========================
# Iniciar el Servidor
# ===========================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
