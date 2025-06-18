#!/bin/bash
accelerate launch train_qlora.py   --model_name codellama/CodeLlama-7b-hf   --mode qlora   --dataset_path backend/temp_projects/fbedf33a/dataset.json   --output_dir backend/temp_projects/fbedf33a/adapter
