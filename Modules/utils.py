# coding: utf-8
"""
Utilidades y constantes globales del proyecto Dental.
(versión con validaciones y estados 0-19, incluidas variantes rojas y
azules de prótesis).
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

    # ---- Prótesis versión ROJA (histórica) ----------------
    "Prótesis Removible SUPERIOR_R": 9,
    "Prótesis Removible INFERIOR_R": 10,
    "Prótesis Completa SUPERIOR_R": 11,
    "Prótesis Completa INFERIOR_R": 12,

    # --------------------------------------------------------
    "Supernumerario": 13,
    "Extracción": 14,
    "Caries": 15,

    # ---- Prótesis versión AZUL (nueva) ---------------------
    "Prótesis Removible SUPERIOR_B": 16,
    "Prótesis Removible INFERIOR_B": 17,
    "Prótesis Completa SUPERIOR_B": 18,
    "Prótesis Completa INFERIOR_B": 19,
}

ESTADOS_POR_NUM = {v: k for k, v in ESTADOS.items()}

MAX_STATE = 19   # rango máximo de estados

# ─────────────────────────────────────────────────────────────
# Abreviaturas para texto de prótesis (ambas variantes → mismo label)
# ─────────────────────────────────────────────────────────────
PROTESIS_SHORT = {
    "Prótesis Removible SUPERIOR_R": "PRS",
    "Prótesis Removible INFERIOR_R": "PRI",
    "Prótesis Completa SUPERIOR_R": "PCS",
    "Prótesis Completa INFERIOR_R": "PCI",

    "Prótesis Removible SUPERIOR_B": "PRS",
    "Prótesis Removible INFERIOR_B": "PRI",
    "Prótesis Completa SUPERIOR_B": "PCS",
    "Prótesis Completa INFERIOR_B": "PCI",
}

# ─────────────────────────────────────────────────────────────
# Configuración geométrica del odontograma
# ─────────────────────────────────────────────────────────────
TOOTH_SIZE: int = 40
TOOTH_MARGIN: int = 10
ROW_MARGIN:   int = 10

# 1) Filas de piezas
TEETH_ROWS: List[List[str]] = [
    ["18","17","16","15","14","13","12","11", "21","22","23","24","25","26","27","28"],
    ["48","47","46","45","44","43","42","41", "31","32","33","34","35","36","37","38"],
    ["55","54","53","52","51","61","62","63","64","65"],
    ["85","84","83","82","81","71","72","73","74","75"],
]

# 2) Posiciones verticales
START_Y = 50
GAP_ADULT = ROW_MARGIN + TOOTH_SIZE
GAP_CHILD_BLOCK = 80
GAP_CHILD = ROW_MARGIN + TOOTH_SIZE

Y_POSITIONS: List[int] = [
    START_Y,
    START_Y + GAP_ADULT,
    START_Y + GAP_ADULT + GAP_CHILD_BLOCK,
    START_Y + GAP_ADULT + GAP_CHILD_BLOCK + GAP_CHILD,
]

# Formato anterior (conservado sólo como referencia)
# TEETH_ROWS_OLD …
# Y_POSITIONS_OLD …

# ─────────────────────────────────────────────────────────────
# Caras ↔ letra para obturación selectiva
# ─────────────────────────────────────────────────────────────
FACE_MAP = {
    "M": "left", "D": "right", "V": "top", "B": "top",
    "L": "bottom", "P": "bottom", "I": "center", "O": "center",
}
VALID_FACE_CHARS = set(FACE_MAP.keys())

# Conjunto de dientes válidos (para validación externa)
ALL_TEETH = {int(n) for fila in TEETH_ROWS for n in fila}

# ─────────────────────────────────────────────────────────────
# Funciones de utilidad
# ─────────────────────────────────────────────────────────────
def resource_path(relative_path: str) -> str:
    """Devuelve la ruta absoluta a un recurso, compatible con PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)
