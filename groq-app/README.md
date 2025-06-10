# Proyecto Groq + LLaMA

Este proyecto cumple con los requerimientos del challenge de Groq:  
✅ Integración con la API de Groq  
✅ Uso de modelos LLaMA (`llama3-8b-8192`)

---

## 📦 Estructura

groq_app/
├── backend/ # Flask API
│ ├── app.py
│ ├── groq_api.py
│ ├── backup.py
│ └── requirements.txt
│
├── frontend/ # Vue 3 + Vite
│ ├── index.html
│ ├── vite.config.js
│ ├── package.json
│ └── src/
│ ├── main.js
│ └── views/
│ └── Home.vue
│
├── start.sh
└── README.md


---

## 🚀 Instrucciones de uso

### 1. Clave de API Groq
Registrate en [https://console.groq.com](https://console.groq.com)  
Obtené tu clave de API y reemplazá `"TU_CLAVE"` en `backend/groq_api.py`:

```python
GROQ_API_KEY = "TU_CLAVE"
```

### 2. Backend (Python + Flask)

cd backend
python -m venv venv
source venv/bin/activate  # o venv\\Scripts\\activate en Windows
pip install -r requirements.txt
python app.py
Se levantará en: http://localhost:5000

3. Frontend (Vue + Vite)

cd frontend
npm install
npm run dev
Se abrirá en: http://localhost:5173

🧠 Uso
Escribí un mensaje en el textarea.

Se envía a la API de Groq usando el modelo llama3-8b-8192.

El backend Flask hace la llamada y devuelve la respuesta.

Vue muestra el resultado en pantalla.

💾 Backup
Para crear un backup comprimido del backend:


python backend/backup.py
Esto genera un ZIP en la carpeta backend/backups.

🧠 Modelo usado
Modelo: llama3-8b-8192
Endpoint: https://api.groq.com/openai/v1/chat/completions
