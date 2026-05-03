"""
Módulo UPP / decúbito / Braden.

Incluye cálculo de Braden, mapa corporal SVG interactivo (anterior/posterior)
y formateo del bloque de piel / UPP para la evolución final.
"""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlencode

import streamlit as st


# --- MAPA CORPORAL SVG INTERACTIVO ---
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

# Posiciones de hotspots sobre la silueta simplificada
_HOTSPOTS = {
    "Anterior": {
        1:(160,48), 2:(205,72), 3:(94,114), 4:(160,135), 5:(160,171), 6:(160,214),
        7:(160,258), 8:(160,300), 9:(138,356), 10:(138,442), 11:(138,515), 12:(138,572),
        13:(138,635), 14:(138,675), 15:(252,706),
    },
    "Posterior": {
        1:(160,48), 2:(205,72), 3:(96,116), 4:(160,150), 5:(87,220), 6:(160,274),
        7:(160,317), 8:(160,356), 9:(232,346), 10:(138,414), 11:(138,486), 12:(138,548),
        13:(138,646), 14:(138,685), 15:(252,706),
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


def _extraer_numero_zona(zona: str) -> int | None:
    match = re.match(r"\s*(\d+)", str(zona or ""))
    return int(match.group(1)) if match else None


def _texto_zona_sin_numero(zona: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", str(zona or "")).strip()


def resumen_mapa_corporal() -> dict[str, str]:
    return {
        "Anterior": "Silueta anterior: cara, región malar, hombro/clavícula, tórax, pliegue submamario, abdomen, cresta ilíaca, periné, muslo, rodilla, tibia, maléolo medial, dorso y dedos del pie.",
        "Posterior": "Silueta posterior: occipital, pabellón auricular, escápula, columna dorsal, codo, sacro/cóccix, glúteo, isquion, trocánter, muslo posterior, hueco poplíteo, pantorrilla, talón y planta del pie.",
    }


def _build_pick_url(vista: str, zona: str, state_key: str) -> str:
    params = dict(st.query_params)
    params["upp_pick_slot"] = state_key
    params["upp_pick_view"] = vista
    params["upp_pick_zone"] = zona
    return "?" + urlencode(params, doseq=False)


def _svg_hotspot(vista: str, zona: str, state_key: str, selected: bool) -> str:
    numero = _extraer_numero_zona(zona) or 0
    cx, cy = _HOTSPOTS[vista][numero]
    fill = "#ef4444" if selected else "#f59e0b"
    stroke = "#7f1d1d" if selected else "#1f2937"
    text_fill = "#ffffff" if selected else "#111827"
    title = html.escape(_texto_zona_sin_numero(zona))
    href = html.escape(_build_pick_url(vista, zona, state_key), quote=True)
    return (
        f"<a href='{href}' target='_top'>"
        f"<title>{title}</title>"
        f"<circle cx='{cx}' cy='{cy}' r='16' fill='{fill}' stroke='{stroke}' stroke-width='2'/>"
        f"<text x='{cx}' y='{cy + 5}' text-anchor='middle' font-family='Arial' font-size='14' font-weight='700' fill='{text_fill}'>{numero}</text>"
        f"</a>"
    )


def _svg_body_base() -> str:
    return """
        <circle cx='160' cy='58' r='36' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='144' y='92' width='32' height='22' rx='10' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='110' y='116' width='100' height='168' rx='42' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='122' y='284' width='76' height='98' rx='28' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='80' y='126' width='24' height='124' rx='12' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='216' y='126' width='24' height='124' rx='12' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='74' y='245' width='22' height='112' rx='11' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='224' y='245' width='22' height='112' rx='11' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='118' y='380' width='28' height='148' rx='14' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='174' y='380' width='28' height='148' rx='14' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='118' y='528' width='28' height='128' rx='14' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <rect x='174' y='528' width='28' height='128' rx='14' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <ellipse cx='132' cy='678' rx='28' ry='15' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
        <ellipse cx='188' cy='678' rx='28' ry='15' fill='#d1d5db' stroke='#475569' stroke-width='3'/>
    """


def render_svg_mapa_corporal(vista: str, state_key: str, selected_zone: str = "") -> str:
    """Devuelve HTML/SVG interactivo real con zonas clickeables sobre una silueta."""
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    selected_zone = s(selected_zone)
    hotspots = "".join(
        _svg_hotspot(vista, zona, state_key, zona == selected_zone)
        for zona in MAPA_CORPORAL.get(vista, [])
    )
    leyenda = "".join(
        f"<li><b>{_extraer_numero_zona(z) or ''}</b>: {html.escape(_texto_zona_sin_numero(z))}</li>"
        for z in MAPA_CORPORAL.get(vista, [])
    )
    titulo = f"Silueta corporal {vista.lower()} clickeable"
    return f"""
    <div style='border:1px solid #334155;border-radius:14px;background:#0f172a;padding:12px;margin:4px 0 10px 0;'>
      <div style='color:#f8fafc;font-weight:700;font-size:15px;margin-bottom:4px'>{titulo}</div>
      <div style='color:#cbd5e1;font-size:12px;margin-bottom:10px'>Haga clic sobre una zona numerada para seleccionar la localización anatómica de la lesión.</div>
      <div style='display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;'>
        <div style='background:#e5e7eb;border-radius:14px;padding:8px;'>
          <svg width='320' height='730' viewBox='0 0 320 730' xmlns='http://www.w3.org/2000/svg'>
            {_svg_body_base()}
            {hotspots}
          </svg>
        </div>
        <div style='flex:1;min-width:240px;background:#ffffff;border-radius:12px;padding:12px;border:1px solid #cbd5e1;color:#111827;'>
          <div style='font-weight:700;margin-bottom:8px'>Referencias anatómicas</div>
          <ul style='margin:0;padding-left:18px;font-size:13px;line-height:1.35;list-style:none'>{leyenda}</ul>
          <div style='margin-top:10px;font-size:12px;color:#475569'>La zona seleccionada se resalta en rojo.</div>
        </div>
      </div>
    </div>
    """


def resolver_seleccion_svg(vista: str, state_key: str) -> str:
    """Consume los query params del mapa SVG y guarda la selección en session_state."""
    estado_key = f"upp_svg_sel_{state_key}"
    seleccion = s(st.session_state.get(estado_key, ""))
    q_slot = s(st.query_params.get("upp_pick_slot", ""))
    q_view = s(st.query_params.get("upp_pick_view", ""))
    q_zone = s(st.query_params.get("upp_pick_zone", ""))

    if q_slot == state_key and q_view == vista and q_zone in MAPA_CORPORAL.get(vista, []):
        st.session_state[estado_key] = q_zone
        seleccion = q_zone

    if seleccion and seleccion not in MAPA_CORPORAL.get(vista, []):
        seleccion = ""
        st.session_state[estado_key] = ""

    return seleccion


def limpiar_seleccion_svg(state_key: str) -> None:
    st.session_state[f"upp_svg_sel_{state_key}"] = ""


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
    dimensiones = formatear_dimensiones(lesion.get("largo_cm"), lesion.get("ancho_cm"), lesion.get("profundidad_cm"))
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
