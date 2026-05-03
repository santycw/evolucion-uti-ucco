"""Validaciones numéricas, cálculo auxiliar y alertas clínicas no bloqueantes."""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple

def p_num(val) -> Optional[float]:
    try:
        texto = str(val).replace(",", ".").strip()
        return float(texto) if texto else None
    except Exception:
        return None

def parse_tension_arterial(ta: str) -> Tuple[Optional[float], Optional[float]]:
    if not ta or "/" not in str(ta):
        return None, None
    try:
        partes = str(ta).split("/")
        if len(partes) != 2:
            return None, None
        return float(partes[0].replace(",", ".").strip()), float(partes[1].replace(",", ".").strip())
    except Exception:
        return None, None

def calcular_tam_pp(ta: str):
    sys_bp, dia_bp = parse_tension_arterial(ta)
    if sys_bp is None or dia_bp is None:
        return None, None, "", ""
    return sys_bp, dia_bp, round((sys_bp + 2 * dia_bp) / 3), int(sys_bp - dia_bp)

def calcular_par(fc, pvc, tam):
    fc_n = p_num(fc)
    pvc_n = p_num(pvc)
    if fc_n is None or pvc_n is None or not tam:
        return ""
    try:
        tam_f = float(tam)
        return f"{(fc_n * pvc_n) / tam_f:.2f}" if tam_f > 0 else ""
    except Exception:
        return ""

def calcular_qtc_bazett(fc, qt) -> str:
    fc_val = p_num(fc)
    qt_val = p_num(qt)
    if fc_val is None or qt_val is None or fc_val <= 0:
        return ""
    return f"{qt_val / math.sqrt(60.0 / fc_val):.0f}"

def _agregar(alertas: List[dict], nivel: str, campo: str, mensaje: str, sugerencia: str = "") -> None:
    alertas.append({"nivel": nivel, "campo": campo, "mensaje": mensaje, "sugerencia": sugerencia})

def _presente(valor: Any) -> bool:
    return str(valor or "").strip() != ""

