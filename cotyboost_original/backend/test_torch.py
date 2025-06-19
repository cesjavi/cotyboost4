import torch

if torch.cuda.is_available():
    print("CUDA está disponible")
    print("Nombre del dispositivo:", torch.cuda.get_device_name(0))
else:
    print("CUDA NO está disponible")
