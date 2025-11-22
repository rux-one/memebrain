from transformers import AutoModelForCausalLM
from PIL import Image
import os
import string
import torch

def cleanup_filename(filename):
    allowed_chars = string.ascii_letters + string.digits + "_"
    sanitized = ''.join(c if c in allowed_chars else '_' for c in filename)
    
    return sanitized.strip('_').lower()

# Load the model
model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    trust_remote_code=True,
    dtype=torch.bfloat16,
    device_map="cuda",
)

path = "easy.jpg"
file_extension = os.path.splitext(path)[1]

# Load your image
image = Image.open(path)

# Optionally set sampling settings
settings = {"temperature": 0.25, "max_tokens": 768, "top_p": 0.3}

# Generate a short caption
short_result = model.caption(
    image, 
    length="short", 
    settings=settings
)
print(short_result)

print("---")

filename = model.query(image, "Return a short, single-line, descriptive caption for the following picture. Use minimum words, like it's a filename. Avoid using special characters.")
filename = cleanup_filename(filename["answer"]) + file_extension
print(filename)