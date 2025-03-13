#!/usr/bin/env python
# coding: utf-8

import sys
import os
from pathlib import Path
import argparse
from collections import defaultdict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView,QGraphicsTextItem, QGraphicsScene, QWidget,
    QComboBox, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton
)
from PyQt5.QtGui import (
    QBrush, QPen, QFont, QPixmap
)
from PyQt5.QtCore import Qt, QRectF

# Módulos locales
try:
    from PyQt5.QtWidgets import QFileDialog
    from Modules.style import apply_style
except ImportError:
    def apply_style(x):
        pass

# Importamos utilidades y modelos
from Modules.utils import (
    resource_path,
    parse_dental_states,
    ESTADOS,
    ESTADOS_POR_NUM
)
from Modules.modelos import ToothFacePolygon, ToothItem


# -----------------------------
# Clase OdontogramView
# -----------------------------
class OdontogramView(QGraphicsView):
    def __init__(self, locked=False):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.current_state_name = "Ninguno"
        self.locked = locked

        self.bridge_lines = []
        self.dientes = []
        self.create_teeth()

    def create_teeth(self):
        size = 40
        margin = 10

        row1 = ["18","17","16","15","14","13","12","11","21","22","23","24","25","26","27","28"]
        row2 = ["55","54","53","52","51","61","62","63","64","65"]
        row3 = ["85","84","83","82","81","71","72","73","74","75"]
        row4 = ["48","47","46","45","44","43","42","41","31","32","33","34","35","36","37","38"]

        rows = [row1, row2, row3, row4]
        y_positions = [50, 200, 350, 500]

        total_width_row1 = len(row1)*(size+margin) - margin
        total_width_row2 = len(row2)*(size+margin) - margin
        total_width_row3 = len(row3)*(size+margin) - margin

        offset_x_row2 = (total_width_row1 - total_width_row2)//2
        offset_x_row3 = (total_width_row1 - total_width_row3)//2

        for idx, row in enumerate(rows):
            y = y_positions[idx]
            if idx == 1:
                x_start = 50 + offset_x_row2
            elif idx == 2:
                x_start = 50 + offset_x_row3
            else:
                x_start = 50

            tooth_row = []
            for i, tnum in enumerate(row):
                x = x_start + i*(size+margin)
                t = ToothItem(x, y, size, self.scene, self, tnum)
                tooth_row.append(t)

                # Texto debajo del diente
                txt = QGraphicsTextItem(tnum)
                txt.setFont(QFont("Arial", 10))
                txt.setDefaultTextColor(Qt.black)
                txt.setPos(x + size/2 - txt.boundingRect().width()/2, y + size + 3)
                self.scene.addItem(txt)

            self.dientes.append(tooth_row)

    def set_current_state(self, state_name):
        self.current_state_name = state_name

    def update_bridges(self):
        """
        Redibuja las líneas de puente entre dientes marcados.
        """
        for line_item in self.bridge_lines:
            self.scene.removeItem(line_item)
        self.bridge_lines.clear()

        for row in self.dientes:
            bridging_teeth = [t for t in row if t.has_bridge]
            if not bridging_teeth:
                continue
            for tooth in bridging_teeth:
                rect = tooth.top.mapToScene(tooth.top.boundingRect()).boundingRect()
                y_line = rect.center().y() + (tooth.size / 2) - 10
                x_left = rect.left() - 5
                x_right = rect.right() + 5
                pen_bridge = QPen(Qt.blue, 4)
                puente_line = self.scene.addLine(x_left, y_line, x_right, y_line, pen_bridge)
                puente_line.setZValue(0)
                self.bridge_lines.append(puente_line)

    def apply_batch_states(self, states_list):
        """
        Aplica en lote una lista de estados, p.ej. [(1, 11, 'MD'), (2, 12, 'V'), ...].
        El primer elemento de la tupla es el estado (int), el segundo el diente (int),
        y el tercero las caras (str).
        """
        from collections import defaultdict
        tooth_states = defaultdict(list)
        for (st_int, d_int, faces) in states_list:
            estado_name = ESTADOS_POR_NUM.get(st_int, None)
            if not estado_name:
                print(f"Estado {st_int} no definido")
                continue
            found = self.find_tooth(str(d_int))
            if not found:
                print(f"No se encontró la pieza {d_int}")
                continue
            tooth_states[d_int].append((estado_name, faces))

        # Primero reseteamos todos los dientes
        for row in self.dientes:
            for t in row:
                t.reset_tooth()

        # Luego aplicamos los estados
        for d_int, est_list in tooth_states.items():
            found = self.find_tooth(str(d_int))
            for (ename, faces) in est_list:
                if ename == "Obturacion" and faces:
                    found.apply_obturation_faces(faces)
                else:
                    found.apply_state(ename)

        self.update_bridges()

    def find_tooth(self, d_str):
        for row in self.dientes:
            for t in row:
                if t.tooth_num == d_str:
                    return t
        return None


