#!/usr/bin/env python
# coding: utf-8

import sys
import os
import argparse
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QWidget,
    QComboBox, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QFileDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


# Función para cargar imágenes en modo desarrollo o ejecutable
def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Estados del odontograma
ESTADOS = {
    "Ninguno": 0,
    "Obturacion": 1,
    "Agenesia": 2,
    "PD Ausente": 3,
    "Corona": 4,
    "Implante": 5,
    "Puente": 6,
    "Selladores": 7,
    "Ausente Fisiológico": 8,
    "Prótesis Removible SUPERIOR": 9,
    "Prótesis Removible INFERIOR": 10,
    "Prótesis Completa SUPERIOR": 11,
    "Prótesis Completa INFERIOR": 12,
    "Supernumerario": 13
}


# Clase para visualizar el odontograma
class OdontogramView(QGraphicsView):
    def __init__(self, locked=False):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.current_state_name = "Ninguno"
        self.locked = locked


# Ventana principal
class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.setWindowTitle("Odontograma")

        self.odontogram_view = OdontogramView()

        # =========================
        # 1) Datos del Paciente
        # =========================
        self.credencialEdit = QLineEdit(self.args.credencial or "")
        self.prestadorEdit = QLineEdit(self.args.prestador or "")
        self.titularEdit = QLineEdit(self.args.titular or "")
        self.fechaEdit = QLineEdit(self.args.fecha or "")
        self.observacionesEdit = QLineEdit(self.args.observaciones or "")
        self.observacionesEdit.setMaxLength(100)

        formLayout = QFormLayout()
        formLayout.addRow("Credencial:", self.credencialEdit)
        formLayout.addRow("Prestador:", self.prestadorEdit)
        formLayout.addRow("Titular:", self.titularEdit)
        formLayout.addRow("Fecha:", self.fechaEdit)
        formLayout.addRow("Observaciones:", self.observacionesEdit)

        # =========================
        # 2) Leyenda con imagen y selector de estado
        # =========================
        self.legendLabel = QLabel()
        leyenda_path = resource_path("leyenda.png")
        if os.path.exists(leyenda_path):
            self.legendLabel.setPixmap(QPixmap(leyenda_path))
        else:
            self.legendLabel.setText("No se encontró leyenda.png")
        self.legendLabel.setScaledContents(True)
        self.legendLabel.setFixedWidth(280)
        self.legendLabel.setFixedHeight(550)

        # Selector de estado
        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)

        # Layout para leyenda + selector de estado
        legendLayout = QVBoxLayout()
        legendLayout.addWidget(self.legendLabel)
        legendLayout.addWidget(QLabel("Estado actual:"))
        legendLayout.addWidget(self.state_selector)

        # =========================
        # 3) Odontograma a la derecha
        # =========================
        odontogramLayout = QVBoxLayout()
        odontogramLayout.addWidget(self.odontogram_view)

        # =========================
        # Layout horizontal: (Leyenda + Estado) | Odontograma
        # =========================
        hLayoutOdon = QHBoxLayout()
        hLayoutOdon.addLayout(legendLayout)
        hLayoutOdon.addLayout(odontogramLayout)

        # =========================
        # Layout principal
        # =========================
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(hLayoutOdon)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        self.resize(1400, 800)

    def on_state_changed(self, new_state):
        self.odontogram_view.current_state_name = new_state


# Función principal
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titular", default="")
    parser.add_argument("--credencial", default="")
    parser.add_argument("--prestador", default="")
    parser.add_argument("--fecha", default="")
    parser.add_argument("--observaciones", default="", help="Hasta 100 caracteres")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    w = MainWindow(args)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
