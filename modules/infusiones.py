"""Módulo de infusiones con rangos orientativos y doble chequeo."""
from __future__ import annotations
from copy import deepcopy
from typing import Dict, Optional, Tuple

DICCIONARIO_DROGAS: Dict[str, dict] = {
    "Noradrenalina (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0, "rango": (0.01, 3.0), "critico_alto": 3.0, "nota": "Vasopresor de alto riesgo. Titular a objetivo hemodinámico."},
    "Adrenalina (1 mg)": {"unidad": "mcg/kg/min", "mg": 1.0, "rango": (0.01, 1.0), "critico_alto": 1.0, "nota": "Vasopresor/inotrópico de alto riesgo. Monitoreo continuo."},
    "Dopamina (200 mg)": {"unidad": "mcg/kg/min", "mg": 200.0, "rango": (1.0, 20.0), "critico_alto": 20.0, "nota": "Titular según respuesta hemodinámica y arritmias."},
    "Dobutamina (250 mg)": {"unidad": "mcg/kg/min", "mg": 250.0, "rango": (2.0, 20.0), "critico_alto": 20.0, "nota": "Inotrópico. Vigilar TA, FC y perfusión."},
    "Milrinona (10 mg)": {"unidad": "mcg/kg/min", "mg": 10.0, "rango": (0.125, 0.75), "critico_alto": 0.75, "nota": "Ajustar en disfunción renal. Vigilar hipotensión/arritmias."},
    "Vasopresina (20 UI)": {"unidad": "UI/min", "mg": 20.0, "rango": (0.01, 0.07), "critico_alto": 0.1, "nota": "Shock vasodilatado. Verificar protocolo local."},
    "Fentanilo (0.25 mg)": {"unidad": "mcg/kg/h", "mg": 0.25, "rango": (0.5, 5.0), "critico_alto": 10.0, "nota": "Opioide. Monitorizar sedación y ventilación."},
    "Remifentanilo (2 mg)": {"unidad": "mcg/kg/h", "mg": 2.0, "rango": (3.0, 12.0), "critico_alto": 30.0, "nota": "Confirmar unidad: rango expresado en mcg/kg/h por compatibilidad con la app."},
    "Remifentanilo (5 mg)": {"unidad": "mcg/kg/h", "mg": 5.0, "rango": (3.0, 12.0), "critico_alto": 30.0, "nota": "Confirmar unidad: rango expresado en mcg/kg/h por compatibilidad con la app."},
    "Morfina (10 mg)": {"unidad": "mg/h", "mg": 10.0, "rango": (1.0, 10.0), "critico_alto": 20.0, "nota": "Opioide. Ajustar a analgesia, ventilación y función renal."},
    "Propofol 1% (200 mg)": {"unidad": "mg/kg/h", "mg": 200.0, "rango": (0.3, 4.0), "critico_alto": 4.0, "nota": "Dosis altas/prolongadas aumentan riesgo de síndrome de infusión por propofol."},
    "Midazolam (15 mg)": {"unidad": "mg/kg/h", "mg": 15.0, "rango": (0.02, 0.2), "critico_alto": 0.2, "nota": "Riesgo de acumulación, delirium y depresión respiratoria."},
    "Midazolam (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0, "rango": (0.02, 0.2), "critico_alto": 0.2, "nota": "Riesgo de acumulación, delirium y depresión respiratoria."},
    "Dexmedetomidina (0.2 mg)": {"unidad": "mcg/kg/h", "mg": 0.2, "rango": (0.2, 0.7), "critico_alto": 1.0, "nota": "Vigilar bradicardia/hipotensión. Considerar ajuste en adultos mayores/hepatopatía."},
    "Ketamina (500 mg)": {"unidad": "mg/kg/h", "mg": 500.0, "rango": (0.05, 2.0), "critico_alto": 4.0, "nota": "Rango amplio según analgesia/sedación. Controlar TA y FC."},
    "Atracurio (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0, "rango": (0.3, 0.6), "critico_alto": 1.0, "nota": "Bloqueante neuromuscular. Usar con sedoanalgesia adecuada y monitoreo."},
    "Pancuronio (4 mg)": {"unidad": "mg/kg/h", "mg": 4.0, "rango": (0.02, 0.1), "critico_alto": 0.15, "nota": "Bloqueante neuromuscular. Verificar indicación y sedación."},
    "Nitroglicerina (25 mg/5 ml)": {"unidad": "mcg/min", "mg": 25.0, "rango": (5.0, 200.0), "critico_alto": 400.0, "nota": "Vasodilatador. Titular según TA/dolor/isquemia; usar bomba."},
    "Nitroprusiato de sodio (50 mg)": {"unidad": "mcg/kg/min", "mg": 50.0, "rango": (0.3, 10.0), "critico_alto": 10.0, "nota": "Proteger de luz. Riesgo de toxicidad por cianuro/tiocianato."},
    "Isoproterenol (1 mg/5 ml)": {"unidad": "mcg/min", "mg": 1.0, "rango": (0.5, 20.0), "critico_alto": 20.0, "nota": "Cronotrópico. Vigilar taquiarritmias, isquemia e hipotensión."},
}

