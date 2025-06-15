from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from routes.process_project import project_bp
from routes.train import train_bp
from routes.metrics import metrics_bp
from routes.logs import logs_bp
import subprocess
import os
import signal

app = Flask(__name__)
CORS(app)
app.register_blueprint(logs_bp)
app.register_blueprint(project_bp)
app.register_blueprint(train_bp)
app.register_blueprint(metrics_bp)

training_processes = {}

@app.route('/train_stream/<project_id>', methods=['GET'])
def train_stream(project_id):
    model_name = request.args.get("model_name")
    mode = request.args.get("mode")

    # Comando de entrenamiento
    command = [
        "accelerate", "launch", "train_qlora.py",
        "--model_name", model_name,
        "--mode", mode,
        "--dataset_path", f"temp_projects/{project_id}/dataset.json",
        "--output_dir", f"temp_projects/{project_id}/adapter"
    ]

    log_path = f"temp_projects/{project_id}/train.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Lanzar el proceso en segundo plano
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    training_processes[project_id] = process

    def generate():
        with open(log_path, "a") as log:
            for line in iter(process.stdout.readline, ""):
                print(line, end="")
                log.write(line)
                log.flush()
                yield f"data: {line}\n\n"
        process.wait()
        training_processes.pop(project_id, None)

    return Response(generate(), content_type='text/event-stream')
@app.route('/stop_train', methods=['POST'])
def stop_train():
    project_id = request.json.get("project_id")
    process = training_processes.get(project_id)

    if process and process.poll() is None:  # Verifica si sigue corriendo
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.terminate()
        process.wait()
        del training_processes[project_id]
        return jsonify({"message": f"Entrenamiento para el proyecto {project_id} detenido exitosamente."}), 200
    else:
        return jsonify({"error": "No se encontró un proceso en ejecución para este proyecto."}), 404



if __name__ == '__main__':
    app.run(debug=True)
