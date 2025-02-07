import sys
import argparse
from collections import defaultdict

# Importamos PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QWidget,
    QGraphicsPolygonItem, QGraphicsTextItem, QComboBox, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QLineEdit, QLabel
)
from PyQt5.QtGui import (
    QBrush, QPen, QFont, QPolygonF, QPixmap
)
from PyQt5.QtCore import Qt, QPointF, QRectF

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
# Funciones para parsear estados dentales
# -----------------------------
def parse_dental_states(dental_str):
    """
    Interpreta una cadena como "652,1052" => 
    (6, 52, ""), (10, 52, "")
    o "651MOD" => (6, 51, "MOD")
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
# Clase para cada cara de la pieza dental
# -----------------------------
class ToothFacePolygon(QGraphicsPolygonItem):
    """
    Representa una cara (top, bottom, left, right, center) del diente.
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
        # Bloquear si la vista está en modo "locked"
        if self.tooth.odontogram_view.locked:
            return

        current_state = self.tooth.odontogram_view.current_state_name
        if current_state == "Obturacion":
            # Toggle de color 
            if not self.is_selected:
                self.setBrush(QBrush(Qt.blue))
                self.is_selected = True
            else:
                self.setBrush(QBrush(Qt.white))
                self.is_selected = False

        elif current_state == "Puente":
            # Toggle en la pieza entera
            self.tooth.has_bridge = not self.tooth.has_bridge
            self.tooth.odontogram_view.update_bridges()

        else:
            # Otros estados
            self.tooth.apply_state(current_state)

        super().mousePressEvent(event)


