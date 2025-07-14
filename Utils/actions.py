# Modules/Utils/actions.py
# coding: utf-8
"""
Acciones comunes:
  • Capturar el QGraphicsView a imagen PNG.
  • Refrescar el odontograma relanzando el SP de estados dentales.
  • Crear botón pequeño “Actualizar”.
"""

# Modules/Utils/actions.py
from __future__ import annotations

import datetime as _dt
import os
from typing import Callable, Sequence, Tuple

from PyQt5.QtCore import Qt, QSize      # ←  añadido QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QToolButton

from Modules.utils import parse_dental_states, resource_path


# ----------------------------------------------------------------------
# 1) Captura del odontograma a PNG
# ----------------------------------------------------------------------
def _default_filename(patient: str | None = None) -> str:
    """Genera nombre 'odontograma_<paciente>_<YYYY-MM-DD>.png'."""
    today = _dt.date.today().isoformat()
    clean_name = patient.replace(" ", "_") if patient else "SIN_TITULAR"
    return f"odontograma_{clean_name}_{today}.png"


def capture_odontogram(
    view: QGraphicsView,
    patient_name: str | None = None,
    captures_dir: str = "Captures",
) -> str:
    """
    Guarda la imagen del QGraphicsView y devuelve la ruta final.
    Lanza excepciones si algo falla (deja que la capa UI las maneje).
    """
    # Asegura carpeta
    os.makedirs(captures_dir, exist_ok=True)

    # Render a pixmap
    pixmap = view.grab()  # Qt >= 5.15

    # Nombre final
    filename = _default_filename(patient_name)
    full_path = os.path.join(captures_dir, filename)

    # Guarda
    if not pixmap.save(full_path, "PNG"):
        raise IOError("No se pudo guardar la captura en PNG")

    return full_path


# ----------------------------------------------------------------------
# 2) Refresco de estados vía Stored Procedure
# ----------------------------------------------------------------------
# Firma esperada del SP:  sp_get_dental_states(conn, patient_id) -> Sequence[Tuple[int,int,str]]
def refresh_states(
    db_connection,
    patient_id: int,
    odontogram_view,  # tipo OdontogramView
    sp_func: Callable[[object, int], Sequence[Tuple[int, int, str]]],
) -> None:
    """
    Llama al stored procedure `sp_func`, obtiene lista
    [(estado_int, diente_int, caras_str), …]
    y la aplica a `odontogram_view`.
    """
    raw_states = sp_func(db_connection, patient_id)
    # El formato ya es (int,int,str); si recibes '117OV' etc. usa parse_dental_states.
    odontogram_view.apply_batch_states(list(raw_states))
    odontogram_view.viewport().update()


# ----------------------------------------------------------------------
# 3) Botón pequeño “Actualizar” (a colocar en tu toolbar / layout)
# ----------------------------------------------------------------------
def make_refresh_button(
    tooltip: str = "Actualizar odontograma",
    on_click: Callable[[], None] | None = None,
) -> QToolButton:
    """Devuelve un botón pequeño con icono de recarga."""
    btn = QToolButton()
    btn.setIcon(QIcon(resource_path("src/icon_refresh.png")))  # usa tu icono real
    btn.setToolTip(tooltip)
    btn.setIconSize(QSize(18, 18))      # ←  antes Qt.QSize
    if on_click:
        btn.clicked.connect(on_click)   # type: ignore[arg-type]
    return btn
