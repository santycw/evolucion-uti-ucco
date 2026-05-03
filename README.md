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

## Cambios v2.0 motor de scores tipo biblioteca clínica

Se incorporó `modules/scores_catalog.py` como catálogo institucional de scores:

- centraliza categoría, estado de implementación, datos requeridos, uso clínico, referencia base y nota institucional;
- permite mostrar en la app una biblioteca de scores disponibles y próximos a automatizar;
- en cada score activo, el botón **“Ver cómo se calculó”** ahora muestra también datos requeridos, referencia y nota institucional;
- mantiene bloqueo de interpretación cuando faltan datos críticos configurados en el catálogo;
- distingue scores automáticos, manuales y pendientes de automatización.

Estados usados:

- `implementado`: cálculo automático disponible o integración activa completa;
- `manual`: se registra manualmente porque requiere evaluación clínica directa o datos no estructurados;
- `manual_pendiente_auto`: disponible como ingreso manual y planificado para automatización futura.

> Las referencias del catálogo son orientativas para trazabilidad/auditoría. Validar fórmulas, puntos de corte e indicaciones con guías institucionales antes de uso clínico formal.

## Módulo Piel / UPP / Decúbito

La versión actual incorpora una pestaña específica para documentar:

- estado general de piel;
- decúbito actual;
- frecuencia de cambios posturales;
- superficie de apoyo;
- medidas preventivas de lesiones por presión;
- score de Braden automático;
- registro simple de lesiones por presión, localización, lado, estadio/tipo, dimensiones, lecho, exudado, piel perilesional, signos de infección, dolor, observaciones y conducta.

El bloque se imprime en la evolución final bajo `PIEL / UPP / DECÚBITO`.
