# Parche laboratorio y FAST HUG BID

Cambios aplicados:
- Laboratorio / EAB: agrega selector de tipo de gases: arteriales o venosos.
- Laboratorio: agrega lipasa sérica y amilasa sérica.
- Hemograma: agrega fórmula leucocitaria: neutrófilos, linfocitos, monocitos, eosinófilos, basófilos y cayados.
- Hemograma: agrega índices hematimétricos: VCM, HCM, CHCM y RDW.
- Evolución final: incorpora estos campos solo si fueron completados.
- FAST HUG BID: reemplaza el símbolo `✓` por `-`, compatible con texto plano.

Archivos modificados:
- app.py
- modules/evolucion.py
