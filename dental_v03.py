#!/usr/bin/env python
# coding: utf-8

import sys
import argparse
from collections import defaultdict

# Importamos PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QWidget,
    QGraphicsPolygonItem, QGraphicsTextItem, QComboBox, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QLineEdit, QLabel, QPlainTextEdit
)
from PyQt5.QtGui import (
    QBrush, QPen, QFont, QPolygonF
)
from PyQt5.QtCore import Qt, QPointF, QRectF

# Importamos la función de estilo
from Modules.style import apply_style

# -----------------------------
# Diccionario de ESTADOS
# -----------------------------
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
ESTADOS_POR_NUM = {v: k for k, v in ESTADOS.items()}


# -----------------------------
# Parseador con backtracking
# -----------------------------
def parse_dental_states(dental_str):
    """
    Ejemplo de entrada: "652,1052"
    - '652' se interpreta como estado=6, diente=52 (caras= vacío).
    - '1052' se interpreta como estado=10, diente=52 (caras= vacío).
    También se soporta algo como '652MOD' => estado=6, diente=52, caras='MOD'
    """
    if not dental_str:
        return []
    items = [x.strip() for x in dental_str.split(",") if x.strip()]
    parsed_list = []
    for item in items:
        p = parse_item_with_backtracking(item)
        if p:
            parsed_list.append(p)  # (estado_int, d_int, caras_str)
        else:
            print(f"WARNING: No se pudo interpretar: {item}")
    return parsed_list

def parse_item_with_backtracking(item_str):
    # Intenta 2 dígitos de estado
    if len(item_str) >= 4:
        try:
            st_candidate = item_str[:2]
            st_int = int(st_candidate)
            if 1 <= st_int <= 13:
                d_candidate = item_str[2:4]
                d_int = int(d_candidate)
                if 11 <= d_int <= 85:
                    faces = item_str[4:].upper()
                    return (st_int, d_int, faces)
        except:
            pass
    # Intenta 1 dígito de estado
    if len(item_str) >= 3:
        try:
            st_candidate = item_str[0]
            st_int = int(st_candidate)
            if 1 <= st_int <= 13:
                d_candidate = item_str[1:3]
                d_int = int(d_candidate)
                if 11 <= d_int <= 85:
                    faces = item_str[3:].upper()
                    return (st_int, d_int, faces)
        except:
            pass
    return None


# -----------------------------
# Clase ToothFacePolygon
# -----------------------------
class ToothFacePolygon(QGraphicsPolygonItem):
    """
    Polígono que representa una cara del diente.
    La interacción del mouse se bloquea si 'locked=True' en la vista.
    """
    def __init__(self, points, parent_tooth, face_name):
        super().__init__()
        poly = QPolygonF()
        for (px, py) in points:
            poly.append(QPointF(px, py))
        self.setPolygon(poly)
        self.tooth = parent_tooth
        self.face_name = face_name
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 2))
        self.is_selected = False

    def mousePressEvent(self, event):
        # Si la vista está bloqueada, ignoramos la interacción
        if self.tooth.odontogram_view.locked:
            return

        # Modo manual: cambiar estado según el combobox seleccionado
        current_state = self.tooth.odontogram_view.current_state_name

        if current_state == "Obturacion":
            # Toggle de color para ejemplificar
            if not self.is_selected:
                self.setBrush(QBrush(Qt.blue))
                self.is_selected = True
            else:
                self.setBrush(QBrush(Qt.white))
                self.is_selected = False

        elif current_state == "Puente":
            # Toggle de "has_bridge" en el diente completo
            self.tooth.has_bridge = not self.tooth.has_bridge
            self.tooth.odontogram_view.update_bridges()

        else:
            # Otros estados
            self.tooth.apply_state(current_state)

        super().mousePressEvent(event)


