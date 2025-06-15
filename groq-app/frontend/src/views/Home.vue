<template>
  <div class="container">
    <h1>Groq App</h1>

    <section class="process">
      <h2>Analizar proyecto</h2>
      <input v-model="githubUrl" type="text" placeholder="https://github.com/user/repo" />
      <button @click="processProject" :disabled="loading">Procesar</button>
    </section>

    <section v-if="analysis" class="analysis">
      <h2>Resultado</h2>
      <ul>
        <li><strong>Archivos:</strong> {{ analysis.file_count }}</li>
        <li><strong>Líneas:</strong> {{ analysis.total_lines }}</li>
        <li><strong>Tamaño:</strong> {{ analysis.total_size_mb }} MB</li>
        <li><strong>Estrategia:</strong> {{ analysis.recommendation }}</li>
        <li><strong>Modelo sugerido:</strong> {{ analysis.suggested_model }}</li>
      </ul>
      <h3>Preview dataset</h3>
      <pre>{{ JSON.stringify(analysis.dataset_preview, null, 2) }}</pre>
      <pre>{{ analysis.log_preview }}</pre>
      <button @click="downloadDataset">Descargar dataset</button>
    </section>

    <section class="chat">
      <h2>Chat</h2>
      <textarea v-model="prompt" rows="5" />
      <button @click="send">Enviar</button>
      <pre>{{ result }}</pre>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const prompt = ref('')
const result = ref('')
const githubUrl = ref('')
const analysis = ref(null)
const loading = ref(false)

const modelName = ref('codellama/CodeLlama-7b-hf')
const mode = ref('lora')
const training = ref(false)
const trainResult = ref('')
const liveLog = ref('')
let logInterval = null

async function send() {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: prompt.value })
  })
  result.value = await res.json()
}

async function processProject() {
  loading.value = true
  analysis.value = null
  const res = await fetch('/api/process_project/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ github_url: githubUrl.value })
  })
  analysis.value = await res.json()
  loading.value = false
}

function downloadDataset() {
  if (analysis.value?.project_id) {
    window.location.href = `/api/download_dataset/${analysis.value.project_id}`
  }
}
</script>
