# Fix FAST HUG BID con asterisco

Corrige definitivamente la salida de FAST HUG BID.

Salida esperada:

```text
>> FAST HUG BID:
* F - Feeding
* U - Úlceras estrés
```

El parche modifica `app.py` y `modules/evolucion.py` para evitar símbolos heredados y convertir cualquier `✓`, `√`, `✔`, `☑` a `*`.
