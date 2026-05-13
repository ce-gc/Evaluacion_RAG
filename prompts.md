# Iteraciones de Prompt (v1 - v17)

| Versión | Cambio realizado | Fallo observado | Arreglo aplicado |
| :--- | :--- | :--- | :--- |
| **v1-v10** | Evolución básica | Texto libre o JSON sin tipos. | Se añadió "EXCLUSIVAMENTE" y tipos en el schema. |
| **v11** | Prompt Estricto | El modelo Base (no-it) ignora órdenes. | Cambiar a modelo Instruct (`-it`). |
| **v12** | Formato Chat Manual | El modelo Instruct "charla" antes del JSON. | Implementar `apply_chat_template` oficial. |
| **v13** | Reglas de Oro | Sigue incluyendo bloques ```json que ensucian. | Prohibir markdown y forzar inicio con `{`. |
| **v14** | Prompt de Completado | Error `char 1` por prefijos del motor. | Limpiar prefijos en código y terminar prompt en `{"ok":`. |
| **v15** | Estilo Markdown | El modelo se inventa campos (`status`, `result`). | Usar bloque `json` explícito para anclar al modelo. |
| **v16** | **Few-Shot (3 ejemplos)** | Hallucinaciones de enlaces StackOverflow. | Dar 3 ejemplos reales de Input/JSON para fijar el patrón. |
| **v17** | **Restricción de Tipos** | `answer` venía como Lista en vez de String. | Especificar: "answer must be a single STRING". |

## Prompt Final Seleccionado (v17)

```text
Generate a JSON object for the request.
The 'answer' field must be a single STRING (not a list).
The 'actions' field must be a LIST of strings.

Schema: {"ok": true, "data": {"answer": "string response", "confidence": 0.95, "actions": ["action1", "action2"], "error": null}}

INPUT: {input}
JSON:
```
