# Cambios evolución final / ARM / pupilas

Cambios aplicados:
- En evolución final, los scores se imprimen sin origen Auto/Manual y sin interpretación orientativa.
- Si no hay infusiones ni invasiones cargadas, se omite el bloque `INFUSIONES Y DISPOSITIVOS`.
- Se agrega campo `Pupilas` al examen neurológico y se vuelca en evolución final.
- Días ARM se calcula automáticamente desde `Fecha de intubación` cuando se marca `Paciente con ARM / intubado`.

Archivos modificados:
- app.py
- modules/evolucion.py
