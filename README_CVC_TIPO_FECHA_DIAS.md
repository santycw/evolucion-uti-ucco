# Parche CVC: tipo + fecha + días automáticos

Cambios en `app.py`:

- Reemplaza el campo libre `CVC (Sitio/Día)` por:
  - `Tipo de CVC`
  - `Fecha CVC`
  - cálculo automático de día de dispositivo
- Día de CVC = fecha actual - fecha de colocación + 1.
- Si la fecha es hoy, se informa `Día 1`.
- Mantiene `cvc_info` para que el generador de evolución siga usando el mismo nombre de variable.
- Incluye también FiO2 automática para máscaras Venturi si no estaba aplicada en la base.
