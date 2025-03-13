#!/usr/bin/env python
# coding: utf-8

import os
from PyQt5.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QPushButton, QComboBox, QWidget
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from Modules.modelos import OdontogramView
from Modules.utils import (
    resource_path,
    parse_dental_states,
    ESTADOS
)

class MainWindow(QMainWindow):
    def __init__(self, data_dict):
        """
        data_dict -> credencial, afiliado, prestador, fecha, observaciones, dientes
                     (pueden estar vacíos si no hay param).
        """
        super().__init__()
        self.setWindowTitle("Odontograma")

        # Decide si la interfaz estará bloqueada o no.
        # Ejemplo: si "dientes" viene vacío => lo dejamos editable (False).
        #          si "dientes" tiene algo => lo bloqueamos (True).
        # Ajusta la lógica según tu preferencia.
        self.locked_mode = bool(data_dict.get("dientes"))

        # Creamos la vista del odontograma con la bandera locked_mode
        self.odontogram_view = OdontogramView(locked=self.locked_mode)

        # Campos
        self.credencialEdit = QLineEdit(data_dict.get("credencial", ""))
        self.prestadorEdit  = QLineEdit(data_dict.get("prestador", ""))
        self.afiliadoEdit   = QLineEdit(data_dict.get("afiliado", ""))  # Antes era titular
        self.fechaEdit      = QLineEdit(data_dict.get("fecha", ""))
        self.observacionesEdit = QLineEdit(data_dict.get("observaciones", ""))
        self.observacionesEdit.setMaxLength(100)

        # Si locked_mode => bloquea todos los campos
        if self.locked_mode:
            for field in [
                self.credencialEdit, self.prestadorEdit, 
                self.afiliadoEdit, self.fechaEdit, self.observacionesEdit
            ]:
                field.setReadOnly(True)

        # Layout formulario
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
        formLayout.addRow(row1)

        row1.addWidget(QLabel("Prestador:"))
        row1.addWidget(self.prestadorEdit)
        formLayout.addRow(row1)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Observaciones:"))
        row3.addWidget(self.observacionesEdit)
        formLayout.addRow(row3)

        # Leyenda + Estado actual + Botón Descargar
        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)

        # Si locked => inhabilita el selector
        if self.locked_mode:
            self.state_selector.setEnabled(False)

        self.legendLabel = QLabel()
        leyenda_path = resource_path("leyenda.png")
        if os.path.exists(leyenda_path):
            self.legendLabel.setPixmap(QPixmap(leyenda_path))
        else:
            self.legendLabel.setText("No se encontró leyenda.png")
        self.legendLabel.setScaledContents(True)
        self.legendLabel.setFixedWidth(280)
        self.legendLabel.setFixedHeight(550)

        self.descargarButton = QPushButton("Descargar")
        self.descargarButton.clicked.connect(self.on_descargar_clicked)

        legendLayout = QVBoxLayout()
        legendLayout.addWidget(self.legendLabel)
        lblEstado = QLabel("Estado actual:")
        legendLayout.addWidget(lblEstado)
        legendLayout.addWidget(self.state_selector)
        legendLayout.addWidget(self.descargarButton)

        odontoLayout = QVBoxLayout()
        odontoLayout.addWidget(self.odontogram_view)

        hLayoutOdon = QHBoxLayout()
        hLayoutOdon.addLayout(legendLayout)
        hLayoutOdon.addLayout(odontoLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(hLayoutOdon)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        self.resize(1400, 800)

        # Aplica estados
        self.apply_dental_args(data_dict.get("dientes", ""))

    def on_state_changed(self, new_state):
        self.odontogram_view.set_current_state(new_state)

    def on_descargar_clicked(self):
        from PyQt5.QtWidgets import QFileDialog

        afiliado = self.afiliadoEdit.text().strip().replace(" ", "_")
        fecha = self.fechaEdit.text().strip().replace(" ", "_")
        if not afiliado:
            afiliado = "SIN_AFILIADO"
        if not fecha:
            fecha = "SIN_FECHA"
        file_name = f"odontograma_{afiliado}_{fecha}.png"

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
            from Modules.utils import parse_dental_states
            parsed = parse_dental_states(dientes_str)
            self.odontogram_view.apply_batch_states(parsed)
