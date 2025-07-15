#Utils/sp_data_parse.py
# coding: utf-8
"""
Parseo de la columna `dientes` devuelta por los SP odontológicos.

Reglas:
• Los ÚLTIMOS 2 dígitos numéricos ⇒ diente (00-99).
• Los dígitos previos ⇒ estado (1-2 dígitos, 1-19).
• Lo que sigue, si existe, son caras (letras MDVBLPIO).

Ejemplos
--------
    "1155"     → estado 11, diente 55, caras ""
    "155"      → estado 1,  diente 55, caras ""
    "117OV"    → estado 1,  diente 17, caras "OV"
    "1418M"    → estado 14, diente 18, caras "M"
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

# --- dependencias centrales desde Modules.utils --------------------
from Modules.utils import (
    MAX_STATE,
    ALL_TEETH,
    VALID_FACE_CHARS,
)

_NUM_FACE_RE = re.compile(r"^(\d{3,4})([A-Za-z]*)$")   # 3-4 dígitos + opcional letras


# ─────────────────────────────────────────────────────────────
# helpers internos
# ─────────────────────────────────────────────────────────────
def _sanitize_faces(faces: str) -> str:
    """Devuelve sólo las letras válidas (M D V B L P I O, mayúsculas)."""
    faces_up = faces.upper()
    if any(c not in VALID_FACE_CHARS for c in faces_up):
        logging.warning("Caras inválidas en '%s'; se descartan las desconocidas", faces)
    return "".join(c for c in faces_up if c in VALID_FACE_CHARS)


# ─────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────
def parse_dientes_sp(raw: str | None) -> List[Tuple[int, int, str]]:
    """
    Convierte un string del SP en lista de tuplas:
        [(estado_int, diente_int, caras_str), …]

    Valida:
    • estado en 1-19
    • diente ∈ ALL_TEETH
    """
    if not raw:
        return []

    tokens = (tok.strip() for tok in raw.split(","))
    result: List[Tuple[int, int, str]] = []

    for tok in tokens:
        if not tok:
            continue

        m = _NUM_FACE_RE.fullmatch(tok)
        if not m:
            logging.warning("Token inválido en columna dientes: '%s'", tok)
            continue

        num_part, face_part = m.groups()

        # — diente: últimos 2 dígitos —
        diente = int(num_part[-2:])

        # — estado: el resto (1 o 2 dígitos) —
        estado = int(num_part[:-2])

        # validaciones
        if not (1 <= estado <= MAX_STATE):
            logging.warning("Estado fuera de rango (1-%d) en '%s'", MAX_STATE, tok)
            continue
        if diente not in ALL_TEETH:
            logging.warning("Diente %s no reconocido en '%s'", diente, tok)
            continue

        caras = _sanitize_faces(face_part)
        result.append((estado, diente, caras))

    return result
