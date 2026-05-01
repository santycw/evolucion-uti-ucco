# Asistente de Evolución UTI / UCCO - Versión 2.0 modular segura

Esta versión mantiene el diseño general y el flujo de uso del asistente original, pero separa la lógica crítica en módulos para facilitar mantenimiento, auditoría y crecimiento seguro.

## Estructura

```text
app.py
modules/
  __init__.py
  evolucion.py
  infusiones.py
  scores.py
  terminologia.py
  validaciones.py
requirements.txt
.gitignore
```

## Módulos

- `modules/infusiones.py`: drogas disponibles y cálculo universal de infusiones.
- `modules/scores.py`: cálculos automáticos, motor de scores e interpretación.
- `modules/validaciones.py`: conversión numérica segura, TA, PAR, QTc y base de alertas.
- `modules/evolucion.py`: generación del texto final de evolución.
- `modules/terminologia.py`: diccionario médico, normalización y detección diagnóstica.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub

Archivos recomendados para subir:

```bash
git add app.py modules requirements.txt README.md .gitignore
git commit -m "Refactor modular v2 segura del asistente de evolución"
git push
```

## Nota institucional

No subir datos reales de pacientes al repositorio. Mantener credenciales, claves, configuraciones privadas y cualquier dato sensible fuera de GitHub.
