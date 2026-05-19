# Proyecto de Inferencia Estructurada

Este proyecto ha evolucionado de un simple servidor de texto a un **Pipeline de Inferencia Estructurada** capaz de obligar a modelos de lenguaje (Gemma 2 2B) a devolver respuestas en formato JSON válido, validarlas y repararlas automáticamente.

## Funcionalidades Principales

### 1. Motor de Inferencia (Gemma 2 2B Instruct)
- **Modelo**: `google/gemma-2-2b-it`.
- **Optimización CPU**: Implementación de *Greedy Decoding* y límites de tokens dinámicos para ejecución local fluida.
- **Chat Templates**: Uso del formato oficial de Google para maximizar la obediencia del modelo.

### 2. Validador Robusto (`validator.py`)
- **Extracción Inteligente**: Uso de Regex para localizar el bloque JSON incluso si el modelo añade texto extra o bloques Markdown.
- **Validación de Schema**: Comprobación estricta de claves (`ok`, `data`, `answer`, `confidence`, `actions`, `error`).
- **Validación de Tipos**: Verificación de strings, números (rango 0-1), listas y nulos.

### 3. Sistema de Logs (Observabilidad)
- **Modo Dev**: Trazabilidad completa paso a paso para depuración.
- **Modo Prod**: Logs minimalistas y seguros (recorte de texto y ocultación de datos sensibles).
- **Request Tracking**: Generación de `request_id` único para seguir el ciclo de vida de cada petición.

### 4. Estrategia de Reparación Automática (Bonus)
- Ante un fallo de parseo, el sistema activa un **Prompt Reparador** que re-envía la salida malformada al modelo solicitando exclusivamente la corrección del JSON.

---

## Instalación y Uso

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt python-dotenv
   ```

2. **Configurar el Token de Hugging Face:**
   Para evitar problemas de seguridad, no incluyas tu token en el código. Crea un archivo `.env` en la raíz del proyecto o configura una variable de entorno:
   - **Opción A (Archivo .env):** Crea un archivo llamado `.env` y añade: `HF_TOKEN=tu_token_aqui`
   - **Opción B (PowerShell):** `$env:HF_TOKEN="tu_token_aqui"`

2. **Configuración de Modo:**
   Puedes alternar entre logs detallados o mínimos:
   ```powershell
   $env:MODE = "dev"   # Para desarrollo
   $env:MODE = "prod"  # Para producción
   ```

3. **Ejecutar Evaluación (`run_eval.py`):**
   Procesa 10 casos de prueba complejos (incluyendo ataques de inyección y preguntas imposibles) y genera un reporte de éxito:
   ```bash
   python run_eval.py
   ```

---

## Arquitectura de Prompts (Iteración v1-v20)

Se han realizado **20 iteraciones de Prompt Engineering** para estabilizar la salida en un modelo de solo 2 billones de parámetros. El historial completo se encuentra en `prompts.md`.

**Técnicas utilizadas:**
- **Few-Shot Prompting**: Ejemplos de alta calidad para fijar el patrón.
- **Fill-in-the-blank**: Forzado del inicio del JSON (`{"ok": ...`) para evitar saludos.
- **Negative Constraints**: Prohibición explícita de explicaciones fuera del JSON.

---

## Estructura del Proyecto

- `engine_gemma2.py`: Motor de inferencia real (HuggingFace).
- `validator.py`: Lógica de validación, limpieza y logging.
- `run_eval.py`: Suite de testeo y métricas de éxito.
- `schema.md`: Contrato oficial del JSON.
- `prompts.md`: Registro de aprendizaje y evolución del prompt.
- `server.py` & `app.py`: Backend FastAPI y Frontend Gradio (originales).

---

## Notas de Hardware
- **Entorno**: Ejecución en CPU (Windows).
- **Latencia**: Debido al peso del modelo y la validación, cada respuesta estructurada toma entre **60-120 segundos**. El sistema de validación reduce radicalmente la tasa de error en este entorno limitado.

---

## Evidencia: Experimento RAG vs Baseline

Se incluye un experimento reproducible que compara 10 ejecuciones sin RAG (baseline) y 10 ejecuciones con RAG.

Cómo ejecutar:

```powershell
c:/python314/python.exe run_eval.py --experiment
```

Salida generada en este repo:
- `results_baseline.json` — 10 ejecuciones sin RAG
- `results_rag.json` — 10 ejecuciones con RAG

Resumen del experimento (ejecutado localmente con el stub):
- Baseline: 10 casos → PASS 9 / FAIL 1 → PASS_RATE 90.00%
- Con RAG: 10 casos → PASS 1 / FAIL 9 → PASS_RATE 10.00%

Observación: cuando se usa el stub de respuesta (`engine_gemma.predict`) el comportamiento no replica un LLM real. El RAG construye un prompt largo (CONTEXT + QUESTION) que con el stub produce salidas que el validador no puede parsear, de ahí la caída en pass_rate. En un despliegue con `engine_gemma2` real o un servicio remoto, se espera que el RAG mejore la calidad al proporcionar contexto relevante.

Recomendaciones siguientes:
- Ejecutar el experimento contra el servicio real (`--use-http`) o habilitar `engine_gemma2` para evaluar correctamente el impacto del RAG.
- Añadir reparación automática (`validator.repair_prompt`) y reintentos para reducir `json_parse_error`.

