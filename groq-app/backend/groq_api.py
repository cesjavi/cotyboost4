import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY environment variable not set")

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def send_prompt(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Sos un asistente técnico."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()

        # Verificar estructura esperada
        if "choices" in data and len(data["choices"]) > 0:
            return data
        else:
            return {"error": "Respuesta sin 'choices':", "raw": data}

    except requests.RequestException as e:
        return {"error": f"Error de red o HTTP: {str(e)}"}
    except Exception as e:
        return {"error": f"Error inesperado: {str(e)}"}
