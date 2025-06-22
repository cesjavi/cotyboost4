# CotyBoost Projects

Este repositorio agrupa dos aplicaciones independientes:

1. **cotyboost/** – Plataforma principal para el análisis de código y entrenamiento de modelos.
2. **groq-app/** – Versión para el challenge de Groq con integración específica.

A continuación se resumen los pasos básicos para ejecutar cada una.

## Ejecución rápida

### Frontend renovado

Cada aplicación incluye ahora un nuevo estilo. Desde la carpeta
`frontend` ejecute `npm install` para obtener las dependencias y luego
`npm run dev` para probar la interfaz mejorada.

### CotyBoost

```bash
# Backend
cd cotyboost/backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r ../requirements.txt
python app.py
```

En otra terminal inicie el frontend:

```bash
cd cotyboost/frontend
npm install
npm run dev
```

### Groq-app

Antes de comenzar exporte la clave de API de Groq:

```bash
export GROQ_API_KEY="TU_CLAVE"
```

Ejecute el backend y frontend por separado:

```bash
cd groq-app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

```bash
cd ../frontend
npm install
npm run dev
```

Para más detalles consulte los README dentro de cada carpeta.
