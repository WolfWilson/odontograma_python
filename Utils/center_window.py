#!/usr/bin/env python
# coding: utf-8
"""
Utils.center_window
Función reutilizable para centrar cualquier `QWidget`.
"""

from __future__ import annotations

from PyQt5.QtCore      import Qt
from PyQt5.QtWidgets   import QApplication, QStyle, QWidget


def center_on_screen(widget: QWidget) -> None:
    """Centrar *widget* en el monitor principal."""
    screen = QApplication.primaryScreen()
    if screen is None:          # ‒ fallback por seguridad
        return

    # ▸ Qt.LeftToRight y Qt.AlignCenter existen en runtime; los «type: ignore»
    #   evitan falsos positivos de Pylance.
    geo = QStyle.alignedRect(
        Qt.LeftToRight,            # type: ignore[attr-defined]
        Qt.AlignCenter,            # type: ignore[attr-defined]
        widget.size(),
        screen.availableGeometry()
    )
    widget.setGeometry(geo)
