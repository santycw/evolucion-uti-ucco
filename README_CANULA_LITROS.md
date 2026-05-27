# Parche: litros por cánula nasal

Cambios aplicados:
- Si se selecciona `Cánula Nasal` como dispositivo de O2, se habilita el campo `O₂ cánula (L/min)`.
- El campo permite valores de 0 a 15 L/min con paso de 0,5 L/min.
- El valor se vuelca en la evolución final junto al dispositivo respiratorio.

Ejemplo de salida:

```text
- RESP: Dispositivo: Cánula Nasal 2.0 L/min | FiO2 21%.
```

Archivos modificados:
- app.py
- modules/evolucion.py
