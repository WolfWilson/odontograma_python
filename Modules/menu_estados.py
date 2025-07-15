# Modules/menu_estados.py
# coding: utf-8

import os
from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QToolButton
)

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
# al inicio, después de importar Qt
try:
    # PyQt6
    TOOL_BTN_TEXT_BESIDE_ICON = Qt.ToolButtonStyle.ToolButtonTextBesideIcon  # type: ignore[attr-defined]
except AttributeError:
    # PyQt5
    TOOL_BTN_TEXT_BESIDE_ICON = Qt.ToolButtonTextBesideIcon # type: ignore[attr-defined]

from Modules.utils import resource_path


# Diccionario global: nombre del estado -> icono
ESTADOS_ICONOS = {
    "Obturacion": "icon_obturacion.png",
    "Agenesia": "icon_agenesia.png",
    "PD Ausente": "icon_pd_ausente.png",
    "Corona": "icon_corona.png",
    "Implante": "icon_implante.png",
    "Puente": "icon_puente.png",
    "Selladores": "icon_selladores.png",
    "Ausente Fisiológico": "icon_ausente_fisio.png",
    "Prótesis Removible SUPERIOR": "icon_prs.png",
    "Prótesis Removible INFERIOR": "icon_pri.png",
    "Prótesis Completa SUPERIOR": "icon_pcs.png",
    "Prótesis Completa INFERIOR": "icon_pci.png",
    "Supernumerario": "icon_supernumerario.png"
}

class MenuEstados(QWidget):
    """
    Un panel con botones estilo ícono + texto.
    Permite pasar estados personalizados o usar los globales.
    """
    def __init__(self, on_estado_selected, locked=False, title="Lista de Estados", estados_personalizados=None):
        """
        :param on_estado_selected: función a invocar al hacer clic
        :param locked: deshabilita los botones si True
        :param title: título del groupbox
        :param estados_personalizados: diccionario opcional de estados -> íconos
        """
        super().__init__()
        self.on_estado_selected = on_estado_selected
        self.locked = locked

        # Usa estados personalizados si se pasan, si no usa los globales
        self.estados_dict = estados_personalizados if estados_personalizados else ESTADOS_ICONOS

        self.grp_box = QGroupBox(title)
        layout_group = QVBoxLayout()
        layout_group.setSpacing(10)

        for estado_text, icon_file in self.estados_dict.items():
            btn = QToolButton()
            btn.setText(estado_text)
            
            btn.setToolButtonStyle(TOOL_BTN_TEXT_BESIDE_ICON)
            btn.setIconSize(QSize(80, 80))

            icon_path = resource_path(os.path.join("src", icon_file))
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            else:
                print(f"[WARN] Ícono no encontrado: {icon_path}")

            btn.clicked.connect(lambda _, est=estado_text: self.handle_click(est))
            btn.setEnabled(not locked)

            layout_group.addWidget(btn)

        self.grp_box.setLayout(layout_group)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.grp_box)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def handle_click(self, estado_str):
        """Invoca el callback si no está bloqueado."""
        if not self.locked and callable(self.on_estado_selected):
            self.on_estado_selected(estado_str)
