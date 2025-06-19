<template>
  <div class="generate-form">
    <h2>🤖 Generar Texto con el Adaptador</h2>
    
    <textarea 
      v-model="prompt" 
      placeholder="Escribe tu prompt aquí..." 
      rows="4">
    </textarea>

    <button @click="generateText" :disabled="isLoading">
      Generar
    </button>

    <div v-if="isLoading" class="loading">
      🔄 Generando respuesta...
    </div>

    <div v-if="response" class="response">
      <h3>📝 Respuesta:</h3>
      <pre>{{ response }}</pre>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: ["projectId"],
  data() {
    return {
      prompt: "",
      response: null,
      isLoading: false
    };
  },
  methods: {
    async generateText() {
      this.isLoading = true;
      try {
        const result = await axios.post("http://localhost:5000/generate_text", {
          prompt: this.prompt,
          project_id: this.projectId,
          max_length: 200
        });
        this.response = result.data.response;
      } catch (err) {
        console.error("Error en la inferencia:", err.message);
      } finally {
        this.isLoading = false;
      }
    }
  }
};
</script>
