<template>
  <div class="container">
    <!-- Tabs -->
    <div class="tabs">
      <button @click="changeTab('main')" :class="{active: activeTab==='main'}">Entrenamiento</button>
      <button @click="changeTab('projects')" :class="{active: activeTab==='projects'}">Proyectos</button>
    </div>

    <!-- Entrenamiento Tab -->
    <section v-if="activeTab === 'main'">
      <h1>MyQLoraApp</h1>
      <section class="upload-section">
        <h2>1. Subir ZIP o ingresar GitHub</h2>
        <input type="file" @change="handleFile" accept=".zip" />
        <p>o</p>
        <input type="text" v-model="githubUrl" placeholder="https://github.com/usuario/proyecto" />
        <p>o</p>
        <input type="text" v-model="localPath" placeholder="/ruta/a/tu/carpeta" />
        <!-- Añade esto dentro de tu sección de upload-section, antes del botón de analizar -->
      <label for="model-select"><strong>Modelo base para LoRA/QLoRA:</strong></label>
      <select v-model="selectedModel" id="model-select">
        <option v-for="model in availableModels" :key="model" :value="model">
          {{ model }}
        </option>
      </select>
        <button @click="processProject" :disabled="isProcessing">
          Subir y Analizar
        </button>
      </section>

      <section v-if="analysis" class="result-section">
        <h2>📁 Proyecto: {{ analysis.project_name }}</h2>
        <h2>2. Resultado del Análisis</h2>
        <ul>
          <li><strong>Archivos:</strong> {{ analysis.file_count }}</li>
          <li><strong>Líneas de código:</strong> {{ analysis.total_lines }}</li>
          <li><strong>Tamaño:</strong> {{ analysis.total_size_mb }} MB</li>
          <li><strong>Estrategia recomendada:</strong> {{ analysis.recommendation }}</li>
          <li><strong>Modelo sugerido:</strong> {{ analysis.suggested_model }}</li>
        </ul>

        <div class="actions">
          <button @click="startTraining" :disabled="isTraining || adapterExists">Entrenar Modelo</button>
          <button @click="stopTraining" :disabled="!isTraining">Detener Entrenamiento</button>
          <p v-if="isTraining" style="color: blue;">🧠 Entrenamiento en curso... (revisá backend para el progreso)</p>
          <button @click="enableInference" :disabled="!adapterExists">Abrir Inferencia</button>
        </div>

        <div class="command-box">
          <h3>📜 Comando sugerido:</h3>
          <pre>{{ trainingCommand }}</pre>
          <button @click="copyCommand">📋 Copiar comando</button>
          <button @click="downloadCommand">⬇️ Descargar train.sh</button>
          <button @click="downloadDataset">📁 Descargar dataset.json</button>
          <button v-if="adapterExists" @click="downloadAdapter">📦 Descargar adaptador LoRA</button>
          <p v-else style="color: gray;">Adaptador aún no generado.</p>
        </div>

        <section v-if="isTraining" class="log-section">
          <h2>📝 Logs de Entrenamiento en Tiempo Real:</h2>
          <div class="log-box">
            <pre>{{ trainingLog }}</pre>
          </div>
        </section>

        <div class="inference-box" v-if="inferenceEnabled">
          <h2>🧠 Inferencia</h2>
          <input v-model="prompt" placeholder="Escribe tu prompt..." />
          <button @click="runInference">Generar Respuesta</button>
          <div v-if="inferenceResult">
            <h3>📝 Respuesta:</h3>
            <pre>{{ inferenceResult }}</pre>
          </div>
        </div>
      </section>
    </section>

    <!-- Proyectos Tab -->
    <section v-if="activeTab === 'projects'" class="projects-section">
      <h2>📂 Proyectos Entrenados</h2>
      <ul>
        <li v-for="project in projects" :key="project.id">
          <strong>{{ project.name }}</strong> ({{ project.id }})<br>
          Modelo: {{ project.model }}<br>
          Estrategia: {{ project.recommendation }}<br>
          <button @click="openInference(project)">Inferencia</button>
          <a :href="`http://localhost:5000/download_adapter/${project.id}`" target="_blank" style="margin-left:10px">Descargar adaptador</a>
          <a :href="`http://localhost:5000/download_dataset/${project.id}`" target="_blank" style="margin-left:10px">Descargar dataset</a>
        </li>
      </ul>
    </section>

    <div v-if="error" class="error">⚠️ Error: {{ error }}</div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'MainPage',
  data() {
    return {
      selectedFile: null,
      githubUrl: '',
      analysis: null,
      error: null,
      isProcessing: false,
      isTraining: false,
      adapterExists: false,
      metrics: null,
      metricsInterval: null,
      trainingLog: "",
      eventSource: null,
      inferenceEnabled: false,
      prompt: "",
      inferenceResult: "",
      trainingCommand: "",
      activeTab: "main",
      projects: [],
      // En data()
      availableModels: [
        "codellama/CodeLlama-7b-hf",
        "Salesforce/codegen-2B-mono",
        "bigcode/starcoder",
        "mistralai/Mistral-7B-v0.1",
        "meta-llama/Llama-2-7b-hf",
        "EleutherAI/gpt-neo-1.3B"
      ],
      selectedModel: "codellama/CodeLlama-7b-hf"
    };
  },
  methods: {
    handleFile(event) {
      this.selectedFile = event.target.files[0];
      this.githubUrl = '';
    },
    async processProject() {
      this.analysis = null;
      this.error = null;
      this.adapterExists = false;
      this.isProcessing = true;
      try {
        let response;
        if (this.selectedFile) {
          const formData = new FormData();
          formData.append('file', this.selectedFile);
          formData.append('suggested_model', this.selectedModel);
          response = await axios.post('http://localhost:5000/process_project/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
        } else if (this.githubUrl.trim() !== '') {
          response = await axios.post('http://localhost:5000/process_project/', {
            github_url: this.githubUrl,
            suggested_model: this.selectedModel
          });
        } else if (this.localPath && this.localPath.trim() !== '') {
          response = await axios.post('http://localhost:5000/process_project/', {
            local_path: this.localPath,
            suggested_model: this.selectedModel
          });
        } else {
          this.error = 'Debes subir un ZIP o ingresar una URL de GitHub.';
          this.isProcessing = false;
          return;
        }
        this.analysis = response.data;

        // Generar el comando sugerido
        this.trainingCommand = `accelerate launch backend/train_qlora.py \\\n  --model_name ${this.analysis.suggested_model} \\\n  --mode ${this.analysis.recommendation} \\\n  --dataset_path temp_projects/${this.analysis.project_id}/dataset.json \\\n  --output_dir temp_projects/${this.analysis.project_id}/adapter`;

        await this.checkAdapterExists();
      } catch (err) {
        this.error = err.response?.data?.error || err.message;
      } finally {
        this.isProcessing = false;
      }
    },
    async checkAdapterExists() {
      if (!this.analysis?.project_id) return;
      const url = `http://localhost:5000/download_adapter/${this.analysis.project_id}`;
      try {
        const response = await axios.head(url);
        if (response.status === 200) {
          this.adapterExists = true;
        } else {
          setTimeout(this.checkAdapterExists, 10000);
        }
      } catch (e) {
        setTimeout(this.checkAdapterExists, 10000);
      }
    },
    async startTraining() {
  this.isTraining = true;
  this.trainingLog = "";
  try {
    const response = await axios.post(
      `http://localhost:5000/train_stream/${this.analysis.project_id}`,
      {
        model_name: this.analysis.suggested_model,
        mode: this.analysis.recommendation
      }
    );
    this.trainingLog = response.data?.log || "Entrenamiento iniciado.";
    // Podrías agregar aquí polling para saber cuándo termina/adaptador listo
  } catch (err) {
    this.error = err.response?.data?.error || err.message;
    this.isTraining = false;
  }
}
,
    stopTraining() {
      this.isTraining = false;
      if (this.eventSource) {
        this.eventSource.close();
      }
      axios.post('http://localhost:5000/stop_train', {
        project_id: this.analysis.project_id
      });
    },
    enableInference() {
      this.inferenceEnabled = true;
    },
    async runInference() {
      try {
        const response = await axios.post('http://localhost:5000/inference', {
          project_id: this.analysis.project_id,
          prompt: this.prompt
        });
        this.inferenceResult = response.data.result;
      } catch (error) {
        this.inferenceResult = "";
        this.error = "Error en la inferencia: " + (error.response?.data?.error || error.message);
      }
    },
    copyCommand() {
      navigator.clipboard.writeText(this.trainingCommand);
    },
    downloadCommand() {
      const blob = new Blob([this.trainingCommand], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'train.sh';
      a.click();
      URL.revokeObjectURL(url);
    },
    downloadDataset() {
      window.open(`http://localhost:5000/download_dataset/${this.analysis.project_id}`);
    },
    downloadAdapter() {
      window.open(`http://localhost:5000/download_adapter/${this.analysis.project_id}`);
    },
    changeTab(tab) {
      this.activeTab = tab;
      if (tab === 'projects') {
        this.loadProjects();
      }
    },
    async loadProjects() {
      try {
        const response = await axios.get('http://localhost:5000/list_projects');
        this.projects = response.data.projects;
      } catch (err) {
        this.projects = [];
        this.error = err.response?.data?.error || err.message;
      }
    },
    openInference(project) {
      // Carga el proyecto seleccionado en la vista de inferencia
      this.analysis = {
        project_id: project.id,
        project_name: project.name,
        suggested_model: project.model
      };
      this.adapterExists = true; // Asume que ya existe el adaptador si aparece en la lista
      this.inferenceEnabled = true;
      this.activeTab = 'main';
    }
  }
};
</script>

<style>
.container {
  max-width: 900px;
  margin: 20px auto;
  padding: 16px;
  background: #181d23;
  color: #f1f1f1;
  border-radius: 18px;
  box-shadow: 0 3px 24px #0008;
  font-family: 'Inter', sans-serif;
}

.tabs {
  margin-bottom: 24px;
  display: flex;
  gap: 8px;
}

.tabs button {
  padding: 8px 20px;
  border: none;
  border-radius: 18px 18px 0 0;
  background: #262d35;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.tabs button.active {
  background: #536dfe;
  color: #fff;
}

.upload-section,
.projects-section,
.result-section {
  margin-bottom: 24px;
  background: #232936;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 2px 6px #0005;
}

input[type="file"],
input[type="text"] {
  margin: 6px 0;
  padding: 8px;
  width: 100%;
  background: #181d23;
  color: #fff;
  border: 1px solid #3b4656;
  border-radius: 6px;
}

button {
  margin: 6px 6px 6px 0;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: #536dfe;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

button:disabled {
  background: #333b44;
  color: #aaa;
  cursor: not-allowed;
}

.command-box pre, .log-box pre, .inference-box pre {
  background: #1a1e25;
  color: #aaf;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.error {
  color: #ff7979;
  background: #291819;
  padding: 10px;
  border-radius: 6px;
  margin-top: 16px;
}
</style>
