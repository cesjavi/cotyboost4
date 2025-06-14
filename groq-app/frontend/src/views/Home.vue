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
      <button @click="downloadDataset">Descargar dataset</button>

      <h3>Entrenamiento</h3>
      <select v-model="modelName">
        <option value="codellama/CodeLlama-7b-hf">CodeLlama 7B</option>
        <option value="meta-llama/Meta-Llama-3-8B-Instruct">LLaMA3 8B</option>
      </select>
      <select v-model="mode">
        <option value="lora">LoRA</option>
        <option value="qlora">QLoRA</option>
      </select>
      <button @click="autoTrain" :disabled="training">Entrenar</button>
      <pre>{{ trainResult }}</pre>

      <h4>Log en vivo</h4>
      <pre style="background:#000; color:#0f0; max-height:400px; overflow:auto;">
{{ liveLog }}
      </pre>
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

function startLogStream() {
  if (!analysis.value?.project_id) return
  logInterval = setInterval(async () => {
    const res = await fetch(`/api/log/${analysis.value.project_id}`)
    const data = await res.json()
    liveLog.value = data.log
  }, 3000)
}

async function autoTrain() {
  if (!analysis.value?.project_id) {
    trainResult.value = "❌ No hay análisis cargado."
    return
  }

  training.value = true
  trainResult.value = "⏳ Iniciando entrenamiento..."
  startLogStream()

  const res = await fetch(`/auto_train/${analysis.value.project_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_name: modelName.value,
      mode: mode.value
    })
  })

  const data = await res.json()
  trainResult.value = JSON.stringify(data, null, 2)
  training.value = false
}
</script>