# -----------------------------
# Clase ToothItem
# -----------------------------
class ToothItem:
    """
    Un diente con 5 polígonos + overlays y un flag de puente.
    """
    def __init__(self, x, y, size, scene, odontogram_view, tooth_num):
        self.scene = scene
        self.odontogram_view = odontogram_view
        self.size = size
        self.tooth_num = tooth_num  # string (p.ej "11", "48")

        # Polígonos
        self.top = None
        self.right = None
        self.bottom = None
        self.left = None
        self.center = None

        # Overlays
        self.cross_lines = []
        self.corona_circle = None
        self.implante_text = None
        self.sellador_circle = None
        self.ausente_fisio_circle = None
        self.protesis_text = None
        self.supernumerario_circle = None
        self.supernumerario_text = None

        # Flag para el puente
        self.has_bridge = False

        self.create_faces(x, y, size)
        self.create_overlays(x, y, size)

    def create_faces(self, x, y, size):
        fs = size / 3
        tl = (x,       y)
        tr = (x+size,  y)
        br = (x+size,  y+size)
        bl = (x,       y+size)
        ctl= (x+fs,       y+fs)
        ctr= (x+size-fs,  y+fs)
        cbr= (x+size-fs,  y+size-fs)
        cbl= (x+fs,       y+size-fs)

        self.top    = ToothFacePolygon([tl,tr,ctr,ctl], self, "top")
        self.right  = ToothFacePolygon([tr,br,cbr,ctr], self, "right")
        self.bottom = ToothFacePolygon([br,bl,cbl,cbr], self, "bottom")
        self.left   = ToothFacePolygon([bl,tl,ctl,cbl], self, "left")
        self.center = ToothFacePolygon([ctl,ctr,cbr,cbl], self, "center")

        for f in [self.top, self.right, self.bottom, self.left, self.center]:
            self.scene.addItem(f)

    def create_overlays(self, x, y, size):
        pen_b = QPen(Qt.blue, 3)

        # Línea en X para "PD Ausente"
        line1 = self.scene.addLine(x, y, x+size, y+size, pen_b)
        line2 = self.scene.addLine(x+size, y, x, y+size, pen_b)
        line1.setVisible(False)
        line2.setVisible(False)
        self.cross_lines = [line1, line2]

        # Círculo de corona
        r = size*1.1
        cx = x+size/2 - r/2
        cy = y+size/2 - r/2
        self.corona_circle = self.scene.addEllipse(cx, cy, r, r, pen_b, QBrush(Qt.transparent))
        self.corona_circle.setVisible(False)

        # Texto de Implante
        self.implante_text = QGraphicsTextItem("IMP")
        self.implante_text.setFont(QFont("Arial", 10, QFont.Bold))
        self.implante_text.setDefaultTextColor(Qt.blue)
        self.implante_text.setPos(x+5, y+5)
        self.implante_text.setVisible(False)
        self.implante_text.setZValue(1)

        # Círculo Sellador
        srad = size*0.2
        sx = x+size/2 - srad/2
        sy = y+size/2 - srad/2
        pen_y = QPen(Qt.yellow, 2)
        brush_y = QBrush(Qt.yellow)
        self.sellador_circle = self.scene.addEllipse(sx, sy, srad, srad, pen_y, brush_y)
        self.sellador_circle.setVisible(False)

        # Círculo Ausente Fisiológico
        dotted = QPen(Qt.blue, 2, Qt.DotLine)
        afr = size
        ax = x+size/2 - afr/2
        ay = y+size/2 - afr/2
        self.ausente_fisio_circle = self.scene.addEllipse(ax, ay, afr, afr, dotted, QBrush(Qt.transparent))
        self.ausente_fisio_circle.setVisible(False)

        # Texto de Prótesis
        self.protesis_text = QGraphicsTextItem("")
        self.protesis_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.protesis_text.setDefaultTextColor(Qt.red)
        self.protesis_text.setVisible(False)
        self.protesis_text.setZValue(1)
        self.scene.addItem(self.protesis_text)

        # Círculo de Supernumerario
        sup_r = size*0.4
        sx2 = x+size/2 - sup_r/2
        sy2 = y+size/2 - sup_r/2
        pen_b2 = QPen(Qt.blue, 2)
        self.supernumerario_circle = self.scene.addEllipse(sx2, sy2, sup_r, sup_r, pen_b2, QBrush(Qt.transparent))
        self.supernumerario_circle.setVisible(False)

        # Texto 'S' de Supernumerario
        s_text = QGraphicsTextItem("S")
        s_text.setFont(QFont("Arial", 12, QFont.Bold))
        s_text.setDefaultTextColor(Qt.blue)
        s_text.setPos(sx2+sup_r/2 - s_text.boundingRect().width()/2,
                      sy2+sup_r/2 - s_text.boundingRect().height()/2)
        s_text.setVisible(False)
        s_text.setZValue(1)
        self.supernumerario_text = s_text
        self.scene.addItem(s_text)

        # Agregar a la escena
        for ov in [line1, line2, self.corona_circle, self.implante_text,
                   self.sellador_circle, self.ausente_fisio_circle,
                   self.supernumerario_circle, s_text]:
            self.scene.addItem(ov)

    # -----------------------
    # Métodos de "estado"
    # -----------------------
    def apply_state(self, state_name):
        """
        Para estados en los que no importan las caras,
        simplemente aplicamos de forma global al diente.
        """
        if state_name == "Ninguno":
            self.reset_tooth()

        elif state_name == "Agenesia":
            self.set_agenesia(True)

        elif state_name == "PD Ausente":
            self.set_pd_ausente(True)

        elif state_name == "Corona":
            self.set_corona(True)

        elif state_name == "Implante":
            self.set_implante(True)

        elif state_name == "Selladores":
            self.set_sellador(True)

        elif state_name == "Ausente Fisiológico":
            self.set_ausente_fisio(True)

        elif state_name in [
            "Prótesis Removible SUPERIOR",
            "Prótesis Removible INFERIOR",
            "Prótesis Completa SUPERIOR",
            "Prótesis Completa INFERIOR",
        ]:
            self.set_protesis_text(self._short_protesis_label(state_name))

        elif state_name == "Supernumerario":
            self.set_supernumerario(True)

        elif state_name == "Obturacion":
            # Obturación sin especificar caras => se pinta todo
            for f in [self.top, self.right, self.bottom, self.left, self.center]:
                f.setBrush(QBrush(Qt.blue))

        elif state_name == "Puente":
            # Activar "has_bridge"
            self.has_bridge = True
            self.odontogram_view.update_bridges()

    def _short_protesis_label(self, full_label):
        # Simplifica las etiquetas de prótesis
        if full_label == "Prótesis Removible SUPERIOR":
            return "PRS"
        if full_label == "Prótesis Removible INFERIOR":
            return "PRI"
        if full_label == "Prótesis Completa SUPERIOR":
            return "PCS"
        if full_label == "Prótesis Completa INFERIOR":
            return "PCI"
        return ""

    def apply_obturation_faces(self, faces_str):
        face_map = {
            "M": self.left, "D": self.right,
            "V": self.top,  "B": self.top,
            "L": self.bottom, "P": self.bottom,
            "I": self.center, "O": self.center,
            "G": None  # "Gingival", si quieres manejarlo aparte
        }
        for c in faces_str.upper():
            poly = face_map.get(c)
            if poly:
                poly.setBrush(QBrush(Qt.blue))

    def set_agenesia(self, enabled):
        col = Qt.darkGray if enabled else Qt.white
        for f in [self.top, self.right, self.bottom, self.left, self.center]:
            f.setBrush(QBrush(col))

    def set_pd_ausente(self, enabled):
        for line in self.cross_lines:
            line.setVisible(enabled)

    def set_corona(self, enabled):
        if self.corona_circle:
            self.corona_circle.setVisible(enabled)

    def set_implante(self, enabled):
        if self.implante_text:
            self.implante_text.setVisible(enabled)

    def set_sellador(self, enabled):
        if self.sellador_circle:
            self.sellador_circle.setVisible(enabled)

    def set_ausente_fisio(self, enabled):
        if self.ausente_fisio_circle:
            self.ausente_fisio_circle.setVisible(enabled)

    def set_protesis_text(self, label):
        self.protesis_text.setPlainText(label)
        # Lo ubico sobre la parte superior del diente
        top_rect = self.top.mapToScene(self.top.boundingRect()).boundingRect()
        tw = self.protesis_text.boundingRect().width()
        th = self.protesis_text.boundingRect().height()
        cx = top_rect.center().x() - tw/2
        cy = top_rect.top() - 5 - th
        self.protesis_text.setPos(cx, cy)
        self.protesis_text.setVisible(True)

    def set_supernumerario(self, enabled):
        if enabled:
            self.supernumerario_circle.setVisible(True)
            self.supernumerario_text.setVisible(True)

    def reset_tooth(self):
        # Limpia TODO en la pieza
        for f in [self.top, self.right, self.bottom, self.left, self.center]:
            f.setBrush(QBrush(Qt.white))
            f.setPen(QPen(Qt.black, 2))
            f.is_selected = False
        for line in self.cross_lines:
            line.setVisible(False)
        if self.corona_circle:
            self.corona_circle.setVisible(False)
        if self.implante_text:
            self.implante_text.setVisible(False)
        if self.sellador_circle:
            self.sellador_circle.setVisible(False)
        if self.ausente_fisio_circle:
            self.ausente_fisio_circle.setVisible(False)
        if self.protesis_text:
            self.protesis_text.setVisible(False)
        if self.supernumerario_circle:
            self.supernumerario_circle.setVisible(False)
        if self.supernumerario_text:
            self.supernumerario_text.setVisible(False)
        self.has_bridge = False  # Reiniciar flag de puente


