import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY environment variable not set")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

def send_prompt(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Sos un asistente técnico."},
            {"role": "user", "content": prompt}
        ]
    }
    res = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)
    return res.json()
