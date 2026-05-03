"""
Módulo UPP / decúbito / Braden.

Incluye cálculo de Braden, mapa corporal anterior/posterior clickeable por
coordenadas de imagen y formateo del bloque de piel / UPP para la evolución final.
"""

from __future__ import annotations

import math
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont


VISTAS_CORPORALES = ["Anterior", "Posterior"]

MAPA_CORPORAL = {
    "Anterior": [
        "1. Frente / cara",
        "2. Oreja / región malar",
        "3. Hombro / clavícula",
        "4. Tórax anterior",
        "5. Mamas / pliegue submamario",
        "6. Abdomen",
        "7. Cresta ilíaca anterior",
        "8. Periné / región inguinal",
        "9. Muslo anterior",
        "10. Rodilla",
        "11. Tibia / cara anterior pierna",
        "12. Maléolo medial",
        "13. Dorso del pie",
        "14. Dedos del pie",
        "15. Otra localización anterior",
    ],
    "Posterior": [
        "1. Occipital",
        "2. Pabellón auricular",
        "3. Hombro / escápula",
        "4. Columna dorsal",
        "5. Codo / olécranon",
        "6. Sacro / cóccix",
        "7. Glúteo",
        "8. Isquion",
        "9. Trocánter",
        "10. Muslo posterior",
        "11. Hueco poplíteo",
        "12. Gemelos / pantorrilla",
        "13. Talón",
        "14. Planta del pie",
        "15. Otra localización posterior",
    ],
}

# Coordenadas sobre la imagen generada por crear_imagen_mapa_corporal().
_HOTSPOTS = {
    "Anterior": {
        1: (160, 54),
        2: (207, 82),
        3: (96, 128),
        4: (160, 150),
        5: (160, 190),
        6: (160, 238),
        7: (160, 286),
        8: (160, 334),
        9: (136, 392),
        10: (136, 480),
        11: (136, 555),
        12: (136, 620),
        13: (136, 684),
        14: (136, 724),
        15: (260, 724),
    },
    "Posterior": {
        1: (160, 54),
        2: (207, 82),
        3: (96, 128),
        4: (160, 166),
        5: (86, 244),
        6: (160, 306),
        7: (160, 352),
        8: (160, 394),
        9: (232, 384),
        10: (136, 456),
        11: (136, 532),
        12: (136, 598),
        13: (136, 700),
        14: (136, 736),
        15: (260, 724),
    },
}

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

LECHOS_UPP = ["", "Piel intacta", "Granulación", "Epitelización", "Fibrina", "Esfacelos", "Necrosis", "Escara", "Mixto"]
EXUDADOS_UPP = ["", "Ausente", "Escaso", "Moderado", "Abundante", "Purulento", "Hemático", "Seroso", "Serohemático"]
PERILESIONAL_UPP = ["", "Íntegra", "Eritema", "Maceración", "Edema", "Induración", "Calor local", "Dermatitis", "Frágil"]
INFECCION_UPP = ["", "Sin signos clínicos", "Dolor/calor/eritema local", "Exudado purulento", "Mal olor", "Celulitis", "Sospecha de infección profunda"]
DOLOR_UPP = ["", "No evaluable", "Sin dolor", "Leve", "Moderado", "Severo"]

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

BRADEN_PERCEPCION = [
    "4 - Sin limitación",
    "3 - Ligeramente limitada",
    "2 - Muy limitada",
    "1 - Completamente limitada",
]
BRADEN_HUMEDAD = [
    "4 - Raramente húmeda",
    "3 - Ocasionalmente húmeda",
    "2 - Muy húmeda",
    "1 - Constantemente húmeda",
]
BRADEN_ACTIVIDAD = [
    "4 - Camina frecuentemente",
    "3 - Camina ocasionalmente",
    "2 - En silla",
    "1 - En cama",
]
BRADEN_MOVILIDAD = [
    "4 - Sin limitación",
    "3 - Ligeramente limitada",
    "2 - Muy limitada",
    "1 - Completamente inmóvil",
]
BRADEN_NUTRICION = [
    "4 - Excelente",
    "3 - Adecuada",
    "2 - Probablemente inadecuada",
    "1 - Muy pobre",
]
BRADEN_FRICCION = [
    "3 - Sin problema aparente",
    "2 - Problema potencial",
    "1 - Problema presente",
]


def s(valor: Any) -> str:
    return str(valor or "").strip()


def obtener_zonas_mapa(vista: Any) -> list[str]:
    vista_txt = s(vista)
    zonas = MAPA_CORPORAL.get(vista_txt, [])
    return [""] + zonas if zonas else [""]


def _extraer_numero_zona(zona: Any) -> int | None:
    match = re.match(r"\s*(\d+)", str(zona or ""))
    return int(match.group(1)) if match else None


