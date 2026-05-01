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

## Cambios v2.0 seguridad clínica

Se agregaron tres capas de seguridad sin cambiar el flujo general de la aplicación:

1. **Validación de datos críticos**
   - TA mal formateada o fisiológicamente improbable.
   - TAM baja, bradicardia/taquicardia, taquipnea, hipoxemia, fiebre/hipotermia.
   - Alteraciones críticas de K, Na, glucemia, pH, lactato, PaFiO2, Hb, plaquetas, RIN y QTc.

2. **Alertas de seguridad clínica**
   - Panel visible en la pestaña Plan y FAST-HUG.
   - Alertas categorizadas como crítico, advertencia o revisión.
   - Las alertas son una medida de seguridad clínica visible en la app y no se imprimen en el texto final de evolución.

3. **Calculadora de infusiones con rangos y doble chequeo**
   - Cada droga tiene rango orientativo configurable en `modules/infusiones.py`.
   - La app muestra si la dosis calculada está dentro, por debajo o por encima del rango configurado.
   - Para anexar una infusión a la evolución, exige doble confirmación de droga, dilución, unidad, peso, indicación y monitoreo.
   - Si la dosis está fuera de rango, exige una confirmación adicional.

> Los rangos son orientativos y deben ajustarse al protocolo institucional vigente antes de uso asistencial.
