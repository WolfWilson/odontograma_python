#!/usr/bin/env python
# coding: utf-8

import sys
import argparse
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QMainWindow,
    QGraphicsPolygonItem, QGraphicsTextItem, QComboBox, QVBoxLayout, QWidget
)
from PyQt5.QtGui import QBrush, QPen, QFont, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRectF

# --------------------------------------------------------------------
# Diccionario de ESTADOS (1..13)
# --------------------------------------------------------------------
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

# Para mapear estado_int (1..13) a nombres
ESTADOS_POR_NUM = {v: k for k,v in ESTADOS.items()}

# --------------------------------------------------------------------
# NUEVO PARSEADOR que soporta estados de 1 O 2 dígitos + diente 2 dígitos
# --------------------------------------------------------------------
def parse_dental_states(dental_str):
    """
    Convierte una cadena tipo: "325,126VI,327,1053" 
    en una lista de tuplas (estado_int, diente_int, caras_str).
    
    Soporta estado de 1 o 2 dígitos (1..13) 
    y diente de 2 dígitos (11..85). 
    Caras es el resto (opcional).
    """
    if not dental_str:
        return []

    items = dental_str.split(",")
    result = []

    for item in items:
        item = item.strip()
        if not item:
            continue

        parsed = parse_item_with_backtracking(item)
        if parsed:
            result.append(parsed)  # (estado, diente, caras)
        else:
            print(f"WARNING: No se pudo interpretar: {item}")
    
    return result

def parse_item_with_backtracking(item_str):
    """
    Intenta:
      1) leer los primeros 2 dígitos como estado (si 1..13),
         luego 2 dígitos como diente (11..85),
         resto -> caras
         SI falla, reintenta:
      2) leer el primer dígito como estado (1..9),
         luego 2 dígitos como diente (11..85),
         resto -> caras
      Devuelve (estado_int, diente_int, caras_str) o None si falla.
    """
    # Opción A: 2 dígitos de estado, 2 de diente
    if len(item_str) >= 4:
        st_candidate = item_str[:2]  # p.ej. "10"
        try:
            st_int = int(st_candidate)
            if 1 <= st_int <= 13:  # estado válido
                d_candidate = item_str[2:4]  # p.ej. "53"
                d_int = int(d_candidate)
                if 11 <= d_int <= 85:
                    # Resto => caras
                    faces = item_str[4:].upper()
                    return (st_int, d_int, faces)
        except:
            pass  # no entró, reintentamos con 1 dígito

    # Opción B: 1 dígito de estado, 2 de diente
    if len(item_str) >= 3:
        st_candidate = item_str[0]
        try:
            st_int = int(st_candidate)
            if 1 <= st_int <= 13:
                d_candidate = item_str[1:3]
                d_int = int(d_candidate)
                if 11 <= d_int <= 85:
                    faces = item_str[3:].upper()
                    return (st_int, d_int, faces)
        except:
            pass

    # Si ninguno funcionó:
    return None

# --------------------------------------------------------------------
# Clases PyQt del Odontograma
# --------------------------------------------------------------------
class ToothFacePolygon(QGraphicsPolygonItem):
    def __init__(self, points, parent_tooth, face_name):
        super().__init__()
        poly = QPolygonF()
        for (px, py) in points:
            poly.append(QPointF(px, py))

        self.setPolygon(poly)
        self.tooth = parent_tooth
        self.face_name = face_name
        self.default_color = Qt.white
        self.setBrush(QBrush(self.default_color))
        self.setPen(QPen(Qt.black, 2))
        self.is_selected = False

    def mousePressEvent(self, event):
        current_state = self.tooth.odontogram_view.current_state_name

        if current_state == "Obturacion":
            if not self.is_selected:
                self.setBrush(QBrush(Qt.blue))
                self.is_selected = True
            else:
                self.setBrush(QBrush(self.default_color))
                self.is_selected = False

        elif current_state == "Puente":
            self.tooth.odontogram_view.handle_puente_click(self.tooth)

        else:
            self.tooth.apply_state(current_state)

        super().mousePressEvent(event)

