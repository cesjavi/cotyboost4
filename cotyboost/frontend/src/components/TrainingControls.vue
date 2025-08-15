<template>
  <section class="result-section">
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
      <button @click="$emit('start-training')" :disabled="isTraining">Entrenar Modelo</button>
      <button @click="$emit('stop-training')" :disabled="!isTraining">Detener Entrenamiento</button>
      <p v-if="isTraining" class="loading">🧠 Entrenamiento en curso...</p>
    </div>

    <div class="command-box">
      <h3>📜 Comando sugerido:</h3>
      <pre>{{ trainingCommand }}</pre>
      <button @click="$emit('copy-command')">📋 Copiar comando</button>
      <button @click="$emit('download-command')">⬇️ Descargar train.sh</button>
      <button @click="$emit('download-dataset')">📁 Descargar dataset.json</button>
      <button v-if="adapterExists" @click="$emit('download-adapter')">📦 Descargar adaptador LoRA</button>
      <p v-else class="adapter-pending">Adaptador aún no generado.</p>
    </div>

    <section v-if="isTraining" class="log-section">
      <h2>📝 Logs de Entrenamiento en Tiempo Real:</h2>
      <div class="log-box">
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
</template>

<script>
export default {
  name: 'TrainingControls',
  props: {
    analysis: Object,
    isTraining: Boolean,
    adapterExists: Boolean,
    trainingCommand: String,
    trainingLog: String,
    metrics: Object
  },
  emits: [
    'start-training',
    'stop-training',
    'copy-command',
    'download-command',
    'download-dataset',
    'download-adapter'
  ]
};
</script>

<style scoped>
.result-section {
  margin-bottom: 24px;
  background: #232936;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 2px 6px #0005;
}

.actions {
  margin-top: 12px;
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

.command-box pre,
.log-box pre {
  background: #1a1e25;
  color: #aaf;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.log-box {
  max-height: 300px;
  overflow-y: auto;
}

.adapter-pending {
  color: gray;
}


.loading {
  display: inline-block;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

@media (max-width: 600px) {
  .result-section {
    padding: 16px;
  }
}
</style>
