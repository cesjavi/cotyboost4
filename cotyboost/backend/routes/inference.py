from flask import Blueprint, jsonify, request
import os
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMP_ROOT = os.path.join(BASE_DIR, "temp_projects")

inference_bp = Blueprint('inference', __name__)

# Cache for loaded models/tokenizers per project
INFERENCE_SESSIONS = {}


@inference_bp.route('/list_projects', methods=['GET'])
def list_projects():
    """Return available processed projects."""
    projects = []
    if os.path.exists(TEMP_ROOT):
        for d in os.listdir(TEMP_ROOT):
            folder = os.path.join(TEMP_ROOT, d)
            if os.path.isdir(folder):
                analysis_path = os.path.join(folder, 'analysis.json')
                if os.path.exists(analysis_path):
                    with open(analysis_path, 'r') as f:
                        analysis = json.load(f)
                    projects.append({
                        'id': d,
                        'name': analysis.get('project_name', d),
                        'model': analysis.get('suggested_model', '')
                    })
                else:
                    projects.append({'id': d, 'name': d, 'model': ''})
    return jsonify({'projects': projects})


def load_inference_model(project_id):
    """Load and cache tokenizer and model for a project."""
    if project_id not in INFERENCE_SESSIONS:
        adapter_path = os.path.join(TEMP_ROOT, project_id, 'adapter')
        analysis_path = os.path.join(TEMP_ROOT, project_id, 'analysis.json')
        model_name = 'Salesforce/codegen-6B-mono'
        if os.path.exists(analysis_path):
            with open(analysis_path) as f:
                analysis = json.load(f)
                model_name = analysis.get('suggested_model', model_name)

        offload_dir = os.path.join(TEMP_ROOT, project_id, 'offload')
        os.makedirs(offload_dir, exist_ok=True)

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map='auto',
            offload_folder=offload_dir,
            low_cpu_mem_usage=True,
        )

        model = PeftModel.from_pretrained(model, adapter_path)
        model.eval()
        INFERENCE_SESSIONS[project_id] = {'tokenizer': tokenizer, 'model': model}
    return INFERENCE_SESSIONS[project_id]


@inference_bp.route('/inference', methods=['POST'])
def inference():
    project_id = request.json.get('project_id')
    prompt = request.json.get('prompt')
    max_new_tokens = request.json.get('max_new_tokens', 256)

    if not project_id or not prompt:
        return jsonify({'error': 'Missing parameters'}), 400
    try:
        session = load_inference_model(project_id)
        tokenizer = session['tokenizer']
        model = session['model']

        inputs = tokenizer(
            prompt,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=2048
        ).to(model.device)

        outputs = model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.95,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({'result': response_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

