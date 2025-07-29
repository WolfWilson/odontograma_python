# coding: utf-8
"""
menu_estados.py – Panel lateral con botones de estados clínicos

• Centraliza la tabla estado → icono.
• Admite:
  – Selección de sufijo de iconos para prótesis (R, B, A…).
  – Listas *include* / *exclude* para mostrar u ocultar estados.
"""

from __future__ import annotations

import os
from typing import Dict, Iterable

from PyQt5.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QToolButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

from Modules.utils import resource_path

# Compatibilidad PyQt5 / PyQt6 -------------------------------------------------
try:                                   # PyQt6
    TOOL_BTN_TEXT_BESIDE_ICON = Qt.ToolButtonStyle.ToolButtonTextBesideIcon  # type: ignore[attr-defined]
except AttributeError:                 # PyQt5
    TOOL_BTN_TEXT_BESIDE_ICON = Qt.ToolButtonTextBesideIcon                  # type: ignore[attr-defined]

# -----------------------------------------------------------------------------
# 1) Diccionario base – usa placeholder {} para los iconos de prótesis
# -----------------------------------------------------------------------------
_BASE_ICONOS: Dict[str, str] = {
    "Obturacion": "icon_obturacion.png",
    "Agenesia": "icon_agenesia.png",
    "PD Ausente": "icon_pd_ausente.png",
    "Corona": "icon_corona.png",
    "Implante": "icon_implante.png",
    "Puente": "icon_puente.png",
    "Selladores": "icon_selladores.png",
    "Ausente Fisiológico": "icon_ausente_fisio.png",

    # Prótesis (el sufijo se inserta dinámicamente)
    "Prótesis Removible SUPERIOR": "icon_prs{}.png",
    "Prótesis Removible INFERIOR": "icon_pri{}.png",
    "Prótesis Completa SUPERIOR":  "icon_pcs{}.png",
    "Prótesis Completa INFERIOR":  "icon_pci{}.png",

    # "Supernumerario": "icon_supernumerario.png",   # oculto temporal
    "Extracción": "icon_extraccionR.png",
    "Caries":     "icon_cariesR.png",
}

# -----------------------------------------------------------------------------
# 2) Helper de construcción
# -----------------------------------------------------------------------------
def build_icon_dict(
    *,
    prosthesis_suffix: str = "R",
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> Dict[str, str]:
    """
    Devuelve un mapping {estado: nombre_icono}.

    :param prosthesis_suffix: “R”, “B”, “A”… usado sólo en iconos de prótesis.
    :param include: si se provee, SOLO estos estados se incluyen.
    :param exclude: estados a descartar.
    """
    incl_set = set(include) if include else None
    excl_set = set(exclude or ())

    out: Dict[str, str] = {}
    for estado, icon_tpl in _BASE_ICONOS.items():
        if incl_set is not None and estado not in incl_set:
            continue
        if estado in excl_set:
            continue

        icon_file = icon_tpl.format(prosthesis_suffix) if "{}" in icon_tpl else icon_tpl
        out[estado] = icon_file
    return out

# -----------------------------------------------------------------------------
# 3) Widget del menú
# -----------------------------------------------------------------------------
class MenuEstados(QWidget):
    """
    Panel vertical con botones (icono + texto).

    • on_estado_selected → callback(str) al hacer clic.
    • locked=True        → botones deshabilitados.
    • icon_dict          → mapping estado→icono pre-construido.
    """

    def __init__(
        self,
        on_estado_selected,
        *,
        locked: bool = True,
        title: str = "Estados",
        icon_dict: Dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.on_estado_selected = on_estado_selected
        self.locked = locked
        self.icon_dict = icon_dict or build_icon_dict()

        grp_box = QGroupBox(title)
        vbox = QVBoxLayout()
        vbox.setSpacing(10)

        for estado, icon_file in self.icon_dict.items():
            btn = QToolButton()
            btn.setText(estado)
            btn.setToolButtonStyle(TOOL_BTN_TEXT_BESIDE_ICON)
            btn.setIconSize(QSize(80, 80))

            icon_path = resource_path(os.path.join("src", icon_file))
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            else:
                print(f"[WARN] Ícono no encontrado: {icon_path}")

            btn.clicked.connect(lambda _, est=estado: self._on_click(est))
            btn.setEnabled(not self.locked)
            vbox.addWidget(btn)

        grp_box.setLayout(vbox)

        root = QVBoxLayout()
        root.addWidget(grp_box)
        root.addStretch()
        self.setLayout(root)

    # ------------------------------------------------------------------
    def _on_click(self, estado: str) -> None:
        if not self.locked and callable(self.on_estado_selected):
            self.on_estado_selected(estado)
