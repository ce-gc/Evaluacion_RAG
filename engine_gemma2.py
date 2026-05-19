"""Engine adapter para `gemma2:2b`.

Preferencia por Ollama local (http://127.0.0.1:11434). Si Ollama no responde,
intenta un fallback a Hugging Face (solo si está disponible). El objetivo es
que `predict(text)` devuelva un `str` con la respuesta generada.
"""

import os
import json
import requests
import subprocess
import shlex
from typing import Optional

# Host y modelo por defecto para Ollama (el usuario indicó tenerlo local)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")


def _parse_ollama_stream(resp) -> str:
    """Parsea respuestas en streaming de Ollama (si las hay)."""
    out_parts = []
    try:
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            payload = line
            if payload.startswith("data: "):
                payload = payload[len("data: "):]
            try:
                j = json.loads(payload)
            except Exception:
                out_parts.append(payload)
                continue
            # Extraer texto de distintos formatos posibles
            txt = None
            if isinstance(j, dict):
                if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
                    c = j["choices"][0]
                    if isinstance(c, dict):
                        txt = c.get("text") or c.get("content")
                txt = txt or j.get("text") or j.get("content") or j.get("completion")
            if txt:
                out_parts.append(txt)
    except Exception:
        pass
    return "".join(out_parts)


def _call_ollama(prompt: str, max_tokens: int = 350, temperature: float = 0.0) -> Optional[str]:
    """Intenta generar usando la API local de Ollama (HTTP). Devuelve None si falla."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        # Pedimos no-streaming cuando sea posible; algunos servidores igualan.
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
    except Exception as e:
        # No hay servidor Ollama disponible en el host indicado
        print(f"Ollama HTTP request failed: {e}")
        return None

    if resp.status_code == 200:
        # Intentar parsear JSON con distintos formatos
        try:
            data = resp.json()
            if isinstance(data, dict):
                if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                    return (data["choices"][0].get("text") or data["choices"][0].get("content") or "").strip()
                if "text" in data:
                    return str(data["text"]).strip()
                if "content" in data:
                    return str(data["content"]).strip()
                if "completion" in data:
                    return str(data["completion"]).strip()
        except ValueError:
            # No JSON; caeremos a texto plano
            pass
        return resp.text.strip()

    # Si status != 200, intentar lectura en streaming (algunos endpoints usan stream)
    try:
        resp = requests.post(url, json=payload, stream=True, timeout=60)
        return _parse_ollama_stream(resp).strip() or None
    except Exception:
        return None


def _call_ollama_cli(prompt: str) -> Optional[str]:
    """Intento alternativo usando la CLI `ollama` si está disponible en PATH.
    Prueba varios subcomandos conocidos; no es garantizado en todas las versiones.
    """
    candidates = [
        ["ollama", "query", OLLAMA_MODEL, prompt],
        ["ollama", "generate", OLLAMA_MODEL, prompt],
        ["ollama", "run", OLLAMA_MODEL, "--prompt", prompt],
    ]
    for cmd in candidates:
        try:
            # `subprocess.run` con shell=False; el prompt pasa como argumento final
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
            out = proc.stdout.strip()
            if out:
                return out
        except Exception:
            continue
    return None


_hf_tokenizer = None
_hf_model = None


def _hf_predict(prompt: str) -> Optional[str]:
    """Fallback a Hugging Face si Ollama no está disponible; carga perezosa.
    Solo se usa si las librerías están instaladas y el usuario lo desea.
    """
    global _hf_tokenizer, _hf_model
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from huggingface_hub import login
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
    except Exception as e:
        print(f"HF fallback no disponible (librerías faltantes): {e}")
        return None

    HF_TOKEN = os.getenv("HF_TOKEN")
    if HF_TOKEN:
        try:
            login(token=HF_TOKEN)
        except Exception:
            pass

    MODEL_ID = os.getenv("HF_MODEL_ID", "google/gemma-2-2b-it")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        if _hf_tokenizer is None or _hf_model is None:
            print(f"Cargando modelo HF {MODEL_ID} en {device} (fallback)...")
            _hf_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
            _hf_model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto")

        # Mantener API similar a la implementación previa
        messages = [{"role": "user", "content": prompt}]
        try:
            chat_prompt = _hf_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            chat_prompt = prompt

        inputs = _hf_tokenizer(chat_prompt, return_tensors="pt").to(_hf_model.device)
        with torch.no_grad():
            outputs = _hf_model.generate(**inputs, max_new_tokens=350, do_sample=False, repetition_penalty=1.1)
        new_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
        response = _hf_tokenizer.decode(new_tokens, skip_special_tokens=True)
        return response.strip()
    except Exception as e:
        print(f"Error en HF fallback: {e}")
        return None


def predict(text: str) -> str:
    """Interfaz única `predict(text) -> str` usada por el resto del repo.

    Intenta en orden:
    1. Ollama HTTP local
    2. Ollama CLI
    3. Hugging Face (si está disponible)
    """
    # 1) Ollama HTTP
    try:
        resp = _call_ollama(text)
        if resp:
            return resp
    except Exception:
        pass

    # 2) Ollama CLI fallback
    try:
        resp = _call_ollama_cli(text)
        if resp:
            return resp
    except Exception:
        pass

    # 3) Hugging Face fallback (perezoso)
    try:
        resp = _hf_predict(text)
        if resp:
            return resp
    except Exception:
        pass

    return "[ERROR] No se pudo generar respuesta: Ollama no disponible y HF fallback falló."