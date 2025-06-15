# Proyecto Groq + LLaMA

Este proyecto cumple con los requerimientos del challenge de Groq:

✅ Integración con la API de Groq  
✅ Uso de modelos LLaMA (`llama3-8b-8192`)

---

## 📦 Estructura

```
groq_app/
├── backend/       # Flask API
│   ├── app.py
│   ├── groq_api.py
│   ├── backup.py
│   └── requirements.txt
│
├── frontend/      # Vue 3 + Vite
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.js
│       └── views/
│           └── Home.vue
│
├── start.sh
└── README.md
```

---

## 🚀 Instrucciones de uso

### 1. Clave de API Groq

Regístrate en [https://console.groq.com](https://console.groq.com) y exporta la variable de entorno `GROQ_API_KEY`:

```bash
export GROQ_API_KEY="TU_CLAVE"
```

### 2. Backend (Python + Flask)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # en Windows usa venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La API quedará disponible en <http://localhost:5000>

### 3. Frontend (Vue + Vite)

```bash
cd frontend
npm install
npm run dev
```

La aplicación se abrirá en <http://localhost:5173>

---

## 🧠 Uso

1. Escribe un mensaje en el textarea.
2. La petición se envía a la API de Groq usando el modelo `llama3-8b-8192`.
3. El backend Flask devuelve la respuesta y Vue la muestra en pantalla.

## 💾 Backup

Para crear un backup comprimido del backend:

```bash
python backend/backup.py
```

El archivo ZIP se guardará en `backend/backups`.

## 🧠 Modelo usado

Modelo: `llama3-8b-8192`  
Endpoint: <https://api.groq.com/openai/v1/chat/completions>
