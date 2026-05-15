# Parche RASS y Glasgow

Cambios:
- Reemplaza los campos manuales de Glasgow y RASS por escalas seleccionables.
- Glasgow se calcula automáticamente a partir de apertura ocular, respuesta verbal y respuesta motora.
- Permite respuesta verbal `Vt` si el paciente está intubado/TQT.
- RASS se selecciona desde +4 a -5.
- Mantiene Pupilas en examen neurológico.
- Agrega defensa adicional para eliminar el bloque vacío `INFUSIONES Y DISPOSITIVOS` si aparece heredado.

Archivos modificados:
- app.py
- modules/evolucion.py
