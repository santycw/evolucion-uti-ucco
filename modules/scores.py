"""
Módulo de scores clínicos v2.0.

Incluye:
- cálculo automático conservador de scores UTI/UCCO;
- metadatos para distinguir manual vs automático;
- faltantes críticos por score;
- detalle de componentes para "ver cómo se calculó";
- interpretación bloqueada cuando faltan datos imprescindibles.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from .validaciones import p_num, calcular_tam_pp
from .scores_catalog import obtener_metadata_score


def _presente(valor: Any) -> bool:
    return str(valor or "").strip() != ""


def _bool(datos: Dict[str, Any], clave: str) -> bool:
    return bool(datos.get(clave, False))


def _num_from_value(value_str: Any) -> Optional[float]:
    if value_str is None:
        return None
    if any(txt in str(value_str) for txt in ["Faltan", "Pendiente", "No calculado", "No calculable"]):
        return None
    matches = re.findall(r"-?\d+\.?\d*", str(value_str))
    return float(matches[0]) if matches else None


def _puntaje_news2_fr(fr: float) -> int:
    if fr <= 8:
        return 3
    if fr <= 11:
        return 1
    if fr <= 20:
        return 0
    if fr <= 24:
        return 2
    return 3


def _puntaje_news2_sat(sat: float) -> int:
    if sat <= 91:
        return 3
    if sat <= 93:
        return 2
    if sat <= 95:
        return 1
    return 0


def _puntaje_news2_tas(tas: float) -> int:
    if tas <= 90:
        return 3
    if tas <= 100:
        return 2
    if tas <= 110:
        return 1
    if tas <= 219:
        return 0
    return 3


def _puntaje_news2_fc(fc: float) -> int:
    if fc <= 40:
        return 3
    if fc <= 50:
        return 1
    if fc <= 90:
        return 0
    if fc <= 110:
        return 1
    if fc <= 130:
        return 2
    return 3


def _puntaje_news2_temp(temp: float) -> int:
    if temp <= 35.0:
        return 3
    if temp <= 36.0:
        return 1
    if temp <= 38.0:
        return 0
    if temp <= 39.0:
        return 1
    return 2


def calcular_scores_contexto(datos: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula valores numéricos derivados y scores automáticos."""
    ta = datos.get("ta", "")
    sys_bp, dia_bp, tam_val, pp_val = calcular_tam_pp(ta)

    glasgow = str(datos.get("glasgow", "") or "")
    gl_val = 15
    if glasgow:
        try:
            gl_val = int(glasgow.split("/")[0])
        except Exception:
            pass

    fio2 = datos.get("fio2", 21)
    try:
        fio2 = float(fio2)
    except Exception:
        fio2 = 21.0

    pafi_manual = datos.get("pafi_manual", "")
    po2 = datos.get("po2", "")

    pafi_val = p_num(pafi_manual)
    po2_n = p_num(po2)

    if not pafi_val and po2_n and fio2:
        pafi_final = str(int(po2_n / (fio2 / 100)))
        pafi_val = float(pafi_final)
    else:
        pafi_final = pafi_manual

    plaq_n = p_num(datos.get("plaq", ""))
    bt_n = p_num(datos.get("bt", ""))
    cr_n = p_num(datos.get("cr", ""))
    fr_n = p_num(datos.get("fr", ""))
    fc_n = p_num(datos.get("fc", ""))
    pvc_n = p_num(datos.get("pvc", ""))
    urea_n = p_num(datos.get("urea", ""))
    edad_n = int(datos.get("edad_paciente", 0) or 0)
    temp_n = p_num(datos.get("temp", ""))
    ph_f = p_num(datos.get("ph", ""))
    pco2_f = p_num(datos.get("pco2", ""))
    na_f = p_num(datos.get("na", ""))
    k_f = p_num(datos.get("potasio", ""))
    hto_f = p_num(datos.get("hto", ""))
    gb_f = p_num(datos.get("gb", ""))
    rin_n = p_num(datos.get("rin", ""))
    sat_n = p_num(datos.get("sat", ""))
    lactato_n = p_num(datos.get("lactato", ""))
    tropo_n = p_num(datos.get("tropo", ""))

    paciente_ventilado = bool(datos.get("paciente_ventilado", False))
    infusiones_automatizadas = datos.get("infusiones_automatizadas", []) or []

    details: Dict[str, List[str]] = {}
    missing: Dict[str, List[str]] = {}

    # --- CÁLCULO SOFA ---
    s_pts = 0
    sofa_detalle: List[str] = []
    sofa_missing: List[str] = []

    if pafi_val:
        resp_pts = 0
        if pafi_val < 100 and paciente_ventilado:
            resp_pts = 4
        elif pafi_val < 200 and paciente_ventilado:
            resp_pts = 3
        elif pafi_val < 300:
            resp_pts = 2
        elif pafi_val < 400:
            resp_pts = 1
        s_pts += resp_pts
        sofa_detalle.append(f"Respiratorio PaFiO2 {pafi_val:g}: {resp_pts} pts")
    else:
        sofa_missing.append("PaFiO2 o PaO2+FiO2")

    if plaq_n:
        p_val = plaq_n / 1000 if plaq_n > 2000 else plaq_n
        coag_pts = 0
        if p_val < 20:
            coag_pts = 4
        elif p_val < 50:
            coag_pts = 3
        elif p_val < 100:
            coag_pts = 2
        elif p_val < 150:
            coag_pts = 1
        s_pts += coag_pts
        sofa_detalle.append(f"Coagulación plaquetas {p_val:g} mil/mm³: {coag_pts} pts")
    else:
        sofa_missing.append("Plaquetas")

    if bt_n:
        hep_pts = 0
        if bt_n >= 12.0:
            hep_pts = 4
        elif bt_n >= 6.0:
            hep_pts = 3
        elif bt_n >= 2.0:
            hep_pts = 2
        elif bt_n >= 1.2:
            hep_pts = 1
        s_pts += hep_pts
        sofa_detalle.append(f"Hepático BT {bt_n:g}: {hep_pts} pts")
    else:
        sofa_missing.append("Bilirrubina total")

    cv_pts = 1 if tam_val and tam_val < 70 else 0
    cv_txt = f"Cardiovascular TAM {tam_val}: {cv_pts} pts" if tam_val else "Cardiovascular sin TAM cargada"
    for inf in infusiones_automatizadas:
        inf_l = str(inf).lower()
        if "dobutamina" in inf_l or "dopamina" in inf_l:
            cv_pts = max(cv_pts, 2)
            cv_txt = f"Cardiovascular por inotrópicos/vasopresores cargados: {cv_pts} pts"
        if "adrenalina" in inf_l or "noradrenalina" in inf_l:
            cv_pts = 3
            cv_txt = "Cardiovascular por adrenalina/noradrenalina cargada: 3 pts"
    s_pts += cv_pts
    sofa_detalle.append(cv_txt)
    if not tam_val and not infusiones_automatizadas:
        sofa_missing.append("TAM o vasopresores")

    neuro_pts = 0
    if gl_val < 6:
        neuro_pts = 4
    elif gl_val <= 9:
        neuro_pts = 3
    elif gl_val <= 12:
        neuro_pts = 2
    elif gl_val <= 14:
        neuro_pts = 1
    s_pts += neuro_pts
    sofa_detalle.append(f"Neurológico Glasgow {gl_val}: {neuro_pts} pts")

    if cr_n:
        renal_pts = 0
        if cr_n >= 5.0:
            renal_pts = 4
        elif cr_n >= 3.5:
            renal_pts = 3
        elif cr_n >= 2.0:
            renal_pts = 2
        elif cr_n >= 1.2:
            renal_pts = 1
        s_pts += renal_pts
        sofa_detalle.append(f"Renal Cr {cr_n:g}: {renal_pts} pts")
    else:
        sofa_missing.append("Creatinina")

    details["SOFA"] = sofa_detalle
    missing["SOFA"] = sofa_missing

    # --- qSOFA & CURB-65 ---
    q_detalle = [
        f"Glasgow <15: {'sí' if gl_val < 15 else 'no'}",
        f"FR ≥22: {'sí' if fr_n is not None and fr_n >= 22 else 'no'}",
        f"TAS ≤100: {'sí' if sys_bp is not None and sys_bp <= 100 else 'no'}",
    ]
    q_missing = []
    if fr_n is None:
        q_missing.append("FR")
    if sys_bp is None:
        q_missing.append("TA")
    q_calc = sum([
        gl_val < 15,
        fr_n is not None and fr_n >= 22,
        sys_bp is not None and sys_bp <= 100,
    ])
    details["qSOFA"] = q_detalle
    missing["qSOFA"] = q_missing

    c_calc = sum([
        gl_val < 15,
        urea_n is not None and urea_n >= 42,
        fr_n is not None and fr_n >= 30,
        (sys_bp is not None and sys_bp < 90) or (dia_bp is not None and dia_bp <= 60),
        edad_n >= 65,
    ])
    details["CURB-65"] = [
        f"Confusión/Glasgow <15: {'sí' if gl_val < 15 else 'no'}",
        f"Urea ≥42 mg/dL: {'sí' if urea_n is not None and urea_n >= 42 else 'no'}",
        f"FR ≥30: {'sí' if fr_n is not None and fr_n >= 30 else 'no'}",
        f"TA baja: {'sí' if (sys_bp is not None and sys_bp < 90) or (dia_bp is not None and dia_bp <= 60) else 'no'}",
        f"Edad ≥65: {'sí' if edad_n >= 65 else 'no'}",
    ]
    missing["CURB-65"] = [n for n, cond in [("Urea", urea_n is None), ("FR", fr_n is None), ("TA", sys_bp is None or dia_bp is None)] if cond]

    # --- SIRS ---
    sirs_pts = 0
    sirs_detalle = []
    sirs_missing = []
    if temp_n is not None:
        criterio = temp_n > 38 or temp_n < 36
        sirs_pts += int(criterio)
        sirs_detalle.append(f"Temperatura >38 o <36: {'sí' if criterio else 'no'}")
    else:
        sirs_missing.append("Temperatura")
    if fc_n is not None:
        criterio = fc_n > 90
        sirs_pts += int(criterio)
        sirs_detalle.append(f"FC >90: {'sí' if criterio else 'no'}")
    else:
        sirs_missing.append("FC")
    if fr_n is not None or pco2_f is not None:
        criterio = (fr_n is not None and fr_n > 20) or (pco2_f is not None and pco2_f < 32)
        sirs_pts += int(criterio)
        sirs_detalle.append(f"FR >20 o pCO2 <32: {'sí' if criterio else 'no'}")
    else:
        sirs_missing.append("FR o pCO2")
    if gb_f is not None:
        gb_val = gb_f / 1000 if gb_f > 100 else gb_f
        criterio = gb_val < 4 or gb_val > 12
        sirs_pts += int(criterio)
        sirs_detalle.append(f"GB <4 o >12 mil/mm³: {'sí' if criterio else 'no'}")
    else:
        sirs_missing.append("GB")
    details["SIRS"] = sirs_detalle
    missing["SIRS"] = sirs_missing

    # --- NEWS2 ---
    news2_str = "No calculable"
    news2_pts: Optional[int] = None
    news2_missing = []
    news2_detalle = []
    if fr_n is None:
        news2_missing.append("FR")
    if sat_n is None:
        news2_missing.append("SatO2")
    if sys_bp is None:
        news2_missing.append("TA")
    if fc_n is None:
        news2_missing.append("FC")
    if temp_n is None:
        news2_missing.append("Temperatura")
    if not news2_missing:
        oxigeno = bool(fio2 and fio2 > 21)
        via_aerea = str(datos.get("via_aerea", "") or "").lower()
        if via_aerea and "aire ambiente" not in via_aerea and "aa" not in via_aerea:
            oxigeno = True
        fr_pts = _puntaje_news2_fr(fr_n)
        sat_pts = _puntaje_news2_sat(sat_n)
        ox_pts = 2 if oxigeno else 0
        tas_pts = _puntaje_news2_tas(sys_bp)
        fc_pts = _puntaje_news2_fc(fc_n)
        conc_pts = 3 if gl_val < 15 else 0
        temp_pts = _puntaje_news2_temp(temp_n)
        news2_pts = fr_pts + sat_pts + ox_pts + tas_pts + fc_pts + conc_pts + temp_pts
        news2_str = f"{news2_pts} pts (Auto)"
        news2_detalle = [
            f"FR {fr_n:g}: {fr_pts} pts",
            f"SatO2 {sat_n:g}%: {sat_pts} pts",
            f"Oxígeno suplementario: {ox_pts} pts",
            f"TAS {sys_bp:g}: {tas_pts} pts",
            f"FC {fc_n:g}: {fc_pts} pts",
            f"Conciencia/Glasgow {gl_val}: {conc_pts} pts",
            f"Temperatura {temp_n:g}: {temp_pts} pts",
        ]
    details["NEWS2"] = news2_detalle
    missing["NEWS2"] = news2_missing

    # --- Índice de Shock ---
    shock_index_str = "No calculable"
    if fc_n is not None and sys_bp:
        shock_index = fc_n / sys_bp
        shock_index_str = f"{shock_index:.2f} (Auto)"
        details["Índice de Shock"] = [f"FC/TAS = {fc_n:g}/{sys_bp:g} = {shock_index:.2f}"]
        missing["Índice de Shock"] = []
    else:
        details["Índice de Shock"] = []
        missing["Índice de Shock"] = [n for n, cond in [("FC", fc_n is None), ("TA", sys_bp is None)] if cond]

    # --- ROX ---
    rox_str = "No calculable"
    if sat_n is not None and fr_n is not None and fio2:
        rox = (sat_n / (fio2 / 100.0)) / fr_n
        rox_str = f"{rox:.2f} (Auto)"
        details["ROX"] = [f"(SatO2/FiO2)/FR = ({sat_n:g}/{fio2/100.0:.2f})/{fr_n:g} = {rox:.2f}"]
        missing["ROX"] = []
    else:
        details["ROX"] = []
        missing["ROX"] = [n for n, cond in [("SatO2", sat_n is None), ("FR", fr_n is None), ("FiO2", not fio2)] if cond]

    # --- Clasificación de PaFi / SDRA ---
    pafi_clase_str = "No calculable"
    if pafi_val:
        if pafi_val < 100:
            clase = "Hipoxemia severa"
        elif pafi_val < 200:
            clase = "Hipoxemia moderada"
        elif pafi_val < 300:
            clase = "Hipoxemia leve"
        else:
            clase = "Sin hipoxemia significativa por PaFi"
        pafi_clase_str = f"{int(pafi_val)} - {clase} (Auto)"
        details["PaFiO2 / SDRA"] = [f"PaFiO2 calculada o manual: {pafi_val:g}", "Clasificación orientativa según puntos de corte de oxigenación."]
        missing["PaFiO2 / SDRA"] = []
    else:
        details["PaFiO2 / SDRA"] = []
        missing["PaFiO2 / SDRA"] = ["PaO2 o PaFiO2 manual"]

    # --- APACHE II AUTOMÁTICO ---
    apache_auto_pts = 0
    faltan_datos_apache = False
    apache_missing = []
    apache_detalle = []

    edad_pts = 0
    if edad_n >= 75:
        edad_pts = 6
    elif edad_n >= 65:
        edad_pts = 5
    elif edad_n >= 55:
        edad_pts = 3
    elif edad_n >= 45:
        edad_pts = 2
    apache_auto_pts += edad_pts
    apache_detalle.append(f"Edad {edad_n}: {edad_pts} pts")

    if temp_n is not None:
        pts = 0
        if temp_n >= 41 or temp_n <= 29.9:
            pts = 4
        elif temp_n >= 39 or 30 <= temp_n <= 31.9:
            pts = 3
        elif 32 <= temp_n <= 33.9:
            pts = 2
        elif 38.5 <= temp_n <= 38.9 or 34 <= temp_n <= 35.9:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"Temperatura {temp_n:g}: {pts} pts")
    else:
        faltan_datos_apache = True
        apache_missing.append("Temperatura")

    if tam_val:
        pts = 0
        if tam_val >= 160 or tam_val <= 49:
            pts = 4
        elif 130 <= tam_val <= 159:
            pts = 3
        elif 110 <= tam_val <= 129 or 50 <= tam_val <= 69:
            pts = 2
        apache_auto_pts += pts
        apache_detalle.append(f"TAM {tam_val}: {pts} pts")
    else:
        faltan_datos_apache = True
        apache_missing.append("TAM/TA")

    if fc_n is not None:
        pts = 0
        if fc_n >= 180 or fc_n <= 39:
            pts = 4
        elif 140 <= fc_n <= 179 or 40 <= fc_n <= 54:
            pts = 3
        elif 110 <= fc_n <= 139 or 55 <= fc_n <= 69:
            pts = 2
        apache_auto_pts += pts
        apache_detalle.append(f"FC {fc_n:g}: {pts} pts")
    else:
        faltan_datos_apache = True
        apache_missing.append("FC")

    if fr_n is not None:
        pts = 0
        if fr_n >= 50 or fr_n <= 5:
            pts = 4
        elif 35 <= fr_n <= 49:
            pts = 3
        elif 6 <= fr_n <= 9:
            pts = 2
        elif 25 <= fr_n <= 34 or 10 <= fr_n <= 11:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"FR {fr_n:g}: {pts} pts")
    else:
        faltan_datos_apache = True
        apache_missing.append("FR")

    if fio2 and po2_n:
        pts = 0
        if fio2 >= 50 and pco2_f:
            fio2_dec = fio2 / 100.0
            AaDO2 = (fio2_dec * 713) - (pco2_f / 0.8) - po2_n
            if AaDO2 >= 500:
                pts = 4
            elif AaDO2 >= 350:
                pts = 3
            elif AaDO2 >= 200:
                pts = 2
            apache_detalle.append(f"A-aDO2 {AaDO2:.0f}: {pts} pts")
        elif fio2 < 50:
            if po2_n < 55:
                pts = 4
            elif po2_n <= 60:
                pts = 3
            elif po2_n <= 70:
                pts = 1
            apache_detalle.append(f"PaO2 {po2_n:g}: {pts} pts")
        apache_auto_pts += pts
    else:
        faltan_datos_apache = True
        apache_missing.append("PaO2/FiO2")

    if ph_f:
        pts = 0
        if ph_f >= 7.7 or ph_f < 7.15:
            pts = 4
        elif 7.6 <= ph_f <= 7.69 or 7.15 <= ph_f <= 7.24:
            pts = 3
        elif 7.25 <= ph_f <= 7.32:
            pts = 2
        elif 7.5 <= ph_f <= 7.59:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"pH {ph_f:g}: {pts} pts")

    if na_f:
        pts = 0
        if na_f >= 180 or na_f <= 110:
            pts = 4
        elif 160 <= na_f <= 179 or 111 <= na_f <= 119:
            pts = 3
        elif 155 <= na_f <= 159 or 120 <= na_f <= 129:
            pts = 2
        elif 150 <= na_f <= 154:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"Na {na_f:g}: {pts} pts")

    if k_f:
        pts = 0
        if k_f >= 7 or k_f <= 2.4:
            pts = 4
        elif 6 <= k_f <= 6.9:
            pts = 3
        elif 2.5 <= k_f <= 2.9:
            pts = 2
        elif 5.5 <= k_f <= 5.9 or 3 <= k_f <= 3.4:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"K {k_f:g}: {pts} pts")

    if cr_n:
        cr_pts = 0
        if cr_n >= 3.6:
            cr_pts = 4
        elif 1.5 <= cr_n <= 3.49:
            cr_pts = 2
        elif cr_n < 0.6:
            cr_pts = 2
        if datos.get("apache_ira", False):
            cr_pts *= 2
        apache_auto_pts += cr_pts
        apache_detalle.append(f"Cr {cr_n:g}: {cr_pts} pts")

    if hto_f:
        pts = 0
        if hto_f >= 60 or hto_f < 20:
            pts = 4
        elif 50 <= hto_f <= 59.9 or 20 <= hto_f <= 29.9:
            pts = 2
        elif 46 <= hto_f <= 49.9:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"Hto {hto_f:g}: {pts} pts")

    if gb_f:
        gb_val = gb_f / 1000 if gb_f > 100 else gb_f
        pts = 0
        if gb_val >= 40 or gb_val < 1:
            pts = 4
        elif 20 <= gb_val <= 39.9 or 1 <= gb_val <= 2.9:
            pts = 2
        elif 15 <= gb_val <= 19.9:
            pts = 1
        apache_auto_pts += pts
        apache_detalle.append(f"GB {gb_val:g}: {pts} pts")

    apache_auto_pts += (15 - gl_val)
    apache_detalle.append(f"Glasgow {gl_val}: {15 - gl_val} pts")

    apache_cronico = datos.get("apache_cronico", 0)
    if apache_cronico:
        apache_auto_pts += apache_cronico
    apache_detalle.append(f"Enfermedad crónica: {apache_cronico} pts")

    apache_final_str = f"{apache_auto_pts} (Auto)" if not faltan_datos_apache else "Faltan gases/vitales"
    details["APACHE II"] = apache_detalle
    missing["APACHE II"] = apache_missing

    # --- MELD & CHILD-PUGH ---
    meld_auto_str = "Faltan datos (Cr, BT, INR, Na)"
    meld_detalle = []
    meld_missing = []
    if not cr_n:
        meld_missing.append("Creatinina")
    if not bt_n:
        meld_missing.append("Bilirrubina total")
    if not rin_n:
        meld_missing.append("RIN/INR")
    if cr_n and bt_n and rin_n:
        cr_meld = max(1.0, cr_n)
        bt_meld = max(1.0, bt_n)
        inr_meld = max(1.0, rin_n)
        if datos.get("meld_dialisis", False):
            cr_meld = 4.0
        meld_score = 3.78 * math.log(bt_meld) + 11.2 * math.log(inr_meld) + 9.57 * math.log(cr_meld) + 6.43
        meld_score = round(meld_score)
        meld_detalle.append(f"MELD = 3.78 ln(BT) + 11.2 ln(INR) + 9.57 ln(Cr) + 6.43 = {meld_score}")
        if na_f and 125 <= na_f <= 137:
            meld_na = meld_score + 1.32 * (137 - na_f) - (0.033 * meld_score * (137 - na_f))
            meld_auto_str = f"{round(meld_na)} (MELD-Na Auto)"
            meld_detalle.append(f"Corrección por Na {na_f:g}: MELD-Na {round(meld_na)}")
        else:
            meld_auto_str = f"{meld_score} (Auto)"
            if not na_f:
                meld_missing.append("Sodio para MELD-Na")
    details["MELD"] = meld_detalle
    missing["MELD"] = meld_missing

    child_auto_str = "Faltan datos"
    child_detalle = []
    child_missing = []
    albumina = datos.get("albumina", 0.0) or 0.0
    if not bt_n:
        child_missing.append("Bilirrubina total")
    if not rin_n:
        child_missing.append("RIN/INR")
    if not albumina:
        child_missing.append("Albúmina")
    if bt_n and rin_n and albumina > 0:
        pts_child = 0
        bt_pts = 1 if bt_n < 2 else 2 if bt_n <= 3 else 3
        rin_pts = 1 if rin_n < 1.7 else 2 if rin_n <= 2.2 else 3
        alb_pts = 1 if albumina > 3.5 else 2 if albumina >= 2.8 else 3
        pts_child += bt_pts + rin_pts + alb_pts
        child_detalle.extend([f"BT {bt_n:g}: {bt_pts} pts", f"RIN {rin_n:g}: {rin_pts} pts", f"Albúmina {albumina:g}: {alb_pts} pts"])
        child_encef = str(datos.get("child_encef", "Ausente"))
        child_ascitis = str(datos.get("child_ascitis", "Ausente"))
        encef_pts = 2 if "I-II" in child_encef else 3 if "III-IV" in child_encef else 1
        ascitis_pts = 2 if "Leve" in child_ascitis else 3 if "Severa" in child_ascitis else 1
        pts_child += encef_pts + ascitis_pts
        child_detalle.extend([f"Encefalopatía {child_encef}: {encef_pts} pts", f"Ascitis {child_ascitis}: {ascitis_pts} pts"])
        clase = "A" if pts_child <= 6 else "B" if pts_child <= 9 else "C"
        child_auto_str = f"{pts_child} pts - Clase {clase} (Auto)"
    details["Child-Pugh"] = child_detalle
    missing["Child-Pugh"] = child_missing

    # --- BISAP ---
    bisap_auto_str = "Faltan datos"
    bisap_missing = []
    bisap_detalle = []
    if urea_n is not None:
        bisap_pts = 0
        criterios = [
            (urea_n > 53.5, f"Urea >53.5: {'sí' if urea_n > 53.5 else 'no'}"),
            (gl_val < 15, f"Glasgow <15: {'sí' if gl_val < 15 else 'no'}"),
            (edad_n > 60, f"Edad >60: {'sí' if edad_n > 60 else 'no'}"),
            (datos.get("bisap_derrame", False), f"Derrame pleural: {'sí' if datos.get('bisap_derrame', False) else 'no'}"),
        ]
        for cond, txt in criterios:
            bisap_pts += int(cond)
            bisap_detalle.append(txt)
        sirs_para_bisap = sirs_pts >= 2 and not sirs_missing
        bisap_pts += int(sirs_para_bisap)
        bisap_detalle.append(f"SIRS ≥2: {'sí' if sirs_para_bisap else 'no'}")
        bisap_auto_str = f"{bisap_pts}/5 (Auto)"
    else:
        bisap_missing.append("Urea")
    if sirs_missing:
        bisap_missing.append("Datos SIRS completos")
    details["BISAP"] = bisap_detalle
    missing["BISAP"] = bisap_missing

    # --- CHA₂DS₂-VA ---
    chadva_score = 0
    chadva_str = ""
    chadva_detalle = []
    if datos.get("is_fa", False):
        componentes = [
            (datos.get("chf", False), "Insuficiencia cardíaca", 1),
            (datos.get("hta", False), "HTA", 1),
            (edad_n >= 75, "Edad ≥75", 2),
            (65 <= edad_n <= 74, "Edad 65-74", 1),
            (datos.get("diabetes", False), "Diabetes", 1),
            (datos.get("stroke_fa", False), "ACV/TIA previo", 2),
            (datos.get("vascular", False), "Enfermedad vascular", 1),
        ]
        for cond, label, pts in componentes:
            if cond:
                chadva_score += pts
            chadva_detalle.append(f"{label}: {pts if cond else 0} pts")
        chadva_str = f"{chadva_score} pts (Auto)"
    details["CHA₂DS₂-VA (ESC 2024)"] = chadva_detalle
    missing["CHA₂DS₂-VA (ESC 2024)"] = []

    # --- HAS-BLED ---
    hasbled_score = 0
    hasbled_detalle = []
    if datos.get("is_fa", False):
        componentes_has = [
            (datos.get("hasbled_hta_no_controlada", False), "HTA no controlada", 1),
            (datos.get("hasbled_renal", False), "Función renal alterada", 1),
            (datos.get("hasbled_hepatica", False), "Función hepática alterada", 1),
            (datos.get("stroke_fa", False), "ACV previo", 1),
            (datos.get("hasbled_sangrado", False), "Sangrado previo/predisposición", 1),
            (datos.get("hasbled_inr_labil", False), "INR lábil", 1),
            (edad_n >= 65, "Edad ≥65", 1),
            (datos.get("hasbled_drogas", False), "Fármacos predisponentes", 1),
            (datos.get("hasbled_alcohol", False), "Alcohol", 1),
        ]
        for cond, label, pts in componentes_has:
            if cond:
                hasbled_score += pts
            hasbled_detalle.append(f"{label}: {pts if cond else 0} pts")
    hasbled_str = f"{hasbled_score} pts (Auto)" if datos.get("is_fa", False) else ""
    details["HAS-BLED"] = hasbled_detalle
    missing["HAS-BLED"] = []

    # --- TIMI SCA UA/NSTEMI ---
    timi_auto_score = 0
    timi_detalle = []
    if datos.get("is_isquemia", False):
        criterios_timi = [
            (edad_n >= 65, "Edad ≥65", 1),
            (datos.get("timi_riesgo_ge3", False), "≥3 factores de riesgo coronario", 1),
            (datos.get("timi_cad", False), "Estenosis coronaria conocida ≥50%", 1),
            (datos.get("timi_aspirina", False), "AAS en últimos 7 días", 1),
            (datos.get("timi_angina", False), "≥2 episodios de angina 24 h", 1),
            (datos.get("timi_st", False), "Desviación ST", 1),
            (datos.get("timi_marcadores", False), "Marcadores cardíacos positivos", 1),
        ]
        for cond, label, pts in criterios_timi:
            if cond:
                timi_auto_score += pts
            timi_detalle.append(f"{label}: {pts if cond else 0} pts")
    timi_auto_str = f"{timi_auto_score}/7 (Auto)" if datos.get("is_isquemia", False) else ""
    details["TIMI SCA"] = timi_detalle
    missing["TIMI SCA"] = []

    # --- HEART ---
    heart_str = "No calculable"
    heart_missing = []
    heart_detalle = []
    if datos.get("is_isquemia", False):
        heart_historia = datos.get("heart_historia", "")
        heart_ecg = datos.get("heart_ecg", "")
        heart_riesgo = datos.get("heart_riesgo", "")
        heart_troponina = datos.get("heart_troponina", "")
        if not _presente(heart_historia):
            heart_missing.append("Historia clínica HEART")
        if not _presente(heart_ecg):
            heart_missing.append("ECG HEART")
        if not _presente(heart_riesgo):
            heart_missing.append("Factores de riesgo HEART")
        if not _presente(heart_troponina):
            heart_missing.append("Troponina HEART")
        if not heart_missing:
            def _score_select(valor: str) -> int:
                m = re.search(r"(\d+)\s*pt", str(valor))
                return int(m.group(1)) if m else 0
            h_hist = _score_select(heart_historia)
            h_ecg = _score_select(heart_ecg)
            h_risk = _score_select(heart_riesgo)
            h_trop = _score_select(heart_troponina)
            h_age = 2 if edad_n >= 65 else 1 if edad_n >= 45 else 0
            heart_total = h_hist + h_ecg + h_age + h_risk + h_trop
            heart_str = f"{heart_total}/10 (Auto)"
            heart_detalle = [
                f"Historia: {h_hist} pts",
                f"ECG: {h_ecg} pts",
                f"Edad {edad_n}: {h_age} pts",
                f"Factores de riesgo: {h_risk} pts",
                f"Troponina: {h_trop} pts",
            ]
    details["HEART"] = heart_detalle
    missing["HEART"] = heart_missing

    # --- TFG ---
    tfg_str = ""
    if cr_n and cr_n > 0:
        sexo_paciente = datos.get("sexo_paciente", "Masculino")
        factor_mdrd = 0.742 if sexo_paciente == "Femenino" else 1.0
        mdrd_val = 175 * (cr_n ** -1.154) * (edad_n ** -0.203) * factor_mdrd
        tfg_str = f"{mdrd_val:.1f} ml/min (MDRD4 Auto)"
        details["TFG"] = [f"MDRD4: 175 × Cr^-1.154 × edad^-0.203 × factor sexo = {mdrd_val:.1f} ml/min"]
        missing["TFG"] = []
    else:
        details["TFG"] = []
        missing["TFG"] = ["Creatinina"]

    return {
        "sys_bp": sys_bp,
        "dia_bp": dia_bp,
        "tam_val": tam_val,
        "pp_val": pp_val,
        "gl_val": gl_val,
        "pafi_val": pafi_val,
        "pafi_final": pafi_final,
        "plaq_n": plaq_n,
        "bt_n": bt_n,
        "cr_n": cr_n,
        "fr_n": fr_n,
        "fc_n": fc_n,
        "pvc_n": pvc_n,
        "urea_n": urea_n,
        "edad_n": edad_n,
        "temp_n": temp_n,
        "ph_f": ph_f,
        "pco2_f": pco2_f,
        "na_f": na_f,
        "k_f": k_f,
        "hto_f": hto_f,
        "gb_f": gb_f,
        "rin_n": rin_n,
        "sat_n": sat_n,
        "lactato_n": lactato_n,
        "tropo_n": tropo_n,
        "s_pts": s_pts,
        "q_calc": q_calc,
        "c_calc": c_calc,
        "sirs_pts": sirs_pts,
        "news2_str": news2_str,
        "shock_index_str": shock_index_str,
        "rox_str": rox_str,
        "pafi_clase_str": pafi_clase_str,
        "apache_final_str": apache_final_str,
        "meld_auto_str": meld_auto_str,
        "child_auto_str": child_auto_str,
        "bisap_auto_str": bisap_auto_str,
        "chadva_score": chadva_score,
        "chadva_str": chadva_str,
        "hasbled_score": hasbled_score,
        "hasbled_str": hasbled_str,
        "timi_auto_str": timi_auto_str,
        "heart_str": heart_str,
        "tfg_str": tfg_str,
        "details": details,
        "missing": missing,
    }


