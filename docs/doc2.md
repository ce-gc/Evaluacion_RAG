Title: Formato de respuesta /predict

El endpoint /predict debe devolver un JSON con la siguiente estructura:

{
  "ok": true,
  "data": {
    "answer": "string",
    "confidence": 0.0,
    "actions": ["string"],
    "error": null
  }
}

Si hay un error interno, use ok=false y ponga un mensaje en data.error.
