# Tabla de fallos

Formato: | Tipo de fallo | Ejemplo de input | Qué salió mal | Cómo lo arreglé / Qué haría |
|---|---|---|---|
|json_parse_error|"El JSON lleva { } y \"comillas\""|Salida del modelo no era JSON parseable (texto libre, markdown, o truncado)|Usar `_clean_raw()` en `validator.py`; reintentar con `repair_prompt` para pedir JSON corregido y volver a validar|
|missing_field:data|Input: "Resume en 1 frase..." -> respuesta sin `data`|Falta la clave `data` en la raíz del JSON|Detectar y marcar error; modificar prompt/adapter para incluir `data` o mapear respuesta a `{data: {...}}` antes de devolver|
|data_not_dict|Respuesta con `data` como string|`data` no es un objeto dict|Normalizar añadiendo una estructura `data` válida o rechazar y pedir corrección al modelo|
|missing_field:answer|Respuesta sin `data.answer`|Falta campo obligatorio `answer`|Ajustar prompt para forzar campos requeridos; fallback: rellenar `answer` con mensaje de error y `ok=false`|
 # Tabla de fallos (evidencia real)

 La siguiente tabla recoge 10 tipos de fallo observados en `eval_results_baseline.json` (ejemplos reales), qué salió mal y la acción que implementamos o recomendamos.

 Tipo de fallo | Ejemplo (case id) | Ejemplo de input | Qué salió mal (breve) | Corrección aplicada / recomendada
 ---|---|---|---|---
 answer_not_str | `case_01` | "Dame 3 pasos para depurar un error 500 en una API." | `data.answer` viene como una lista (array) en lugar de string. | Normalizar en el reparador o forzar en prompt; en `validator.py` añadimos heurística para detectar listas en `answer` y, si procede, convertir a string o marcar `answer_not_str`.
 missing_field:error | `case_03` | "Convierte este texto en una lista de acciones..." | Falta el campo `data.error` en la salida (no cumple schema). | El validador marca `missing_field:error`. Recomendado: ajustar prompt o usar `repair_prompt` para pedir JSON completo; `run_eval.py` ahora intenta reintentos y reparación automática.
 missing_field:confidence | `case_08` / `case_24` | "Caso cabrón: input muy largo..." / "¿Qué devuelves si el usuario pide varios formatos...?" | Falta `data.confidence`. | Forzar campo `confidence` en prompt y usar `repair_prompt` para rellenarlo; en validador se recomienda convertir strings numéricas a float si procede.
 missing_field:ok | `case_13` | "Convierte en pasos: 'git pull, pip install, run tests'" | En algunos resultados el JSON parseado era un wrapper (p.ej. `{"model":..., "response": "..."}`) y no contenía `ok` en el nivel raíz. | Implementado: extracción previa en `run_eval.py` que, si detecta un wrapper con `response`, pasa el contenido de `response` al validador.
 json_parse_error (fences/markdown) | múltiples (p.ej. `case_02` raw contiene fences) | Varios | El modelo devuelve bloque con ```json``` y escapes, lo que rompe `json.loads` sin limpieza previa. | Implementado: `_clean_raw()` en `validator.py` elimina fences, extrae el primer bloque JSON y reintenta des-escape.
 missing_field:confidence (string) | `case_24` | "¿Qué devuelves si el usuario pide varios formatos...?" | `confidence` a veces viene ausente o como string. | Recomendado: forzar formato numérico en prompt; en reparación, convertir strings numéricas a float y validar rango 0..1.
 answer_not_str (nested lists) | `case_06` | "Devuélveme acciones en orden: 'Quiero desplegar esto en local'" | `answer` es un array de pasos en vez de string. | Normalizar (join) o pedir lista explícita en `actions` y texto en `answer`.
 ok_true_but_error_not_null | varios | casos con `ok: true` y `data.error` no nulo | Incoherencia semántica entre `ok` y `error`. | Política: si `error` no es null, `ok` debe ser false. Implementar coherencia en prompt/reparador.
 timeout / request_error | n/a en baseline actual | n/a | Fallos de red posibles al llamar al endpoint HTTP. | `call_predict_http` ya implementa reintentos con backoff; registrar timeout como `error_type` y continuar.

 Notas:
 - Los ejemplos citados arriba están tomados de `eval_results_baseline.json`. Revisa las entradas `raw` para ver la forma exacta del fallo (incluye `raw` con fences y wrappers).
 - Correcciones aplicadas en este repositorio:
	 - `validator.py`: `_clean_raw()` robusto + intentos de des-escape + extracción del JSON dentro del campo `response` si aparece.
	 - `run_eval.py`: extracción previa del campo `response` (si el modelo devuelve un wrapper), reintentos con instrucción estricta y fallback a `repair_prompt()`.
	 - Tests: `tests/test_parser_cleanup.py` cubre fenced JSON, JSON escapado y wrapper con `response`.

 Siguientes pasos recomendados:
 - Ejecutar la suite completa y revisar `eval_results_*.json` para recopilar ejemplos concretos y recortar fragmentos `raw` al archivo `errors.md` para evidencias.
 - Añadir normalizaciones en el reparador para `answer` cuando sea lista (coerción o join) y conversión segura de `confidence` si viene como string.
 - Incluir en el README un apartado corto con cómo interpretar `eval_results_*.json` (campos `pass`, `error_type`, `raw`, `parsed`, `latency_ms`).
|timeout|Llamada HTTP larga / sin respuesta|Timeout en petición al servicio|Registrar timeout, reintentar (backoff), y devolver objeto con `ok=false` y `data.error` explicando el timeout|


Notas:
- Esta tabla recoge fallos reales y acciones paliativas recomendadas. Para cada fallo se sugiere una corrección de corto plazo (normalización, reintento, heurística) y una mejora a medio plazo (mejorar prompt, adapter, o el propio servicio `/predict`).
- Sugerencia operativa: instrumentar `run_eval.py` para, ante `json_parse_error`, ejecutar un intento de reparación automática usando `validator.repair_prompt()` y `predict()` de nuevo; registrar tanto el fallo original como el resultado reparado en `eval_results.json`.