# -----------------------------
# Clase OdontogramView
# -----------------------------
class OdontogramView(QGraphicsView):
    """
    Vista principal de la escena de dientes.
    Contiene la lógica para dibujar los puentes con líneas horizontales.
    """
    def __init__(self, locked=False):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.current_state_name = "Ninguno"
        # Para bloquear la modificación manual
        self.locked = locked

        # Lista para guardar las líneas de puentes
        self.bridge_lines = []
        self.dientes = []
        self.create_teeth()

    def create_teeth(self):
        size = 40
        margin = 10
        row1 = ["18","17","16","15","14","13","12","11",
                "21","22","23","24","25","26","27","28"]
        row2 = ["55","54","53","52","51","61","62","63","64","65"]
        row3 = ["85","84","83","82","81","71","72","73","74","75"]
        row4 = ["48","47","46","45","44","43","42","41",
                "31","32","33","34","35","36","37","38"]
        rows = [row1, row2, row3, row4]
        y_positions = [50, 140, 250, 340]

        for idx, row in enumerate(rows):
            y = y_positions[idx]
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
                txt.setPos(x + size/2 - txt.boundingRect().width()/2, y+size+3)
                self.scene.addItem(txt)
            self.dientes.append(tooth_row)

    def set_current_state(self, state_name):
        self.current_state_name = state_name

    def update_bridges(self):
        """
        Dibuja líneas horizontales gruesas en aquellos dientes que tengan has_bridge=True.
        Si hay dientes adyacentes con has_bridge=True, se unifica la línea.
        """
        # 1) Borrar las líneas de puentes previas
        for line_item in self.bridge_lines:
            self.scene.removeItem(line_item)
        self.bridge_lines.clear()

        # 2) Recorremos cada fila. Buscamos secuencias contiguas de dientes con puente
        for row in self.dientes:
            bridging_teeth = [t for t in row if t.has_bridge]
            if not bridging_teeth:
                continue

            # Ordenarlos por número (en la fila ya suelen venir ordenados, pero por seguridad)
            bridging_teeth.sort(key=lambda x: int(x.tooth_num))

            # Hallar secuencias consecutivas
            start_idx = 0
            for i in range(len(bridging_teeth)):
                # Verificamos si el siguiente no es "consecutivo" o ya estamos en el último
                if (i == len(bridging_teeth)-1 or
                   int(bridging_teeth[i+1].tooth_num) != int(bridging_teeth[i].tooth_num) + 1):
                    left_t = bridging_teeth[start_idx]
                    right_t = bridging_teeth[i]

                    # Coordenadas de la línea horizontal
                    left_rect = left_t.top.mapToScene(left_t.top.boundingRect()).boundingRect()
                    right_rect = right_t.top.mapToScene(right_t.top.boundingRect()).boundingRect()

                    # Trazamos la línea un poco por encima del centro vertical del diente
                    y_line = left_rect.center().y() + (left_t.size / 2)
                    y_line -= 10  # ajuste vertical para que se vea un poco arriba

                    x_left = left_rect.left()
                    x_right = right_rect.right()

                    # Crear la línea
                    pen_bridge = QPen(Qt.blue, 4)
                    puente_line = self.scene.addLine(x_left, y_line, x_right, y_line, pen_bridge)
                    puente_line.setZValue(0)  # detrás de otros overlays

                    self.bridge_lines.append(puente_line)
                    start_idx = i + 1

    def apply_batch_states(self, states_list):
        """
        Recibe una lista de (estado_int, diente_int, caras_str).
        Asigna los estados correspondientes y luego dibuja puentes.
        """
        # Agrupamos por diente => diente: [(estadoName, carasStr), ...]
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

            # Guardamos para aplicarlo luego
            tooth_states[d_int].append((estado_name, faces))

        # Primero, reseteamos todo
        for row in self.dientes:
            for t in row:
                t.reset_tooth()

        # Luego aplicamos las listas de estados
        for d_int, est_list in tooth_states.items():
            found = self.find_tooth(str(d_int))
            for (ename, faces) in est_list:
                if ename == "Obturacion" and faces:
                    # Obturación con caras
                    found.apply_obturation_faces(faces)
                else:
                    # Cualquier otro estado
                    found.apply_state(ename)

        # Al final, actualizamos las líneas de puentes
        self.update_bridges()

    def find_tooth(self, d_str):
        for row in self.dientes:
            for t in row:
                if t.tooth_num == d_str:
                    return t
        return None


