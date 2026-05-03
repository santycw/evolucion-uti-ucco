"""
Módulo de terminología médica.

Centraliza normalización de texto y detección de diagnósticos por diccionario.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Dict, List


FALLBACK_DB: Dict[str, List[str]] = {
    "isquemia": ["sca", "scacest", "scasest", "iam", "iamcest", "iamnsest", "iamsest", "infarto", "angina", "angor", "coronario"],
    "ic": ["ic", "ica", "icc", "insuficiencia cardiaca", "falla cardiaca", "eap", "cor pulmonale"],
    "sepsis": ["sepsis", "septic", "shock", "sirs", "bacteriemia", "vasoplegia", "falla multiorganica"],
    "renal": ["ira", "aki", "insuficiencia renal", "falla renal", "erc", "nefropatia"],
    "hepato": ["cirrosis", "hepatopatia", "falla hepatica", "dcl", "hepatitis", "encefalopatia"],
    "pancreas": ["pancreatitis", "pa", "necrosis pancreatica"],
    "acv": ["acv", "ictus", "stroke", "isquemico", "hemorragico", "ait", "tia"],
    "hsa": ["hsa", "hemorragia subaracnoidea", "aneurisma"],
    "nac": ["nac", "neumonia", "pulmonia", "bronconeumonia", "nih"],
    "epoc": ["epoc", "bronquitis cronica", "enfisema", "aeepoc"],
    "tep": ["tep", "tromboembolismo", "embolia pulmonar"],
    "tvp": ["tvp", "trombosis venosa", "trombosis profunda"],
    "hda": ["hda", "hdb", "hemorragia digestiva", "melena", "hematemesis"],
    "cid": ["cid", "coagulacion intravascular diseminada"],
    "fa": ["fa", "fibrilacion", "fibrilacion auricular", "af", "auricular fibrillation"],
}


@lru_cache(maxsize=1)
def cargar_diccionario_medico(ruta_db: str = "diccionario.json") -> Dict[str, List[str]]:
    """Carga diccionario externo si existe y completa categorías faltantes."""
    fallback_db = {k: list(v) for k, v in FALLBACK_DB.items()}

    if os.path.exists(ruta_db):
        try:
            with open(ruta_db, "r", encoding="utf-8") as archivo:
                data = json.load(archivo)
            for k, v in fallback_db.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return fallback_db

    return fallback_db


def normalizar_texto_medico(texto: str) -> str:
    """Normaliza texto libre para detección robusta de palabras clave."""
    texto_norm = str(texto or "").lower()
    texto_norm = texto_norm.replace(".", "").replace(",", " ")
    texto_norm = re.sub(r"[áäâà]", "a", texto_norm)
    texto_norm = re.sub(r"[éëêè]", "e", texto_norm)
    texto_norm = re.sub(r"[íïîì]", "i", texto_norm)
    texto_norm = re.sub(r"[óöôò]", "o", texto_norm)
    texto_norm = re.sub(r"[úüûù]", "u", texto_norm)
    return texto_norm


def detectar_en_db(categoria: str, texto: str, db_terminologia: Dict[str, List[str]]) -> bool:
    """Detecta si el texto normalizado contiene alguna palabra clave exacta."""
    keywords = db_terminologia.get(categoria, [])
    if not keywords:
        return False

    patron = r"\b(?:" + "|".join(re.escape(kw) for kw in keywords) + r")\b"
    return bool(re.search(patron, texto))
