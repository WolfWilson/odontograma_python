#!/usr/bin/env python
# Modules/views.py
# coding: utf-8

import os
from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QPushButton, QWidget
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Opción con/sin imágenes
# from Modules.modelos import OdontogramView
from Modules.modelos_sin_imagenes import OdontogramView

from Modules.utils import resource_path, parse_dental_states
from Modules.menu_estados import MenuEstados


class MainWindow(QMainWindow):
    def __init__(self, data_dict):
        super().__init__()
        self.setWindowTitle("Odontograma")

        # 1) Determina si hay parámetros => locked
        self.locked_mode = bool(data_dict.get("dientes"))

        # 2) Icono
        icon_path = resource_path("src/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 3) Fondo
        bg_path = resource_path("src/background.jpg")
        if os.path.exists(bg_path):
            bg_path_ = bg_path.replace('\\', '/')
            css = f"""
            QMainWindow {{
                background-image: url("{bg_path_}");
                background-repeat: no-repeat;
                background-position: center;
            }}
            """
            self.setStyleSheet(css)

        # 4) Vista odontograma
        self.odontogram_view = OdontogramView(locked=self.locked_mode)
        self.odontogram_view.setStyleSheet("background-color: white;")

        # 5) Campos
        self.credencialEdit = QLineEdit(data_dict.get("credencial", ""))
        self.prestadorEdit  = QLineEdit(data_dict.get("prestador", ""))
        self.afiliadoEdit   = QLineEdit(data_dict.get("afiliado", ""))
        self.fechaEdit      = QLineEdit(data_dict.get("fecha", ""))
        self.observacionesEdit = QLineEdit(data_dict.get("observaciones", ""))

        # Si locked => no editable
        if self.locked_mode:
            for w in [self.credencialEdit, self.prestadorEdit, self.afiliadoEdit,
                      self.fechaEdit, self.observacionesEdit]:
                w.setReadOnly(True)

        # 6) Layout formulario
        formLayout = QFormLayout()

        # Fila 1 => Credencial, Afiliado, Fecha, Prestador
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

        # Fila 2 => Observaciones
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Observaciones:"))
        row2.addWidget(self.observacionesEdit)
        formLayout.addRow(row2)

        # Panel de estados con íconos-botones
        self.menu_estados = MenuEstados(
            on_estado_selected=self.on_estado_clicked,
            locked=self.locked_mode,
            title="Lista de Estados"
        )

        self.descargarButton = QPushButton("Descargar")
        self.descargarButton.clicked.connect(self.on_descargar_clicked)

        # Layout izquierdo
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.menu_estados)
        leftLayout.addWidget(self.descargarButton)
        leftLayout.addStretch()

        # Layout derecho => Odontograma
        odontoLayout = QVBoxLayout()
        odontoLayout.addWidget(self.odontogram_view)

        # Unimos ambos
        hLayout = QHBoxLayout()
        hLayout.addLayout(leftLayout)
        hLayout.addLayout(odontoLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(hLayout)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        # 7) Fijar tamaño => 1200x700 (ajusta si quieres)
        self.setFixedSize(1300, 800)

        # Aplica estados si hay 'dientes'
        self.apply_dental_args(data_dict.get("dientes", ""))

    def on_estado_clicked(self, estado_str):
        """
        Callback al hacer clic en un botón de estado (icono).
        => Cambia el estado actual del odontograma
        => Al hacer clic en caras, se dibuja esa acción.
        """
        print(f"Estado seleccionado: {estado_str}")
        self.odontogram_view.set_current_state(estado_str)

    def on_descargar_clicked(self):
        from PyQt5.QtWidgets import QFileDialog

        afil = self.afiliadoEdit.text().strip().replace(" ", "_")
        fecha = self.fechaEdit.text().strip().replace(" ", "_")
        if not afil:
            afil = "SIN_AFILIADO"
        if not fecha:
            fecha = "SIN_FECHA"
        file_name = f"odontograma_{afil}_{fecha}.png"

        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", "")
        if not folder_path:
            return

        full_path = os.path.join(folder_path, file_name)
        pixmap = self.grab()
        saved_ok = pixmap.save(full_path, "PNG")
        if saved_ok:
            print(f"Captura guardada en: {full_path}")
        else:
            print("Error al guardar la captura.")

    def apply_dental_args(self, dientes_str):
        if dientes_str:
            parsed = parse_dental_states(dientes_str)
            self.odontogram_view.apply_batch_states(parsed)
