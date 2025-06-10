<template>
  <div>
    <h1>Asistente LLaMA</h1>
    <textarea v-model="prompt" rows="5" />
    <button @click="send">Enviar</button>
    <pre>{{ result }}</pre>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const prompt = ref('')
const result = ref('')

async function send() {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: prompt.value })
  })
  result.value = await res.json()
}
</script>