# --------------------------------------------------------------------
# Ventana Principal
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.setWindowTitle("Odontograma")

        # Bloqueo de edición si se especifican dientes
        ds = self.args.dientes.strip()
        self.locked_mode = bool(ds)

        # Vista del odontograma
        self.odontogram_view = OdontogramView(locked=self.locked_mode)

        # -----------------------------
        # Datos del paciente
        # -----------------------------
        self.credencialEdit = QLineEdit(self.args.credencial or "")
        self.prestadorEdit  = QLineEdit(self.args.prestador  or "")
        self.titularEdit    = QLineEdit(self.args.titular    or "")
        self.fechaEdit      = QLineEdit(self.args.fecha      or "")
        self.observacionesEdit = QLineEdit(self.args.observaciones or "")
        self.observacionesEdit.setMaxLength(100)

        # Si está bloqueado, no se pueden editar
        if self.locked_mode:
            self.credencialEdit.setReadOnly(True)
            self.prestadorEdit.setReadOnly(True)
            self.titularEdit.setReadOnly(True)
            self.fechaEdit.setReadOnly(True)
            self.observacionesEdit.setReadOnly(True)

        # Layout formulario
        formLayout = QFormLayout()

        # Fila 1 => Credencial, Titular, Fecha
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Credencial:"))
        row1.addWidget(self.credencialEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Afiliado:"))
        row1.addWidget(self.titularEdit)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Fecha:"))
        row1.addWidget(self.fechaEdit)
        formLayout.addRow(row1)

        row1.addWidget(QLabel("Prestador:"))
        row1.addWidget(self.prestadorEdit)
        formLayout.addRow(row1)

        # Fila 3 => Observaciones
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Observaciones:"))
        row3.addWidget(self.observacionesEdit)
        formLayout.addRow(row3)

        # -----------------------------
        # Leyenda + Estado actual + Botón Descargar
        # -----------------------------
        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)
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

        # Aplica estados si hay 'dientes'
        self.apply_dental_args()

    def on_state_changed(self, new_state):
        self.odontogram_view.set_current_state(new_state)

    def on_descargar_clicked(self):
        """
        Abre un cuadro de diálogo para que el usuario elija el directorio donde guardar la imagen.
        Guarda la captura de la ventana con el nombre "odontograma_{TITULAR}_{FECHA}.png".
        """
        from PyQt5.QtWidgets import QFileDialog

        titular = self.titularEdit.text().strip().replace(" ", "_")
        fecha = self.fechaEdit.text().strip().replace(" ", "_")
        if not titular:
            titular = "SIN_TITULAR"
        if not fecha:
            fecha = "SIN_FECHA"
        file_name = f"odontograma_{titular}_{fecha}.png"

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

    def apply_dental_args(self):
        ds = self.args.dientes
        if ds:
            parsed = parse_dental_states(ds)
            for (s_i, d_i, car) in parsed:
                print(f"PARSE => estado={s_i}, diente={d_i}, caras='{car}'")
            self.odontogram_view.apply_batch_states(parsed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titular", default="")
    parser.add_argument("--credencial", default="")
    parser.add_argument("--prestador", default="")
    parser.add_argument("--fecha", default="")
    parser.add_argument("--observaciones", default="", help="Hasta 100 caracteres")
    parser.add_argument("--dientes", default="", help="p.ej. '652,1052'")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    apply_style(app)
    w = MainWindow(args)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


