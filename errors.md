# Tabla de fallos

Formato: | Tipo de fallo | Ejemplo de input | Qué salió mal | Cómo lo arreglé / Qué haría |
|---|---|---|---|
|json_parse_error|"El JSON lleva { } y \"comillas\""|Salida del modelo no era JSON parseable (texto libre, markdown, o truncado)|Usar `_clean_raw()` en `validator.py`; reintentar con `repair_prompt` para pedir JSON corregido y volver a validar|
|missing_field:data|Input: "Resume en 1 frase..." -> respuesta sin `data`|Falta la clave `data` en la raíz del JSON|Detectar y marcar error; modificar prompt/adapter para incluir `data` o mapear respuesta a `{data: {...}}` antes de devolver|
|data_not_dict|Respuesta con `data` como string|`data` no es un objeto dict|Normalizar añadiendo una estructura `data` válida o rechazar y pedir corrección al modelo|
|missing_field:answer|Respuesta sin `data.answer`|Falta campo obligatorio `answer`|Ajustar prompt para forzar campos requeridos; fallback: rellenar `answer` con mensaje de error y `ok=false`|
|answer_not_str|`data.answer` era lista o número|Tipo incorrecto en `answer`|Coercionar a str donde tenga sentido, o marcar fallo y pedir corrección|
|confidence_out_of_range|`confidence`: 1.5 o -0.1|Valor fuera de [0,1]|Normalizar con clamp(0,1) o marcar error y pedir corrección; preferible: indicar `ok=false` con `error` explicativo|
|actions_not_list|`actions` es string: "do X; do Y"|Tipo incorrecto en `actions`|Intentar split heurístico a lista; si no fiable, marcar fallo y pedir formato correcto|
|actions_has_non_str|`actions`: ["ok", 123]|Lista contiene valores no string|Filtrar/convertir elementos a string o marcar fallo y pedir corrección|
|ok_true_but_error_not_null|`ok` true pero `data.error` contiene texto|Incoherencia semántica entre `ok` y `error`|Corregir política: si hay error, `ok` debe ser false; preferible: setear `ok=false` y propagar `error`|
|timeout|Llamada HTTP larga / sin respuesta|Timeout en petición al servicio|Registrar timeout, reintentar (backoff), y devolver objeto con `ok=false` y `data.error` explicando el timeout|


Notas:
- Esta tabla recoge fallos reales y acciones paliativas recomendadas. Para cada fallo se sugiere una corrección de corto plazo (normalización, reintento, heurística) y una mejora a medio plazo (mejorar prompt, adapter, o el propio servicio `/predict`).
- Sugerencia operativa: instrumentar `run_eval.py` para, ante `json_parse_error`, ejecutar un intento de reparación automática usando `validator.repair_prompt()` y `predict()` de nuevo; registrar tanto el fallo original como el resultado reparado en `eval_results.json`.
