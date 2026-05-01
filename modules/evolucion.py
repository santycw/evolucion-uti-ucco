"""
Módulo de generación de evolución.

Recibe un diccionario de datos clínicos y devuelve el texto final listo para
copiar a la historia clínica.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Tuple
import re

from .scores import formatear_scores_detectados
from .validaciones import p_num


def s(valor: Any) -> str:
    """String seguro para campos opcionales."""
    return str(valor or "")


def construir_linea_lab(items: Iterable[Tuple[str, Any, str]]) -> str:
    """Construye una línea de laboratorio omitiendo campos vacíos."""
    validos = [
        f"{nombre} {s(val).strip()} {uni}".strip()
        for nombre, val, uni in items
        if s(val).strip()
    ]
    return " | ".join(validos) if validos else ""


def eliminar_bloque_alertas_seguridad(texto: str) -> str:
    """Garantiza que las alertas clínicas no se impriman en la evolución final."""
    if not texto:
        return texto

    patron = (
        r"\n?>>\s*ALERTAS DE SEGURIDAD CL[ÍI]NICA:\s*\n"
        r"(?:.*?)(?=\n?>>\s*FAST HUG BID:|\n\(A\)\s*PROBLEMAS ACTIVOS:|\n\(P\)\s*PLAN:|\Z)"
    )
    texto = re.sub(patron, "\n", texto, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"\n{3,}", "\n\n", texto).strip() + "\n"


def generar_texto_evolucion(datos: dict, auto: dict, scores_para_imprimir: List[dict]) -> str:
    """Genera el texto completo de evolución UTI/UCCO."""
    infusiones_automatizadas = datos.get("infusiones_automatizadas", []) or []

    if infusiones_automatizadas:
        str_automatizadas = " | ".join(infusiones_automatizadas)
    else:
        str_automatizadas = "Sin infusiones activas."

    l_eab = construir_linea_lab([
        ("pH", datos.get("ph", ""), ""),
        ("pCO2", datos.get("pco2", ""), "mmHg"),
        ("pO2", datos.get("po2", ""), "mmHg"),
        ("SatO2", datos.get("sato2_eab", ""), "%"),
        ("HCO3", datos.get("hco3", ""), "mEq/L"),
        ("EB", datos.get("eb", ""), "mEq/L"),
        ("Lac", datos.get("lactato", ""), "mmol/L"),
    ])

    l_hemo = construir_linea_lab([
        ("Hb", datos.get("hb", ""), "g/dL"),
        ("Hto", datos.get("hto", ""), "%"),
        ("GB", datos.get("gb", ""), "/mm³"),
        ("Plaq", datos.get("plaq", ""), "/mm³"),
    ])

    l_coag = construir_linea_lab([
        ("APP", datos.get("app", ""), "%"),
        ("KPTT", datos.get("kptt", ""), "s"),
        ("RIN", datos.get("rin", ""), ""),
    ])

    l_quim = construir_linea_lab([
        ("Urea", datos.get("urea", ""), "mg/dL"),
        ("Cr", datos.get("cr", ""), "mg/dL"),
        ("Gluc", datos.get("gluc", ""), "mg/dL"),
        ("Na", datos.get("na", ""), "mEq/L"),
        ("K", datos.get("potasio", ""), "mEq/L"),
        ("Cl", datos.get("cl", ""), "mEq/L"),
        ("Mg", datos.get("mg", ""), "mg/dL"),
        ("Ca", datos.get("ca_tot", ""), "mg/dL"),
        ("Ca++", datos.get("ca_io", ""), "mmol/L"),
        ("P", datos.get("fosforo", ""), "mg/dL"),
    ])

    l_hepa = construir_linea_lab([
        ("BT", datos.get("bt", ""), "mg/dL"),
        ("BD", datos.get("bd", ""), "mg/dL"),
        ("GOT", datos.get("got", ""), "UI/L"),
        ("GPT", datos.get("gpt", ""), "UI/L"),
        ("FAL", datos.get("fal", ""), "UI/L"),
        ("GGT", datos.get("ggt", ""), "UI/L"),
    ])

    l_inflam = construir_linea_lab([
        ("Prot.Tot", datos.get("prot_tot", ""), "g/dL"),
        ("Alb", datos.get("albumina_lab", ""), "g/dL"),
        ("VSG", datos.get("vsg", ""), "mm/h"),
        ("PCR", datos.get("pcr", ""), "mg/L"),
    ])

    l_bio = construir_linea_lab([
        ("LDH", datos.get("ldh", ""), "UI/L"),
        ("CPK", datos.get("cpk", ""), "UI/L"),
        ("CPK-MB", datos.get("cpk_mb", ""), "UI/L"),
        ("Tropo I", datos.get("tropo", ""), "ng/mL"),
        ("proBNP", datos.get("bnp", ""), "pg/mL"),
        ("PCT", datos.get("pct", ""), "ng/mL"),
    ])

    lab_blocks = [l for l in [l_eab, l_hemo, l_coag, l_quim, l_hepa, l_inflam, l_bio] if l]
    texto_laboratorio = "\n".join(lab_blocks) if lab_blocks else "Pendiente / No consta."

    ecg_items = [
        ("FC", datos.get("ecg_fc", ""), "lpm"),
        ("Ritmo", datos.get("ecg_ritmo", ""), ""),
        ("Eje", datos.get("ecg_eje", ""), "°"),
        ("PR", datos.get("ecg_pr", ""), "ms"),
        ("QRS", datos.get("ecg_qrs_ms", ""), "ms"),
        ("QT", datos.get("ecg_qt", ""), "ms"),
        ("QTc", datos.get("ecg_qtc", ""), "ms"),
        ("Onda P", datos.get("ecg_onda_p", ""), "ms"),
        ("ST", datos.get("ecg_st", ""), ""),
    ]

    ecg_validos = [
        f"{n} {s(v).strip()}{u}".strip()
        for n, v, u in ecg_items
        if s(v).strip()
    ]

    if s(datos.get("ecg_conclusiones", "")).strip():
        ecg_validos.append(f"Conclusión: {s(datos.get('ecg_conclusiones', '')).strip()}")

    ecg_final = "- ECG: " + " | ".join(ecg_validos) if ecg_validos else ""

    est_list = []
    if s(datos.get("rx_torax", "")).strip():
        est_list.append(f"- Rx Tórax/Imágenes: {s(datos.get('rx_torax', '')).strip()}")
    if s(datos.get("tc", "")).strip():
        est_list.append(f"- Tomografía (TC): {s(datos.get('tc', '')).strip()}")
    if s(datos.get("eco", "")).strip():
        est_list.append(f"- Ecografía/POCUS: {s(datos.get('eco', '')).strip()}")

    texto_adicionales = "\n".join(est_list)

    bloque_estudios = ""
    if ecg_final or texto_adicionales:
        partes_estudios = [p for p in [ecg_final, texto_adicionales] if p]
        bloque_estudios = "\n>> ECG Y ESTUDIOS COMPLEMENTARIOS:\n" + "\n".join(partes_estudios) + "\n"

    lista_cultivos = []
    if s(datos.get("cult_hemo", "")).strip():
        lista_cultivos.append(f"Hemo: {s(datos.get('cult_hemo', '')).strip()}")
    if s(datos.get("cult_uro", "")).strip():
        lista_cultivos.append(f"Uro: {s(datos.get('cult_uro', '')).strip()}")
    if s(datos.get("cult_resp", "")).strip():
        lista_cultivos.append(f"Resp: {s(datos.get('cult_resp', '')).strip()}")
    if s(datos.get("cult_otros", "")).strip():
        lista_cultivos.append(f"Otros: {s(datos.get('cult_otros', '')).strip()}")

    cultivos_final = " | ".join(lista_cultivos)

    tmax_str = f"Tmax: {s(datos.get('tmax', '')).strip()}°C" if s(datos.get("tmax", "")).strip() else ""
    atbs_ingresados = [
        atb for atb in [
            datos.get("atb1", ""),
            datos.get("atb2", ""),
            datos.get("atb3", ""),
            datos.get("atb4", ""),
        ]
        if s(atb).strip()
    ]
    atb_str = f"ATB: {' / '.join(atbs_ingresados)}" if atbs_ingresados else ""

    infecto_parts = [p for p in [tmax_str, atb_str, cultivos_final] if p]
    bloque_infectologia = "\n>> INFECTOLOGÍA:\n" + "\n".join([f"- {p}" for p in infecto_parts]) + "\n" if infecto_parts else ""

    tam_val = auto.get("tam_val", "")
    pp_val = auto.get("pp_val", "")
    fc_n = auto.get("fc_n")
    pvc_n = auto.get("pvc_n")

    tam_str = f"{tam_val}" if tam_val != "" else "-"
    pp_str = f"{pp_val}" if pp_val != "" else "-"
    par_str = ""

    if fc_n is not None and pvc_n is not None and tam_val and tam_val > 0:
        par_str = f"\n  PAR: {(fc_n * pvc_n) / tam_val:.2f}"

    ta = s(datos.get("ta", ""))
    fc = s(datos.get("fc", ""))
    pvc = s(datos.get("pvc", ""))
    fr = s(datos.get("fr", ""))
    sat = s(datos.get("sat", ""))
    temp = s(datos.get("temp", ""))

    signos_vitales = f"""- SIGNOS VITALES:
  TA: {ta if ta.strip() else '-'} mmHg
  TAM: {tam_str} mmHg
  PP: {pp_str} mmHg
  FC: {fc if fc.strip() else '-'} lpm
  PVC: {pvc if pvc.strip() else '-'} cmH2O{par_str}
  Rell. Capilar: {s(datos.get('relleno_cap', '')).strip() if s(datos.get('relleno_cap', '')).strip() else '-'}
  FR: {fr if fr.strip() else '-'} rpm
  SatO2: {sat if sat.strip() else '-'} %
  FiO2: {datos.get('fio2') if datos.get('fio2') else '-'} %
  T°: {temp if temp.strip() else '-'} °C"""

    pafi_final = auto.get("pafi_final", "")
    if datos.get("paciente_ventilado"):
        dp_final = datos.get("dp_manual", "")
        pplat_val = p_num(datos.get("pplat", ""))
        peep = datos.get("peep", "")

        if not dp_final and pplat_val and peep:
            try:
                dp_final = str(int(pplat_val - float(peep)))
            except Exception:
                pass

        texto_resp = f"""{datos.get('via_aerea', '')}, Modo {datos.get('modo', '')}, FiO2 {datos.get('fio2')}%, PEEP {datos.get('peep')} cmH2O, PPlat {datos.get('pplat', '')} cmH2O, Vt {datos.get('vt', '')} ml.
  Mecánica: P.Pico {datos.get('ppico', '')} cmH2O | DP {dp_final} | PaFiO2 {pafi_final}.
  Examen: {datos.get('ex_resp', '')}"""
    else:
        pafi_str = f" | PaFiO2 {pafi_final}" if pafi_final else ""
        texto_resp = f"""Dispositivo: {datos.get('via_aerea', '')} | FiO2 {datos.get('fio2')}%{pafi_str}.
  Examen: {datos.get('ex_resp', '')}"""

    balance_txt = ""
    val_in = p_num(datos.get("ingresos", ""))
    val_diu = p_num(datos.get("diuresis", ""))
    val_dre = p_num(datos.get("drenajes", ""))
    val_cat = p_num(datos.get("catarsis", ""))

    egresos_list = []
    if s(datos.get("diuresis", "")).strip():
        egresos_list.append(f"Diuresis {s(datos.get('diuresis', '')).strip()}")
    if s(datos.get("drenajes", "")).strip():
        egresos_list.append(f"Drenajes {s(datos.get('drenajes', '')).strip()}")
    if s(datos.get("catarsis", "")).strip():
        egresos_list.append(f"Catarsis {s(datos.get('catarsis', '')).strip()}")

    if val_in is not None or egresos_list:
        v_in = val_in if val_in is not None else 0.0
        v_out = (
            (val_diu if val_diu is not None else 0.0)
            + (val_dre if val_dre is not None else 0.0)
            + (val_cat if val_cat is not None else 0.0)
        )
        bal = v_in - v_out
        ing_str = s(datos.get("ingresos", "")).strip() if s(datos.get("ingresos", "")).strip() else "0"
        str_egresos = " | ".join(egresos_list) if egresos_list else "0"
        balance_txt = f" | Ingresos: {ing_str} ml / Egresos: [{str_egresos}] (Balance: {bal:+.0f} ml)"

    nutricion = datos.get("nutricion", "")
    nutri_txt = f" | Nutrición: {nutricion}" if nutricion else ""

    fast_sel = datos.get("fast_sel", []) or []
    fast_texto = "\n".join([f"  ✓ {letra}" for letra in fast_sel]) if fast_sel else "  Sin marcar."

    bloque_scores_impresion = ""
    if scores_para_imprimir:
        lineas_impresion = formatear_scores_detectados(scores_para_imprimir)
        bloque_scores_impresion = "\n".join(lineas_impresion) + "\n"

    problemas_activos_manual = s(datos.get("problemas_activos_manual", ""))
    bloque_problemas_manual = f"Otros: {problemas_activos_manual.strip()}\n" if problemas_activos_manual.strip() else ""

    texto_final = f"""EVOLUCIÓN UTI / UCCO
