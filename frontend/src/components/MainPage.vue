<template>
  <div class="container">
    <h1>MyQLoraApp</h1>

    <section class="upload-section">
      <h2>1. Subir ZIP o ingresar GitHub</h2>
      <input type="file" @change="handleFile" accept=".zip" />
      <p>o</p>
      <input type="text" v-model="githubUrl" placeholder="https://github.com/usuario/proyecto" />
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
        <button @click="startTraining" :disabled="isTraining">Entrenar Modelo</button>
        <button @click="stopTraining" :disabled="!isTraining">Detener Entrenamiento</button>
        <p v-if="isTraining" style="color: blue;">🧠 Entrenamiento en curso... (revisá backend para el progreso)</p>
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
        <div class="log-box" style="max-height: 300px; overflow-y: auto;">
          <pre>{{ trainingLog }}</pre>
        </div>
      </section>

      <div class="metrics-box" v-if="metrics">
        <h3>📈 Métricas en tiempo real:</h3>
        <ul>
          <li><strong>Loss:</strong> {{ metrics.loss }}</li>
          <li><strong>VRAM usada:</strong> {{ metrics.vram }} MB</li>
          <li><strong>GPU Load:</strong> {{ metrics.gpu_load }}%</li>
        </ul>
      </div>
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
      eventSource: null
    };
  },
  computed: {
    trainingCommand() {
      if (!this.analysis) return '';
      const model = this.analysis.suggested_model;
      const mode = this.analysis.recommendation.toLowerCase();
      const projectId = this.analysis.project_id || 'PROYECTO_ID';
      const path = `temp_projects/${projectId}/dataset.json`;
      const output = `temp_projects/${projectId}/adapter`;
      return `accelerate launch train_qlora.py \
  --model_name ${model} \
  --mode ${mode} \
  --dataset_path ${path} \
  --output_dir ${output}`;
    }
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
          response = await axios.post('http://localhost:5000/process_project/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
        } else if (this.githubUrl.trim() !== '') {
          response = await axios.post('http://localhost:5000/process_project/', {
            github_url: this.githubUrl
          });
        } else {
          this.error = 'Debes subir un ZIP o ingresar una URL de GitHub.';
          this.isProcessing = false;
          return;
        }
        this.analysis = response.data;
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
        }
      } catch (e) {
        this.adapterExists = false;
        setTimeout(this.checkAdapterExists, 10000);
      }
    },

    async fetchMetrics() {
      if (!this.analysis?.project_id) return;
      try {
        const response = await axios.get(`http://localhost:5000/train_metrics/${this.analysis.project_id}`);
        this.metrics = response.data;
      } catch (e) {
        console.error('Error fetching metrics:', e);
      }
    },

    async startTraining() {
  if (!this.analysis?.project_id) return;
  this.isTraining = true;
  this.trainingLog = "";

  const eventSource = new EventSource(`http://localhost:5000/train_stream/${this.analysis.project_id}?model_name=${this.analysis.suggested_model}&mode=${this.analysis.recommendation.toLowerCase()}`);
  this.eventSource = eventSource;

  eventSource.onmessage = (event) => {
    this.trainingLog += event.data + "\n";
    this.$nextTick(() => {
      const logBox = document.querySelector(".log-box");
      logBox.scrollTop = logBox.scrollHeight;
    });
  };

  eventSource.onerror = (err) => {
    console.error("Error en el stream:", err);
    eventSource.close();
  };

  if (this.metricsInterval) clearInterval(this.metricsInterval);
  this.fetchMetrics();
  this.metricsInterval = setInterval(this.fetchMetrics, 5000);
}
,
    async stopTraining() {
      if (!this.analysis?.project_id) return;
      try {
        await axios.post('http://localhost:5000/stop_train', {
          project_id: this.analysis.project_id
        });
        if (this.eventSource) {
          this.eventSource.close();
        }
        this.isTraining = false;
      } catch (err) {
        console.error('Error al detener el entrenamiento:', err);
        this.error = err.response?.data?.error || err.message;
      }
      if (this.metricsInterval) {
        clearInterval(this.metricsInterval);
        this.metricsInterval = null;
      }
      this.isTraining = false;
    },
    downloadAdapter() {
      window.location.href = `http://localhost:5000/download_adapter/${this.analysis.project_id}`;
    }
  },
  beforeUnmount() {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }
    if (this.eventSource) this.eventSource.close();
  }
};
</script>
