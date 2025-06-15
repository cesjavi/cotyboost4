import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, BitsAndBytesConfig
from transformers import DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset, Dataset
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--model_name", required=True)
parser.add_argument("--mode", required=True, choices=["lora", "qlora"])
parser.add_argument("--dataset_path", required=True)
parser.add_argument("--output_dir", required=True)
args = parser.parse_args()

print("🔁 Cargando tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

print("🧠 Cargando modelo base en 4-bit...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=(args.mode == "qlora"),
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    args.model_name,
    quantization_config=bnb_config,
    device_map="auto"
)

print("🎛️ Preparando modelo...")
model = prepare_model_for_kbit_training(model)
"""lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)"""
from peft import LoraConfig, get_peft_model

# Listado de los módulos correctos
target_modules = [f"transformer.h.{i}.attn.qkv_proj" for i in range(32)] + \
                 [f"transformer.h.{i}.attn.out_proj" for i in range(32)]

# Configuración de LoRA
lora_config = LoraConfig(
    task_type="CAUSAL_LM",
    target_modules=target_modules,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1
)

# Inyección de LoRA en el modelo
model = get_peft_model(model, lora_config)


print("📚 Cargando dataset...")
with open(args.dataset_path, "r") as f:
    raw_data = json.load(f)
dataset = Dataset.from_list(raw_data)

def tokenize(example):
    return tokenizer(
        f"### Instrucción:\n{example['instruction']}\n### Entrada:\n{example['input']}\n### Respuesta:\n{example['output']}",
        truncation=True,
        padding="max_length",
        max_length=512
    )

tokenized = dataset.map(tokenize)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

print("🚀 Entrenando modelo...")
training_args = TrainingArguments(
    output_dir=args.output_dir,
    per_device_train_batch_size=1,
    num_train_epochs=1,
    logging_steps=10,
    save_strategy="no",
    report_to="all",
    logging_dir='./training_logs',
    logging_strategy='steps'
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator
)

trainer.train()

print("💾 Guardando adaptador...")
os.makedirs(args.output_dir, exist_ok=True)
model.save_pretrained(args.output_dir)

print("✅ Finalizado. Adaptador guardado en:", args.output_dir)
