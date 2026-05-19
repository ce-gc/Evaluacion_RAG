Title: Seguridad y límites

- Nunca devuelva secretos en `answer`.
- Si la pregunta pide datos sensibles, responda con `ok=false` y un `error` explicativo.
- Limite la longitud de salida para evitar truncamientos.
