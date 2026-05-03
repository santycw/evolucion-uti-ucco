# Versión con mapa SVG interactivo UPP

Esta versión incorpora un mapa corporal SVG interactivo anterior/posterior para registrar escaras / UPP.

## Archivos principales modificados

- `app.py`
- `modules/upp.py`

## Funciones principales nuevas en `modules/upp.py`

- `render_svg_mapa_corporal(vista, state_key, selected_zone="")`
- `resolver_seleccion_svg(vista, state_key)`
- `limpiar_seleccion_svg(state_key)`

## Uso

1. Abrir la pestaña `Piel / UPP / Decúbito`.
2. Indicar cantidad de lesiones.
3. Elegir vista corporal anterior/posterior.
4. Hacer clic sobre la zona anatómica en el SVG.
5. Completar características de la lesión.
6. Generar evolución.

La zona seleccionada se vuelca automáticamente en la evolución final.
