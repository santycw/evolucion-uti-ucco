"""
Módulo UPP / decúbito / Braden.

Centraliza opciones, cálculo de Braden y formateo del bloque de piel para
mantener app.py como interfaz y preservar la generación estructurada.
"""

from __future__ import annotations

import re
from typing import Any


# --- MAPA CORPORAL SIMPLE ---
VISTAS_CORPORALES = [
    "Anterior",
    "Posterior",
    "Lateral derecha",
    "Lateral izquierda",
    "Cabeza / cara / dispositivos",
]

MAPA_CORPORAL = {
    "Anterior": [
        "Frente",
        "Mentón",
        "Tórax anterior",
        "Mamas / pliegue submamario",
        "Abdomen",
        "Cresta ilíaca anterior",
        "Rodilla",
        "Tibia / cara anterior pierna",
        "Dorso del pie",
        "Dedos del pie",
        "Otra localización",
    ],
    "Posterior": [
        "Occipital",
        "Pabellón auricular",
        "Escápula",
        "Columna dorsal",
        "Codo",
        "Sacro",
        "Cóccix",
        "Glúteo",
        "Isquion",
        "Hueco poplíteo",
        "Gemelos / pantorrilla",
        "Talón",
        "Planta del pie",
        "Otra localización",
    ],
    "Lateral derecha": [
        "Hombro derecho",
        "Costado torácico derecho",
        "Trocánter derecho",
        "Muslo lateral derecho",
        "Rodilla lateral derecha",
        "Maléolo externo derecho",
        "Pie / borde externo derecho",
        "Otra localización",
    ],
    "Lateral izquierda": [
        "Hombro izquierdo",
        "Costado torácico izquierdo",
        "Trocánter izquierdo",
        "Muslo lateral izquierdo",
        "Rodilla lateral izquierda",
        "Maléolo externo izquierdo",
        "Pie / borde externo izquierdo",
        "Otra localización",
    ],
    "Cabeza / cara / dispositivos": [
        "Nariz / puente nasal",
        "Labio / comisura",
        "Mejilla",
        "Cuero cabelludo",
        "Cuello",
        "Traqueostomía",
        "Zona de máscara / VNI",
        "Zona de tubo / fijación",
        "Zona de CNG / SNG",
        "Zona de catéter / dispositivo médico",
        "Otra localización",
    ],
}

LOCALIZACIONES_UPP = ["", *sorted({zona for zonas in MAPA_CORPORAL.values() for zona in zonas if zona != "Otra localización"}), "Otra localización"]
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
    """String seguro para campos opcionales."""
    return str(valor or "").strip()


def obtener_zonas_mapa(vista: Any) -> list[str]:
    """Devuelve las zonas anatómicas disponibles para la vista elegida."""
    vista_txt = s(vista)
    zonas = MAPA_CORPORAL.get(vista_txt, [])
    return [""] + zonas if zonas else [""]


def resumen_mapa_corporal() -> dict[str, str]:
    """Resumen breve del mapa corporal para mostrar en la UI."""
    return {
        "Anterior": "Frente, mentón, tórax anterior, pliegue submamario, abdomen, cresta ilíaca anterior, rodilla, tibia, dorso del pie, dedos.",
        "Posterior": "Occipital, pabellón auricular, escápula, columna dorsal, codo, sacro, cóccix, glúteo, isquion, hueco poplíteo, gemelos, talón, planta.",
        "Lateral derecha": "Hombro, costado torácico, trocánter, muslo lateral, rodilla lateral, maléolo externo, borde externo del pie.",
        "Lateral izquierda": "Hombro, costado torácico, trocánter, muslo lateral, rodilla lateral, maléolo externo, borde externo del pie.",
        "Cabeza / cara / dispositivos": "Nariz, labio, mejilla, cuero cabelludo, cuello, traqueostomía y zonas asociadas a dispositivos.",
    }


def puntaje_desde_opcion(opcion: Any) -> int:
    """Extrae el puntaje inicial de una opción tipo '3 - texto'."""
    match = re.match(r"\s*(\d+)", str(opcion or ""))
    return int(match.group(1)) if match else 0


def interpretar_braden(puntaje: int | None) -> dict:
    """Interpreta Braden con categorías habituales de riesgo."""
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
    """Calcula Braden total y devuelve componentes e interpretación."""
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
    """Devuelve una línea clínica para una lesión UPP."""
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

    campos = [
        ("lecho", lesion.get("lecho")),
        ("exudado", lesion.get("exudado")),
        ("piel perilesional", lesion.get("perilesional")),
        ("infección", lesion.get("infeccion")),
        ("dolor", lesion.get("dolor")),
    ]
    for nombre, valor in campos:
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
    """Construye el bloque PIEL / UPP / DECÚBITO para la evolución final."""
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
