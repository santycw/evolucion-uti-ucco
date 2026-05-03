"""
Catálogo institucional de scores clínicos.

Objetivo:
- centralizar metadatos de cada score;
- mostrar datos requeridos, estado de implementación, categoría y referencia;
- permitir una experiencia tipo biblioteca de calculadoras clínicas, sin copiar
  contenido propietario de sitios externos.

Los textos son orientativos y deben ser validados/adaptados al protocolo local.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


SCORES_CATALOG: Dict[str, Dict[str, Any]] = {
    # --- UTI / Seguridad general ---
    "NEWS2": {
        "categoria": "UTI / Seguridad general",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["FR", "SatO2", "TA", "FC", "temperatura", "estado de conciencia", "oxígeno suplementario"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Detección temprana de deterioro clínico y necesidad de escalada de cuidados.",
        "referencia": "Royal College of Physicians. National Early Warning Score 2 (NEWS2).",
        "nota": "Usar como apoyo de seguridad; no reemplaza evaluación clínica ni criterios de UTI.",
    },
    "Índice de Shock": {
        "categoria": "UTI / Seguridad general",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["FC", "TAS"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Tamizaje rápido de inestabilidad hemodinámica/hipoperfusión.",
        "referencia": "Allgöwer M, Burri C. Shock index concept.",
        "nota": "Interpretar con contexto: beta-bloqueantes, marcapasos, embarazo, dolor, fiebre o arritmias pueden modificarlo.",
    },
    "ROX": {
        "categoria": "Respiratorio / UTI",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["SatO2", "FiO2", "FR"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Apoyo para valorar riesgo de fracaso de oxigenoterapia de alto flujo cuando aplica.",
        "referencia": "Roca O et al. ROX index for high-flow nasal cannula outcomes.",
        "nota": "Validar especialmente en pacientes con cánula nasal de alto flujo; no extrapolar automáticamente a todos los dispositivos.",
    },
    "PaFiO2 / SDRA": {
        "categoria": "Respiratorio / UTI",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["PaO2", "FiO2", "PEEP/CPAP si se clasifica SDRA"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación orientativa de hipoxemia y severidad de SDRA por oxigenación.",
        "referencia": "Berlin Definition of ARDS. JAMA 2012.",
        "nota": "La definición formal de SDRA requiere temporalidad, imagen compatible, origen no cardiogénico y PEEP/CPAP ≥5.",
    },
    # --- Sepsis ---
    "SOFA": {
        "categoria": "Sepsis / Falla orgánica",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["PaFiO2", "plaquetas", "bilirrubina", "TAM/vasopresores", "Glasgow", "creatinina/diuresis"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Cuantificación de disfunción orgánica y seguimiento seriado.",
        "referencia": "Vincent JL et al. The SOFA score. Intensive Care Med 1996.",
        "nota": "Más útil como tendencia que como valor aislado.",
    },
    "qSOFA": {
        "categoria": "Sepsis / Tamizaje",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["FR", "TAS", "estado mental/Glasgow"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Identificación rápida de mayor riesgo fuera de UTI.",
        "referencia": "Singer M et al. Sepsis-3. JAMA 2016; Surviving Sepsis Campaign 2021.",
        "nota": "No debe usarse como único método de screening de sepsis.",
    },
    "SIRS": {
        "categoria": "Sepsis / Inflamación",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["temperatura", "FC", "FR o pCO2", "GB"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Respuesta inflamatoria sistémica; sensible pero poco específica.",
        "referencia": "ACCP/SCCM Consensus Conference criteria.",
        "nota": "Puede activarse por causas infecciosas y no infecciosas.",
    },
    "APACHE II": {
        "categoria": "UTI / Severidad global",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["edad", "temperatura", "TAM", "FC", "FR", "oxigenación", "pH", "Na", "K", "creatinina", "hematocrito", "GB", "Glasgow", "enfermedad crónica"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación de severidad en UTI; útil para auditoría y comparación poblacional.",
        "referencia": "Knaus WA et al. APACHE II. Crit Care Med 1985.",
        "nota": "No usar para decidir limitación terapéutica individual sin contexto clínico.",
    },
    # --- Neumonía / respiratorio ---
    "CURB-65": {
        "categoria": "Neumonía",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["confusión/Glasgow", "urea", "FR", "TA", "edad"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación inicial de gravedad en neumonía adquirida en la comunidad.",
        "referencia": "Lim WS et al. Thorax 2003; BTS CAP guidance.",
        "nota": "Complementar con juicio clínico, oxigenación, comorbilidades y contexto social.",
    },
    "PSI": {
        "categoria": "Neumonía",
        "estado": "manual_pendiente_auto",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["demografía", "comorbilidades", "examen físico", "laboratorio", "Rx"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación de mortalidad en NAC.",
        "referencia": "Fine MJ et al. Pneumonia Severity Index. NEJM 1997.",
        "nota": "Pendiente de automatización completa por cantidad de variables.",
    },
    # --- Cardiología / UCCO ---
    "CHA₂DS₂-VA (ESC 2024)": {
        "categoria": "FA / Tromboembolismo",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["IC/disfunción VI", "HTA", "edad", "diabetes", "ACV/TIA previo", "enfermedad vascular"],
        "bloquear_si_faltan": False,
        "uso_clinico": "Estimación de riesgo tromboembólico en fibrilación auricular según enfoque ESC 2024 sin categoría de sexo.",
        "referencia": "2024 ESC Guidelines for the management of atrial fibrillation.",
        "nota": "Confirmar contraindicaciones, sangrado activo, preferencias y contexto clínico antes de anticoagular.",
    },
    "HAS-BLED": {
        "categoria": "FA / Sangrado",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["HTA no controlada", "renal", "hepática", "ACV", "sangrado", "INR lábil", "edad", "drogas", "alcohol"],
        "bloquear_si_faltan": False,
        "uso_clinico": "Identifica riesgo de sangrado y factores modificables en anticoagulación.",
        "referencia": "Pisters R et al. HAS-BLED. Chest 2010; ESC AF guidelines.",
        "nota": "Un HAS-BLED alto no contraindica anticoagulación por sí solo; obliga a corregir factores modificables.",
    },
    "TIMI SCA": {
        "categoria": "SCA / UCCO",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["edad ≥65", "≥3 factores de riesgo", "CAD ≥50%", "AAS reciente", "angina reciente", "desviación ST", "biomarcadores"],
        "bloquear_si_faltan": False,
        "uso_clinico": "Estratificación de riesgo en SCA sin elevación del ST.",
        "referencia": "Antman EM et al. TIMI risk score. JAMA 2000.",
        "nota": "Aplicar al fenotipo clínico correcto; no reemplaza GRACE ni criterio invasivo según guías.",
    },
    "HEART": {
        "categoria": "Dolor torácico / UCCO",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["historia", "ECG", "edad", "factores de riesgo", "troponina"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación inicial de pacientes con dolor torácico en emergencia/UCCO.",
        "referencia": "Six AJ et al. HEART score. Neth Heart J 2008.",
        "nota": "Debe integrarse con ECG seriado, troponina seriada y criterio clínico.",
    },
    "GRACE": {
        "categoria": "SCA / UCCO",
        "estado": "manual_pendiente_auto",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["edad", "FC", "TAS", "creatinina", "Killip", "paro cardíaco", "ST", "enzimas"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación pronóstica en SCA; útil para estrategia invasiva y riesgo de muerte/eventos.",
        "referencia": "GRACE investigators; ESC ACS guidelines.",
        "nota": "Pendiente de automatización; actualmente se permite ingreso manual.",
    },
    "Killip": {
        "categoria": "SCA / UCCO",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["examen clínico", "congestión pulmonar", "shock"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación clínica de insuficiencia cardíaca en IAM.",
        "referencia": "Killip T, Kimball JT. Am J Cardiol 1967.",
        "nota": "Requiere evaluación clínica directa.",
    },
    "NYHA": {
        "categoria": "Insuficiencia cardíaca",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["síntomas con actividad", "limitación funcional"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación funcional de insuficiencia cardíaca.",
        "referencia": "New York Heart Association functional classification.",
        "nota": "Puede no reflejar adecuadamente pacientes sedados, ventilados o inmovilizados.",
    },
    "Stevenson": {
        "categoria": "Insuficiencia cardíaca",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["congestión", "perfusión"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Perfil hemodinámico clínico en IC avanzada/descompensada.",
        "referencia": "Stevenson LW. Clinical profiles in advanced heart failure.",
        "nota": "Debe reevaluarse dinámicamente ante diuresis, vasodilatadores o inotrópicos.",
    },
    "AHA": {
        "categoria": "Insuficiencia cardíaca",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["factores de riesgo", "cardiopatía estructural", "síntomas", "IC avanzada"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estadificación evolutiva de insuficiencia cardíaca.",
        "referencia": "ACC/AHA/HFSA Heart Failure Guidelines.",
        "nota": "Complementa, no reemplaza, clase funcional NYHA.",
    },
    # --- Renal ---
    "TFG": {
        "categoria": "Renal",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": False,
        "inputs_requeridos": ["creatinina", "edad", "sexo"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estimación de filtrado glomerular para clasificación renal y ajuste de fármacos.",
        "referencia": "MDRD Study equation; KDIGO CKD guidance.",
        "nota": "En UTI puede ser imprecisa si creatinina no está en estado estable.",
    },
    "KDIGO IRA": {
        "categoria": "Renal",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["creatinina basal/actual", "diuresis", "tiempo de evolución"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación de injuria renal aguda.",
        "referencia": "KDIGO Clinical Practice Guideline for Acute Kidney Injury.",
        "nota": "Pendiente automatización con tendencia de creatinina y diuresis horaria.",
    },
    "ERC": {
        "categoria": "Renal",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["TFG", "albuminuria", "persistencia ≥3 meses"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación de enfermedad renal crónica.",
        "referencia": "KDIGO CKD guideline.",
        "nota": "No diagnosticar ERC solo por creatinina aguda en UTI.",
    },
    # --- Hepático / digestivo ---
    "MELD": {
        "categoria": "Hepatopatía",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["creatinina", "bilirrubina", "RIN", "sodio para MELD-Na", "diálisis"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación de severidad/pronóstico en hepatopatía avanzada.",
        "referencia": "MELD / MELD-Na models; UNOS/Mayo derivations.",
        "nota": "Verificar unidades y situación de diálisis antes de interpretar.",
    },
    "Child-Pugh": {
        "categoria": "Hepatopatía",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["bilirrubina", "RIN/TP", "albúmina", "ascitis", "encefalopatía"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación de cirrosis y reserva hepática.",
        "referencia": "Child-Turcotte-Pugh classification.",
        "nota": "Ascitis y encefalopatía requieren juicio clínico.",
    },
    "BISAP": {
        "categoria": "Pancreatitis",
        "estado": "implementado",
        "permite_auto": True,
        "permite_manual": True,
        "inputs_requeridos": ["urea", "estado mental", "SIRS", "edad", "derrame pleural"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estratificación temprana de gravedad en pancreatitis aguda.",
        "referencia": "Wu BU et al. BISAP. Gut 2008.",
        "nota": "Complementar con evolución clínica, falla orgánica y estudios por imagen.",
    },
    "Ranson": {
        "categoria": "Pancreatitis",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["variables al ingreso", "variables a 48 h"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Score histórico de gravedad en pancreatitis.",
        "referencia": "Ranson JHC. Prognostic signs and pancreatitis severity.",
        "nota": "Requiere datos a 48 h; evitar interpretar precozmente como completo.",
    },
    "Balthazar": {
        "categoria": "Pancreatitis",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["TC abdominal", "inflamación", "colecciones", "necrosis si CTSI"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Clasificación tomográfica de pancreatitis.",
        "referencia": "Balthazar EJ. CT severity index.",
        "nota": "La indicación y timing de TC dependen del contexto clínico.",
    },
    # --- Neuro ---
    "NIHSS": {
        "categoria": "Neurología",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["evaluación neurológica NIHSS completa"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Cuantificación de déficit neurológico en ACV.",
        "referencia": "NIH Stroke Scale.",
        "nota": "Requiere entrenamiento; no automatizable con datos generales de UTI.",
    },
    "mRS": {
        "categoria": "Neurología",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["situación funcional"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Discapacidad funcional post-ACV.",
        "referencia": "Modified Rankin Scale.",
        "nota": "Diferenciar basal vs actual.",
    },
    "Hunt & Hess": {
        "categoria": "Hemorragia subaracnoidea",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["clínica neurológica", "cefalea", "déficit", "nivel de conciencia"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Gravedad clínica en HSA aneurismática.",
        "referencia": "Hunt WE, Hess RM. J Neurosurg 1968.",
        "nota": "Complementar con Fisher/imagen y evaluación neuroquirúrgica.",
    },
    "Fisher": {
        "categoria": "Hemorragia subaracnoidea",
        "estado": "manual",
        "permite_auto": False,
        "permite_manual": True,
        "inputs_requeridos": ["TC de cráneo"],
        "bloquear_si_faltan": True,
        "uso_clinico": "Estimación de riesgo de vasoespasmo por carga hemática en TC.",
        "referencia": "Fisher CM et al. Neurosurgery 1980.",
        "nota": "Considerar Fisher modificado según protocolo local.",
    },
}


_ALIASES = {
    "PAFIO2 / SDRA": "PaFiO2 / SDRA",
    "PAFI / SDRA": "PaFiO2 / SDRA",
    "CHADSVA": "CHA₂DS₂-VA (ESC 2024)",
    "CHA2DS2-VA": "CHA₂DS₂-VA (ESC 2024)",
    "CHA₂DS₂-VA": "CHA₂DS₂-VA (ESC 2024)",
    "HASBLED": "HAS-BLED",
    "TIMI": "TIMI SCA",
    "TIMI SCA": "TIMI SCA",
    "CHILD": "Child-Pugh",
    "CHILD-PUGH": "Child-Pugh",
    "MDRD": "TFG",
    "TFG MDRD4": "TFG",
    "HUNT & HESS": "Hunt & Hess",
    "HUNT": "Hunt & Hess",
}


def _canonical_key(nombre: str) -> str:
    limpio = str(nombre or "").strip()
    if limpio in SCORES_CATALOG:
        return limpio
    upper = limpio.upper()
    if upper in _ALIASES:
        return _ALIASES[upper]
    for key in SCORES_CATALOG:
        if key.upper() == upper:
            return key
    return limpio


def obtener_metadata_score(nombre: str) -> Dict[str, Any]:
    """Devuelve metadatos normalizados para un score."""
    key = _canonical_key(nombre)
    meta = dict(SCORES_CATALOG.get(key, {}))
    if meta:
        meta.setdefault("nombre", key)
    return meta


def obtener_catalogo_scores() -> Dict[str, Dict[str, Any]]:
    """Devuelve una copia superficial del catálogo completo."""
    return {k: dict(v, nombre=k) for k, v in SCORES_CATALOG.items()}


def agrupar_catalogo_por_categoria() -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa scores por categoría para mostrar en UI."""
    grupos: Dict[str, List[Dict[str, Any]]] = {}
    for nombre, meta in obtener_catalogo_scores().items():
        categoria = meta.get("categoria", "Otros")
        grupos.setdefault(categoria, []).append(meta)
    for categoria in grupos:
        grupos[categoria].sort(key=lambda item: item.get("nombre", ""))
    return dict(sorted(grupos.items(), key=lambda kv: kv[0]))


def resumen_estado_catalogo() -> Dict[str, int]:
    """Conteo simple por estado de implementación."""
    resumen: Dict[str, int] = {}
    for meta in SCORES_CATALOG.values():
        estado = meta.get("estado", "sin_estado")
        resumen[estado] = resumen.get(estado, 0) + 1
    return resumen
