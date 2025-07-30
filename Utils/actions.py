#!/usr/bin/env python
# coding: utf-8
"""
Modules/Utils/actions.py

Acciones comunes:
  • Capturar el QGraphicsView a imagen PNG (incluye fondo degradado).
  • Refrescar el odontograma relanzando el SP de estados dentales.
  • Crear un botón pequeño “Actualizar”.
"""
from __future__ import annotations

import os
from typing import Callable, Sequence, Tuple

from PyQt5.QtCore    import QSize
from PyQt5.QtGui     import (
    QColor, QIcon, QLinearGradient, QPainter, QPixmap,
)
from PyQt5.QtWidgets import QGraphicsView, QToolButton, QWidget

from Modules.utils   import resource_path


# ════════════════════════════════════════════════════════════
# 1) Captura del odontograma a PNG
# ════════════════════════════════════════════════════════════
def _default_filename(tag: str | None = None) -> str:
    """
    Devuelve 'odontograma_<TAG>.png'.

    • TAG suele recibirse como "<credencial>_<dd/mm/aaaa>".
      Se normaliza cambiando espacios → “_” y “/” → “-”.
    """
    if not tag:
        tag = "SIN_TITULAR"
    tag = tag.replace(" ", "_").replace("/", "-")
    return f"odontograma_{tag}.png"


def capture_odontogram(
    view: QGraphicsView,
    patient_name: str | None = None,
    captures_dir: str = "Captures",
) -> str:
    """
    Renderiza `view` en un QPixmap con el mismo degradado
    de la aplicación y guarda la imagen como PNG.

    Devuelve la ruta completa del archivo generado.
    """
    # ── Directorio destino ──────────────────────────────
    os.makedirs(captures_dir, exist_ok=True)

    # ── Viewport (no debería ser None; se valida para Pylance) ──
    vp: QWidget | None = view.viewport()
    if vp is None:                       # seguridad + silencia advertencias
        raise RuntimeError("graphicsView.viewport() devolvió None")

    dpr = vp.devicePixelRatioF()         # factor DPR (Hi-DPI)
    w_px = int(vp.width()  * dpr)
    h_px = int(vp.height() * dpr)

    pm = QPixmap(w_px, h_px)
    pm.setDevicePixelRatio(dpr)

    # ── Painter: fondo degradado + contenido de la vista ──
    painter = QPainter(pm)

    # 1) Fondo (mismo degradado global)
    grad = QLinearGradient(0, 0, 0, h_px / dpr)
    grad.setColorAt(0, QColor("#dff3ff"))   # celeste claro
    grad.setColorAt(1, QColor("#b1e0ff"))   # celeste más intenso
    painter.fillRect(pm.rect(), grad)

    # 2) Render del QGraphicsView encima
    view.render(painter)
    painter.end()

    # ── Guardado ─────────────────────────────────────────
    filename  = _default_filename(patient_name)
    full_path = os.path.join(captures_dir, filename)

    if not pm.save(full_path, "PNG"):
        raise IOError("No se pudo guardar la captura en PNG")

    return full_path


# ════════════════════════════════════════════════════════════
# 2) Refresco de estados vía Stored-Procedure
# ════════════════════════════════════════════════════════════
# Firma esperada del SP:
#   sp_get_dental_states(conn, patient_id) -> Sequence[Tuple[int,int,str]]
def refresh_states(
    db_connection,
    patient_id: int,
    odontogram_view,  # tipo OdontogramView
    sp_func: Callable[[object, int], Sequence[Tuple[int, int, str]]],
) -> None:
    """
    Llama al stored-procedure `sp_func`, obtiene la lista
    [(estado_int, diente_int, caras_str), …]  y la aplica al odontograma.
    """
    raw_states = sp_func(db_connection, patient_id)
    odontogram_view.apply_batch_states(list(raw_states))
    odontogram_view.viewport().update()


# ════════════════════════════════════════════════════════════
# 3) Botón pequeño “Actualizar”
# ════════════════════════════════════════════════════════════
def make_refresh_button(
    tooltip: str = "Actualizar odontograma",
    on_click: Callable[[], None] | None = None,
) -> QToolButton:
    """Devuelve un QToolButton compacto con icono de recarga."""
    btn = QToolButton()
    btn.setIcon(QIcon(resource_path("src/icon_refresh.png")))  # usa tu icono real
    btn.setToolTip(tooltip)
    btn.setIconSize(QSize(18, 18))
    if on_click:
        btn.clicked.connect(on_click)   # type: ignore[arg-type]
    return btn