def evaluar_riesgo_score(score_name: str, value_str: Any, faltantes: Optional[List[str]] = None) -> Tuple[str, str]:
    """Devuelve nivel visual e interpretación. Bloquea interpretación si faltan datos."""
    faltantes = faltantes or []
    if faltantes:
        return "bloqueado", f"Interpretación bloqueada: faltan {', '.join(faltantes)}."
    if not value_str or "Faltan" in str(value_str) or "Pendiente" in str(value_str) or "No calculado" in str(value_str) or "No calculable" in str(value_str):
        return "pendiente", "Pendiente de datos suficientes."

    val_num = _num_from_value(value_str)
    score_upper = score_name.upper()

    if "SOFA" in score_upper and "QSOFA" not in score_upper and val_num is not None:
        if val_num <= 6:
            return "bajo", "Mortalidad estimada baja/intermedia según SOFA. Mantener seguimiento seriado."
        if val_num <= 9:
            return "intermedio", "Riesgo intermedio. Revalorar tendencia y soporte orgánico."
        if val_num <= 12:
            return "alto", "Alto riesgo. Requiere vigilancia intensiva y soporte guiado por metas."
        return "critico", "Riesgo crítico. Priorizar soporte multiorgánico y reevaluación frecuente."

    if "QSOFA" in score_upper and val_num is not None:
        return ("alto", "qSOFA ≥2: alto riesgo clínico; no usar como único screening de sepsis.") if val_num >= 2 else ("bajo", "qSOFA <2; no descarta sepsis si el contexto clínico sugiere infección.")

    if "SIRS" in score_upper and val_num is not None:
        return ("alto", "SIRS ≥2: respuesta inflamatoria sistémica; correlacionar con foco infeccioso/no infeccioso.") if val_num >= 2 else ("bajo", "SIRS <2.")

    if "NEWS2" in score_upper and val_num is not None:
        if val_num >= 7:
            return "critico", "NEWS2 ≥7: riesgo clínico alto. Escalada/reevaluación urgente."
        if val_num >= 5:
            return "alto", "NEWS2 5-6: riesgo alto. Requiere revisión clínica prioritaria."
        if val_num >= 3:
            return "intermedio", "NEWS2 3-4: riesgo intermedio; controlar tendencia."
        return "bajo", "NEWS2 bajo."

    if "ÍNDICE DE SHOCK" in score_upper and val_num is not None:
        if val_num >= 1.3:
            return "critico", "Índice de shock muy elevado; correlacionar con hipoperfusión/shock."
        if val_num >= 0.9:
            return "alto", "Índice de shock elevado. Revisar perfusión, volemia y vasopresores."
        return "bajo", "Índice de shock sin elevación significativa."

    if "ROX" in score_upper and val_num is not None:
        if val_num < 3.85:
            return "alto", "ROX bajo: riesgo de fracaso de oxigenoterapia de alto flujo si aplica."
        if val_num < 4.88:
            return "intermedio", "ROX intermedio; controlar tendencia."
        return "bajo", "ROX favorable si el contexto es oxigenoterapia de alto flujo."

    if "PAFIO2" in score_upper or "SDRA" in score_upper:
        if val_num is not None:
            if val_num < 100:
                return "critico", "Hipoxemia severa por PaFiO2."
            if val_num < 200:
                return "alto", "Hipoxemia moderada por PaFiO2."
            if val_num < 300:
                return "intermedio", "Hipoxemia leve por PaFiO2."
            return "bajo", "PaFiO2 sin hipoxemia significativa."

    if "APACHE" in score_upper and val_num is not None:
        if val_num <= 14:
            return "bajo", "Mortalidad estimada baja/intermedia por APACHE II."
        if val_num <= 24:
            return "alto", "Riesgo elevado por APACHE II."
        return "critico", "Riesgo muy alto por APACHE II."

    if "MELD" in score_upper and val_num is not None:
        if val_num <= 9:
            return "bajo", "Mortalidad 3 meses baja por MELD."
        if val_num <= 19:
            return "intermedio", "Riesgo intermedio por MELD."
        if val_num <= 29:
            return "alto", "Alto riesgo por MELD."
        return "critico", "Riesgo muy alto por MELD."

    if "CHILD" in score_upper:
        upper = str(value_str).upper()
        if "CLASE A" in upper or upper.strip() == "A":
            return "bajo", "Child-Pugh A."
        if "CLASE B" in upper or upper.strip() == "B":
            return "intermedio", "Child-Pugh B."
        if "CLASE C" in upper or upper.strip() == "C":
            return "alto", "Child-Pugh C."

    if "BISAP" in score_upper and val_num is not None:
        return ("alto", "BISAP ≥3: mayor riesgo de mortalidad/falla orgánica.") if val_num >= 3 else ("bajo", "BISAP 0-2: menor riesgo inicial.")

    if "CURB-65" in score_upper and val_num is not None:
        if val_num <= 1:
            return "bajo", "CURB-65 bajo."
        if val_num == 2:
            return "intermedio", "CURB-65 intermedio. Considerar hospitalización según contexto."
        return "alto", "CURB-65 alto. Considerar manejo intensivo según contexto."

    if "CHA₂DS₂-VA" in score_upper and val_num is not None:
        if val_num == 0:
            return "bajo", "Bajo riesgo tromboembólico."
        if val_num == 1:
            return "intermedio", "Riesgo intermedio: considerar anticoagulación oral según ESC 2024."
        return "alto", "Riesgo tromboembólico elevado: anticoagulación oral recomendada si no hay contraindicaciones."

    if "HAS-BLED" in score_upper and val_num is not None:
        return ("alto", "HAS-BLED ≥3: alto riesgo de sangrado; no contraindica anticoagulación, exige corregir factores modificables.") if val_num >= 3 else ("bajo", "HAS-BLED <3.")

    if "TIMI" in score_upper and val_num is not None:
        if val_num <= 2:
            return "bajo", "TIMI bajo."
        if val_num <= 4:
            return "intermedio", "TIMI intermedio."
        return "alto", "TIMI alto."

    if "HEART" in score_upper and val_num is not None:
        if val_num <= 3:
            return "bajo", "HEART bajo."
        if val_num <= 6:
            return "intermedio", "HEART intermedio."
        return "alto", "HEART alto."

    if "TFG" in score_upper and val_num is not None:
        if val_num < 15:
            return "critico", "TFG G5. Ajustar fármacos y evaluar soporte renal según contexto."
        if val_num < 30:
            return "alto", "TFG G4. Ajustar fármacos y seguimiento estrecho."
        if val_num < 60:
            return "intermedio", "TFG G3. Ajustar dosis y controlar tendencia."
        return "bajo", "TFG conservada o levemente disminuida."

    return "info", "Interpretación orientativa no disponible para este score."


