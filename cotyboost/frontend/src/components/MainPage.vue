<template>
  <div class="container">
    <h1>MyQLoraApp</h1>
    <div class="tabs">
      <button :class="{active: activeTab==='train'}" @click="activeTab='train'">Entrenamiento</button>
      <button :class="{active: activeTab==='inference'}" @click="activateInferenceTab">Inferencia</button>
    </div>

    <UploadSection
      v-if="activeTab==='train'"
      :is-processing="isProcessing"
      v-model:github-url="githubUrl"
      @file-selected="handleFile"
      @process-project="processProject"
    />

    <TrainingControls
      v-if="activeTab==='train' && analysis"
      :analysis="analysis"
      :is-training="isTraining"
      :adapter-exists="adapterExists"
      :training-command="trainingCommand"
      :training-log="trainingLog"
      :metrics="metrics"
      @start-training="startTraining"
      @stop-training="stopTraining"
      @copy-command="copyCommand"
      @download-command="downloadCommand"
      @download-dataset="downloadDataset"
      @download-adapter="downloadAdapter"
    />

    <InferencePanel
      v-if="activeTab==='inference'"
      :projects="projects"
      v-model:selected-project="selectedProject"
      v-model:inference-prompt="inferencePrompt"
      :inference-result="inferenceResult"
      :is-inferencing="isInferencing"
      @run-inference="runInference"
    />

    <div v-if="error" class="error">⚠️ Error: {{ error }}</div>
  </div>
</template>

<script>
import axios from 'axios';
import UploadSection from './UploadSection.vue';
import TrainingControls from './TrainingControls.vue';
import InferencePanel from './InferencePanel.vue';

export default {
  name: 'MainPage',
  components: { UploadSection, TrainingControls, InferencePanel },
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
      activeTab: 'train',
      projects: [],
      selectedProject: '',
      inferencePrompt: '',
      inferenceResult: '',
      isInferencing: false
    };
  },
  computed: {
    trainingCommand() {
      if (!this.analysis) return '';
      const model = this.analysis.suggested_model;
      const mode = this.analysis.recommendation.toLowerCase();
      const projectId = this.analysis.project_id || 'PROYECTO_ID';
      const path = `backend/temp_projects/${projectId}/dataset.json`;
      const output = `backend/temp_projects/${projectId}/adapter`;
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

    activateInferenceTab() {
      this.activeTab = 'inference';
      this.loadProjects();
    },

    async loadProjects() {
      try {
        const response = await axios.get('http://localhost:5000/list_projects');
        this.projects = response.data.projects;
      } catch (e) {
        console.error('Error fetching projects:', e);
      }
    },

    async runInference() {
      if (!this.selectedProject || !this.inferencePrompt) return;
      this.isInferencing = true;
      try {
        const resp = await axios.post('http://localhost:5000/inference', {
          project_id: this.selectedProject,
          prompt: this.inferencePrompt
        });
        this.inferenceResult = resp.data.result;
      } catch (e) {
        this.error = e.response?.data?.error || e.message;
      } finally {
        this.isInferencing = false;
      }
    },

    copyCommand() {
      if (!this.trainingCommand) return;
      navigator.clipboard.writeText(this.trainingCommand);
    },

    downloadCommand() {
      if (!this.trainingCommand) return;
      const blob = new Blob([this.trainingCommand], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'train.sh';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },

    downloadDataset() {
      if (!this.analysis?.project_id) return;
      window.location.href = `http://localhost:5000/download_dataset/${this.analysis.project_id}`;
    },

    async startTraining() {
      if (!this.analysis?.project_id) return;
      this.trainingLog = "";
      this.error = null; // Clear previous errors

      try {
        // Make the POST request to /train
        await axios.post('http://localhost:5000/train', {
          project_id: this.analysis.project_id,
          model_name: this.analysis.suggested_model,
          mode: this.analysis.recommendation.toLowerCase()
        });

        // If the request is successful, set isTraining to true and initialize EventSource
        this.isTraining = true;

        const eventSource = new EventSource(`http://localhost:5000/train_stream/${this.analysis.project_id}?model_name=${this.analysis.suggested_model}&mode=${this.analysis.recommendation.toLowerCase()}`);
        this.eventSource = eventSource;

        eventSource.onmessage = (event) => {
          this.trainingLog += event.data + "\n";
          this.$nextTick(() => {
            const logBox = document.querySelector(".log-box");
            if (logBox) { // Ensure logBox exists
              logBox.scrollTop = logBox.scrollHeight;
            }
          });
        };

        eventSource.onerror = (err) => {
          console.error("Error en el stream:", err);
          this.error = "Error en la conexión de logs. El entrenamiento podría continuar en backend.";
          // Consider setting isTraining to false if the error indicates a total failure
          // For now, we'll keep it true as the training might be running in the backend
          // but if it's a persistent error, the user might need to stop it.
          // A more robust solution would be to check the type of error.
          // this.isTraining = false; // Uncomment if SSE failure should stop showing "training"
          eventSource.close();
        };

        if (this.metricsInterval) clearInterval(this.metricsInterval);
        this.fetchMetrics(); // Fetch initial metrics
        this.metricsInterval = setInterval(this.fetchMetrics, 5000);

      } catch (err) {
        console.error('Error al iniciar el entrenamiento:', err);
        this.error = `Error al iniciar el entrenamiento: ${err.response?.data?.error || err.message}`;
        this.isTraining = false; // Ensure isTraining is false if the /train call fails
      }
    },
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
    display: flex;
    flex-direction: column;
  }

  .tabs {
    margin-bottom: 24px;
    display: flex;
    flex-wrap: wrap;
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

  .error {
    color: #ff7979;
    background: #291819;
    padding: 10px;
    border-radius: 6px;
    margin-top: 16px;
  }

  @media (max-width: 600px) {
    .container {
      padding: 12px;
      margin: 10px;
    }
  }
  </style>
