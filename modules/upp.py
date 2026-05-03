
"""
Módulo UPP.

Mapa anatómico clickeable basado en la imagen adjunta de puntos de presión
para úlceras por decúbito.

Se eliminaron de la interfaz:
- Escala de Braden
- Estado general de piel
- Decúbito
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


VISTAS_CORPORALES = ["Anterior", "Posterior"]

LATERALIDADES_UPP = ["", "Derecha", "Izquierda", "Bilateral", "Medial / central", "No aplica"]

ESTADIOS_UPP = [
    "",
    "Estadio I - Eritema no blanqueable",
    "Estadio II - Pérdida parcial de espesor cutáneo",
    "Estadio III - Pérdida total de espesor cutáneo",
    "Estadio IV - Exposición de fascia, músculo, tendón, ligamento, cartílago o hueso",
    "Lesión tisular profunda",
    "No clasificable / cubierta por escara o esfacelos",
    "Lesión asociada a dispositivo médico",
    "Lesión por humedad / DAI",
]

LECHOS_UPP = [
    "",
    "Piel intacta",
    "Granulación",
    "Epitelización",
    "Fibrina",
    "Esfacelos",
    "Necrosis",
    "Escara",
    "Mixto",
]

EXUDADOS_UPP = [
    "",
    "Ausente",
    "Escaso",
    "Moderado",
    "Abundante",
    "Purulento",
    "Hemático",
    "Seroso",
    "Serohemático",
]

PERILESIONAL_UPP = [
    "",
    "Íntegra",
    "Eritema",
    "Maceración",
    "Edema",
    "Induración",
    "Calor local",
    "Dermatitis",
    "Frágil",
]

INFECCION_UPP = [
    "",
    "Sin signos clínicos",
    "Dolor/calor/eritema local",
    "Exudado purulento",
    "Mal olor",
    "Celulitis",
    "Sospecha de infección profunda",
]

DOLOR_UPP = ["", "No evaluable", "Sin dolor", "Leve", "Moderado", "Severo"]

# Se mantienen estas constantes para que otros imports antiguos no rompan la app.
DECUBITOS = ["", "Dorsal", "Lateral derecho", "Lateral izquierdo", "Prono", "Semifowler", "Fowler", "Sedestación"]
FRECUENCIAS_CAMBIO = ["", "Cada 2 h", "Cada 3 h", "Cada 4 h", "Según tolerancia", "No aplica", "Otra"]
SUPERFICIES_APOYO = ["", "Colchón común", "Colchón antiescaras", "Cama de aire alternante", "Superficie viscoelástica", "Sillón", "Otra"]
MEDIDAS_PREVENCION = [
    "Cambios posturales programados",
    "Colchón antiescaras / superficie especial",
    "Taloneras / descarga de talones",
    "Protección sacra preventiva",
    "Control de humedad / dermatitis asociada a incontinencia",
    "Higiene e hidratación de piel",
    "Optimización nutricional",
    "Movilización temprana según tolerancia",
    "Reevaluación diaria de dispositivos",
]

BRADEN_PERCEPCION = ["4 - Sin limitación", "3 - Ligeramente limitada", "2 - Muy limitada", "1 - Completamente limitada"]
BRADEN_HUMEDAD = ["4 - Raramente húmeda", "3 - Ocasionalmente húmeda", "2 - Muy húmeda", "1 - Constantemente húmeda"]
BRADEN_ACTIVIDAD = ["4 - Camina frecuentemente", "3 - Camina ocasionalmente", "2 - En silla", "1 - En cama"]
BRADEN_MOVILIDAD = ["4 - Sin limitación", "3 - Ligeramente limitada", "2 - Muy limitada", "1 - Completamente inmóvil"]
BRADEN_NUTRICION = ["4 - Excelente", "3 - Adecuada", "2 - Probablemente inadecuada", "1 - Muy pobre"]
BRADEN_FRICCION = ["3 - Sin problema aparente", "2 - Problema potencial", "1 - Problema presente"]


MAPA_IMAGEN_PATH = Path(__file__).resolve().parent / "assets" / "mapa_ulceras_presion.png"

# Imagen original 2048 x 1117. Se divide en dos vistas.
CROP_BOXES = {
    "Anterior": (0, 0, 1024, 1117),
    "Posterior": (1024, 0, 2048, 1117),
}

# Coordenadas detectadas sobre la imagen original adjunta.
# Los puntos múltiples permiten seleccionar zonas bilaterales como codos.
_HOTSPOTS_FULL = {
    "Anterior": {
        "1. Cabeza (posterior craneal)": [(694, 190)],
        "2. Hombro (Acromión)": [(592, 318)],
        "3. Tórax/Costillas": [(694, 389)],
        "4. Codo (Epicóndilo medial)": [(577, 472)],
        "5. Cresta Ilíaca": [(635, 542)],
        "6. Trocánter Mayor (cadera)": [(611, 603)],
        "7. Rodilla (Rótula)": [(648, 801)],
        "8. Tobillo (Maléolo lateral)": [(649, 999)],
        "9. Dedos del pie": [(624, 1053)],
    },
    "Posterior": {
        "10. Occipucio": [(1355, 232)],
        "11. Escápula (borde)": [(1403, 330)],
        "12. Columna Vertebral (apófisis)": [(1355, 404)],
        "13. Codo (Olécranon)": [(1235, 480), (1476, 479)],
        "14. Sacro": [(1355, 548)],
        "15. Cóccix": [(1355, 592)],
        "16. Isquiones": [(1441, 617)],
        "6. Trocánter Mayor (cadera)": [(1270, 615)],
        "17. Muslo (posterior)": [(1414, 713)],
        "18. Talón (Posterior/Tendón)": [(1400, 1027)],
        "19. Planta del pie": [(1397, 1053)],
    },
}


def s(valor: Any) -> str:
    return str(valor or "").strip()


def resumen_mapa_corporal() -> dict[str, str]:
    return {
        "Anterior": "Vista anterior del mapa adjunto de puntos de presión.",
        "Posterior": "Vista posterior del mapa adjunto de puntos de presión.",
    }


def _crop_box(vista: str) -> tuple[int, int, int, int]:
    return CROP_BOXES.get(vista, CROP_BOXES["Anterior"])


def _to_crop_coords(vista: str, point: tuple[int, int]) -> tuple[int, int]:
    x0, y0, _, _ = _crop_box(vista)
    return point[0] - x0, point[1] - y0


def referencias_mapa_corporal(vista: str) -> list[str]:
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    return list(_HOTSPOTS_FULL.get(vista, {}).keys())


def obtener_zonas_mapa(vista: Any) -> list[str]:
    vista_txt = s(vista)
    return [""] + referencias_mapa_corporal(vista_txt)


def crear_imagen_mapa_corporal(vista: str, selected_zone: str = "") -> Image.Image:
    """
    Abre la imagen anatómica adjunta, recorta la vista anterior/posterior
    y resalta la zona seleccionada.
    """
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    base = Image.open(MAPA_IMAGEN_PATH).convert("RGBA")
    crop = base.crop(_crop_box(vista)).copy()

    if selected_zone and selected_zone in _HOTSPOTS_FULL.get(vista, {}):
        draw = ImageDraw.Draw(crop)
        for point in _HOTSPOTS_FULL[vista][selected_zone]:
            cx, cy = _to_crop_coords(vista, point)
            draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), outline=(0, 180, 0, 255), width=8)
            draw.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), outline=(0, 180, 0, 255), width=4)

    return crop.convert("RGB")


def zona_desde_coordenadas(vista: str, x: Any, y: Any, radio_px: int = 75) -> str:
    """
    Convierte coordenadas del clic sobre la vista recortada en la zona anatómica más cercana.
    """
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    try:
        x_f = float(x)
        y_f = float(y)
    except Exception:
        return ""

    mejor_zona = ""
    mejor_dist = 10**9

    for zona, points in _HOTSPOTS_FULL.get(vista, {}).items():
        for full_point in points:
            cx, cy = _to_crop_coords(vista, full_point)
            dist = math.sqrt((x_f - cx) ** 2 + (y_f - cy) ** 2)
            if dist < mejor_dist:
                mejor_dist = dist
                mejor_zona = zona

    return mejor_zona if mejor_dist <= radio_px else ""


def puntaje_desde_opcion(opcion: Any) -> int:
    match = re.match(r"\s*(\d+)", str(opcion or ""))
    return int(match.group(1)) if match else 0


def interpretar_braden(puntaje: int | None) -> dict:
    if puntaje is None or puntaje <= 0:
        return {"riesgo": "No calculado", "nivel": "info", "detalle": "Complete los 6 dominios de Braden."}
    if puntaje <= 9:
        return {"riesgo": "Riesgo muy alto", "nivel": "critico", "detalle": "Requiere prevención intensiva y reevaluación frecuente."}
    if puntaje <= 12:
        return {"riesgo": "Riesgo alto", "nivel": "alto", "detalle": "Requiere medidas preventivas estrictas."}
    if puntaje <= 14:
        return {"riesgo": "Riesgo moderado", "nivel": "intermedio", "detalle": "Requiere prevención activa y vigilancia."}
    if puntaje <= 18:
        return {"riesgo": "Riesgo leve", "nivel": "bajo", "detalle": "Mantener medidas preventivas según contexto clínico."}
    return {"riesgo": "Sin riesgo significativo", "nivel": "muy_bajo", "detalle": "Continuar vigilancia clínica habitual."}


def calcular_braden(percepcion: Any, humedad: Any, actividad: Any, movilidad: Any, nutricion: Any, friccion: Any) -> dict:
    componentes = {
        "Percepción sensorial": puntaje_desde_opcion(percepcion),
        "Humedad": puntaje_desde_opcion(humedad),
        "Actividad": puntaje_desde_opcion(actividad),
        "Movilidad": puntaje_desde_opcion(movilidad),
        "Nutrición": puntaje_desde_opcion(nutricion),
        "Fricción/cizalla": puntaje_desde_opcion(friccion),
    }
    puntaje = None if any(valor <= 0 for valor in componentes.values()) else sum(componentes.values())
    interpretacion = interpretar_braden(puntaje)
    return {"puntaje": puntaje, "componentes": componentes, **interpretacion}


def formatear_dimensiones(largo: Any, ancho: Any, profundidad: Any) -> str:
    partes = []
    if s(largo):
        partes.append(f"largo {s(largo)} cm")
    if s(ancho):
        partes.append(f"ancho {s(ancho)} cm")
    if s(profundidad):
        partes.append(f"profundidad {s(profundidad)} cm")
    return ", ".join(partes)


def formatear_lesion_upp(lesion: dict, indice: int) -> str:
    encabezado = []
    vista = s(lesion.get("vista"))
    localizacion = s(lesion.get("localizacion"))
    lateralidad = s(lesion.get("lateralidad"))
    estadio = s(lesion.get("estadio"))
    detalle_topografico = s(lesion.get("detalle_topografico"))

    if vista:
        encabezado.append(f"vista {vista.lower()}")
    if localizacion:
        encabezado.append(localizacion)
    if lateralidad:
        encabezado.append(lateralidad.lower())
    if detalle_topografico:
        encabezado.append(f"detalle anatómico: {detalle_topografico}")
    if estadio:
        encabezado.append(estadio)

    detalle = []
    dimensiones = formatear_dimensiones(
        lesion.get("largo_cm"),
        lesion.get("ancho_cm"),
        lesion.get("profundidad_cm"),
    )
    if dimensiones:
        detalle.append(dimensiones)

    for nombre, valor in [
        ("lecho", lesion.get("lecho")),
        ("exudado", lesion.get("exudado")),
        ("piel perilesional", lesion.get("perilesional")),
        ("infección", lesion.get("infeccion")),
        ("dolor", lesion.get("dolor")),
    ]:
        if s(valor):
            detalle.append(f"{nombre}: {s(valor)}")

    if s(lesion.get("observaciones")):
        detalle.append(f"observaciones: {s(lesion.get('observaciones'))}")
    if s(lesion.get("conducta")):
        detalle.append(f"conducta: {s(lesion.get('conducta'))}")

    linea_base = " / ".join(encabezado) if encabezado else "Lesión sin localización especificada"
    if detalle:
        return f"  {indice}) {linea_base}. " + "; ".join(detalle) + "."
    return f"  {indice}) {linea_base}."


def formatear_bloque_upp(datos: dict) -> str:
    lesiones = datos.get("upp_lesiones", []) or []
    lineas = []

    if lesiones:
        lineas.append("- Lesiones por presión / piel:")
        for indice, lesion in enumerate(lesiones, start=1):
            lineas.append(formatear_lesion_upp(lesion, indice))
    else:
        lineas.append("- Lesiones por presión: no consignadas.")

    if not lineas:
        return ""
    return ">> PIEL / UPP / DECÚBITO:\n" + "\n".join(lineas) + "\n"