def evaluar_morbimortalidad_sugerencias(score_name: str, value_str: Any) -> str:
    """Compatibilidad: devuelve interpretación breve en texto."""
    nivel, texto = evaluar_riesgo_score(score_name, value_str, [])
    if nivel in ["pendiente", "bloqueado"]:
        return ""
    return f" [{texto}]" if texto else ""


def _origen_valor(manual: Any, auto_val: Any, pendiente: str = "Pendiente") -> Tuple[Any, str]:
    if _presente(manual):
        return manual, "Manual"
    if _presente(auto_val):
        return auto_val, "Auto"
    return pendiente, "Pendiente"


def _crear_item(nombre: str, valor: Any, origen: str, auto: Dict[str, Any], detalle_key: Optional[str] = None) -> Dict[str, Any]:
    detalle_key = detalle_key or nombre
    faltantes = list((auto.get("missing") or {}).get(detalle_key, []))
    detalle = list((auto.get("details") or {}).get(detalle_key, []))
    catalogo = obtener_metadata_score(nombre)
    bloquear = bool(catalogo.get("bloquear_si_faltan", True))
    if origen == "Manual":
        # El valor manual puede interpretarse, pero se informa que no fue calculado por el sistema.
        faltantes_visibles: List[str] = []
    elif bloquear:
        faltantes_visibles = faltantes
    else:
        faltantes_visibles = []
    nivel, interpretacion = evaluar_riesgo_score(nombre, valor, faltantes_visibles)
    return {
        "nombre": nombre,
        "valor": valor,
        "origen": origen,
        "faltantes": faltantes,
        "faltantes_bloqueantes": faltantes_visibles,
        "detalle": detalle,
        "nivel": nivel,
        "interpretacion": interpretacion,
        "catalogo": catalogo,
    }


