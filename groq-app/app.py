from flask import Flask, request, jsonify
from backend.groq_api import send_prompt

app = Flask(__name__)

@app.route("/api/chat", methods=["POST"])
def chat():
    prompt = request.json.get("prompt", "")
    response = send_prompt(prompt)
    return jsonify(response)

