import os
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    Trainer, TrainingArguments, BitsAndBytesConfig,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import json
import argparse

# Limpia la memoria CUDA antes de iniciar
torch.cuda.empty_cache()

# === Argumentos ===
parser = argparse.ArgumentParser()
parser.add_argument("--model_name", required=True)
parser.add_argument("--mode", required=True, choices=["lora", "qlora"])
parser.add_argument("--dataset_path", required=True)
parser.add_argument("--output_dir", required=True)
args = parser.parse_args()

print("🔁 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# === Modelo ===
if args.mode == "qlora":
    print("🧠 Loading model in 4-bit mode (QLoRA)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=bnb_config,
        device_map="auto"
    )
    model = prepare_model_for_kbit_training(model)
else:
    print("🧠 Loading model in standard mode (LoRA)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

print("🎛️ Injecting LoRA adapters...")
# Elige target_modules según el modelo
if "codegen" in args.model_name.lower():
    target_modules = [f"transformer.h.{i}.attn.qkv_proj" for i in range(32)] + \
                     [f"transformer.h.{i}.attn.out_proj" for i in range(32)]
elif "llama" in args.model_name.lower() or "mistral" in args.model_name.lower():
    target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
elif "falcon" in args.model_name.lower():
    target_modules = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]
else:
    target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]

lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=target_modules,
    lora_dropout=0.1,#0.1,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

print("📚 Loading and tokenizing dataset...")
with open(args.dataset_path, "r") as f:
    raw_data = json.load(f)
dataset = Dataset.from_list(raw_data)

def format_prompt(example):
    return tokenizer(
        f"### Instruction:\n{example['instruction']}\n### Input:\n{example['input']}\n### Response:\n{example['output']}",
        truncation=True,
        padding="max_length",
        max_length=256
    )

tokenized = dataset.map(format_prompt)
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

print("🚀 Starting training...")
training_args = TrainingArguments(
    output_dir=args.output_dir,
    per_device_train_batch_size=1,#1,
    num_train_epochs=1,
    logging_steps=10,
    save_strategy="no",
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=data_collator
)
trainer.train()

print("💾 Saving adapter...")
os.makedirs(args.output_dir, exist_ok=True)
model.save_pretrained(args.output_dir)
print("✅ Training finished. Adapter saved at:", args.output_dir)