class ToothItem:
    def __init__(self, x, y, size, scene, odontogram_view, tooth_num):
        self.scene = scene
        self.odontogram_view = odontogram_view
        self.size = size
        self.tooth_num = tooth_num

        # Polígonos "top,right,bottom,left,center"
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

        self.create_faces(x, y, size)
        self.create_overlays(x, y, size)

    def create_faces(self, x, y, size):
        fs = size/3
        tl = (x,     y)
        tr = (x+size,y)
        br = (x+size,y+size)
        bl = (x,     y+size)

        ctl = (x+fs,     y+fs)
        ctr = (x+size-fs,y+fs)
        cbr = (x+size-fs,y+size-fs)
        cbl = (x+fs,     y+size-fs)

        self.top = ToothFacePolygon([tl,tr,ctr,ctl], self, "top")
        self.scene.addItem(self.top)
        self.right = ToothFacePolygon([tr,br,cbr,ctr], self, "right")
        self.scene.addItem(self.right)
        self.bottom = ToothFacePolygon([br,bl,cbl,cbr], self, "bottom")
        self.scene.addItem(self.bottom)
        self.left = ToothFacePolygon([bl,tl,ctl,cbl], self, "left")
        self.scene.addItem(self.left)
        self.center = ToothFacePolygon([ctl,ctr,cbr,cbl], self, "center")
        self.scene.addItem(self.center)

    def create_overlays(self, x, y, size):
        pen_b = QPen(Qt.blue, 3)

        # PD Ausente - cruz
        line1 = self.scene.addLine(x,y, x+size,y+size, pen_b)
        line2 = self.scene.addLine(x+size,y, x,y+size, pen_b)
        line1.setVisible(False)
        line2.setVisible(False)
        self.cross_lines = [line1,line2]

        # Corona
        r = size*1.1
        cx = x+size/2 - r/2
        cy = y+size/2 - r/2
        self.corona_circle = self.scene.addEllipse(cx, cy, r, r, pen_b, QBrush(Qt.transparent))
        self.corona_circle.setVisible(False)

        # Implante
        self.implante_text = QGraphicsTextItem("IMP")
        self.implante_text.setFont(QFont("Arial", 10, QFont.Bold))
        self.implante_text.setDefaultTextColor(Qt.blue)
        self.implante_text.setPos(x+5, y+5)
        self.implante_text.setVisible(False)

        # Sellador
        srad = size*0.2
        sx = x+size/2 - srad/2
        sy = y+size/2 - srad/2
        pen_y = QPen(Qt.yellow, 2)
        brush_y = QBrush(Qt.yellow)
        self.sellador_circle = self.scene.addEllipse(sx, sy, srad, srad, pen_y, brush_y)
        self.sellador_circle.setVisible(False)

        # Ausente fisiológico
        dotted = QPen(Qt.blue, 2, Qt.DotLine)
        afr = size
        ax = x+size/2 - afr/2
        ay = y+size/2 - afr/2
        self.ausente_fisio_circle = self.scene.addEllipse(ax, ay, afr, afr, dotted, QBrush(Qt.transparent))
        self.ausente_fisio_circle.setVisible(False)

        # Prótesis
        self.protesis_text = QGraphicsTextItem("")
        self.protesis_text.setFont(QFont("Arial", 12, QFont.Bold))
        self.protesis_text.setDefaultTextColor(Qt.red)
        self.protesis_text.setVisible(False)
        self.scene.addItem(self.protesis_text)

        # Supernumerario
        s_rad = size*0.4
        sx2 = x+size/2 - s_rad/2
        sy2 = y+size/2 - s_rad/2
        pen_b2 = QPen(Qt.blue,2)
        self.supernumerario_circle = self.scene.addEllipse(sx2, sy2, s_rad, s_rad, pen_b2, QBrush(Qt.transparent))
        self.supernumerario_circle.setVisible(False)

        s_item = QGraphicsTextItem("S")
        s_item.setFont(QFont("Arial", 12, QFont.Bold))
        s_item.setDefaultTextColor(Qt.blue)
        s_item.setPos(sx2+s_rad/2 - s_item.boundingRect().width()/2,
                      sy2+s_rad/2 - s_item.boundingRect().height()/2)
        s_item.setVisible(False)
        self.supernumerario_text = s_item

        self.scene.addItem(line1)
        self.scene.addItem(line2)
        self.scene.addItem(self.corona_circle)
        self.scene.addItem(self.implante_text)
        self.scene.addItem(self.sellador_circle)
        self.scene.addItem(self.ausente_fisio_circle)
        self.scene.addItem(self.supernumerario_circle)
        self.scene.addItem(s_item)

    # --- Aplicación de estados --
    def apply_state(self, state_name):
        if state_name == "Agenesia":
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
        elif state_name == "Ninguno":
            self.reset_tooth()
        elif state_name == "Prótesis Removible SUPERIOR":
            self.set_protesis_text("PRS")
        elif state_name == "Prótesis Removible INFERIOR":
            self.set_protesis_text("PRI")
        elif state_name == "Prótesis Completa SUPERIOR":
            self.set_protesis_text("PCS")
        elif state_name == "Prótesis Completa INFERIOR":
            self.set_protesis_text("PCI")
        elif state_name == "Supernumerario":
            self.set_supernumerario(True)

    # -- Obturacion con caras específicas (ejemplo)
    def apply_obturation_faces(self, faces_str):
        """
        Colorea solo las caras indicadas en 'faces_str', p.ej. "VI".
        Ejemplo de mapeo minimal a top/right/left/bottom/center.
        """
        # Resetea primero
        self.reset_tooth()

        # Diccionario de ejemplo, ajusta según la geometría real
        face_map = {
            "M": self.left,
            "D": self.right,
            "V": self.top,   # V(bucal/labial) simplificado
            "B": self.top,   # Bucal
            "L": self.bottom,# Lingual
            "P": self.bottom,# Palatino
            "I": self.center,# Incisal
            "O": self.center,# Oclusal
            "G": None        # Gingival => si quieres dibujar un overlay
        }

        for c in faces_str:
            c = c.upper()
            poly_item = face_map.get(c)
            if poly_item:
                poly_item.setBrush(QBrush(Qt.blue))

    def set_agenesia(self, enabled):
        col = Qt.darkGray if enabled else Qt.white
        for p in [self.top, self.right, self.bottom, self.left, self.center]:
            p.setBrush(QBrush(col))

    def set_pd_ausente(self, enabled):
        for line in self.cross_lines:
            line.setVisible(enabled)

    def set_corona(self, enabled):
        self.corona_circle.setVisible(enabled)

    def set_implante(self, enabled):
        self.implante_text.setVisible(enabled)

    def set_sellador(self, enabled):
        self.sellador_circle.setVisible(enabled)

    def set_ausente_fisio(self, enabled):
        self.ausente_fisio_circle.setVisible(enabled)

    def set_protesis_text(self, label):
        self.reset_tooth()
        self.protesis_text.setPlainText(label)
        # Posicionarlo encima de la cara "top"
        top_rect = self.top.mapToScene(self.top.boundingRect()).boundingRect()
        tw = self.protesis_text.boundingRect().width()
        th = self.protesis_text.boundingRect().height()
        cx = top_rect.center().x() - (tw/2)
        cy = top_rect.top() - 5 - th
        self.protesis_text.setPos(cx, cy)
        self.protesis_text.setVisible(True)

    def set_supernumerario(self, enabled):
        self.reset_tooth()
        if enabled:
            self.supernumerario_circle.setVisible(True)
            self.supernumerario_text.setVisible(True)

    def reset_tooth(self):
        for p in [self.top, self.right, self.bottom, self.left, self.center]:
            p.setBrush(QBrush(Qt.white))
            p.is_selected = False
        for line in self.cross_lines:
            line.setVisible(False)
        self.corona_circle.setVisible(False)
        self.implante_text.setVisible(False)
        self.sellador_circle.setVisible(False)
        self.ausente_fisio_circle.setVisible(False)
        self.protesis_text.setVisible(False)
        if self.supernumerario_circle:
            self.supernumerario_circle.setVisible(False)
        if self.supernumerario_text:
            self.supernumerario_text.setVisible(False)

