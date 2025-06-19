from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("codellama/CodeLlama-7b-hf")
print(model)

