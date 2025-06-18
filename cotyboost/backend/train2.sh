#!/bin/bash

# Entrenamiento QLoRA para proyecto analizado

accelerate launch train_qlora.py \
  --model_name codellama/CodeLlama-7b-hf \
  --mode qlora \
  --dataset_path backend/temp_projects/5b794ac9/dataset.json \
  --output_dir backend/temp_projects/5b794ac9/adapter
