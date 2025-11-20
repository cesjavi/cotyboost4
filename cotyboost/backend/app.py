from flask import Flask, request, jsonify
from flask_cors import CORS
from routes.process_project import project_bp
from routes.train import train_bp
from routes.metrics import metrics_bp
from routes.logs import logs_bp
from routes.inference import inference_bp
import os
import signal
from utils.state import training_processes

app = Flask(__name__)
CORS(app)
app.register_blueprint(logs_bp)
app.register_blueprint(project_bp)
app.register_blueprint(train_bp)
app.register_blueprint(metrics_bp)
app.register_blueprint(inference_bp)

@app.route('/stop_train', methods=['POST'])
def stop_train():
    project_id = request.json.get("project_id")
    process = training_processes.get(project_id)

    if process and process.poll() is None:  # Verifica si sigue corriendo
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        process.terminate()
        process.wait()
        del training_processes[project_id]
        return jsonify({"message": f"Entrenamiento para el proyecto {project_id} detenido exitosamente."}), 200
    else:
        return jsonify({"error": "No se encontró un proceso en ejecución para este proyecto."}), 404



if __name__ == '__main__':
    app.run(debug=True)