Días Hosp: {datos.get('dias_int_hosp')} | Días UTI: {datos.get('dias_int_uti')} | Días ARM: {datos.get('dias_arm')}

DIAGNÓSTICO:
{datos.get('diagnostico')}
{bloque_infectologia}
(S) SUBJETIVO: {datos.get('subj')}

(O) OBJETIVO:
>> INFUSIONES Y DISPOSITIVOS:
Infusiones Activas: {str_automatizadas}
Invasiones: CVC: {datos.get('cvc_info')} | Cat.Art: {datos.get('ca_info')} | SV: {datos.get('sv_dias')} | SNG: {datos.get('sng_dias')}

>> EXAMEN FÍSICO Y SIGNOS VITALES:
{signos_vitales}

- NEURO: {datos.get('neuro_estado')}, Glasgow {datos.get('glasgow')}, RASS {datos.get('rass')}, CAM {datos.get('cam')}.
- CV: {datos.get('ex_cv')}
- RESP: {texto_resp}
- ABD/RENAL: {datos.get('ex_abd')} | Ex. Renal: {datos.get('ex_renal')}{nutri_txt}{balance_txt}

>> LABORATORIO Y MEDIO INTERNO:
{texto_laboratorio}
{bloque_estudios}
>> FAST HUG BID:
{fast_texto}

(A) PROBLEMAS ACTIVOS:
{bloque_scores_impresion}{bloque_problemas_manual}
(P) PLAN:
{datos.get('plan')}
"""
    return eliminar_bloque_alertas_seguridad(texto_final)
