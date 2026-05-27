# Fix NameError re no definido

Corrige el error:

```text
NameError: name 're' is not defined
```

Causa:
`app.py` usa `re.sub(...)` para sanitizar FAST HUG BID antes de generar la evolución, pero no tenía importado el módulo estándar `re`.

Cambio aplicado:
- Agrega `import re` al inicio de `app.py`.