# --------------------------------------------------------------------
# Ventana principal
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.setWindowTitle("Odontograma")  # Título de la ventana

        # Determinamos si hay parámetros 'dientes'
        ds = self.args.dientes.strip()
        self.locked_mode = bool(ds)  # Si hay algo en 'dientes', modo bloqueado

        # Configuramos la vista con la variable locked
        self.odontogram_view = OdontogramView(locked=self.locked_mode)

        # -------------
        # Widgets de parámetros
        # -------------
        self.titleEdit = QLineEdit("Odontograma")
        self.titleEdit.setReadOnly(True)  # Solo muestra "Odontograma"

        self.credencialEdit = QLineEdit()
        self.credencialEdit.setText(self.args.credencial or "")
        self.prestadorEdit = QLineEdit()
        self.prestadorEdit.setText(self.args.prestador or "")
        self.fechaEdit = QLineEdit()
        self.fechaEdit.setText(self.args.fecha or "")
        self.titularEdit = QLineEdit()
        self.titularEdit.setText(self.args.titular or "")

        self.observacionesEdit = QLineEdit()
        self.observacionesEdit.setMaxLength(100)
        self.observacionesEdit.setText(self.args.observaciones or "")

        # Si estamos bloqueados, los ponemos en modo read-only
        if self.locked_mode:
            self.credencialEdit.setReadOnly(True)
            self.prestadorEdit.setReadOnly(True)
            self.fechaEdit.setReadOnly(True)
            self.titularEdit.setReadOnly(True)
            self.observacionesEdit.setReadOnly(True)

        # -------------
        # Combo de estados (abajo del odontograma)
        # -------------
        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)
        # Si estamos en modo bloqueado, deshabilitamos el combo
        if self.locked_mode:
            self.state_selector.setEnabled(False)

        # -------------
        # Layout principal
        # -------------
        # Form con los datos
        formLayout = QFormLayout()
        formLayout.addRow("Título:", self.titleEdit)
        formLayout.addRow("Credencial:", self.credencialEdit)
        formLayout.addRow("Prestador:", self.prestadorEdit)
        formLayout.addRow("Fecha:", self.fechaEdit)
        formLayout.addRow("Titular:", self.titularEdit)
        formLayout.addRow("Observaciones:", self.observacionesEdit)

        # Layout vertical para: form + odontograma + combo
        vLayout = QVBoxLayout()
        vLayout.addLayout(formLayout)
        vLayout.addWidget(self.odontogram_view)
        vLayout.addWidget(QLabel("Estado actual:"))
        vLayout.addWidget(self.state_selector)

        container = QWidget()
        container.setLayout(vLayout)
        self.setCentralWidget(container)

        # Aplicamos estados si hay 'dientes'
        self.apply_dental_args()

    def on_state_changed(self, new_state):
        self.odontogram_view.set_current_state(new_state)

    def apply_dental_args(self):
        ds = self.args.dientes
        if ds:
            # Hay parámetros => aplica y bloquea
            parsed = parse_dental_states(ds)
            for (s_i, d_i, car) in parsed:
                print(f"PARSE => estado={s_i}, diente={d_i}, caras='{car}'")
            self.odontogram_view.apply_batch_states(parsed)
        else:
            print("Modo manual: selecciona estados y haz clic en las caras para modificar.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titular", default="")
    parser.add_argument("--credencial", default="")
    parser.add_argument("--prestador", default="")
    parser.add_argument("--fecha", default="")
    parser.add_argument("--observaciones", default="", help="Hasta 100 caracteres")
    parser.add_argument("--dientes", default="", help="Lista de items p.ej. '652,1052'")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    # Aplicamos estilo
    apply_style(app)

    w = MainWindow(args)
    w.resize(1200, 600)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


#parámetros de call
"""

python dental_v03.py --credencial "123456" --titular "Carlos Pérez" --prestador "Dr. María López" --fecha "2025-02-10" --observaciones "Revisión general y tratamientos aplicados." --dientes "111,212V,313D,414MD,515O,616VI,717V,818,125,225,326,437,548,651,661,662,752,863,974,1085,1147,1245,1342,1341,135OLP"
>> 

"""
