# Parche CVC: ubicación + tipo + fecha + días automáticos

Cambio aplicado en `app.py`:

- Agrega selector `Ubicación CVC` cuando se selecciona un tipo de CVC.
- Mantiene selector `Tipo de CVC`.
- Mantiene `Fecha CVC`.
- Mantiene cálculo automático de días.
- La variable `cvc_info` ahora incluye tipo, ubicación, fecha y día automático.

Ejemplo de salida: `CVC trilumen yugular interna derecha, colocado el 03/05/2026, Día 2`.
