# coding: utf-8
"""
Paleta y estilos gráficos para los modelos del odontograma.
Compatible con PyQt5 y PyQt6, sin que Pylance se queje.
"""

from typing import Final

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen

# ─────────────────────────────────────────────────────────────
# Aliases de colores
# ─────────────────────────────────────────────────────────────
BLUE: Final   = getattr(Qt, "blue",        Qt.GlobalColor.blue)
YELLOW: Final = getattr(Qt, "yellow",      Qt.GlobalColor.yellow)
WHITE: Final  = getattr(Qt, "white",       Qt.GlobalColor.white)
RED: Final    = getattr(Qt, "red",         Qt.GlobalColor.red)
DARK_GRAY: Final   = getattr(Qt, "darkGray",   Qt.GlobalColor.darkGray)
DARK_YELLOW: Final = getattr(Qt, "darkYellow", Qt.GlobalColor.darkYellow)

# ─────────────────────────────────────────────────────────────
# Compat 🔄 enum y color que cambian de lugar entre versiones
# ─────────────────────────────────────────────────────────────
DOT_LINE_STYLE = getattr(
    Qt, "DotLine",                      # PyQt5
    getattr(Qt.PenStyle, "DotLine")     # PyQt6
)

TRANSPARENT_COLOR = getattr(
    Qt, "transparent",                      # PyQt5
    getattr(Qt.GlobalColor, "transparent")  # PyQt6
)

# ─────────────────────────────────────────────────────────────
# Plumas
# ─────────────────────────────────────────────────────────────
BLUE_PEN: Final     = QPen(BLUE,   3)
YELLOW_PEN: Final   = QPen(YELLOW, 2)
DOT_BLUE_PEN: Final = QPen(BLUE,   2, DOT_LINE_STYLE)
BRIDGE_PEN: Final   = QPen(BLUE,   4)

# ─────────────────────────────────────────────────────────────
# Brochas
# ─────────────────────────────────────────────────────────────
WHITE_BRUSH: Final       = QBrush(WHITE)
BLUE_BRUSH: Final        = QBrush(BLUE)
YELLOW_BRUSH: Final      = QBrush(YELLOW)
TRANSPARENT_BRUSH: Final = QBrush(TRANSPARENT_COLOR)

BLACK: Final  = getattr(Qt, "black", Qt.GlobalColor.black)  # ← NUEVO
# ─────────────────────────────────────────────────────────────
# Exportación explícita (ayuda adicional a Pylance)
# ─────────────────────────────────────────────────────────────
__all__ = [
    "BLUE", "YELLOW", "WHITE", "RED", "DARK_GRAY", "DARK_YELLOW",
    "BLUE_PEN", "YELLOW_PEN", "DOT_BLUE_PEN", "BRIDGE_PEN",
    "WHITE_BRUSH", "BLUE_BRUSH", "YELLOW_BRUSH", "TRANSPARENT_BRUSH",
]
