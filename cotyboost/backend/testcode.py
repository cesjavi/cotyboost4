from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-2B-mono")
print("=== Listado de módulos del modelo ===\n")
for name, module in model.named_modules():
    print(name)
