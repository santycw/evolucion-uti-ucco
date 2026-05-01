"""
Módulo de validaciones y utilidades numéricas.

Primera capa segura: conversiones tolerantes, parsing de tensión arterial y
cálculos auxiliares usados por la app.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple


def p_num(val) -> Optional[float]:
    """Convierte texto numérico con coma/punto a float. Devuelve None si falla."""
    try:
        texto = str(val).replace(",", ".").strip()
        if not texto:
            return None
        return float(texto)
    except Exception:
        return None


def parse_tension_arterial(ta: str) -> Tuple[Optional[float], Optional[float]]:
    """Parsea TA en formato sistólica/diastólica."""
    if not ta or "/" not in str(ta):
        return None, None

    try:
        partes = str(ta).split("/")
        sys_bp = float(partes[0].replace(",", ".").strip())
        dia_bp = float(partes[1].replace(",", ".").strip())
        return sys_bp, dia_bp
    except Exception:
        return None, None


def calcular_tam_pp(ta: str):
    """Calcula TAM y presión de pulso desde TA."""
    sys_bp, dia_bp = parse_tension_arterial(ta)
    if sys_bp is None or dia_bp is None:
        return None, None, "", ""

    tam_val = round((sys_bp + 2 * dia_bp) / 3)
    pp_val = int(sys_bp - dia_bp)
    return sys_bp, dia_bp, tam_val, pp_val


def calcular_par(fc, pvc, tam):
    """Calcula PAR = (FC × PVC) / TAM."""
    fc_n = p_num(fc)
    pvc_n = p_num(pvc)

    if fc_n is None or pvc_n is None or not tam:
        return ""

    try:
        tam_f = float(tam)
        if tam_f > 0:
            return f"{(fc_n * pvc_n) / tam_f:.2f}"
    except Exception:
        return ""

    return ""


def calcular_qtc_bazett(fc, qt) -> str:
    """Calcula QTc por fórmula de Bazett."""
    fc_val = p_num(fc)
    qt_val = p_num(qt)

    if fc_val is None or qt_val is None or fc_val <= 0:
        return ""

    rr_sec = 60.0 / fc_val
    qtc_val = qt_val / math.sqrt(rr_sec)
    return f"{qtc_val:.0f}"


def generar_alertas_basicas(valores: dict) -> list[str]:
    """
    Genera alertas clínicas básicas no bloqueantes.

    No cambia la funcionalidad actual: sirve como base para futuras alertas
    visibles en la versión 2.x.
    """
    alertas = []

    k = p_num(valores.get("potasio"))
    if k is not None and k >= 6:
        alertas.append("⚠️ Potasio elevado: verificar ECG y conducta.")

    na = p_num(valores.get("na"))
    if na is not None and (na < 125 or na > 155):
        alertas.append("⚠️ Sodio en rango crítico: verificar corrección y tendencia.")

    lactato = p_num(valores.get("lactato"))
    if lactato is not None and lactato >= 4:
        alertas.append("⚠️ Lactato elevado: evaluar hipoperfusión/shock.")

    return alertas
