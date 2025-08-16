<template>
  <div class="inference-panel">
    <section class="projects-section">
      <h2>Proyectos Procesados</h2>
      <select v-model="selectedProjectProxy">
        <option disabled value="">Selecciona un proyecto</option>
        <option v-for="p in projects" :key="p.id" :value="p.id">
          {{ p.name }} - {{ p.model }}
        </option>
      </select>
    </section>

    <section class="inference-box">
      <textarea
        v-model="inferencePromptProxy"
        placeholder="Ingresa tu prompt"
      ></textarea>
      <button
        @click="$emit('run-inference')"
        :disabled="isInferencing || !selectedProjectProxy || !inferencePromptProxy"
      >
        <span v-if="isInferencing" class="loading">Enviando...</span>
        <span v-else>Enviar</span>
      </button>
      <div v-if="inferenceResult">
        <h3>Respuesta:</h3>
        <pre>{{ inferenceResult }}</pre>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'InferencePanel',
  props: {
    projects: Array,
    selectedProject: String,
    inferencePrompt: String,
    inferenceResult: String,
    isInferencing: Boolean
  },
  emits: ['update:selectedProject', 'update:inferencePrompt', 'run-inference'],
  computed: {
    selectedProjectProxy: {
      get() {
        return this.selectedProject;
      },
      set(val) {
        this.$emit('update:selectedProject', val);
      }
    },
    inferencePromptProxy: {
      get() {
        return this.inferencePrompt;
      },
      set(val) {
        this.$emit('update:inferencePrompt', val);
      }
    }
  }
};
</script>

<style scoped>
.projects-section,
.inference-box {
  margin-bottom: 24px;
  background: #232936;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 2px 6px #0005;
  display: flex;
  flex-direction: column;
}

.projects-section select,
.inference-box textarea {
  margin: 6px 0;
  padding: 8px;
  width: 100%;
  background: #181d23;
  color: #fff;
  border: 1px solid #3b4656;
  border-radius: 6px;
}

button {
  margin-top: 8px;
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

.inference-box pre {
  background: #1a1e25;
  color: #aaf;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
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
  .projects-section,
  .inference-box {
    padding: 16px;
  }
}
</style>