def obtener_diccionario_drogas() -> Dict[str, dict]:
    return deepcopy(DICCIONARIO_DROGAS)

def calcular_infusion_universal(modo: str, cantidad_droga_mg_ui: float, volumen_ml: float, peso_kg: float, valor_input: float, unidad_objetivo: str) -> float:
    if volumen_ml == 0 or cantidad_droga_mg_ui == 0:
        return 0.0
    conc_base = cantidad_droga_mg_ui / volumen_ml
    conc_final = conc_base * 1000 if ("mcg" in unidad_objetivo or "gammas" in unidad_objetivo) else conc_base
    peso_factor = peso_kg if "kg" in unidad_objetivo else 1.0
    tiempo_factor = 60.0 if "min" in unidad_objetivo else 1.0
    if modo == "DOSIS":
        return (valor_input * conc_final) / (peso_factor * tiempo_factor)
    return (valor_input * peso_factor * tiempo_factor) / conc_final

def calcular_concentracion(cantidad_droga_mg_ui: float, volumen_ml: float, unidad_objetivo: str) -> Tuple[float, str]:
    if volumen_ml <= 0:
        return 0.0, ""
    conc_base = cantidad_droga_mg_ui / volumen_ml
    if "mcg" in unidad_objetivo or "gammas" in unidad_objetivo:
        return conc_base * 1000, "mcg/ml"
    if "UI" in unidad_objetivo:
        return conc_base, "UI/ml"
    return conc_base, "mg/ml"

def texto_rango_infusion(info_droga: dict) -> str:
    rango = info_droga.get("rango")
    unidad = info_droga.get("unidad", "")
    return f"{rango[0]:g} a {rango[1]:g} {unidad}" if rango else "Sin rango orientativo configurado."

def evaluar_rango_infusion(dosis: Optional[float], info_droga: dict) -> dict:
    if dosis is None:
        return {"estado": "sin_dosis", "mensaje": "Ingrese una dosis válida para evaluar el rango."}
    rango = info_droga.get("rango")
    unidad = info_droga.get("unidad", "")
    if not rango:
        return {"estado": "sin_rango", "mensaje": "Sin rango orientativo configurado. Verificar protocolo institucional."}
    minimo, maximo = rango
    critico = info_droga.get("critico_alto", maximo)
    if dosis == 0:
        return {"estado": "cero", "mensaje": "Dosis en cero. Verificar antes de anexar."}
    if dosis < minimo:
        return {"estado": "bajo", "mensaje": f"Dosis por debajo del rango orientativo ({minimo:g}-{maximo:g} {unidad})."}
    if dosis > critico:
        return {"estado": "critico", "mensaje": f"Dosis por encima del umbral crítico configurado ({critico:g} {unidad})."}
    if dosis > maximo:
        return {"estado": "alto", "mensaje": f"Dosis por encima del rango orientativo ({minimo:g}-{maximo:g} {unidad})."}
    return {"estado": "ok", "mensaje": f"Dosis dentro del rango orientativo ({minimo:g}-{maximo:g} {unidad})."}

def requiere_confirmacion_extra(evaluacion: dict) -> bool:
    return evaluacion.get("estado") in {"bajo", "alto", "critico", "cero", "sin_rango"}

def construir_detalle_infusion(nombre_limpio: str, dosis: float, unidad: str, velocidad_mlh: float, cantidad_droga_mg_ui: float, volumen_ml: float) -> str:
    conc, conc_unidad = calcular_concentracion(cantidad_droga_mg_ui, volumen_ml, unidad)
    return f"{nombre_limpio}: {cantidad_droga_mg_ui:g} mg/UI en {volumen_ml:g} ml ({conc:.2f} {conc_unidad}); Bomba {velocidad_mlh:.2f} ml/h; Dosis {dosis:.4f} {unidad}"
