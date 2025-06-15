# groq-app/backend/utils/lora_trainer.py
import argparse
import json
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from datasets import load_dataset, Dataset
from peft import get_peft_model, LoraConfig, TaskType, prepare_model_for_kbit_training
import torch
import os

def load_json_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    inputs = [f"{ex['instruction']}\n\n{ex['input']}" for ex in data]
    outputs = [ex['output'] for ex in data]
    return Dataset.from_dict({"text": [f"{i}\n{o}" for i, o in zip(inputs, outputs)]})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--dataset_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--mode", type=str, choices=["lora", "qlora"], default="lora")
    args = parser.parse_args()

    print(f"📚 Cargando modelo {args.model_name} en modo {args.mode}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    dataset = load_json_dataset(args.dataset_path)

    def tokenize(example):
        return tokenizer(example["text"], truncation=True, padding="max_length", max_length=512)

    dataset = dataset.map(tokenize)

    model_kwargs = {"trust_remote_code": True}

    if args.mode == "qlora":
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

    model = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)

    if args.mode in ["lora", "qlora"]:
        model = prepare_model_for_kbit_training(model)
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none"
        )
        model = get_peft_model(model, peft_config)

    training_args = TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_dir=os.path.join(args.output_dir, "logs"),
        logging_steps=10,
        output_dir=args.output_dir,
        save_total_limit=1,
        save_strategy="epoch",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
    )

    print("🚀 Entrenando modelo...")
    trainer.train()
    model.save_pretrained(args.output_dir)
    print("✅ Entrenamiento finalizado.")

if __name__ == "__main__":
    main()
