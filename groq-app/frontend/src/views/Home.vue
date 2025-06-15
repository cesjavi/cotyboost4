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
      <div class="train-block">
        <label>
          Modelo:
          <select v-model="modelName">
            <option value="codellama/CodeLlama-7b-hf">codellama/CodeLlama-7b-hf</option>
            <option value="TinyLlama/TinyLlama-1.1B-Chat-v1.0">TinyLlama/TinyLlama-1.1B-Chat-v1.0</option>
          </select>
        </label>
        <label>
          Modo:
          <select v-model="mode">
            <option value="lora">lora</option>
            <option value="full">full</option>
          </select>
        </label>
        <button @click="completeDataset" :disabled="loading || training">Completar dataset</button>
        <button @click="startTraining" :disabled="loading || training">Entrenar</button>
        <button @click="downloadAdapter" :disabled="loading || training">Descargar adapter</button>
        <button @click="downloadLog" :disabled="loading || training">Descargar log</button>
        <p>Última modificación: {{ lastModified }}</p>
        <pre>{{ liveLog }}</pre>
      </div>
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
const lastModified = ref('')

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

async function completeDataset() {
  if (!analysis.value?.project_id) return
  loading.value = true
  const res = await fetch(`/api/complete_dataset/${analysis.value.project_id}`, {
    method: 'POST'
  })
  trainResult.value = JSON.stringify(await res.json(), null, 2)
  loading.value = false
}

async function startTraining() {
  if (!analysis.value?.project_id) return
  training.value = true
  liveLog.value = ''
  trainResult.value = ''
  if (logInterval) clearInterval(logInterval)
  logInterval = setInterval(fetchLog, 2000)
  const res = await fetch(`/api/auto_train/${analysis.value.project_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_name: modelName.value, mode: mode.value })
  })
  const data = await res.json()
  trainResult.value = data.message || ''
  if (data.status === 'ok') {
    clearInterval(logInterval)
    logInterval = null
    training.value = false
  }
}

async function downloadAdapter() {
  if (analysis.value?.project_id) {
    window.location.href = `/api/download_adapter/${analysis.value.project_id}`
    if (logInterval) {
      clearInterval(logInterval)
      logInterval = null
    }
    training.value = false
  }
}

function downloadLog() {
  if (analysis.value?.project_id) {
    window.location.href = `/api/download_log/${analysis.value.project_id}`
  }
}

async function fetchLog() {
  if (!analysis.value?.project_id) return
  const res = await fetch(`/api/log/${analysis.value.project_id}`)
  const data = await res.json()
  liveLog.value = data.log
  lastModified.value = data.last_modified
}
</script>