"""
Módulo de scores clínicos.

Contiene cálculos automáticos y motor de armado de scores, separado del UI.
No modifica las fórmulas originales: solo las encapsula para mantenimiento.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List

from .validaciones import p_num, calcular_tam_pp


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

    paciente_ventilado = bool(datos.get("paciente_ventilado", False))
    infusiones_automatizadas = datos.get("infusiones_automatizadas", []) or []

    # --- CÁLCULO SOFA ---
    s_pts = 0
    if pafi_val:
        if pafi_val < 100 and paciente_ventilado:
            s_pts += 4
        elif pafi_val < 200 and paciente_ventilado:
            s_pts += 3
        elif pafi_val < 300:
            s_pts += 2
        elif pafi_val < 400:
            s_pts += 1

    if plaq_n:
        p_val = plaq_n / 1000 if plaq_n > 2000 else plaq_n
        if p_val < 20:
            s_pts += 4
        elif p_val < 50:
            s_pts += 3
        elif p_val < 100:
            s_pts += 2
        elif p_val < 150:
            s_pts += 1

    if bt_n:
        if bt_n >= 12.0:
            s_pts += 4
        elif bt_n >= 6.0:
            s_pts += 3
        elif bt_n >= 2.0:
            s_pts += 2
        elif bt_n >= 1.2:
            s_pts += 1

    cv_pts = 1 if tam_val and tam_val < 70 else 0
    for inf in infusiones_automatizadas:
        inf_l = str(inf).lower()
        if "dobutamina" in inf_l or "dopamina" in inf_l:
            cv_pts = max(cv_pts, 2)
        if "adrenalina" in inf_l or "noradrenalina" in inf_l:
            cv_pts = 3
    s_pts += cv_pts

    if gl_val < 6:
        s_pts += 4
    elif gl_val <= 9:
        s_pts += 3
    elif gl_val <= 12:
        s_pts += 2
    elif gl_val <= 14:
        s_pts += 1

    if cr_n:
        if cr_n >= 5.0:
            s_pts += 4
        elif cr_n >= 3.5:
            s_pts += 3
        elif cr_n >= 2.0:
            s_pts += 2
        elif cr_n >= 1.2:
            s_pts += 1

    # --- CÁLCULO qSOFA & CURB-65 ---
    q_calc = sum([
        gl_val < 15,
        fr_n is not None and fr_n >= 22,
        sys_bp is not None and sys_bp <= 100,
    ])

    c_calc = sum([
        gl_val < 15,
        urea_n is not None and urea_n >= 42,
        fr_n is not None and fr_n >= 30,
        (sys_bp is not None and sys_bp < 90) or (dia_bp is not None and dia_bp <= 60),
        edad_n >= 65,
    ])

    # --- CÁLCULO APACHE II AUTOMÁTICO ---
    apache_auto_pts = 0
    faltan_datos_apache = False

    if edad_n >= 75:
        apache_auto_pts += 6
    elif edad_n >= 65:
        apache_auto_pts += 5
    elif edad_n >= 55:
        apache_auto_pts += 3
    elif edad_n >= 45:
        apache_auto_pts += 2

    if temp_n is not None:
        if temp_n >= 41 or temp_n <= 29.9:
            apache_auto_pts += 4
        elif temp_n >= 39 or 30 <= temp_n <= 31.9:
            apache_auto_pts += 3
        elif 32 <= temp_n <= 33.9:
            apache_auto_pts += 2
        elif 38.5 <= temp_n <= 38.9 or 34 <= temp_n <= 35.9:
            apache_auto_pts += 1
    else:
        faltan_datos_apache = True

    if tam_val:
        if tam_val >= 160 or tam_val <= 49:
            apache_auto_pts += 4
        elif 130 <= tam_val <= 159:
            apache_auto_pts += 3
        elif 110 <= tam_val <= 129 or 50 <= tam_val <= 69:
            apache_auto_pts += 2
    else:
        faltan_datos_apache = True

    if fc_n is not None:
        if fc_n >= 180 or fc_n <= 39:
            apache_auto_pts += 4
        elif 140 <= fc_n <= 179 or 40 <= fc_n <= 54:
            apache_auto_pts += 3
        elif 110 <= fc_n <= 139 or 55 <= fc_n <= 69:
            apache_auto_pts += 2
    else:
        faltan_datos_apache = True

    if fr_n is not None:
        if fr_n >= 50 or fr_n <= 5:
            apache_auto_pts += 4
        elif 35 <= fr_n <= 49:
            apache_auto_pts += 3
        elif 6 <= fr_n <= 9:
            apache_auto_pts += 2
        elif 25 <= fr_n <= 34 or 10 <= fr_n <= 11:
            apache_auto_pts += 1
    else:
        faltan_datos_apache = True

    if fio2 and po2_n:
        if fio2 >= 50 and pco2_f:
            fio2_dec = fio2 / 100.0
            AaDO2 = (fio2_dec * 713) - (pco2_f / 0.8) - po2_n
            if AaDO2 >= 500:
                apache_auto_pts += 4
            elif AaDO2 >= 350:
                apache_auto_pts += 3
            elif AaDO2 >= 200:
                apache_auto_pts += 2
        elif fio2 < 50:
            if po2_n < 55:
                apache_auto_pts += 4
            elif po2_n <= 60:
                apache_auto_pts += 3
            elif po2_n <= 70:
                apache_auto_pts += 1
    else:
        faltan_datos_apache = True

    if ph_f:
        if ph_f >= 7.7 or ph_f < 7.15:
            apache_auto_pts += 4
        elif 7.6 <= ph_f <= 7.69 or 7.15 <= ph_f <= 7.24:
            apache_auto_pts += 3
        elif 7.25 <= ph_f <= 7.32:
            apache_auto_pts += 2
        elif 7.5 <= ph_f <= 7.59:
            apache_auto_pts += 1

    if na_f:
        if na_f >= 180 or na_f <= 110:
            apache_auto_pts += 4
        elif 160 <= na_f <= 179 or 111 <= na_f <= 119:
            apache_auto_pts += 3
        elif 155 <= na_f <= 159 or 120 <= na_f <= 129:
            apache_auto_pts += 2
        elif 150 <= na_f <= 154:
            apache_auto_pts += 1

    if k_f:
        if k_f >= 7 or k_f <= 2.4:
            apache_auto_pts += 4
        elif 6 <= k_f <= 6.9:
            apache_auto_pts += 3
        elif 2.5 <= k_f <= 2.9:
            apache_auto_pts += 2
        elif 5.5 <= k_f <= 5.9 or 3 <= k_f <= 3.4:
            apache_auto_pts += 1

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

    if hto_f:
        if hto_f >= 60 or hto_f < 20:
            apache_auto_pts += 4
        elif 50 <= hto_f <= 59.9 or 20 <= hto_f <= 29.9:
            apache_auto_pts += 2
        elif 46 <= hto_f <= 49.9:
            apache_auto_pts += 1

    if gb_f:
        gb_val = gb_f / 1000 if gb_f > 100 else gb_f
        if gb_val >= 40 or gb_val < 1:
            apache_auto_pts += 4
        elif 20 <= gb_val <= 39.9 or 1 <= gb_val <= 2.9:
            apache_auto_pts += 2
        elif 15 <= gb_val <= 19.9:
            apache_auto_pts += 1

    if gl_val:
        apache_auto_pts += (15 - gl_val)

    apache_cronico = datos.get("apache_cronico", 0)
    if apache_cronico:
        apache_auto_pts += apache_cronico

    apache_final_str = f"{apache_auto_pts} (Auto)" if not faltan_datos_apache else "Faltan gases/vitales"

    # --- CÁLCULO MELD & CHILD-PUGH ---
    meld_auto_str = "Faltan datos (Cr, BT, INR, Na)"
    if cr_n and bt_n and rin_n:
        cr_meld = max(1.0, cr_n)
        bt_meld = max(1.0, bt_n)
        inr_meld = max(1.0, rin_n)

        if datos.get("meld_dialisis", False):
            cr_meld = 4.0

        meld_score = 3.78 * math.log(bt_meld) + 11.2 * math.log(inr_meld) + 9.57 * math.log(cr_meld) + 6.43
        meld_score = round(meld_score)

        if na_f and 125 <= na_f <= 137:
            meld_na = meld_score + 1.32 * (137 - na_f) - (0.033 * meld_score * (137 - na_f))
            meld_auto_str = f"{round(meld_na)} (MELD-Na Auto)"
        else:
            meld_auto_str = f"{meld_score} (Auto)"

    child_auto_str = "Faltan datos"
    albumina = datos.get("albumina", 0.0) or 0.0
    if bt_n and rin_n and albumina > 0:
        pts_child = 0

        if bt_n < 2:
            pts_child += 1
        elif bt_n <= 3:
            pts_child += 2
        else:
            pts_child += 3

        if rin_n < 1.7:
            pts_child += 1
        elif rin_n <= 2.2:
            pts_child += 2
        else:
            pts_child += 3

        if albumina > 3.5:
            pts_child += 1
        elif albumina >= 2.8:
            pts_child += 2
        else:
            pts_child += 3

        child_encef = str(datos.get("child_encef", "Ausente"))
        child_ascitis = str(datos.get("child_ascitis", "Ausente"))

        if "I-II" in child_encef:
            pts_child += 2
        elif "III-IV" in child_encef:
            pts_child += 3
        else:
            pts_child += 1

        if "Leve" in child_ascitis:
            pts_child += 2
        elif "Severa" in child_ascitis:
            pts_child += 3
        else:
            pts_child += 1

        clase = "A" if pts_child <= 6 else "B" if pts_child <= 9 else "C"
        child_auto_str = f"{pts_child} pts - Clase {clase} (Auto)"

    # --- CÁLCULO BISAP ---
    bisap_auto_str = "Faltan datos"
    if urea_n is not None:
        bisap_pts = 0
        if urea_n > 53.5:
            bisap_pts += 1
        if gl_val < 15:
            bisap_pts += 1
        if edad_n > 60:
            bisap_pts += 1
        if datos.get("bisap_derrame", False):
            bisap_pts += 1

        sirs_pts = 0
        if temp_n and (temp_n < 36 or temp_n > 38):
            sirs_pts += 1
        if fc_n and fc_n > 90:
            sirs_pts += 1
        if fr_n and (fr_n > 20 or (pco2_f and pco2_f < 32)):
            sirs_pts += 1
        if gb_f:
            g_val = gb_f / 1000 if gb_f > 100 else gb_f
            if g_val < 4 or g_val > 12:
                sirs_pts += 1

        if sirs_pts >= 2:
            bisap_pts += 1

        bisap_auto_str = f"{bisap_pts}/5 (Auto)"

    # --- CÁLCULO CHA₂DS₂-VA ---
    chadva_score = 0
    chadva_str = ""

    if datos.get("is_fa", False):
        if datos.get("chf", False):
            chadva_score += 1
        if datos.get("hta", False):
            chadva_score += 1
        if edad_n >= 75:
            chadva_score += 2
        elif 65 <= edad_n <= 74:
            chadva_score += 1
        if datos.get("diabetes", False):
            chadva_score += 1
        if datos.get("stroke_fa", False):
            chadva_score += 2
        if datos.get("vascular", False):
            chadva_score += 1

        chadva_str = f"{chadva_score} pts (Auto)"

    # --- CÁLCULO TFG ---
    tfg_str = ""
    if cr_n and cr_n > 0:
        sexo_paciente = datos.get("sexo_paciente", "Masculino")
        factor_mdrd = 0.742 if sexo_paciente == "Femenino" else 1.0
        mdrd_val = 175 * (cr_n ** -1.154) * (edad_n ** -0.203) * factor_mdrd
        tfg_str = f" | TFG (MDRD4): {mdrd_val:.1f} ml/min"

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
        "s_pts": s_pts,
        "q_calc": q_calc,
        "c_calc": c_calc,
        "apache_final_str": apache_final_str,
        "meld_auto_str": meld_auto_str,
        "child_auto_str": child_auto_str,
        "bisap_auto_str": bisap_auto_str,
        "chadva_score": chadva_score,
        "chadva_str": chadva_str,
        "tfg_str": tfg_str,
    }


def evaluar_morbimortalidad_sugerencias(score_name: str, value_str: Any) -> str:
    """Agrega interpretación breve de riesgo para scores calculados."""
    if not value_str or "Faltan" in str(value_str) or "Pendiente" in str(value_str) or "No calculado" in str(value_str):
        return ""

    num_matches = re.findall(r"-?\d+\.?\d*", str(value_str))
    val_num = float(num_matches[0]) if num_matches else None

    texto = ""
    score_upper = score_name.upper()

    if "SOFA" in score_upper and "QSOFA" not in score_upper and val_num is not None:
        if val_num <= 6:
            texto = "[Mortalidad <10%]"
        elif val_num <= 9:
            texto = "[Mortalidad ~15-20%]"
        elif val_num <= 12:
            texto = "[Mortalidad ~40-50%]"
        else:
            texto = "[Mortalidad >50%]"
        texto += " Sugerencia: Mantener soporte orgánico guiado por metas."

    elif "QSOFA" in score_upper and val_num is not None:
        if val_num >= 2:
            texto = "[Alto riesgo] Sugerencia: Considerar monitoreo estricto o ingreso a UCI."
        else:
            texto = "[Riesgo basal]"

    elif "APACHE" in score_upper and val_num is not None:
        if val_num <= 9:
            texto = "[Mortalidad ~4%]"
        elif val_num <= 14:
            texto = "[Mortalidad ~15%]"
        elif val_num <= 19:
            texto = "[Mortalidad ~25%]"
        elif val_num <= 24:
            texto = "[Mortalidad ~40%]"
        elif val_num <= 29:
            texto = "[Mortalidad ~55%]"
        else:
            texto = "[Mortalidad >75%]"

    elif "MELD" in score_upper and val_num is not None:
        if val_num <= 9:
            texto = "[Mortalidad 3 meses ~1.9%]"
        elif val_num <= 19:
            texto = "[Mortalidad 3 meses ~6%]"
        elif val_num <= 29:
            texto = "[Mortalidad 3 meses ~19.6%]"
        elif val_num <= 39:
            texto = "[Mortalidad 3 meses ~52.6%]"
        else:
            texto = "[Mortalidad 3 meses ~71.3%]"

    elif "CHILD" in score_upper:
        if "A" in str(value_str).upper():
            texto = "[Sobrevida 1 año ~100%]"
        elif "B" in str(value_str).upper():
            texto = "[Sobrevida 1 año ~80%]"
        elif "C" in str(value_str).upper():
            texto = "[Sobrevida 1 año ~45%]"

    elif "BISAP" in score_upper and val_num is not None:
        if val_num <= 2:
            texto = "[Mortalidad <2%]"
        else:
            texto = "[Mortalidad >15%] Sugerencia: Alto riesgo de necrosis o falla orgánica. Soporte intensivo."

    elif "CURB-65" in score_upper and val_num is not None:
        if val_num <= 1:
            texto = "[Mortalidad <2%] Sugerencia: Tratamiento ambulatorio."
        elif val_num == 2:
            texto = "[Mortalidad ~9%] Sugerencia: Considerar hospitalización en sala."
        else:
            texto = "[Mortalidad 15-40%] Sugerencia: Hospitalización en UCI."

    elif "CHA₂DS₂-VA" in score_upper and val_num is not None:
        if val_num == 0:
            texto = "[Bajo riesgo de ACV] Sugerencia: Anticoagulación no requerida."
        elif val_num == 1:
            texto = "[Riesgo intermedio] Sugerencia: Considerar anticoagulación oral."
        else:
            texto = "[Alto riesgo] Sugerencia: Anticoagulación oral formalmente indicada."

    return f" {texto}" if texto else ""


def motor_scores(flags: Dict[str, bool], manuales: Dict[str, Any], auto: Dict[str, Any]) -> List[Dict[str, Dict[str, Any]]]:
    """Arma la lista de scores activos según diagnóstico detectado."""
    resultados = []

    if flags.get("is_sepsis"):
        sofa_val = manuales.get("sofa", "") if str(manuales.get("sofa", "")).strip() else str(auto.get("s_pts", ""))
        qsofa_val = manuales.get("qsofa", "") if str(manuales.get("qsofa", "")).strip() else str(auto.get("q_calc", ""))
        apache_val = manuales.get("apache", "") if str(manuales.get("apache", "")).strip() else auto.get("apache_final_str", "")
        resultados.append({
            "categoria": "Sepsis",
            "scores": {
                "SOFA": sofa_val,
                "qSOFA": qsofa_val,
                "APACHE II": apache_val,
            },
        })

    if flags.get("is_isquemia"):
        resultados.append({
            "categoria": "SCA/IAM",
            "scores": {
                "Killip": manuales.get("killip") if manuales.get("killip") else "Pendiente",
                "GRACE": manuales.get("grace") if manuales.get("grace") else "Pendiente",
                "TIMI": manuales.get("timi") if manuales.get("timi") else "Pendiente",
            },
        })

    if flags.get("is_ic"):
        resultados.append({
            "categoria": "Insuficiencia Cardíaca",
            "scores": {
                "NYHA": manuales.get("nyha") if manuales.get("nyha") else "Pendiente",
                "Stevenson": manuales.get("stevenson") if manuales.get("stevenson") else "Pendiente",
                "AHA": manuales.get("aha_ic") if manuales.get("aha_ic") else "Pendiente",
            },
        })

    if flags.get("is_renal"):
        resultados.append({
            "categoria": "Renal",
            "scores": {
                "KDIGO IRA": manuales.get("kdigo_ira") if manuales.get("kdigo_ira") else "Pendiente",
                "ERC": manuales.get("kdigo_erc") if manuales.get("kdigo_erc") else "Pendiente",
                "TFG": auto.get("tfg_str") if auto.get("tfg_str") else "No calculado",
            },
        })

    if flags.get("is_hepato"):
        resultados.append({
            "categoria": "Hepatopatía",
            "scores": {
                "Child-Pugh": manuales.get("child") if manuales.get("child") else auto.get("child_auto_str", ""),
                "MELD": manuales.get("meld") if manuales.get("meld") else auto.get("meld_auto_str", ""),
            },
        })

    if flags.get("is_pancreas"):
        resultados.append({
            "categoria": "Pancreatitis",
            "scores": {
                "BISAP": manuales.get("bisap") if manuales.get("bisap") else auto.get("bisap_auto_str", ""),
                "Ranson": manuales.get("ranson") if manuales.get("ranson") else "Pendiente",
                "Balthazar": manuales.get("balthazar") if manuales.get("balthazar") else "Pendiente",
            },
        })

    if flags.get("is_acv"):
        resultados.append({
            "categoria": "ACV",
            "scores": {
                "NIHSS": manuales.get("nihss") if manuales.get("nihss") else "Pendiente",
                "mRS": manuales.get("mrs") if manuales.get("mrs") else "Pendiente",
            },
        })

    if flags.get("is_hsa"):
        resultados.append({
            "categoria": "HSA",
            "scores": {
                "Hunt & Hess": manuales.get("hunt") if manuales.get("hunt") else "Pendiente",
                "Fisher": manuales.get("fisher") if manuales.get("fisher") else "Pendiente",
            },
        })

    if flags.get("is_nac"):
        resultados.append({
            "categoria": "Neumonía",
            "scores": {
                "CURB-65": manuales.get("curb65") if manuales.get("curb65") else str(auto.get("c_calc", "")),
                "PSI": manuales.get("psi") if manuales.get("psi") else "Pendiente",
            },
        })

    if flags.get("is_fa"):
        resultados.append({
            "categoria": "Fibrilación Auricular",
            "scores": {
                "CHA₂DS₂-VA (ESC 2024)": auto.get("chadva_str", ""),
            },
        })

    return resultados


def formatear_scores_detectados(scores_globales: List[Dict[str, Any]]) -> List[str]:
    """Devuelve líneas listas para mostrar/imprimir con interpretación."""
    texto_scores = []

    for grupo in scores_globales:
        partes_evaluadas = []
        for k, v in grupo["scores"].items():
            evaluacion = evaluar_morbimortalidad_sugerencias(k, v)
            partes_evaluadas.append(f"{k}: {v}{evaluacion}")
        lineas_detalle = " | ".join(partes_evaluadas)
        linea = f"{grupo['categoria']} -> {lineas_detalle}"
        texto_scores.append(f"- {linea}")

    return texto_scores
