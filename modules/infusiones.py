"""
Módulo de infusiones.

Mantiene la lógica original de cálculo universal y centraliza el vademécum
de drogas disponibles para evitar editar el cuerpo principal de la app.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict


DICCIONARIO_DROGAS: Dict[str, dict] = {
    "Noradrenalina (4 mg)": {"unidad": "mcg/kg/min", "mg": 4.0},
    "Adrenalina (1 mg)": {"unidad": "mcg/kg/min", "mg": 1.0},
    "Dopamina (200 mg)": {"unidad": "mcg/kg/min", "mg": 200.0},
    "Dobutamina (250 mg)": {"unidad": "mcg/kg/min", "mg": 250.0},
    "Milrinona (10 mg)": {"unidad": "mcg/kg/min", "mg": 10.0},
    "Vasopresina (20 UI)": {"unidad": "UI/min", "mg": 20.0},
    "Fentanilo (0.25 mg)": {"unidad": "mcg/kg/h", "mg": 0.25},
    "Remifentanilo (2 mg)": {"unidad": "mcg/kg/h", "mg": 2.0},
    "Remifentanilo (5 mg)": {"unidad": "mcg/kg/h", "mg": 5.0},
    "Morfina (10 mg)": {"unidad": "mg/h", "mg": 10.0},
    "Propofol 1% (200 mg)": {"unidad": "mg/kg/h", "mg": 200.0},
    "Midazolam (15 mg)": {"unidad": "mg/kg/h", "mg": 15.0},
    "Midazolam (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
    "Dexmedetomidina (0.2 mg)": {"unidad": "mcg/kg/h", "mg": 0.2},
    "Ketamina (500 mg)": {"unidad": "mg/kg/h", "mg": 500.0},
    "Atracurio (50 mg)": {"unidad": "mg/kg/h", "mg": 50.0},
    "Pancuronio (4 mg)": {"unidad": "mg/kg/h", "mg": 4.0},
    "Nitroglicerina (25 mg/5 ml)": {"unidad": "mcg/min", "mg": 25.0},
    "Nitroprusiato de sodio (50 mg)": {"unidad": "mcg/kg/min", "mg": 50.0},
    "Isoproterenol (1 mg/5 ml)": {"unidad": "mcg/min", "mg": 1.0},
}


def obtener_diccionario_drogas() -> Dict[str, dict]:
    """Devuelve una copia del diccionario de drogas para uso seguro en UI."""
    return deepcopy(DICCIONARIO_DROGAS)


def calcular_infusion_universal(
    modo: str,
    cantidad_droga_mg_ui: float,
    volumen_ml: float,
    peso_kg: float,
    valor_input: float,
    unidad_objetivo: str,
) -> float:
    """Calcula dosis o velocidad respetando la fórmula original de la app."""
    if volumen_ml == 0 or cantidad_droga_mg_ui == 0:
        return 0.0

    conc_base = cantidad_droga_mg_ui / volumen_ml

    if "mcg" in unidad_objetivo or "gammas" in unidad_objetivo:
        conc_final = conc_base * 1000
    else:
        conc_final = conc_base

    usa_peso = "kg" in unidad_objetivo
    peso_factor = peso_kg if usa_peso else 1.0

    usa_min = "min" in unidad_objetivo
    tiempo_factor = 60.0 if usa_min else 1.0

    if modo == "DOSIS":
        dosis = (valor_input * conc_final) / (peso_factor * tiempo_factor)
        return dosis

    velocidad = (valor_input * peso_factor * tiempo_factor) / conc_final
    return velocidad
