# Parche: FiO2 automática por cánula nasal

Cambios aplicados:
- Si se selecciona `Cánula Nasal`, se habilita `O₂ cánula (L/min)`.
- La FiO2 se calcula automáticamente según flujo por cánula nasal convencional.
- La FiO2 calculada queda bloqueada para evitar inconsistencias.
- El valor calculado se usa en scores y evolución final.

Regla implementada:
- 0 L/min -> 21%
- 1 L/min -> 24%
- 2 L/min -> 28%
- 3 L/min -> 32%
- 4 L/min -> 36%
- 5 L/min -> 40%
- 6 L/min -> 44%

Nota: estimación orientativa para cánula nasal convencional de bajo flujo.

Archivo modificado:
- app.py
