#!/usr/bin/env python
# coding: utf-8

import os
from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QPushButton, QWidget, QTabWidget
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from Modules.modelos_sin_imagenes import OdontogramView
from Modules.utils import resource_path, parse_dental_states
from Modules.menu_estados import MenuEstados

class MainWindow(QMainWindow):
    def __init__(self, data_dict):
        super().__init__()
        self.setWindowTitle("Odontograma")

        # 1) Modo lectura si hay parámetros
        self.locked_mode = bool(data_dict.get("dientes"))

        # 2) Icono
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 3) Prepara stylesheet global
        self.setup_stylesheet()

        # 4) Vista odontograma
        self.odontogram_view = OdontogramView(locked=self.locked_mode)
        # Se mantendrá un fondo semitransparente o blanco para la zona de dibujo

        # 5) Campos
        self.credencialEdit = QLineEdit(data_dict.get("credencial", ""))
        self.prestadorEdit  = QLineEdit(data_dict.get("prestador", ""))
        self.afiliadoEdit   = QLineEdit(data_dict.get("afiliado", ""))
        self.fechaEdit      = QLineEdit(data_dict.get("fecha", ""))
        self.observacionesEdit = QLineEdit(data_dict.get("observaciones", ""))

        if self.locked_mode:
            for w in [self.credencialEdit, self.prestadorEdit, self.afiliadoEdit,
                      self.fechaEdit, self.observacionesEdit]:
                w.setReadOnly(True)

        # 6) Layout formulario
        formLayout = QFormLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Credencial:"))
        row1.addWidget(self.credencialEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Afiliado:"))
        row1.addWidget(self.afiliadoEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Fecha:"))
        row1.addWidget(self.fechaEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Prestador:"))
        row1.addWidget(self.prestadorEdit)
        formLayout.addRow(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Observaciones:"))
        row2.addWidget(self.observacionesEdit)
        formLayout.addRow(row2)

        # 7) Panel de pestañas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        # Pestaña 1: Prestaciones Existentes
        self.menu_existentes = MenuEstados(
            on_estado_selected=self.on_estado_clicked,
            locked=self.locked_mode,
            title="Lista de Estados"
        )
        self.tabs.addTab(self.menu_existentes, "Prestaciones Existentes")

        # Pestaña 2: Prestaciones Requeridas
        self.menu_requeridas = MenuEstados(
            on_estado_selected=self.on_estado_clicked,
            locked=self.locked_mode,
            title="Lista de Estados",
            estados_personalizados={
                "Caries": "icon_cariesR.png",
                "Extracción": "icon_extraccionR.png",
                "Prótesis Removible SUPERIOR": "icon_prsR.png",
                "Prótesis Removible INFERIOR": "icon_priR.png",
                "Prótesis Completa SUPERIOR": "icon_pcsR.png",
                "Prótesis Completa INFERIOR": "icon_pciR.png",
            }
        )
        self.tabs.addTab(self.menu_requeridas, "Prestaciones Requeridas")

        # 8) Botón Descargar
        self.descargarButton = QPushButton("Descargar")
        self.descargarButton.clicked.connect(self.on_descargar_clicked)

        # Layout izquierdo
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.tabs)
        leftLayout.addWidget(self.descargarButton)
        leftLayout.addStretch()

        # Layout odontograma
        odontoLayout = QVBoxLayout()
        odontoLayout.addWidget(self.odontogram_view)

        # Unión
        hLayout = QHBoxLayout()
        hLayout.addLayout(leftLayout, stretch=0)
        hLayout.addLayout(odontoLayout, stretch=1)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(hLayout)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        self.setFixedSize(1300, 800)
        self.apply_dental_args(data_dict.get("dientes", ""))

    def setup_stylesheet(self):
        """
        Aplica una hoja de estilo global para usar background.jpg como fondo
        y dejar los labels transparentes, etc.
        """
        bg_path = resource_path("src/background.jpg")
        if os.path.exists(bg_path):
            bg_path_ = bg_path.replace('\\', '/')
            self.setStyleSheet(f"""
                /* Fondo global */
                QMainWindow, QWidget {{
                    background-image: url("{bg_path_}");
                    background-repeat: no-repeat;
                    background-position: center;
                }}

                /* Hacemos que inputs y contenedores tengan fondo blanco translúcido */
                QLineEdit, QPushButton, QToolButton, QTabWidget::pane, QComboBox,
                QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
                    background-color: rgba(255,255,255, 0.8);
                }}

                /* QLabels sin fondo */
                QLabel {{
                    background: transparent;
                }}

                /* QGraphicsView con fondo blanco */
                QGraphicsView {{
                    background-color: rgba(255,255,255, 0.9);
                }}
            """)
        else:
            print("[WARN] No se encontró src/background.jpg")

    def on_estado_clicked(self, estado_str):
        print(f"[INFO] Estado seleccionado: {estado_str}")
        self.odontogram_view.set_current_state(estado_str)

    def on_descargar_clicked(self):
        from PyQt5.QtWidgets import QFileDialog

        afil = self.afiliadoEdit.text().strip().replace(" ", "_")
        fecha = self.fechaEdit.text().strip().replace(" ", "_")
        if not afil: afil = "SIN_AFILIADO"
        if not fecha: fecha = "SIN_FECHA"
        file_name = f"odontograma_{afil}_{fecha}.png"

        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not folder_path:
            return

        full_path = os.path.join(folder_path, file_name)
        pixmap = self.grab()
        if pixmap.save(full_path, "PNG"):
            print(f"[OK] Captura guardada: {full_path}")
        else:
            print("[ERROR] No se pudo guardar la imagen.")

    def apply_dental_args(self, dientes_str):
        if dientes_str:
            parsed = parse_dental_states(dientes_str)
            self.odontogram_view.apply_batch_states(parsed)
