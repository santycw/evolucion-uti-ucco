# Parche: infusiones y dispositivos separados

Modifica `modules/evolucion.py` para que la evolución final use el formato:

```text
>> INFUSIONES:
Infusiones activas:
- Noradrenalina: 0.0571 mcg/kg/min
- Dopamina: 2.3810 mcg/kg/min

>> DISPOSITIVOS:
CVC: CVC bilumen localización no consignada, Día 1
Cat Art: Otro catéter arterial localización no consignada, Día 1
SV: Sonda vesical látex, 2 vías, Día 1
SNG/SOG/SNY/Botón gástrico: SNG, Día 1
```

Si no existen infusiones, se omite `>> INFUSIONES:`.
Si no existen dispositivos, se omite `>> DISPOSITIVOS:`.