def generar_validaciones_datos_criticos(valores: Dict[str, Any], auto_scores: Optional[Dict[str, Any]] = None) -> List[dict]:
    """Genera alertas clínicas no bloqueantes para revisión antes de copiar a HC."""
    alertas: List[dict] = []
    auto_scores = auto_scores or {}

    ta = valores.get("ta", "")
    sys_bp, dia_bp = parse_tension_arterial(ta)
    if _presente(ta) and (sys_bp is None or dia_bp is None):
        _agregar(alertas, "revision", "TA", "Formato de tensión arterial no reconocido.", "Usar formato sistólica/diastólica, ej. 120/80.")
    elif sys_bp is not None and dia_bp is not None:
        if sys_bp < dia_bp:
            _agregar(alertas, "revision", "TA", "La sistólica es menor que la diastólica.", "Verificar carga de TA.")
        if sys_bp < 70 or dia_bp < 40:
            _agregar(alertas, "critico", "TA", f"Hipotensión severa: TA {sys_bp:g}/{dia_bp:g} mmHg.", "Verificar perfusión, TAM, vasopresores y conducta.")
        elif sys_bp >= 180 or dia_bp >= 110:
            _agregar(alertas, "advertencia", "TA", f"TA muy elevada: {sys_bp:g}/{dia_bp:g} mmHg.", "Correlacionar con dolor, SCA, ACV, emergencia hipertensiva o drogas vasoactivas.")

    tam = auto_scores.get("tam_val", "")
    if isinstance(tam, (int, float)) and tam < 65:
        _agregar(alertas, "critico", "TAM", f"TAM baja: {tam:g} mmHg.", "Revisar objetivo hemodinámico, perfusión y vasopresores.")

    fc = p_num(valores.get("fc"))
    if fc is not None:
        if fc <= 40:
            _agregar(alertas, "critico", "FC", f"Bradicardia marcada: {fc:g} lpm.", "Correlacionar con perfusión, ECG y fármacos.")
        elif fc >= 130:
            _agregar(alertas, "advertencia", "FC", f"Taquicardia significativa: {fc:g} lpm.", "Evaluar dolor, fiebre, shock, FA, hipovolemia o drogas.")

    fr = p_num(valores.get("fr"))
    if fr is not None and fr >= 30:
        _agregar(alertas, "advertencia", "FR", f"Taquipnea: {fr:g} rpm.", "Correlacionar con trabajo respiratorio, EAB y PaFiO2.")

    sat = p_num(valores.get("sat"))
    if sat is not None:
        if sat < 88:
            _agregar(alertas, "critico", "SatO2", f"SatO2 crítica: {sat:g}%.", "Verificar sensor, vía aérea, oxígeno, EAB y soporte ventilatorio.")
        elif sat < 92:
            _agregar(alertas, "advertencia", "SatO2", f"SatO2 baja: {sat:g}%.", "Revisar oxigenoterapia y objetivo individual.")

    temp = p_num(valores.get("temp"))
    if temp is not None:
        if temp < 35:
            _agregar(alertas, "critico", "Temperatura", f"Hipotermia: {temp:g} °C.", "Correlacionar con shock, exposición, sepsis o postoperatorio.")
        elif temp >= 39:
            _agregar(alertas, "advertencia", "Temperatura", f"Fiebre alta: {temp:g} °C.", "Revisar foco, cultivos, antimicrobianos y control térmico.")

    lactato = p_num(valores.get("lactato"))
    if lactato is not None and lactato >= 4:
        _agregar(alertas, "critico", "Lactato", f"Lactato elevado: {lactato:g} mmol/L.", "Evaluar hipoperfusión/shock y tendencia.")

    ph = p_num(valores.get("ph"))
    if ph is not None:
        if ph < 7.20:
            _agregar(alertas, "critico", "pH", f"Acidemia severa: pH {ph:g}.", "Correlacionar con ventilación, lactato, función renal y causa metabólica/respiratoria.")
        elif ph > 7.55:
            _agregar(alertas, "advertencia", "pH", f"Alcalemia marcada: pH {ph:g}.", "Revisar ventilación, pérdidas digestivas, diuréticos o corrección metabólica.")

    pco2 = p_num(valores.get("pco2"))
    if pco2 is not None:
        if pco2 >= 70:
            _agregar(alertas, "advertencia", "pCO2", f"Hipercapnia importante: {pco2:g} mmHg.", "Correlacionar con ventilación, EPOC, sedación o fatiga respiratoria.")
        elif pco2 < 25:
            _agregar(alertas, "advertencia", "pCO2", f"Hipocapnia marcada: {pco2:g} mmHg.", "Correlacionar con hiperventilación, dolor, sepsis o ventilador.")

    pafi = auto_scores.get("pafi_val")
    if isinstance(pafi, (int, float)):
        if pafi < 100:
            _agregar(alertas, "critico", "PaFiO2", f"PaFiO2 crítica: {pafi:g}.", "Evaluar SDRA, PEEP, pronación, reclutamiento y estrategia ventilatoria.")
        elif pafi < 200:
            _agregar(alertas, "advertencia", "PaFiO2", f"PaFiO2 baja: {pafi:g}.", "Revisar oxigenación, mecánica ventilatoria y tendencia.")

    k = p_num(valores.get("potasio"))
    if k is not None:
        if k > 9:
            _agregar(alertas, "revision", "Potasio", f"Valor de K improbable: {k:g}.", "Revisar si se ingresó 55 en lugar de 5,5.")
        elif k >= 6.0:
            _agregar(alertas, "critico", "Potasio", f"Hiperpotasemia: K {k:g} mEq/L.", "Verificar hemólisis, ECG y tratamiento según protocolo.")
        elif k <= 2.8:
            _agregar(alertas, "critico", "Potasio", f"Hipopotasemia severa: K {k:g} mEq/L.", "Reponer y controlar Mg/ECG según contexto.")

    na = p_num(valores.get("na"))
    if na is not None:
        if na < 120 or na > 160:
            _agregar(alertas, "critico", "Sodio", f"Sodio crítico: Na {na:g} mEq/L.", "Verificar síntomas, osmolaridad, velocidad de corrección y causa.")
        elif na < 125 or na > 155:
            _agregar(alertas, "advertencia", "Sodio", f"Sodio muy alterado: Na {na:g} mEq/L.", "Revisar tendencia y plan de corrección.")

    gluc = p_num(valores.get("gluc"))
    if gluc is not None:
        if gluc < 60:
            _agregar(alertas, "critico", "Glucemia", f"Hipoglucemia: {gluc:g} mg/dL.", "Confirmar y tratar según protocolo.")
        elif gluc > 400:
            _agregar(alertas, "advertencia", "Glucemia", f"Hiperglucemia severa: {gluc:g} mg/dL.", "Revisar cetosis/osmolaridad e insulinoterapia.")

    cr = p_num(valores.get("cr"))
    if cr is not None and cr >= 3:
        _agregar(alertas, "advertencia", "Creatinina", f"Creatinina elevada: {cr:g} mg/dL.", "Correlacionar con diuresis, KDIGO, nefrotóxicos y ajuste de dosis.")

    hb = p_num(valores.get("hb"))
    if hb is not None and hb < 7:
        _agregar(alertas, "advertencia", "Hemoglobina", f"Hb baja: {hb:g} g/dL.", "Correlacionar con sangrado, isquemia, shock y umbral transfusional institucional.")

    plaq = p_num(valores.get("plaq"))
    if plaq is not None:
        plaq_miles = plaq / 1000 if plaq > 2000 else plaq
        if plaq_miles < 20:
            _agregar(alertas, "critico", "Plaquetas", f"Plaquetopenia severa: {plaq_miles:g} mil/mm³.", "Evaluar sangrado, CID, sepsis, drogas y hemoderivados.")
        elif plaq_miles < 50:
            _agregar(alertas, "advertencia", "Plaquetas", f"Plaquetas bajas: {plaq_miles:g} mil/mm³.", "Revisar procedimientos, anticoagulación y tendencia.")

    rin = p_num(valores.get("rin"))
    if rin is not None and rin >= 5:
        _agregar(alertas, "advertencia", "RIN", f"RIN elevado: {rin:g}.", "Revisar anticoagulación, hepatopatía, sangrado y conducta.")

    qtc = p_num(valores.get("ecg_qtc"))
    if qtc is not None and qtc >= 500:
        _agregar(alertas, "advertencia", "QTc", f"QTc prolongado: {qtc:g} ms.", "Revisar K/Mg/Ca y fármacos que prolongan QT.")

    return alertas

def formatear_alerta(alerta: dict) -> str:
    return f"{alerta.get('mensaje', '')} {alerta.get('sugerencia', '')}".strip()

def generar_alertas_basicas(valores: dict) -> list[str]:
    return [formatear_alerta(a) for a in generar_validaciones_datos_criticos(valores)]
