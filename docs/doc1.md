Title: Cómo desplegar la API

Para desplegar la API en local:

- Instala las dependencias con pip install -r requirements.txt
- Exporta HF_TOKEN si usas modelos de Hugging Face
- Ejecuta: uvicorn server:app --reload --host 127.0.0.1 --port 8000

Comprueba /hola_mundo para verificar el servicio.
