import json
import logging
import os
import uuid

# Configuración de Logging
LOGGER = logging.getLogger("validator")
MODE = os.getenv("MODE", "dev")
level = logging.DEBUG if MODE == "dev" else logging.INFO

# Formato de log que incluye el request_id será manejado manualmente en las funciones
logging.basicConfig(level=level, format="%(levelname)s - %(message)s")

def new_request_id():
    return str(uuid.uuid4())[:8]

def clip(s: str, n: int = 200) -> str:
    if not s: return ""
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"

def validate_output(raw: str, request_id: str):
    """Devuelve (ok: bool, result: dict, error: str|None)."""
    
    if MODE == "dev":
        LOGGER.debug(f"[{request_id}] recibo output: {clip(raw)}")
        LOGGER.debug(f"[{request_id}] intento parsear JSON")

    try:
        # Limpieza agresiva de bloques de código markdown
        clean_raw = raw.strip()
        if "```json" in clean_raw:
            clean_raw = clean_raw.split("```json")[-1].split("```")[0]
        elif "```" in clean_raw:
            # Buscar el par de triple comillas
            parts = clean_raw.split("```")
            if len(parts) >= 3:
                clean_raw = parts[1]
            else:
                clean_raw = parts[-1]

        # Intentar extraer el bloque JSON {...} 
        import re
        match = re.search(r'(\{.*\})', clean_raw, re.DOTALL)
        if match:
            clean_raw = match.group(1)
        
        clean_raw = clean_raw.strip()
        obj = json.loads(clean_raw)
    except Exception as e:
        err_msg = f"json_parse_error: {e}"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    # 1) estructura base
    if not isinstance(obj, dict):
        err_msg = "not_a_dict"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    if "ok" not in obj or "data" not in obj:
        err_msg = "missing_ok_or_data"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    if not isinstance(obj["ok"], bool):
        err_msg = "ok_not_bool"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    data = obj["data"]
    if not isinstance(data, dict):
        err_msg = "data_not_dict"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    # 2) claves obligatorias
    required = ["answer", "confidence", "actions", "error"]
    for k in required:
        if k not in data:
            err_msg = f"missing_field:{k}"
            LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
            return False, None, err_msg

    # 3) tipos
    if not isinstance(data["answer"], str):
        err_msg = "answer_not_str"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    conf = data["confidence"]
    if not isinstance(conf, (int, float)):
        err_msg = "confidence_not_number"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg
    
    if conf < 0 or conf > 1:
        err_msg = "confidence_out_of_range"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    if not isinstance(data["actions"], list) or not all(isinstance(x, str) for x in data["actions"]):
        err_msg = "actions_not_list_of_str"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    if data["error"] is not None and not isinstance(data["error"], str):
        err_msg = "error_not_str_or_null"
        LOGGER.error(f"[{request_id}] ERROR: {err_msg}")
        return False, None, err_msg

    if MODE == "prod":
        LOGGER.info(f"[{request_id}] OK")
    else:
        LOGGER.debug(f"[{request_id}] validación OK")

    return True, obj, None

def repair_prompt(bad_output: str) -> str:
    """Prompt para intentar reparar un JSON roto."""
    return f"""Te voy a dar una salida que debería ser JSON, pero es inválida o no cumple el schema.
Devuelve SOLO el JSON corregido, cumpliendo exactamente el schema.

SCHEMA REQUERIDO:
{{
  "ok": boolean,
  "data": {{
    "answer": string,
    "confidence": number (0..1),
    "actions": array[string],
    "error": string|null
  }}
}}

SALIDA INVÁLIDA:
{bad_output}"""