def _texto_zona_sin_numero(zona: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", str(zona or "")).strip()


def resumen_mapa_corporal() -> dict[str, str]:
    return {
        "Anterior": "Haga clic en los puntos numerados de la silueta anterior para seleccionar la localización.",
        "Posterior": "Haga clic en los puntos numerados de la silueta posterior para seleccionar la localización.",
    }


def _get_font(size: int = 15):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_centered_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        w, h = draw.textlength(text, font=font), 12
    draw.text((xy[0] - w / 2, xy[1] - h / 2 - 1), text, font=font, fill=fill)


def _draw_body_base(draw: ImageDraw.ImageDraw):
    outline = "#475569"
    fill = "#d1d5db"
    # Cabeza y cuello
    draw.ellipse((124, 24, 196, 96), fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((144, 94, 176, 118), radius=10, fill=fill, outline=outline, width=3)
    # Tronco/pelvis
    draw.rounded_rectangle((108, 118, 212, 300), radius=42, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((120, 296, 200, 400), radius=28, fill=fill, outline=outline, width=3)
    # Brazos
    draw.rounded_rectangle((78, 128, 104, 260), radius=13, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((216, 128, 242, 260), radius=13, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((70, 254, 96, 374), radius=13, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((224, 254, 250, 374), radius=13, fill=fill, outline=outline, width=3)
    # Piernas
    draw.rounded_rectangle((116, 398, 148, 558), radius=15, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((172, 398, 204, 558), radius=15, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((116, 558, 148, 698), radius=15, fill=fill, outline=outline, width=3)
    draw.rounded_rectangle((172, 558, 204, 698), radius=15, fill=fill, outline=outline, width=3)
    # Pies
    draw.ellipse((104, 696, 160, 730), fill=fill, outline=outline, width=3)
    draw.ellipse((160, 696, 216, 730), fill=fill, outline=outline, width=3)


def crear_imagen_mapa_corporal(vista: str, selected_zone: str = "") -> Image.Image:
    """Crea una imagen PIL con silueta corporal y puntos clickeables."""
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    img = Image.new("RGB", (360, 790), "#0f172a")
    draw = ImageDraw.Draw(img)
    font_title = _get_font(18)
    font_small = _get_font(12)
    font_marker = _get_font(15)

    draw.text((18, 14), f"Mapa corporal {vista.lower()} clickeable", fill="#f8fafc", font=font_title)
    draw.text((18, 42), "Haga clic sobre un punto numerado para seleccionar la localización.", fill="#cbd5e1", font=font_small)

    # Panel de silueta
    draw.rounded_rectangle((20, 70, 340, 770), radius=16, fill="#e5e7eb", outline="#334155", width=2)
    _draw_body_base(draw)

    selected_num = _extraer_numero_zona(selected_zone)
    zonas = MAPA_CORPORAL.get(vista, [])
    for zona in zonas:
        numero = _extraer_numero_zona(zona)
        if numero is None:
            continue
        cx, cy = _HOTSPOTS[vista][numero]
        selected = numero == selected_num
        marker_fill = "#ef4444" if selected else "#f59e0b"
        marker_outline = "#7f1d1d" if selected else "#111827"
        text_fill = "#ffffff" if selected else "#111827"
        r = 18 if selected else 16
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=marker_fill, outline=marker_outline, width=3)
        _draw_centered_text(draw, (cx, cy), str(numero), font_marker, text_fill)

    return img


def zona_desde_coordenadas(vista: str, x: Any, y: Any, radio_px: int = 28) -> str:
    """Convierte un clic en coordenadas de imagen a la zona anatómica más cercana."""
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    try:
        x_f = float(x)
        y_f = float(y)
    except Exception:
        return ""

    mejor_num = None
    mejor_dist = 10**9
    for numero, (cx, cy) in _HOTSPOTS.get(vista, {}).items():
        dist = math.sqrt((x_f - cx) ** 2 + (y_f - cy) ** 2)
        if dist < mejor_dist:
            mejor_dist = dist
            mejor_num = numero

    if mejor_num is None or mejor_dist > radio_px:
        return ""

    for zona in MAPA_CORPORAL.get(vista, []):
        if _extraer_numero_zona(zona) == mejor_num:
            return zona
    return ""


def referencias_mapa_corporal(vista: str) -> list[str]:
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    return MAPA_CORPORAL.get(vista, [])


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


def calcular_braden(
    percepcion: Any,
    humedad: Any,
    actividad: Any,
    movilidad: Any,
    nutricion: Any,
    friccion: Any,
) -> dict:
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
    estado_piel = s(datos.get("piel_estado"))
    decubito = s(datos.get("decubito_actual"))
    cambios = s(datos.get("cambios_posturales"))
    superficie = s(datos.get("superficie_apoyo"))
    medidas = datos.get("upp_medidas_prevencion", []) or []
    conducta_general = s(datos.get("upp_conducta_general"))
    lesiones = datos.get("upp_lesiones", []) or []
    braden = datos.get("braden_resultado", {}) or {}

    lineas = []
    if estado_piel:
        lineas.append(f"- Piel: {estado_piel}")

    decubito_partes = []
    if decubito:
        decubito_partes.append(f"Decúbito actual: {decubito}")
    if cambios:
        decubito_partes.append(f"Cambios posturales: {cambios}")
    if superficie:
        decubito_partes.append(f"Superficie de apoyo: {superficie}")
    if decubito_partes:
        lineas.append("- " + " | ".join(decubito_partes))

    puntaje = braden.get("puntaje")
    if puntaje is not None:
        lineas.append(f"- Braden: {puntaje}/23 - {braden.get('riesgo', 'No interpretado')}")

    if medidas:
        lineas.append("- Prevención UPP: " + " | ".join([s(m) for m in medidas if s(m)]))

    if lesiones:
        lineas.append("- Lesiones por presión / piel:")
        for indice, lesion in enumerate(lesiones, start=1):
            lineas.append(formatear_lesion_upp(lesion, indice))
    else:
        lineas.append("- Lesiones por presión: no consignadas.")

    if conducta_general:
        lineas.append(f"- Conducta piel/UPP: {conducta_general}")

    if not lineas:
        return ""
    return ">> PIEL / UPP / DECÚBITO:\n" + "\n".join(lineas) + "\n"
