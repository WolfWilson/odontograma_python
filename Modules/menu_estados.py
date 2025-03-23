# Modules/menu_estados.py
# coding: utf-8

import os
from PyQt5.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QToolButton
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
from Modules.utils import resource_path

# Diccionario: "Nombre del estado" -> "Nombre de ícono"
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
    Un contenedor (QGroupBox) con un botón por cada estado,
    mostrando un ícono más grande (50×50) y texto.
    Al hacer clic en un botón, se llama on_estado_selected(estado_str).
    Si locked=True, los botones están deshabilitados.
    """
    def __init__(self, on_estado_selected, locked=False, title="Lista de Estados"):
        super().__init__()
        self.on_estado_selected = on_estado_selected
        self.locked = locked

        self.grp_box = QGroupBox(title)
        layout_group = QVBoxLayout()
        layout_group.setSpacing(10)

        for estado_text, icon_file in ESTADOS_ICONOS.items():
            # Creamos un QToolButton con ícono y texto
            btn = QToolButton()
            btn.setText(estado_text)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

            # Ajusta el tamaño de ícono a 50×50
            btn.setIconSize(QSize(80, 80))

            # Carga el ícono desde src/
            icon_path = resource_path(os.path.join("src", icon_file))
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            else:
                print(f"[WARN] Ícono no encontrado: {icon_path}")

            # Conectamos la señal de clic
            btn.clicked.connect(lambda _, est=estado_text: self.handle_click(est))
            btn.setEnabled(not locked)

            layout_group.addWidget(btn)

        self.grp_box.setLayout(layout_group)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.grp_box)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def handle_click(self, estado_str):
        """Invoca el callback on_estado_selected si no está locked."""
        if not self.locked and callable(self.on_estado_selected):
            self.on_estado_selected(estado_str)
