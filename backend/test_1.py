from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import torch

bnb_config = BitsAndBytesConfig(load_in_4bit=True)

base_model = AutoModelForCausalLM.from_pretrained(
    "codellama/CodeLlama-7b-hf",
    quantization_config=bnb_config,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")
model = PeftModel.from_pretrained(base_model, "temp_projects/5b794ac9/adapter")

prompt = "Instrucción: Explica qué hace este código.\
Input:\
import os\
import sys\
root = os.path.dirname(os.path.abspath(__file__)) \
sys.path.append(root)\
os.chdir(root)\
try:\
    import pygit2\
    pygit2.option(pygit2.GIT_OPT_SET_OWNER_VALIDATION, 0)\
    repo = pygit2.Repository(os.path.abspath(os.path.dirname(__file__)))\
    branch_name = repo.head.shorthand\
    remote_name = 'origin'\
    remote = repo.remotes[remote_name]\
"

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

output = model.generate(
    **inputs,
    max_new_tokens=1000,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
    repetition_penalty=1.2
)

print(tokenizer.decode(output[0], skip_special_tokens=True))