class OdontogramView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.current_state_name = "Ninguno"
        self.puente_pilar_inicial = None

        self.dientes = []  # filas de ToothItem
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

        rows = [row1,row2,row3,row4]
        y_positions = [50,140,250,340]

        for idx, row in enumerate(rows):
            y = y_positions[idx]
            x_start = 50
            tooth_row = []
            for i, tnum in enumerate(row):
                x = x_start + i*(size+margin)
                tooth_item = ToothItem(x, y, size, self.scene, self, tnum)
                tooth_row.append(tooth_item)

                # Texto del diente
                text = QGraphicsTextItem(tnum)
                text.setFont(QFont("Arial", 10))
                text.setDefaultTextColor(Qt.black)
                text.setPos(x + size/2 - text.boundingRect().width()/2, y+size+3)
                self.scene.addItem(text)

            self.dientes.append(tooth_row)

    def set_current_state(self, state_name):
        self.current_state_name = state_name
        if state_name != "Puente":
            self.puente_pilar_inicial = None

    def handle_puente_click(self, clicked_tooth):
        if self.puente_pilar_inicial is None:
            self.puente_pilar_inicial = clicked_tooth
        else:
            p1 = self.puente_pilar_inicial
            p2 = clicked_tooth
            # Simplificado: si primer dígito igual => "misma fila"
            if p1.tooth_num[0] == p2.tooth_num[0]:
                self.draw_bridge(p1, p2)
            else:
                print("No se puede dibujar puente entre piezas de filas distintas.")
            self.puente_pilar_inicial = None

    def draw_bridge(self, p1, p2):
        # Ejemplo omitido. Podrías dibujar la línea horizontal y verticales en los pilares.
        pass

    # -- NUEVO: aplicar una lista de (estado_int, diente_int, caras)
    def apply_batch_states(self, states_list):
        """
        states_list: [(3,25,""), (1,26,"VI"), (3,27,""), (10,53,"")]
        - estado_int => se mapea a ESTADOS_POR_NUM
        - diente_int => str(diente_int) p.ej. "25"
        - caras => "VI"
        """
        for (estado_int, d_int, faces_str) in states_list:
            # Convertir a nombre
            estado_name = ESTADOS_POR_NUM.get(estado_int, None)
            if not estado_name:
                print(f"Estado {estado_int} no definido.")
                continue

            # Buscar la pieza
            tooth_str = str(d_int)
            found = self.find_tooth(tooth_str)
            if not found:
                print(f"Tooth {d_int} no encontrado en la vista.")
                continue

            # Si es Obturacion y hay caras => apply_obturation_faces
            if estado_name == "Obturacion" and faces_str:
                found.apply_obturation_faces(faces_str)
            else:
                found.reset_tooth()
                found.apply_state(estado_name)

    def find_tooth(self, tooth_str):
        for row in self.dientes:
            for tooth_item in row:
                if tooth_item.tooth_num == tooth_str:
                    return tooth_item
        return None

