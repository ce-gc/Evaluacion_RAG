# JSON Schema de Salida

El modelo debe devolver un objeto JSON con la siguiente estructura:

```json
{
  "ok": boolean,
  "data": {
    "answer": string,
    "confidence": number,
    "actions": array[string],
    "error": string | null
  }
}
```

## Campos

- `ok`: (boolean) Indica si la respuesta es válida y cumple con el formato.
- `data`: (object) Contiene la información de la respuesta.
  - `answer`: (string) La respuesta textual del modelo.
  - `confidence`: (number) Un valor entre 0 y 1 que indica la seguridad del modelo.
  - `actions`: (array of strings) Una lista de acciones derivadas de la respuesta.
  - `error`: (string or null) Un mensaje de error si `ok` es false, de lo contrario `null`.

## Ejemplo Exitoso

```json
{
  "ok": true,
  "data": {
    "answer": "Para depurar un error 500, revisa los logs del servidor, verifica la conectividad de la base de datos y comprueba las variables de entorno.",
    "confidence": 0.95,
    "actions": [
      "Revisar logs",
      "Verificar DB",
      "Comprobar variables de entorno"
    ],
    "error": null
  }
}
```

## Ejemplo de Error

```json
{
  "ok": false,
  "data": {
    "answer": "",
    "confidence": 0,
    "actions": [],
    "error": "El input proporcionado está vacío."
  }
}
```
