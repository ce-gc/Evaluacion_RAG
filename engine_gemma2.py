from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from huggingface_hub import login

import os
from dotenv import load_dotenv

# Cargamos variables de entorno si existe un archivo .env
load_dotenv()

# Intentamos obtener el token de las variables de entorno
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    login(token=HF_TOKEN)
else:
    print("Aviso: No se ha detectado HF_TOKEN en las variables de entorno.")

MODEL_ID = "google/gemma-2-2b-it"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Cargando modelo en {device}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    dtype=torch.bfloat16 if device == "cuda" else torch.float32,
    device_map="auto"
)

def predict(text: str) -> str:
    messages = [{"role": "user", "content": text}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=350, # Aumentado para que no se corte el JSON
            do_sample=False,    
            repetition_penalty=1.1
        )
    
    # Obtener solo los tokens generados (ignorando el prompt)
    new_tokens = outputs[0][inputs['input_ids'].shape[-1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True)
    return response.strip()