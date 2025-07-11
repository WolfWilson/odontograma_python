# coding: utf-8
"""
Utilidades y constantes globales del proyecto Dental.
"""

import os
import sys
from typing import List

# ─────────────────────────────────────────────────────────────
# Estados y mapeos
# ─────────────────────────────────────────────────────────────
ESTADOS = {
    "Ninguno": 0,
    "Obturacion": 1,
    "Agenesia": 2,
    "PD Ausente": 3,
    "Corona": 4,
    "Implante": 5,
    "Puente": 6,
    "Selladores": 7,
    "Ausente Fisiológico": 8,
    "Prótesis Removible SUPERIOR": 9,
    "Prótesis Removible INFERIOR": 10,
    "Prótesis Completa SUPERIOR": 11,
    "Prótesis Completa INFERIOR": 12,
    "Supernumerario": 13,
    "Extracción": 14,
    "Caries": 15,
}

ESTADOS_POR_NUM = {v: k for k, v in ESTADOS.items()}

# ─────────────────────────────────────────────────────────────
# Abreviaturas para texto de prótesis
# ─────────────────────────────────────────────────────────────
PROTESIS_SHORT = {
    "Prótesis Removible SUPERIOR": "PRS",
    "Prótesis Removible INFERIOR": "PRI",
    "Prótesis Completa SUPERIOR": "PCS",
    "Prótesis Completa INFERIOR": "PCI",
}

# ─────────────────────────────────────────────────────────────
# Configuración geométrica del odontograma
# ─────────────────────────────────────────────────────────────
TOOTH_SIZE: int = 40        # píxeles del cuadrado base
TOOTH_MARGIN: int = 10      # espacio entre piezas

TEETH_ROWS: List[List[str]] = [
    # Adultos superiores
    ["18", "17", "16", "15", "14", "13", "12", "11",
     "21", "22", "23", "24", "25", "26", "27", "28"],
    # Niños superiores
    ["55", "54", "53", "52", "51", "61", "62", "63", "64", "65"],
    # Niños inferiores
    ["85", "84", "83", "82", "81", "71", "72", "73", "74", "75"],
    # Adultos inferiores
    ["48", "47", "46", "45", "44", "43", "42", "41",
     "31", "32", "33", "34", "35", "36", "37", "38"],
]

Y_POSITIONS: List[int] = [50, 200, 350, 500]  # coordenada Y fila a fila

# ─────────────────────────────────────────────────────────────
# Caras ↔ letra para obturación selectiva
# ─────────────────────────────────────────────────────────────
FACE_MAP = {
    "M": "left",     # Mesial  → cara izquierda
    "D": "right",    # Distal  → cara derecha
    "V": "top",      # Vestibular / Bucal → superior
    "B": "top",
    "L": "bottom",   # Lingual / Palatino → inferior
    "P": "bottom",
    "I": "center",   # Incisal / Oclusal → centro
    "O": "center",
}

# ─────────────────────────────────────────────────────────────
# Funciones de utilidad
# ─────────────────────────────────────────────────────────────
def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta a un recurso, compatible con PyInstaller.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def parse_dental_states(dental_str: str):
    """
    Convierte un string '117OV,118OVG' en
    [(estado_int, diente_int, caras_str), …]
    """
    if not dental_str:
        return []
    items = [x.strip() for x in dental_str.split(",") if x.strip()]
    parsed_list = []
    for item in items:
        p = _parse_item_with_backtracking(item)
        if p:
            parsed_list.append(p)
        else:
            print(f"[WARN] No se pudo interpretar: {item}")
    return parsed_list


def _parse_item_with_backtracking(item_str: str):
    """
    Intenta resolver (estado)(diente)(caras). Estado puede ser 1-2 dígitos.
    """
    # Prueba 2 dígitos para estado
    if len(item_str) >= 4:
        try:
            st_int = int(item_str[:2])
            d_int = int(item_str[2:4])
            if st_int in ESTADOS_POR_NUM and 11 <= d_int <= 85:
                return (st_int, d_int, item_str[4:].upper())
        except ValueError:
            pass
    # Prueba 1 dígito para estado
    if len(item_str) >= 3:
        try:
            st_int = int(item_str[0])
            d_int = int(item_str[1:3])
            if st_int in ESTADOS_POR_NUM and 11 <= d_int <= 85:
                return (st_int, d_int, item_str[3:].upper())
        except ValueError:
            pass
    return None