# --------------------------------------------------------------------
# Ventana principal + argparse
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.setWindowTitle("Odontograma - Soporte estados 2 dígitos")
        self.setGeometry(100,100,1400,600)

        self.args = args
        self.odontogram_view = OdontogramView()

        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.odontogram_view)
        layout.addWidget(self.state_selector)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Aplicar parámetros si hay
        self.apply_dental_args()

    def on_state_changed(self, new_state):
        self.odontogram_view.set_current_state(new_state)

    def apply_dental_args(self):
        # Parsear la cadena "325,126VI,327,1053" etc.
        d_str = self.args.dientes
        states_list = parse_dental_states(d_str)
        self.odontogram_view.apply_batch_states(states_list)

def main():
    parser = argparse.ArgumentParser(description="Odontograma con parseo de estado 1 o 2 dígitos.")
    parser.add_argument("--credencial", type=str, required=True, help="Credencial")
    parser.add_argument("--titular", type=str, required=True, help="Titular")
    parser.add_argument("--prestador", type=str, required=True, help="Prestador")
    parser.add_argument("--fecha", type=str, required=True, help="Fecha")
    parser.add_argument("--observaciones", type=str, default="", help="Observaciones")
    parser.add_argument("--dientes", type=str, default="", help="String de estados-dientes-caras")

    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow(args)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


#python dental_v02.py --credencial "354495" --titular "Antonella Bouvier" --prestador "Dr. Juan Pérez" --fecha "2025-01-30" --observaciones " " --dientes "325,126VI,327,428V,585VI,584,652,761V,1052,154MDVOLIOG"
