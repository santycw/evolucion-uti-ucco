# Fix FAST HUG BID símbolo texto plano

Corrige de forma robusta la salida de FAST HUG BID en evolución final.

Cambio aplicado:
- Elimina símbolos heredados `✓`, `√`, `✔`, `☑` al inicio de cada ítem.
- Reemplaza siempre por guion simple `-`.
- Normaliza guion largo `–` a guion simple `-`.

Salida esperada:

```text
>> FAST HUG BID:
- F - Feeding
- U - Úlceras estrés
```

Archivo modificado:
- modules/evolucion.py