# -----------------------------
# Clase ToothItem (pieza completa)
# -----------------------------
class ToothItem:
    """
    Un diente con 5 polígonos + sus "overlays" (líneas, círculos, textos...).
    """
    def __init__(self, x, y, size, scene, odontogram_view, tooth_num):
        self.scene = scene
        self.odontogram_view = odontogram_view
        self.size = size
        self.tooth_num = tooth_num  # string, ej "11", "54"

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

        # Flag para indicar si tiene puente
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

        # Línea en X para PD Ausente
        line1 = self.scene.addLine(x, y, x+size, y+size, pen_b)
        line2 = self.scene.addLine(x+size, y, x, y+size, pen_b)
        line1.setVisible(False)
        line2.setVisible(False)
        self.cross_lines = [line1, line2]

        # Corona
        r = size*1.1
        cx = x+size/2 - r/2
        cy = y+size/2 - r/2
        self.corona_circle = self.scene.addEllipse(cx, cy, r, r, pen_b, QBrush(Qt.transparent))
        self.corona_circle.setVisible(False)

        # Implante texto
        self.implante_text = QGraphicsTextItem("IMP")
        self.implante_text.setFont(QFont("Arial", 10, QFont.Bold))
        self.implante_text.setDefaultTextColor(Qt.blue)
        self.implante_text.setPos(x+5, y+5)
        self.implante_text.setVisible(False)
        self.implante_text.setZValue(1)

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
        self.protesis_text.setZValue(1)
        self.scene.addItem(self.protesis_text)

        # Supernumerario
        sup_r = size*0.4
        sx2 = x+size/2 - sup_r/2
        sy2 = y+size/2 - sup_r/2
        pen_b2 = QPen(Qt.blue, 2)
        self.supernumerario_circle = self.scene.addEllipse(sx2, sy2, sup_r, sup_r, pen_b2, QBrush(Qt.transparent))
        self.supernumerario_circle.setVisible(False)

        # Texto S
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
    # Métodos de estado
    # -----------------------
    def apply_state(self, state_name):
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
            # Pintar todo de azul
            for f in [self.top, self.right, self.bottom, self.left, self.center]:
                f.setBrush(QBrush(Qt.blue))

        elif state_name == "Puente":
            self.has_bridge = True
            self.odontogram_view.update_bridges()

    def _short_protesis_label(self, full_label):
        if full_label == "Prótesis Removible SUPERIOR": return "PRS"
        if full_label == "Prótesis Removible INFERIOR": return "PRI"
        if full_label == "Prótesis Completa SUPERIOR":  return "PCS"
        if full_label == "Prótesis Completa INFERIOR":  return "PCI"
        return ""

    def apply_obturation_faces(self, faces_str):
        face_map = {
            "M": self.left, "D": self.right,
            "V": self.top,  "B": self.top,
            "L": self.bottom, "P": self.bottom,
            "I": self.center, "O": self.center,
            "G": None
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

        self.has_bridge = False


# -----------------------------
# Clase OdontogramView
# -----------------------------
class OdontogramView(QGraphicsView):
    """
    Contiene la escena con los dientes y dibuja los puentes cuando procede.
    """
    def __init__(self, locked=False):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.current_state_name = "Ninguno"

        # Indica si se permite la interacción o está bloqueado
        self.locked = locked

        # Guardaremos referencias a las líneas de puente
        self.bridge_lines = []
        self.dientes = []
        self.create_teeth()

    def create_teeth(self):
        size = 40  # Tamaño de cada diente
        margin = 10  # Espaciado entre dientes

        # Definimos las filas de dientes
        row1 = ["18","17","16","15","14","13","12","11","21","22","23","24","25","26","27","28"]
        row2 = ["55","54","53","52","51","61","62","63","64","65"]  # Infantil sup
        row3 = ["85","84","83","82","81","71","72","73","74","75"]  # Infantil inf
        row4 = ["48","47","46","45","44","43","42","41","31","32","33","34","35","36","37","38"]
        
        rows = [row1, row2, row3, row4]
        y_positions = [50, 140, 250, 340]  # Posiciones verticales de cada fila
        
        # Ancho total de la fila 1 (para centrar las infantiles)
        total_width_row1 = len(row1) * (size + margin) - margin  
        total_width_row2 = len(row2) * (size + margin) - margin  
        total_width_row3 = len(row3) * (size + margin) - margin  

        offset_x_row2 = (total_width_row1 - total_width_row2) // 2
        offset_x_row3 = (total_width_row1 - total_width_row3) // 2

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
                x = x_start + i * (size + margin)
                t = ToothItem(x, y, size, self.scene, self, tnum)
                tooth_row.append(t)

                # Texto debajo del diente
                txt = QGraphicsTextItem(tnum)
                txt.setFont(QFont("Arial", 10))
                txt.setDefaultTextColor(Qt.black)
                txt.setPos(x + size / 2 - txt.boundingRect().width() / 2, y + size + 3)
                self.scene.addItem(txt)

            self.dientes.append(tooth_row)

    def set_current_state(self, state_name):
        self.current_state_name = state_name

    def update_bridges(self):
        """
        Dibujamos una línea horizontal por cada diente con has_bridge=True.
        Sin agrupar ni comprobar consecutividad, lo que da la ilusión 
        de línea continua cuando los dientes están juntos.
        """
        # 1) Eliminar líneas anteriores
        for line_item in self.bridge_lines:
            self.scene.removeItem(line_item)
        self.bridge_lines.clear()

        # 2) Para cada fila, buscamos los dientes con has_bridge=True
        for row in self.dientes:
            bridging_teeth = [t for t in row if t.has_bridge]
            if not bridging_teeth:
                continue

            # Dibujamos una línea por cada diente con puente
            for tooth in bridging_teeth:
                rect = tooth.top.mapToScene(tooth.top.boundingRect()).boundingRect()
                y_line = rect.center().y() + (tooth.size / 2) - 10
                x_left = rect.left() - 5
                x_right = rect.right() + 5

                pen_bridge = QPen(Qt.blue, 4)
                puente_line = self.scene.addLine(x_left, y_line, x_right, y_line, pen_bridge)
                puente_line.setZValue(0)  # que quede detrás
                self.bridge_lines.append(puente_line)

    def apply_batch_states(self, states_list):
        """
        Aplica masivamente los estados parseados a los dientes
        y luego actualiza el dibujado de puentes.
        """
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

        # Reseteamos todo primero
        for row in self.dientes:
            for t in row:
                t.reset_tooth()

        # Aplicamos los estados
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
# Ventana principal con la imagen a la IZQUIERDA del odontograma
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.setWindowTitle("Odontograma")

        ds = self.args.dientes.strip()
        self.locked_mode = bool(ds)  # Si hay algo en 'dientes', bloqueamos edición

        self.odontogram_view = OdontogramView(locked=self.locked_mode)

        # -----------------------------
        # 1) SECCIÓN DATOS DEL PACIENTE
        # -----------------------------
        self.credencialEdit = QLineEdit(self.args.credencial or "")
        self.prestadorEdit  = QLineEdit(self.args.prestador  or "")
        self.titularEdit    = QLineEdit(self.args.titular    or "")
        self.fechaEdit      = QLineEdit(self.args.fecha      or "")
        self.observacionesEdit = QLineEdit(self.args.observaciones or "")
        self.observacionesEdit.setMaxLength(100)

        if self.locked_mode:
            self.credencialEdit.setReadOnly(True)
            self.prestadorEdit.setReadOnly(True)
            self.titularEdit.setReadOnly(True)
            self.fechaEdit.setReadOnly(True)
            self.observacionesEdit.setReadOnly(True)

        formLayout = QFormLayout()
        formLayout.addRow("Credencial:", self.credencialEdit)
        formLayout.addRow("Prestador:", self.prestadorEdit)
        formLayout.addRow("Titular:", self.titularEdit)
        formLayout.addRow("Fecha:", self.fechaEdit)
        formLayout.addRow("Observaciones:", self.observacionesEdit)

        # -----------------------------
        # 2) CREAMOS UN LABEL CON LA IMAGEN
        # -----------------------------
        self.legendLabel = QLabel()  
        pixmap = QPixmap("leyenda.png")  # Cambia aquí a tu archivo .png
        self.legendLabel.setPixmap(pixmap)
        self.legendLabel.setScaledContents(True)  # Si quieres escalar
        self.legendLabel.setFixedWidth(300)       # Para fijar ancho, si es necesario
        self.legendLabel.setFixedHeight(550)  #CONTENEDOR
        # -----------------------------
        # 3) ORGANIZAMOS: IMAGEN IZQUIERDA + ODONTOGRAMA A LA DERECHA
        # -----------------------------
        hLayoutOdon = QHBoxLayout()    
        hLayoutOdon.addWidget(self.legendLabel)       # Imagen
        hLayoutOdon.addWidget(self.odontogram_view)   # Odontograma

        self.state_selector = QComboBox()
        self.state_selector.addItems(ESTADOS.keys())
        self.state_selector.currentTextChanged.connect(self.on_state_changed)
        if self.locked_mode:
            self.state_selector.setEnabled(False)

        # -----------------------------
        # 4) CONSTRUIMOS EL LAYOUT PRINCIPAL
        # -----------------------------
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)       # Datos del paciente (arriba)
        mainLayout.addLayout(hLayoutOdon)      # Imagen + Odontograma lado a lado
        mainLayout.addWidget(QLabel("Estado actual:"))
        mainLayout.addWidget(self.state_selector)

        container = QWidget()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        # Aplica estados si hay 'dientes'
        self.apply_dental_args()

    def on_state_changed(self, new_state):
        self.odontogram_view.set_current_state(new_state)

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
    w = MainWindow(args)
    w.resize(1200, 600)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