def motor_scores(flags: Dict[str, bool], manuales: Dict[str, Any], auto: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Arma la lista de scores activos según diagnóstico detectado, con metadatos visuales."""
    resultados: List[Dict[str, Any]] = []

    # Scores generales UTI visibles cuando hay datos críticos cargados o diagnósticos activos.
    hay_datos_generales = any(_presente(auto.get(k)) for k in ["news2_str", "shock_index_str", "rox_str", "pafi_clase_str"])
    if hay_datos_generales and any([flags.get("is_sepsis"), flags.get("is_nac"), flags.get("is_ic"), flags.get("is_isquemia"), flags.get("is_renal")]):
        items_generales = [
            _crear_item("NEWS2", auto.get("news2_str", "No calculable"), "Auto", auto),
            _crear_item("Índice de Shock", auto.get("shock_index_str", "No calculable"), "Auto", auto),
            _crear_item("ROX", auto.get("rox_str", "No calculable"), "Auto", auto),
            _crear_item("PaFiO2 / SDRA", auto.get("pafi_clase_str", "No calculable"), "Auto", auto),
        ]
        resultados.append({"categoria": "UTI / Seguridad general", "items": items_generales, "scores": {i["nombre"]: i["valor"] for i in items_generales}})

    if flags.get("is_sepsis"):
        sofa_val, sofa_origen = _origen_valor(manuales.get("sofa", ""), str(auto.get("s_pts", "")))
        qsofa_val, qsofa_origen = _origen_valor(manuales.get("qsofa", ""), str(auto.get("q_calc", "")))
        apache_val, apache_origen = _origen_valor(manuales.get("apache", ""), auto.get("apache_final_str", ""))
        items = [
            _crear_item("SOFA", sofa_val, sofa_origen, auto),
            _crear_item("qSOFA", qsofa_val, qsofa_origen, auto),
            _crear_item("SIRS", f"{auto.get('sirs_pts', '')}/4 (Auto)", "Auto", auto),
            _crear_item("APACHE II", apache_val, apache_origen, auto),
        ]
        resultados.append({"categoria": "Sepsis", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_isquemia"):
        killip_val, killip_origen = _origen_valor(manuales.get("killip", ""), "")
        grace_val, grace_origen = _origen_valor(manuales.get("grace", ""), "")
        timi_val, timi_origen = _origen_valor(manuales.get("timi", ""), auto.get("timi_auto_str", ""))
        items = [
            _crear_item("Killip", killip_val, killip_origen, auto),
            _crear_item("GRACE", grace_val, grace_origen, auto),
            _crear_item("TIMI SCA", timi_val, timi_origen, auto),
            _crear_item("HEART", auto.get("heart_str", "No calculable"), "Auto", auto),
        ]
        resultados.append({"categoria": "SCA/IAM", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_ic"):
        items = [
            _crear_item("NYHA", manuales.get("nyha") if manuales.get("nyha") else "Pendiente", "Manual" if manuales.get("nyha") else "Pendiente", auto),
            _crear_item("Stevenson", manuales.get("stevenson") if manuales.get("stevenson") else "Pendiente", "Manual" if manuales.get("stevenson") else "Pendiente", auto),
            _crear_item("AHA", manuales.get("aha_ic") if manuales.get("aha_ic") else "Pendiente", "Manual" if manuales.get("aha_ic") else "Pendiente", auto),
        ]
        resultados.append({"categoria": "Insuficiencia Cardíaca", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_renal"):
        items = [
            _crear_item("KDIGO IRA", manuales.get("kdigo_ira") if manuales.get("kdigo_ira") else "Pendiente", "Manual" if manuales.get("kdigo_ira") else "Pendiente", auto),
            _crear_item("ERC", manuales.get("kdigo_erc") if manuales.get("kdigo_erc") else "Pendiente", "Manual" if manuales.get("kdigo_erc") else "Pendiente", auto),
            _crear_item("TFG", auto.get("tfg_str") if auto.get("tfg_str") else "No calculado", "Auto", auto),
        ]
        resultados.append({"categoria": "Renal", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_hepato"):
        child_val, child_origen = _origen_valor(manuales.get("child", ""), auto.get("child_auto_str", ""))
        meld_val, meld_origen = _origen_valor(manuales.get("meld", ""), auto.get("meld_auto_str", ""))
        items = [
            _crear_item("Child-Pugh", child_val, child_origen, auto),
            _crear_item("MELD", meld_val, meld_origen, auto),
        ]
        resultados.append({"categoria": "Hepatopatía", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_pancreas"):
        bisap_val, bisap_origen = _origen_valor(manuales.get("bisap", ""), auto.get("bisap_auto_str", ""))
        items = [
            _crear_item("BISAP", bisap_val, bisap_origen, auto),
            _crear_item("Ranson", manuales.get("ranson") if manuales.get("ranson") else "Pendiente", "Manual" if manuales.get("ranson") else "Pendiente", auto),
            _crear_item("Balthazar", manuales.get("balthazar") if manuales.get("balthazar") else "Pendiente", "Manual" if manuales.get("balthazar") else "Pendiente", auto),
        ]
        resultados.append({"categoria": "Pancreatitis", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_acv"):
        items = [
            _crear_item("NIHSS", manuales.get("nihss") if manuales.get("nihss") else "Pendiente", "Manual" if manuales.get("nihss") else "Pendiente", auto),
            _crear_item("mRS", manuales.get("mrs") if manuales.get("mrs") else "Pendiente", "Manual" if manuales.get("mrs") else "Pendiente", auto),
        ]
        resultados.append({"categoria": "ACV", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_hsa"):
        items = [
            _crear_item("Hunt & Hess", manuales.get("hunt") if manuales.get("hunt") else "Pendiente", "Manual" if manuales.get("hunt") else "Pendiente", auto),
            _crear_item("Fisher", manuales.get("fisher") if manuales.get("fisher") else "Pendiente", "Manual" if manuales.get("fisher") else "Pendiente", auto),
        ]
        resultados.append({"categoria": "HSA", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_nac"):
        curb_val, curb_origen = _origen_valor(manuales.get("curb65", ""), str(auto.get("c_calc", "")))
        items = [
            _crear_item("CURB-65", curb_val, curb_origen, auto),
            _crear_item("PSI", manuales.get("psi") if manuales.get("psi") else "Pendiente", "Manual" if manuales.get("psi") else "Pendiente", auto),
        ]
        resultados.append({"categoria": "Neumonía", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    if flags.get("is_fa"):
        items = [
            _crear_item("CHA₂DS₂-VA (ESC 2024)", auto.get("chadva_str", ""), "Auto", auto),
            _crear_item("HAS-BLED", auto.get("hasbled_str", ""), "Auto", auto),
        ]
        resultados.append({"categoria": "Fibrilación Auricular", "items": items, "scores": {i["nombre"]: i["valor"] for i in items}})

    return resultados


def formatear_scores_detectados(scores_globales: List[Dict[str, Any]]) -> List[str]:
    """Devuelve líneas listas para mostrar/imprimir con origen e interpretación."""
    texto_scores: List[str] = []

    for grupo in scores_globales:
        partes_evaluadas = []
        if "items" in grupo:
            for item in grupo["items"]:
                origen = item.get("origen", "")
                valor = item.get("valor", "")
                interpretacion = item.get("interpretacion", "")
                if item.get("faltantes_bloqueantes"):
                    interpretacion = f"Interpretación bloqueada: faltan {', '.join(item.get('faltantes_bloqueantes', []))}."
                partes_evaluadas.append(f"{item.get('nombre')}: {valor} [{origen}] - {interpretacion}")
        else:
            for k, v in grupo.get("scores", {}).items():
                evaluacion = evaluar_morbimortalidad_sugerencias(k, v)
                partes_evaluadas.append(f"{k}: {v}{evaluacion}")
        lineas_detalle = " | ".join(partes_evaluadas)
        linea = f"{grupo['categoria']} -> {lineas_detalle}"
        texto_scores.append(f"- {linea}")

    return texto_scores
