import torch
import bitsandbytes as bnb

x = torch.randn((2, 2)).to('cuda')
quant = bnb.nn.Linear8bitLt(2, 2).to('cuda')
print(quant(x))
