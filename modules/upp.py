"""
Módulo UPP / decúbito / Braden.

Centraliza opciones, cálculo de Braden, representación visual del mapa corporal
(anterior/posterior) y formateo del bloque de piel para mantener app.py como
interfaz y preservar la generación estructurada.
"""

from __future__ import annotations

import re
from typing import Any

import streamlit as st


# --- MAPA CORPORAL VISUAL SIMPLE (ANTERIOR / POSTERIOR) ---
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


def resumen_mapa_corporal() -> dict[str, str]:
    return {
        "Anterior": "Cara, hombro/clavícula, tórax anterior, pliegue submamario, abdomen, cresta ilíaca anterior, periné, muslo anterior, rodilla, tibia, maléolo medial, dorso y dedos del pie.",
        "Posterior": "Occipital, pabellón auricular, escápula, columna dorsal, codo, sacro/cóccix, glúteo, isquion, trocánter, muslo posterior, hueco poplíteo, pantorrilla, talón y planta del pie.",
    }


def _extraer_numero_zona(zona: str) -> str:
    match = re.match(r"\s*(\d+)", str(zona or ""))
    return match.group(1) if match else str(zona or "")


def _texto_zona_sin_numero(zona: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", str(zona or "")).strip()


def resumen_mapa_corporal() -> dict[str, str]:
    return {
        "Anterior": "Cara, hombro/clavícula, tórax anterior, pliegue submamario, abdomen, cresta ilíaca anterior, periné, muslo anterior, rodilla, tibia, maléolo medial, dorso y dedos del pie.",
        "Posterior": "Occipital, pabellón auricular, escápula, columna dorsal, codo, sacro/cóccix, glúteo, isquion, trocánter, muslo posterior, hueco poplíteo, pantorrilla, talón y planta del pie.",
    }


MAPA_CLICK_LAYOUT = {
    "Anterior": [
        [None, None, "1. Frente / cara", None, None],
        [None, None, "2. Oreja / región malar", None, None],
        [None, "3. Hombro / clavícula", "4. Tórax anterior", None, None],
        [None, None, "5. Mamas / pliegue submamario", None, None],
        [None, None, "6. Abdomen", None, None],
        [None, None, "7. Cresta ilíaca anterior", None, None],
        [None, None, "8. Periné / región inguinal", None, None],
        [None, None, "9. Muslo anterior", None, None],
        [None, None, "10. Rodilla", None, None],
        [None, None, "11. Tibia / cara anterior pierna", None, None],
        [None, None, "12. Maléolo medial", None, None],
        [None, None, "13. Dorso del pie", None, None],
        [None, None, "14. Dedos del pie", None, None],
        [None, None, "15. Otra localización anterior", None, None],
    ],
    "Posterior": [
        [None, None, "1. Occipital", None, None],
        [None, None, "2. Pabellón auricular", None, None],
        [None, "3. Hombro / escápula", "4. Columna dorsal", None, None],
        [None, "5. Codo / olécranon", None, None, None],
        [None, None, "6. Sacro / cóccix", None, None],
        [None, None, "7. Glúteo", None, None],
        [None, None, "8. Isquion", None, None],
        [None, None, "9. Trocánter", None, None],
        [None, None, "10. Muslo posterior", None, None],
        [None, None, "11. Hueco poplíteo", None, None],
        [None, None, "12. Gemelos / pantorrilla", None, None],
        [None, None, "13. Talón", None, None],
        [None, None, "14. Planta del pie", None, None],
        [None, None, "15. Otra localización posterior", None, None],
    ],
}


def render_mapa_clickeable(vista: str, state_key: str) -> str:
    """Renderiza un mapa corporal clickeable con botones y devuelve la zona seleccionada."""
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    estado_key = f"{state_key}_seleccion"
    layout = MAPA_CLICK_LAYOUT.get(vista, [])
    zonas_validas = MAPA_CORPORAL.get(vista, [])

    seleccion_actual = st.session_state.get(estado_key, "")
    if seleccion_actual and seleccion_actual not in zonas_validas:
        st.session_state[estado_key] = ""
        seleccion_actual = ""

    st.markdown(
        f"<div style='border:1px solid #cbd5e1;border-radius:12px;padding:12px;background:#f8fafc;'>"
        f"<div style='font-weight:700;margin-bottom:6px'>Mapa corporal {vista.lower()} clickeable</div>"
        f"<div style='font-size:12px;color:#475569;margin-bottom:8px'>Haga clic sobre el número/zona anatómica que corresponda a la escara o lesión por presión.</div>",
        unsafe_allow_html=True,
    )

    for fila in layout:
        cols = st.columns(5, gap='small')
        for i, zona in enumerate(fila):
            with cols[i]:
                if zona:
                    numero = _extraer_numero_zona(zona)
                    etiqueta = f"✅ {numero}" if zona == seleccion_actual else numero
                    if st.button(etiqueta, key=f"{state_key}_{vista}_{numero}", help=_texto_zona_sin_numero(zona), use_container_width=True):
                        st.session_state[estado_key] = zona
                        seleccion_actual = zona
                else:
                    st.markdown("<div style='height:2.3rem'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([4,1])
    with c1:
        if seleccion_actual:
            st.success(f"Zona seleccionada: {seleccion_actual}")
        else:
            st.info("Todavía no hay una zona anatómica seleccionada.")
    with c2:
        if st.button("Limpiar", key=f"{state_key}_limpiar"):
            st.session_state[estado_key] = ""
            seleccion_actual = ""
            st.rerun()

    with st.expander("Ver referencia anatómica del mapa", expanded=False):
        for zona in zonas_validas:
            st.markdown(f"- **{_extraer_numero_zona(zona)}**: {_texto_zona_sin_numero(zona)}")

    st.markdown("</div>", unsafe_allow_html=True)
    return seleccion_actual


def render_silueta_corporal(vista: str) -> str:
    """Compatibilidad retroactiva: conserva una vista no interactiva cuando sea necesario."""
    vista = vista if vista in VISTAS_CORPORALES else "Anterior"
    zonas = MAPA_CORPORAL.get(vista, [])
    items = "".join([f"<li style='margin-bottom:3px'>{zona}</li>" for zona in zonas])
    return (
        f"<div style='border:1px solid #cbd5e1;border-radius:12px;padding:12px;background:#f8fafc'>"
        f"<div style='font-weight:700;margin-bottom:6px'>Mapa corporal {vista.lower()}</div>"
        f"<ol style='padding-left:18px;margin-top:8px'>{items}</ol>"
        f"</div>"
    )


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
    if any(valor <= 0 for valor in componentes.values()):
        puntaje = None
    else:
        puntaje = sum(componentes.values())
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
