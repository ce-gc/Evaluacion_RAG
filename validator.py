"""
validator.py
============
Checker del contrato JSON del endpoint /predict.

Firma pública (estándar de la práctica):
    validate_output(raw: str) -> Tuple[bool, Optional[str], Optional[Dict]]
        - bool          → True si cumple el contrato
        - Optional[str] → error_type (None si pass=True)
        - Optional[Dict]→ objeto parseado (None si no se pudo parsear)

Firma extendida (con logging por request):
    validate_output_with_id(raw: str, request_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]
        - bool          → True si cumple el contrato
        - Optional[Dict]→ objeto parseado
        - Optional[str] → mensaje de error

Ambas comparten la misma lógica interna (_check).
"""
import json
import logging
import os
import re
import uuid
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGER = logging.getLogger("validator")
MODE = os.getenv("MODE", "dev")
_level = logging.DEBUG if MODE == "dev" else logging.INFO
logging.basicConfig(level=_level, format="%(levelname)s - %(message)s")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_request_id() -> str:
    return str(uuid.uuid4())[:8]


def clip(s: str, n: int = 200) -> str:
    if not s:
        return ""
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def _clean_raw(raw: str) -> str:
    """Elimina envolturas markdown, extrae el primer bloque JSON y limpia escapes.

    Intenta varios enfoques para manejar respuestas comunes del modelo:
    - quitar fences ``` y ```json
    - extraer el primer bloque que empiece por '{' o '[' y termine en '}' o ']'
    - si el bloque es una cadena JSON escapada (ej. "{\"ok\": ...}"), intentar des-escapar
    - reemplazar comillas escapadas si es necesario
    """
    text = raw.strip()

    # Quitar fences markdown si existen
    text = re.sub(r"^\s*```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)

    # Extraer primer objeto/array JSON
    m = re.search(r'([\{\[][\s\S]*[\}\]])', text)
    if m:
        text = m.group(1)

    text = text.strip()

    # Si parece ser una cadena JSON (comienza y termina con comillas), intentar unquote via json.loads
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        try:
            inner = json.loads(text)
            if isinstance(inner, str):
                text = inner
            else:
                text = json.dumps(inner)
        except Exception:
            text = text.strip('"')

    # Si contiene comillas escapadas, intentar reemplazarlas
    if '\\"' in text or "\\n" in text:
        try:
            candidate = text.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n')
            # no forzar, sólo aceptar si parece JSON válido
            json.loads(candidate)
            text = candidate
        except Exception:
            pass

    return text.strip()


# ---------------------------------------------------------------------------
# Núcleo de validación (sin efectos secundarios de logging)
# ---------------------------------------------------------------------------

def _check(raw: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Lógica pura de validación.
    Devuelve (pass, error_type, parsed_obj).
    """
    # 1) Parseo JSON (con limpieza previa y estrategias de reparación simples)
    cleaned = _clean_raw(raw)
    try:
        obj = json.loads(cleaned)
    except Exception:
        # 1st fallback: si cleaned es una cadena JSON encodificada, intentar cargarla y parsear de nuevo
        try:
            maybe = json.loads(cleaned)
            if isinstance(maybe, str):
                obj = json.loads(maybe)
            else:
                obj = maybe
        except Exception:
            # 2nd fallback: reemplazar comillas escapadas y reintentar
            try:
                candidate = cleaned.replace('\\"', '"').replace("\\'", "'")
                obj = json.loads(candidate)
            except Exception:
                return False, "json_parse_error", None

    # Si el objeto parseado es un wrapper (p. ej. contiene 'response' con el JSON real), extraerlo
    if isinstance(obj, dict) and "ok" not in obj and "response" in obj and isinstance(obj["response"], str):
        inner_raw = obj["response"]
        try:
            inner_clean = _clean_raw(inner_raw)
            inner_obj = json.loads(inner_clean)
            obj = inner_obj
        except Exception:
            # intentar des-escape y reintentar
            try:
                inner_candidate = inner_raw.replace('\\"', '"').replace("\\'", "'")
                inner_clean = _clean_raw(inner_candidate)
                obj = json.loads(inner_clean)
            except Exception:
                # no pudo extraer inner JSON, continuar con el objeto original (fallará más adelante)
                pass

    if not isinstance(obj, dict):
        return False, "not_a_dict", None

    # 2) Campos raíz obligatorios
    if "ok" not in obj:
        return False, "missing_field:ok", obj
    if "data" not in obj:
        return False, "missing_field:data", obj

    if not isinstance(obj["ok"], bool):
        return False, "ok_not_bool", obj

    data = obj["data"]
    if not isinstance(data, dict):
        return False, "data_not_dict", obj

    # 3) Campos obligatorios dentro de data
    for k in ("answer", "confidence", "actions", "error"):
        if k not in data:
            return False, f"missing_field:{k}", obj

    # 4) Tipos y rangos
    if not isinstance(data["answer"], str):
        return False, "answer_not_str", obj

    conf = data["confidence"]
    if not isinstance(conf, (int, float)):
        return False, "confidence_not_number", obj
    if not (0 <= conf <= 1):
        return False, "confidence_out_of_range", obj

    if not isinstance(data["actions"], list):
        return False, "actions_not_list", obj
    if any(not isinstance(x, str) for x in data["actions"]):
        return False, "actions_has_non_str", obj

    err_field = data["error"]
    if err_field is not None and not isinstance(err_field, str):
        return False, "error_not_str_or_null", obj

    # 5) Coherencia ok / error
    if obj["ok"] is True and data["error"] is not None:
        return False, "ok_true_but_error_not_null", obj

    return True, None, obj


# ---------------------------------------------------------------------------
# API pública — firma estándar de la práctica
# ---------------------------------------------------------------------------

def validate_output(raw: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Firma estándar exigida por la práctica.

    Parámetros
    ----------
    raw : str
        Texto crudo devuelto por el modelo.

    Retorna
    -------
    (pass, error_type, parsed_obj)
        pass        → True si la salida cumple el contrato mínimo
        error_type  → None si pass=True; si no, string tipo 'json_parse_error',
                      'missing_field:answer', etc.
        parsed_obj  → dict parseado si se pudo parsear; si no, None
    """
    passed, error_type, parsed_obj = _check(raw)
    if not passed:
        LOGGER.error("validate_output FAIL: %s | raw=%s", error_type, clip(raw))
    else:
        LOGGER.debug("validate_output OK")
    return passed, error_type, parsed_obj


# ---------------------------------------------------------------------------
# API extendida — con request_id para run_eval.py
# ---------------------------------------------------------------------------

def validate_output_with_id(
    raw: str, request_id: str
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Firma extendida usada por run_eval.py.
    Devuelve (ok, parsed_obj, error_message).
    """
    if MODE == "dev":
        LOGGER.debug("[%s] recibo output: %s", request_id, clip(raw))

    passed, error_type, parsed_obj = _check(raw)

    if not passed:
        LOGGER.error("[%s] ERROR: %s", request_id, error_type)
        return False, None, error_type

    if MODE == "dev":
        LOGGER.debug("[%s] validación OK", request_id)
    else:
        LOGGER.info("[%s] OK", request_id)

    return True, parsed_obj, None


# ---------------------------------------------------------------------------
# Utilidad de reparación
# ---------------------------------------------------------------------------

def repair_prompt(bad_output: str) -> str:
    """Devuelve un prompt para pedirle al modelo que corrija un JSON roto."""
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
