# Parche FAST HUG con asterisco y PaFi/IROX solo gases arteriales

Cambios aplicados:
- FAST HUG BID en evolución final usa `*` como viñeta de texto plano.
- Se normaliza cualquier símbolo heredado `✓`, `√`, `✔`, `☑` o guion dentro del bloque FAST HUG a `*`.
- PaFiO2 manual, PaO2, SatO2 de gases y SatO2 para IROX solo se pasan al motor de scores si `Tipo de gases = Gases arteriales`.
- Si se seleccionan gases venosos, PaFiO2/IROX no se calculan.

Archivos modificados:
- app.py
- modules/evolucion.py
