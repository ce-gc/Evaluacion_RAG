Title: Guía rápida de debugging

- Revisa logs y metadatos en la respuesta (`meta` si el servicio los devuelve).
- Para timeouts, aumenta el timeout o añade reintentos exponenciales.
- Testea con casos límite: entradas vacías, caracteres especiales y parrafos largos.
