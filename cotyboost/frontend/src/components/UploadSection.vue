<template>
  <section class="upload-section">
    <h2>1. Subir ZIP o ingresar GitHub</h2>
    <input type="file" @change="onFileChange" accept=".zip" />
    <p>o</p>
    <input
      type="text"
      v-model="githubUrlProxy"
      placeholder="https://github.com/usuario/proyecto"
    />
    <button @click="$emit('process-project')" :disabled="isProcessing">
      <span v-if="isProcessing" class="loading">Procesando...</span>
      <span v-else>Subir y Analizar</span>
    </button>
  </section>
</template>

<script>
export default {
  name: 'UploadSection',
  props: {
    isProcessing: Boolean,
    githubUrl: String
  },
  emits: ['file-selected', 'update:githubUrl', 'process-project'],
  computed: {
    githubUrlProxy: {
      get() {
        return this.githubUrl;
      },
      set(value) {
        this.$emit('update:githubUrl', value);
      }
    }
  },
  methods: {
    onFileChange(event) {
      this.$emit('file-selected', event);
    }
  }
};
</script>

<style scoped>
.upload-section {
  margin-bottom: 24px;
  background: #232936;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 2px 6px #0005;
  display: flex;
  flex-direction: column;
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
  .upload-section {
    padding: 16px;
  }
}
</style>
