# CotyBoost

Plataforma para analizar proyectos de código, generar datasets y entrenar modelos LLM usando LoRA/QLoRA desde ZIPs o repositorios GitHub.

---

## 📁 Estructura

```
cotyboost/
├── backend/
│   ├── app.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── process_project.py  # Define el endpoint POST /process_project/
│   └── utils/
│       ├── __init__.py
│       └── analyzer.py  # Analiza el código fuente
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       └── components/
│           └── MainPage.vue  # UI completa con subida, análisis, entrenamiento, inferencia
```

---

## 🚀 Cómo correr

### 🔧 Backend (Flask + Transformers)

```bash
cd cotyboost/backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install flask flask-cors transformers peft datasets accelerate bitsandbytes
python app.py
```

> Asegurate de tener CUDA si usás GPU (recomendado para entrenamiento/inferencia).

### 🖥️ Frontend (Vue 3 + Vite)

```bash
cd cotyboost/frontend
npm install
npm run dev
```

Abrir `http://localhost:5173` en el navegador.

---

## 🔄 Flujo

1. Subir un ZIP o ingresar URL de GitHub
2. Analizar código fuente
3. Generar dataset
4. Entrenar modelo (LoRA o QLoRA sugerido)
5. Realizar inferencia
6. Descargar adaptador `.bin`
7. Integrar el adaptador en una extensión de VS Code para obtener asistencia en tiempo real.

## Diagrama conceptual

```
┌───────────────────────────────────────────┐
│              Usuario final                │
└───────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────┐
│    Subida de ZIP o URL de GitHub         │
│  (/process_project en backend Flask)     │
└───────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────┐
│    Análisis del código fuente            │
│  (utils/analyzer.py y rutas en Flask)    │
└───────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────┐
│  Generación automática de dataset         │
└───────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────┐
│      Entrenamiento LoRA/QLoRA             │
│  (train_qlora.py con accelerate)          │
└───────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────┐
│  Adaptador resultante (.bin)              │
└───────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────┐
│ Extensión de VS Code                      │
│ Utiliza el adaptador para asistencia      │
└───────────────────────────────────────────┘
```

---

## 🛠 Requisitos

- Python ≥ 3.10
- Node.js ≥ 18
- `nvm`, `git`, `CUDA` (para GPU)
- 20+ GB libres en disco para modelos grandes

---

## ✍️ Autor

CotyBoost - Proyecto de entrenamiento de modelos personalizados sobre código fuente.
